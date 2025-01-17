import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd

def upload_dataframe_to_mongodb(df, mongodb_uri, db_name, collection_name, unique_field):
    """
    Uploads data from a DataFrame to a MongoDB collection, ensuring no duplicates 
    based on the specified unique field.

    Parameters:
    - df (pd.DataFrame): The DataFrame containing data to upload.
    - mongodb_uri (str): The MongoDB connection URI.
    - db_name (str): The name of the database.
    - collection_name (str): The name of the collection.
    - unique_field (str): The field to check for duplicates (e.g., 'link').

    Returns:
    - dict: A summary of the operation with counts of inserted and skipped documents.
    """
    # Connect to MongoDB
    client = MongoClient(mongodb_uri)
    db = client[db_name]
    collection = db[collection_name]

    # Fetch existing unique field values
    existing_values = set(doc[unique_field] for doc in collection.find({}, {unique_field: 1, "_id": 0}))

    # Filter the DataFrame to exclude duplicates
    df_to_insert = df[~df[unique_field].isin(existing_values)]

    # Insert new documents
    if not df_to_insert.empty:
        collection.insert_many(df_to_insert.to_dict(orient="records"))

    # Return a summary of the operation
    return {
        "inserted_count": len(df_to_insert),
        "skipped_count": len(df) - len(df_to_insert)
    }

def reading_data(db, collection):

    mongodb_uri = os.getenv("MONGODB_URI")

    client = MongoClient(mongodb_uri, server_api=ServerApi('1'))
    # Send a ping to confirm a successful connection

# Specify the database and collection
    db = client[db]
    collection = db[collection]

    data = list(collection.find())

    # Convert to DataFrame
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])

    # df['content'] = df['content'].astype(str)
    # df['content'] = df['content'].str.replace('\n', ' ')
    # df['content'] = df['content'].str.replace(r"[\[\]\'/\\]", "", regex=True)

    return df