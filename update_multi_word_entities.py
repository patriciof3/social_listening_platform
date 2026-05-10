import pymongo
import json
from tqdm import tqdm  # optional, for progress bar
import os
# --- CONFIG ---
MONGO_URI = os.getenv("MONGODB_URI")  # change to your MongoDB URI
DB_NAME = "social_listening"
COLLECTION_NAME = "drugtrafficking"
ENTITIES_JSON = "entities.json"

# --- Load multiword entities ---
with open(ENTITIES_JSON, "r", encoding="utf-8") as f:
    ENTITIES = json.load(f)

# --- Connect to MongoDB ---
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --- Helper function ---
def join_entities(text, entities):
    for e in entities:
        text = text.replace(e, e.replace(" ", "_"))
    return text

# --- Update all documents ---
cursor = collection.find({}, {"_id": 1, "cleaned_content": 1})

for doc in tqdm(cursor, desc="Updating documents"):
    updated_text = join_entities(doc.get("cleaned_content", ""), ENTITIES)
    collection.update_one(
        {"_id": doc["_id"]},
        {"$set": {"cleaned_content": updated_text}}
    )

print("All documents updated with multiword entities.")