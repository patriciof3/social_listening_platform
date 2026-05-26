import os
import time
import json
from google import genai
from google.genai import types
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

client_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# --- CHUNKING ---
def chunk_text(text, chunk_size=400, overlap=60):
    """Split text into overlapping chunks of ~chunk_size words."""
    words = str(text).split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # overlap so context isn't lost at boundaries
    return chunks


# --- EMBEDDING ---
def get_embedding(text, retries=5):
    for i in range(retries):
        try:
            result = client_gemini.models.embed_content(
                model="gemini-embedding-001",
                contents=text,  # no prefix needed, task_type handles it
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=768
                )
            )
            return result.embeddings[0].values

        except Exception as e:
            error_str = str(e).lower()
            if "quota" in error_str or "resource exhausted" in error_str:
                wait_time = (2 ** i) + 5
                print(f"[RATE LIMIT] Quota exceeded. Waiting {wait_time}s... (attempt {i+1}/{retries})")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] Unexpected error: {e}")
                break

    print("[FAILED] Could not get embedding after all retries.")
    return Nones

# --- MAIN PIPELINE ---
def embed_collection(db_name, collection_name, content_field="content"):
    mongodb_uri = os.getenv("MONGODB_URI")
    mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=30000, socketTimeoutMS=60000)
    source_collection = mongo_client[db_name][collection_name]

    # Store chunks in a separate collection to keep originals clean
    chunks_collection = mongo_client[db_name][f"{collection_name}_chunks"]

    # Count unprocessed docs (resumable — skips already chunked)
    processed_ids = set(doc["original_id"] for doc in chunks_collection.find({}, {"original_id": 1}))
    query = {content_field: {"$exists": True}}
    total = source_collection.count_documents(query)
    print(f"[EMBED] {total} total docs | {len(processed_ids)} already processed")

    done = 0
    failed = 0

    for doc in source_collection.find(query).batch_size(50):
        doc_id = doc["_id"]

        if doc_id in processed_ids:
            print(f"[SKIP] doc {doc_id} already chunked, skipping.")
            continue

        text = doc.get(content_field, "")
        if not text or not str(text).strip():
            print(f"[SKIP] doc {doc_id} has empty {content_field}.")
            failed += 1
            continue

        chunks = chunk_text(text)
        print(f"[CHUNK] doc {doc_id} → {len(chunks)} chunks")

        doc_chunks = []
        for i, chunk in enumerate(chunks):
            vector = get_embedding(chunk)

            if vector:
                doc_chunks.append({
                    "original_id": doc_id,
                    "chunk_id": i,
                    "title": doc.get("title", ""),
                    "date": doc.get("date", ""),
                    "link": doc.get("link", ""),
                    "media": doc.get("media", ""),
                    "text_content": chunk,
                    "embedding": vector
                })
            else:
                print(f"[FAILED] chunk {i} of doc {doc_id} could not be embedded.")
                failed += 1

        if doc_chunks:
            chunks_collection.insert_many(doc_chunks)
            done += 1
            print(f"[DONE] {done} docs processed so far (doc: {doc_id})")

        time.sleep(0.5)  # rate limiting

    mongo_client.close()
    print(f"\n[EMBED] Finished. {done} docs embedded, {failed} failed/skipped out of {total} total.")


# Run it
embed_collection("social_listening", "drugtrafficking")