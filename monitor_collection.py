from pymongo import MongoClient
import os
from dotenv import load_dotenv
import time

load_dotenv()

client = MongoClient(os.getenv('MONGO_URI'))
db = client.Documenttask
collection = db.imagesdemo_erl

def monitor_collection():
    while True:
        stats = {
            'total': collection.count_documents({}),
            'legalpassed': collection.count_documents({'status': 'legalpassed'}),
            'mailingpassed': collection.count_documents({'status': 'mailingpassed'}),
            'error': collection.count_documents({'status': 'error'}),
            'pending': collection.count_documents({
                'status': 'legalpassed',
                'mailing_passed': {'$ne': True}
            })
        }
        
        print("\nCollection Status:")
        print(f"Total Documents: {stats['total']}")
        print(f"Legal Passed: {stats['legalpassed']}")
        print(f"Mailing Passed: {stats['mailingpassed']}")
        print(f"Errors: {stats['error']}")
        print(f"Pending Mailing: {stats['pending']}")
        
        time.sleep(5)

if __name__ == "__main__":
    monitor_collection() 