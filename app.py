import os
from dotenv import load_dotenv
from document_processor_mailing import process_ocr_data
from ocr_handler import extract_text_from_image
from aws_utils import upload_to_s3, analyze_with_textract
from db_handler import fetch_documents_from_mongo, update_document_status

# Load environment variables
load_dotenv()

def main():
    # Step 1: Fetch documents from MongoDB
    print("Fetching documents from MongoDB...")
    documents = fetch_documents_from_mongo(status="legalpassed")
    if not documents:
        print("No documents found with the specified status.")
        return

    for doc in documents:
        try:
            print(f"\nProcessing document ID: {doc['_id']}")

            # Step 2: Extract OCR text
            image_data = doc.get('image_data', None)
            if image_data:
                ocr_text = extract_text_from_image(image_data)
                print(f"OCR text extracted: {ocr_text[:100]}...")
            else:
                print("No image data found. Skipping this document.")
                continue

            # Step 3: Analyze with AWS Textract
            textract_data = analyze_with_textract(ocr_text)
            print("Textract analysis completed.")

            # Step 4: Process document with Claude
            processed_data = process_ocr_data(textract_data)
            print("Data post-processed with Claude.")

            # Step 5: Update MongoDB status and data
            update_document_status(doc['_id'], "processed", processed_data)
            print("Document status updated in MongoDB.")

            # Step 6: Optional - Upload results to S3
            result_file_path = f"outputs/{doc['_id']}_result.txt"
            upload_to_s3(result_file_path, bucket_name="your-s3-bucket")
            print(f"Results uploaded to S3: {result_file_path}")

        except Exception as e:
            print(f"Error processing document {doc['_id']}: {str(e)}")
            continue

if __name__ == "__main__":
    main()
