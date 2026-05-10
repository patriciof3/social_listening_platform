import os
import time
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import _OperationCancelled, ConnectionFailure, ServerSelectionTimeoutError


def upload_dataframe_to_mongodb(df, mongodb_uri, db_name, collection_name, unique_field):
    """
    Uploads data from a DataFrame to a MongoDB collection, ensuring no duplicates
    based on the specified unique field.
    """
    print(f"\n[UPLOAD] Starting upload to '{db_name}.{collection_name}'")
    print(f"[UPLOAD] Total rows in DataFrame: {len(df)}")
    print(f"[UPLOAD] Unique field: '{unique_field}'")

    try:
        client = MongoClient(
            mongodb_uri,
            serverSelectionTimeoutMS=30000,
            socketTimeoutMS=60000,
            connectTimeoutMS=20000
        )
        print("[UPLOAD] MongoDB client created. Pinging server...")
        client.admin.command("ping")
        print("[UPLOAD] Ping successful — connected to MongoDB.")
    except ServerSelectionTimeoutError as e:
        print(f"[UPLOAD ERROR] Could not reach MongoDB server: {e}")
        raise
    except Exception as e:
        print(f"[UPLOAD ERROR] Connection failed: {e}")
        raise

    db = client[db_name]
    collection = db[collection_name]

    # Validate unique field exists in DataFrame
    if unique_field not in df.columns:
        raise ValueError(f"[UPLOAD ERROR] Unique field '{unique_field}' not found in DataFrame columns: {list(df.columns)}")

    print(f"[UPLOAD] Fetching existing '{unique_field}' values from collection...")
    try:
        existing_values = set(
            doc[unique_field]
            for doc in collection.find({}, {unique_field: 1, "_id": 0})
            if unique_field in doc
        )
        print(f"[UPLOAD] Found {len(existing_values)} existing records in collection.")
    except Exception as e:
        print(f"[UPLOAD ERROR] Failed to fetch existing values: {e}")
        raise

    df_to_insert = df[~df[unique_field].isin(existing_values)]
    print(f"[UPLOAD] New records to insert: {len(df_to_insert)}")
    print(f"[UPLOAD] Duplicate records skipped: {len(df) - len(df_to_insert)}")

    if not df_to_insert.empty:
        try:
            collection.insert_many(df_to_insert.to_dict(orient="records"))
            print(f"[UPLOAD] Successfully inserted {len(df_to_insert)} records.")
        except Exception as e:
            print(f"[UPLOAD ERROR] insert_many failed: {e}")
            raise
    else:
        print("[UPLOAD] Nothing to insert — all records already exist.")

    client.close()
    print("[UPLOAD] Connection closed.\n")

    return {
        "inserted_count": len(df_to_insert),
        "skipped_count": len(df) - len(df_to_insert)
    }


def reading_data(db_name, collection_name, retries=3, batch_size=100):
    """
    Reads data from a MongoDB collection into a DataFrame.
    Includes retry logic, batching, and verbose console logging.
    """
    print(f"\n[READ] Starting read from '{db_name}.{collection_name}'")

    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        raise EnvironmentError("[READ ERROR] MONGODB_URI environment variable is not set.")
    print("[READ] MONGODB_URI loaded from environment.")

    client = None
    for attempt in range(1, retries + 1):
        print(f"[READ] Connection attempt {attempt}/{retries}...")
        try:
            client = MongoClient(
                mongodb_uri,
                serverSelectionTimeoutMS=30000,
                socketTimeoutMS=60000,
                connectTimeoutMS=20000
            )
            print("[READ] Pinging MongoDB server...")
            client.admin.command("ping")
            print("[READ] Ping successful — connected.")
            break  # Connection succeeded, exit retry loop

        except ServerSelectionTimeoutError as e:
            print(f"[READ ERROR] Attempt {attempt} — server selection timeout: {e}")
        except ConnectionFailure as e:
            print(f"[READ ERROR] Attempt {attempt} — connection failure: {e}")
        except Exception as e:
            print(f"[READ ERROR] Attempt {attempt} — unexpected error: {e}")

        if attempt < retries:
            wait = 2 ** attempt
            print(f"[READ] Retrying in {wait}s...")
            time.sleep(wait)
        else:
            raise ConnectionError(f"[READ ERROR] All {retries} connection attempts failed.")

    db = client[db_name]
    collection = db[collection_name]

    print(f"[READ] Fetching documents in batches of {batch_size}...")
    data = []
    try:
        cursor = collection.find().batch_size(batch_size)
        for i, doc in enumerate(cursor, start=1):
            data.append(doc)
            if i % batch_size == 0:
                print(f"[READ] ...{i} documents fetched so far")
    except _OperationCancelled as e:
        print(f"[READ ERROR] Operation cancelled mid-read after {len(data)} docs: {e}")
        raise
    except Exception as e:
        print(f"[READ ERROR] Unexpected error during fetch after {len(data)} docs: {e}")
        raise
    finally:
        client.close()
        print("[READ] Connection closed.")

    print(f"[READ] Total documents fetched: {len(data)}")

    if not data:
        print("[READ WARNING] Collection returned 0 documents — returning empty DataFrame.")
        return pd.DataFrame()

    print("[READ] Converting to DataFrame...")
    df = pd.DataFrame(data)
    print(f"[READ] DataFrame shape: {df.shape}")
    print(f"[READ] Columns: {list(df.columns)}")

    if 'date' not in df.columns:
        print("[READ WARNING] 'date' column not found — skipping date conversion.")
    else:
        print("[READ] Parsing 'date' column to datetime...")
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        nat_count = df['date'].isna().sum()
        if nat_count > 0:
            print(f"[READ WARNING] {nat_count} 'date' values could not be parsed and are now NaT.")

    print("[READ] Done.\n")
    return df