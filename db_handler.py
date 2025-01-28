from pymongo import MongoClient

def fetch_documents_from_mongo(status):
    """
    Fetch documents from MongoDB with a specific status.
    :param status: Status to filter documents
    :return: List of documents
    """
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client.Documenttask
        collection = db.imagesdemo_erl
        return list(collection.find({"status": status}))
    except Exception as e:
        print(f"Error fetching documents: {str(e)}")
        return []

def update_document_status(doc_id, status, processed_data):
    """
    Update document status in MongoDB.
    :param doc_id: Document ID
    :param status: New status
    :param processed_data: Processed data to update
    """
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client.Documenttask
        collection = db.imagesdemo_erl
        collection.update_one(
            {"_id": doc_id},
            {"$set": {"status": status, "processed_data": processed_data}}
        )
        print(f"Document {doc_id} updated successfully.")
    except Exception as e:
        print(f"Error updating document status: {str(e)}")
