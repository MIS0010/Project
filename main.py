import os
import time
from pymongo import MongoClient
from document_processor import LegalDocumentProcessor
from utils import convert_document_to_images, format_output, generate_header, process_document_batch
from config import *

def process_legal_documents():
    """Monitor MongoDB collection and process new legal documents."""
    print("Starting legal document processing service...")
    
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    collection = db[COLLECTION_NAME]
    output_collection = db[OUTPUT_COLLECTION]
    
    processor = LegalDocumentProcessor()
    
    while True:
        try:
            query = {"status": "mailingpassed"}
            unprocessed_docs = list(collection.find(query))
            count = len(unprocessed_docs)
            
            if count == 0:
                print("Waiting for new documents...")
                time.sleep(10)
                continue
            
            print(f"Processing {count} documents in parallel...")
            
            # Initialize output file
            if unprocessed_docs:
                batch_name = unprocessed_docs[0].get('cat_name', '06107-20241205-01')
                output_file = f"Outputs/{batch_name}/{batch_name}_Legal.txt"
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                
                if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                    with open(output_file, "w") as f:
                        f.write(generate_header() + "\n")
            
            # Process documents in parallel
            results = process_document_batch(unprocessed_docs, processor, batch_name)
            
            # Bulk write results
            with open(output_file, "a") as f:
                for result in results:
                    f.write(result["output_line"] + "\n")
                    
                    # Update MongoDB
                    output_collection.insert_one({
                        "original_id": result["doc_id"],
                        "filename": result["image_name"],
                        "batch_name": result["batch_name"],
                        "processed_at": time.time(),
                        "output": result["output_line"],
                        "processed_data": result["processed_data"],
                        "status": "legalpassed"
                    })
                    
                    collection.update_one(
                        {"_id": result["doc_id"]},
                        {"$set": {
                            "status": "legalpassed",
                            "processed": True,
                            "processed_data": result["processed_data"]
                        }}
                    )
            
            print(f"Successfully processed {len(results)} documents")
            
        except Exception as e:
            print(f"Error in main processing loop: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    process_legal_documents() 