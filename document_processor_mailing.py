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

# Load environment variables
load_dotenv()

# Initialize AWS and Claude clients
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION = os.getenv('AWS_REGION')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "admin"
COLLECTION_NAME = "images"
OUTPUT_COLLECTION = "output_legal"

if not all([ACCESS_KEY, SECRET_KEY, REGION, ANTHROPIC_API_KEY, MONGO_URI]):
    raise ValueError("Required credentials not found in environment variables")

# Initialize clients
textract_client = boto3.client(
    'textract',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION
)

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# MongoDB setup with error handling
try:
    mongo_client = MongoClient(MONGO_URI)
    # Test the connection
    mongo_client.admin.command('ping')
    print("Successfully connected to MongoDB")
    
    db = mongo_client.Documenttask
    collection = db.imagesdemo_erl
    
except Exception as e:
    print(f"Error connecting to MongoDB: {str(e)}")
    print("Please check your MONGO_URI in .env file")
    print("Current MONGO_URI:", MONGO_URI)
    raise

# Define required fields at module level
REQUIRED_FIELDS = [
    "Mailing_Address_Level", "Care_Of", "House_Number_Alpha", "House_Alpha", 
    "Pre_Direction", "Street_Name", "Street_Suffix", "Post_Direction", 
    "Unit_Designator", "Unit_Number", "City", "State", "Zip", "Zip_4",
    "Carrier_Route", "Latitude", "Longitude", "Census_Tract_block"
]

def generate_header():
    """Generate header for mailing output file"""
    return "ImageName|BatchName|ImageHeaderID|Mailing_Address_Level|Care_Of|House_Number_Alpha|House_Alpha|Pre_Direction|Street_Name|Street_Suffix|Post_Direction|Unit_Designator|Unit_Number|City|State|Zip|Zip_4|Carrier_Route|Latitude|Longitude|Census_Tract_block|CL_Mailing_Address_Level|CL_Care_Of|CL_House_Number_Alpha|CL_House_Alpha|CL_Pre_Direction|CL_Street_Name|CL_Street_Suffix|CL_Post_Direction|CL_Unit_Designator|CL_Unit_Number|CL_City|CL_State|CL_Zip|CL_Zip_4|CL_Carrier_Route|CL_Latitude|CL_Longitude|CL_Census_Tract_block|ReferenceId|SourceId"

def format_output(image_name: str, batch_name: str, image_header_id: str, processed_data: Dict) -> str:
    """Format output line with all fields"""
    fields = [image_name, batch_name, image_header_id]
    
    # Add all data fields
    data_fields = ["Mailing_Address_Level", "Care_Of", "House_Number_Alpha", "House_Alpha", 
                  "Pre_Direction", "Street_Name", "Street_Suffix", "Post_Direction", 
                  "Unit_Designator", "Unit_Number", "City", "State", "Zip", "Zip_4",
                  "Carrier_Route", "Latitude", "Longitude", "Census_Tract_block"]
    
    # Add values
    for field in data_fields:
        value = processed_data.get(field, {}).get('value', 'NONE')
        fields.append(str(value))
    
    # Add confidence levels
    for field in data_fields:
        confidence = processed_data.get(field, {}).get('confidence', 0)
        fields.append("HIGH" if confidence >= 90 else "LOW")
    
    # Add empty ReferenceId and SourceId
    fields.extend(["", ""])
    
    return "|".join(fields)

def post_process_with_claude(extracted_data: Dict) -> Dict:
    """Process extracted text with Claude 3.5 Sonnet"""
    text = extracted_data["text"]
    if isinstance(text, list):
        text = ' '.join(text)
    text = str(text)
    
    prompt = """You are an expert address parser. Extract the most complete mailing address from the text.

TEXT TO ANALYZE:
{}

CRITICAL REQUIREMENTS:
1. Set Mailing_Address_Level:
   - "FULL_ADDRESS" if street/PO Box, city, state, and ZIP are present
   - "PARTIAL" if some components are present
   - "NONE" if no address found

2. P.O. Box Format:
   - House_Number_Alpha: Exactly "P.O. BOX"
   - Street_Name: Box number only
   - Set other fields appropriately

3. Street Address Format:
   - House_Number_Alpha: Full street number (e.g., "3033")
   - House_Alpha: Letter part of number (e.g., "A" from "123A")
   - Street_Name: Name only (e.g., "SHASTA DAISY")
   - Street_Suffix: Standard abbreviation (e.g., "CIR", "ST", "AVE")
   - Pre/Post_Direction: N, S, E, W, NE, NW, SE, SW only

4. Unit Information:
   - Unit_Designator: Standard type (APT, STE, UNIT, FL, #)
   - Unit_Number: Number/letter only

5. Location Fields:
   - City: Full city name
   - State: Two-letter state code
   - Zip: 5-digit ZIP code (required if present)
   - Zip_4: 4-digit extension if present

6. Care Of / Attention:
   - Care_Of: Full C/O or ATTN line
   - Remove from other fields

ALL VALUES MUST BE UPPERCASE. Use "NONE" for missing fields.
Return a clean JSON object with value and confidence for each field."""

    try:
        message = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0.1,
            system="You are an expert address parser. Return clean, valid JSON with all required fields.",
            messages=[{
                "role": "user", 
                "content": prompt.format(text)
            }]
        )
        
        # Extract and clean JSON response
        response_text = message.content[0].text
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise ValueError("No valid JSON found in response")
            
        json_str = response_text[json_start:json_end]
        parsed_data = json.loads(json_str)
        
        # Ensure all required fields are present
        for field in REQUIRED_FIELDS:
            if field not in parsed_data:
                parsed_data[field] = {
                    "value": "NONE",
                    "confidence": 0,
                    "flags": ["FIELD_NOT_FOUND"]
                }
            elif not isinstance(parsed_data[field], dict):
                parsed_data[field] = {
                    "value": str(parsed_data[field]).upper(),
                    "confidence": 95,
                    "flags": ["VALUE_NORMALIZED"]
                }
        
        return parsed_data
        
    except Exception as e:
        print(f"Claude processing error: {str(e)}")
        return {field: {"value": "NONE", "confidence": 0, "flags": ["PROCESSING_ERROR"]} 
                for field in REQUIRED_FIELDS}

def write_output_file(output_schema: str, output_line: str, batch_name: str):
    """Write output to file with proper directory handling"""
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.join("Outputs", batch_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output file path
        output_file = os.path.join(output_dir, f"{batch_name}_Mailing.txt")
        
        # Write header if file doesn't exist or is empty
        write_header = False
        if not os.path.exists(output_file):
            write_header = True
        else:
            # Check if file is empty or missing header
            with open(output_file, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if not first_line or first_line != output_schema:
                    write_header = True
        
        if write_header:
            # Write header and output line
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_schema + "\n")
                f.write(output_line + "\n")
            print(f"Created new file with header: {output_file}")
        else:
            # Append only output line
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(output_line + "\n")
            print(f"Appended to existing file: {output_file}")
            
    except Exception as e:
        print(f"Error writing output file: {str(e)}")
        raise

def process_ocr_data():
    """Monitor MongoDB collection and process documents with legalpassed status"""
    print("Starting mailing address processing service...")
    print(f"Connected to MongoDB database: {db.name}")
    print(f"Monitoring collection: {collection.name}")
    
    while True:
        try:
            query = {"status": "legalpassed"}
            unprocessed_docs = collection.find(query)
            count = collection.count_documents(query)
            print(f"\nFound {count} documents with legalpassed status")
            
            for doc in unprocessed_docs:
                try:
                    # Debug document structure
                    print(f"\nProcessing document: {doc['_id']}")
                    print("Document fields:", list(doc.keys()))
                    
                    # Try to get OCR text from different possible fields
                    text_content = None
                    
                    # Check ocr_text field first
                    if 'ocr_text' in doc:
                        text_content = doc['ocr_text']
                    # Fallback to ocr_output if needed
                    elif 'ocr_output' in doc:
                        ocr_output = doc['ocr_output']
                        if isinstance(ocr_output, dict):
                            text_content = ocr_output.get('text', '')
                        elif isinstance(ocr_output, list):
                            text_content = ' '.join(str(item) for item in ocr_output)
                        else:
                            text_content = str(ocr_output)
                    
                    # Debug OCR content
                    print("OCR text type:", type(text_content))
                    print("OCR text content:", text_content[:200] if text_content else "No text")
                    
                    if not text_content or not str(text_content).strip():
                        raise ValueError("No valid OCR text found in document")
                    
                    processed_data = post_process_with_claude({"text": str(text_content)})
                    
                    # Debug Claude response
                    print("Claude Response Sample:", json.dumps(processed_data, indent=2)[:200])
                    
                    image_name = doc.get('filename', 'unknown.TIF')
                    batch_name = doc.get('cat_name', '06107-20241205-01')
                    output_schema = generate_header()
                    output_line = format_output(image_name, batch_name, "1", processed_data)
                    
                    # Write output to file
                    write_output_file(output_schema, output_line, batch_name)
                    
                    # Update MongoDB
                    collection.update_one(
                        {"_id": doc['_id']},
                        {"$set": {
                            "status": "mailingpassed",
                            "processed_data": processed_data,
                            "output_legal": {
                                "schema": output_schema,
                                "value": output_line,
                                "processed_at": time.time(),
                                "process_type": "mailing",
                                "metadata": {
                                    "image_name": image_name,
                                    "batch_name": batch_name,
                                    "header_id": "1"
                                },
                                "processing_details": {
                                    "success": True,
                                    "error": None
                                }
                            }
                        }}
                    )
                    
                    print(f"Successfully processed document {doc['_id']}")
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"Error processing document {doc['_id']}: {error_msg}")
                    collection.update_one(
                        {"_id": doc['_id']},
                        {"$set": {
                            "status": "error",
                            "error_message": error_msg
                        }}
                    )
            
            time.sleep(10)
            
        except Exception as e:
            print(f"Error in main processing loop: {str(e)}")
            time.sleep(30)

if __name__ == "__main__":
    try:
        process_ocr_data()
    except KeyboardInterrupt:
        print("\nStopping mailing address processing service...")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
    finally:
        mongo_client.close() 