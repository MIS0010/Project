import os
from dotenv import load_dotenv
import boto3
import json
from typing import List, Dict
from PIL import Image
import io
from anthropic import Anthropic
from pymongo import MongoClient
import time
import re

load_dotenv()

ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION = os.getenv('AWS_REGION')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

if not (ACCESS_KEY and SECRET_KEY and REGION and ANTHROPIC_API_KEY):
    raise ValueError("Required credentials not found in environment variables")

textract_client = boto3.client(
    'textract',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION
)

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY) 

FIELD_INSTRUCTIONS = {
    "APN_Level": {
        "description": "The hierarchical level in the APN structure, almost always 'A' in these documents.",
        "datatype": "varchar",
        "max_length": 1,
        "format": "Single character 'A'",
        "required": True
    },
    "APN_AIN": {
        "description": "Assessor's Identification Number (APN/Parcel ID) in various formats",
        "datatype": "varchar",
        "max_length": 50,
        "format": "Can be: XXX-XXX-XXX-XXX, XXXXXXXXXX, XXXX-XXXXXXX-XX",
        "required": True
    }
}

FIELD_GROUPS = list(FIELD_INSTRUCTIONS.keys())

system_prompt = '''You are an expert APN (Assessor's Parcel Number) extraction system. Your primary task is to identify and extract APN information from real estate documents with extremely high accuracy.

Key Requirements:
1. ALWAYS extract APN_Level as "A" unless explicitly different in the document
2. Look for APN_AIN numbers in these formats:
    - XXX-XXX-XXX-XXX (dashed format)
    - XXXXXXXXXX (continuous numbers)
    - XXXX-XXXXXXX-XX (year-sequence format)
    
3. Common indicators of APN/Parcel numbers:
    - Near terms like "APN:", "Parcel:", "PIN:", "Property ID:"
    - Often found in document headers or top sections
    - Usually formatted distinctly from other numbers
    - May be preceded by "Book", "Page", or "Map" references

4. Set confidence levels:
    - HIGH: When number clearly matches APN patterns
    - LOW: Only when uncertain or pattern doesn't match

Accuracy is critical - extract with high confidence when patterns match known APN formats.'''

def generate_header():
    # Return the exact header format with pipe separators
    return "ImageName|BatchName|ImageHeaderID|APN_Level|APN_AIN|CL_APN_Level|CL_APN_AIN"

def format_output(image_name: str, batch_name: str, image_header_id: str, extracted_data: Dict) -> str:
    # Initialize list to store all fields
    output_fields = [image_name, batch_name, image_header_id]
    
    # Add APN_Level and APN_AIN values
    for field in FIELD_GROUPS:
        field_data = extracted_data.get(field, {})
        value = field_data.get("value", "") if isinstance(field_data, dict) else ""
        value = str(value) if value is not None else ""
        output_fields.append(value)
        
        confidence = field_data.get("confidence", 0) if isinstance(field_data, dict) else 0
        confidence_label = "HIGH" if confidence >= 90 else "LOW"
        output_fields.append(confidence_label)
        
        output_fields.extend(["", ""])  # Add empty Confidence Scores (CS_)
    
    return "|".join(output_fields)

def post_process_with_llm(extracted_data: Dict) -> Dict:
    prompt = f"""Analyze this document text and extract APN information with high accuracy.

CRITICAL REQUIREMENTS:
1. APN_Level should ALWAYS be "A" with HIGH confidence unless explicitly different
2. For APN_AIN, look for numbers that match these patterns:
    - XXX-XXX-XXX-XXX (e.g., 492-050-006-000)
    - XXXXXXXXXX (e.g., 0009843004)
    - XXXX-XXXXXXX-XX (e.g., 2024-0067300-00)

3. Look specifically for:
    - Numbers near terms like "APN:", "Parcel:", "PIN:", "Assessment Number:"
    - Numbers in document headers or top sections
    - Distinctly formatted number sequences
    - Numbers following "Book", "Page", or "Map" references

4. Confidence Scoring:
    - Set HIGH confidence (95) when number matches known APN patterns
    - Set HIGH confidence (95) for APN_Level when "A" is appropriate
    - Only use LOW confidence if truly uncertain

Document Text to Analyze:
{extracted_data.get('text', '')}

RESPOND IN THIS EXACT FORMAT:
{{
    "APN_Level": {{
        "value": "A",
        "confidence": 95,
        "flags": ["STANDARD_APN_LEVEL"]
    }},
    "APN_AIN": {{
        "value": "EXTRACTED_NUMBER",
        "confidence": 95,
        "flags": ["MATCHES_APN_PATTERN"]
    }}
}}

IMPORTANT: 
- ALL VALUES MUST BE UPPERCASE
- ALWAYS include APN_Level as "A" unless explicitly different
- Extract ANY number matching APN patterns, even without explicit "APN" label
- Pay special attention to numbers in standard APN formats
"""
    try:
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = response.content[0].text

        start_index = response_text.find('{')
        end_index = response_text.rfind('}') + 1

        if start_index == -1 or end_index == 0:
            print("Error: No valid JSON found in response")
            return {field: {"value": None, "confidence": 0, "flags": ["EXTRACTION_FAILED"]} for field in FIELD_GROUPS}

        try:
            json_response = response_text[start_index:end_index]
            parsed_response = json.loads(json_response)

            formatted_response = {}
            for field in FIELD_GROUPS:
                field_data = parsed_response.get(field, {})
                formatted_response[field] = {
                    "value": str(field_data.get("value", "")).upper() if field_data.get("value") else "",
                    "confidence": field_data.get("confidence", 0),
                    "flags": [str(flag).upper() for flag in field_data.get("flags", ["NO_FLAGS"])]
                }
            return formatted_response

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {str(e)}")
            
    except Exception as e:
        print(f"Error calling Claude API: {str(e)}")
        return {field: {"value": None, "confidence": 0, "flags": ["CLAUDE_API_ERROR"]} for field in FIELD_GROUPS} 

def process_images(image_directory: str, output_file: str):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w") as f:
        # Write header
        header = generate_header()
        f.write(header + "\n")

        for image_name in os.listdir(image_directory):
            if image_name.lower().endswith(('.tif', '.tiff')):  # Removed .pdf since sample only shows .TIF
                print(f"\nProcessing file: {image_name}")
                image_path = os.path.join(image_directory, image_name)
                
                try:
                    extracted_data = process_document(image_path)
                    batch_name = os.path.basename(image_directory)
                    image_header_id = "1"

                    output_line = format_output(image_name, batch_name, image_header_id, extracted_data)
                    f.write(output_line + "\n")
                    print(f"Successfully processed {image_name}")
                except Exception as e:
                    print(f"Error processing {image_name}: {str(e)}")
                    # Create error output line with pipe separators
                    error_fields = [image_name, os.path.basename(image_directory), "1"]
                    error_fields.extend(["ERROR"] * 6)  # For the remaining 6 fields
                    f.write("|".join(error_fields) + "\n")

def process_document(file_path: str) -> Dict:
    """Process a document file and extract text using Textract and Claude."""
    # Convert document to images first
    images = convert_document_to_images(file_path)
    
    # Process with Textract
    print("Processing Textract...")
    extracted_data = extract_text_with_textract(images)
    
    # Process with Claude
    print("Processing with Claude...")
    processed_data = post_process_with_llm(extracted_data)
    
    return processed_data

def extract_text_with_textract(images: List[Image.Image]) -> Dict:
    """Process images with AWS Textract and return combined text."""
    combined_text = ""
    
    for page_num, image in enumerate(images, start=1):
        # Convert image to bytes
        image_byte_array = io.BytesIO()
        image.save(image_byte_array, format="PNG")
        image_bytes = image_byte_array.getvalue()

        # Call AWS Textract
        response = textract_client.analyze_document(
            Document={'Bytes': image_bytes},
            FeatureTypes=['TABLES', 'FORMS']
        )

        # Extract text
        combined_text += f"\n=== PAGE {page_num} ===\n"
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                combined_text += block['Text'] + "\n"
    
    return {"text": combined_text}

def convert_document_to_images(file_path: str) -> List[Image.Image]:
    """Convert TIFF file to list of images."""
    images = []
    with Image.open(file_path) as img:
        for i in range(getattr(img, 'n_frames', 1)):
            try:
                img.seek(i)
                images.append(img.copy())
            except EOFError:
                break
    return images

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "admin"
COLLECTION_NAME = "images"
OUTPUT_COLLECTION = "output_legal"

def process_ocr_data():
    """Monitor MongoDB collection and process new OCR data."""
    print("Starting OCR data processing service...")
    
    # Initialize MongoDB
    try:
        client = MongoClient(MONGO_URI)
        database = client[DB_NAME]
        collection = database[COLLECTION_NAME]
        print(f"Connected to MongoDB database: {DB_NAME}")
        print(f"Monitoring collection: {COLLECTION_NAME}")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return  # Exit the function if MongoDB connection fails

    while True:
        try:
            # Query for documents to process
            query = {"status": "ocrpassed", "apnpassed": {"$exists": False}}
            unprocessed_docs = collection.find(query)
            count = collection.count_documents(query)
            print(f"\nFound {count} unprocessed documents with OCR passed")

            if count == 0:
                print("Waiting for new documents with OCR passed status...")
                time.sleep(10)
                continue

            # Process each document
            for doc in unprocessed_docs:
                try:
                    print(f"\nProcessing document ID: {doc['_id']}")
                    print(f"Document fields: {list(doc.keys())}")

                    # Extract text from OCR output
                    ocr_output = doc.get('ocr_text', None)
                    if not ocr_output:
                        print(f"Warning: No ocr_text field found in document {doc['_id']}")
                        continue
                    
                    print(f"OCR output type: {type(ocr_output)}")

                    # Process with Claude (ensure post_process_with_llm is defined elsewhere)
                    extracted_data = {"text": str(ocr_output)}
                    processed_data = post_process_with_llm(extracted_data)  # Ensure this function exists
                    
                    # Prepare output
                    image_name = doc.get('filename', 'unknown.TIF')
                    batch_name = doc.get('foldername', 'default_batch')
                    image_header_id = "1"
                    
                    output_schema = generate_header()  # Ensure this function exists
                    output_line = format_output(image_name, batch_name, image_header_id, processed_data)

                    # Print formatted output
                    print("\nProcessed Output:")
                    print("-" * 80)
                    print(f"Schema:  {output_schema}")
                    print(f"Values:  {output_line}")
                    print("-" * 80)

                    # Update MongoDB
                    collection.update_one(
                        {"_id": doc['_id']},
                        {"$set": {
                            "status": "apnpassed",
                            "processeddata": processed_data,
                            "apnoutput": {
                                "schema": output_schema,
                                "value": output_line,
                                "processedat": time.time()
                            }
                        }}
                    )
                    
                    # Save to output file
                    output_file = f"Outputs/{batch_name}/{batch_name}_APN.txt"
                    os.makedirs(os.path.dirname(output_file), exist_ok=True)

                    # Write to file
                    with open(output_file, "a") as f:
                        if os.path.getsize(output_file) == 0:  # File is empty
                            f.write(output_schema + "\n")  # Write header
                        f.write(output_line + "\n")  # Append data

                    print(f"Successfully processed document {doc['_id']}")

                except Exception as e:
                    print(f"Error processing document {doc['_id']}: {e}")
                    collection.update_one(
                        {"_id": doc['_id']},
                        {"$set": {
                            "status": "apnfailed",
                            "apnerror": str(e),
                            "apnoutput": {
                                "error": str(e),
                                "processedat": time.time()
                            }
                        }}
                    )

            time.sleep(10)

        except Exception as e:
            print(f"Error in main processing loop: {e}")
            time.sleep(30)


if __name__ == "__main__":
    process_ocr_data() 