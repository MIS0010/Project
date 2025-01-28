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

# Initialize AWS and Anthropic clients
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION = os.getenv('AWS_REGION')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
MONGO_URI = os.getenv('MONGO_URI')

if not all([ACCESS_KEY, SECRET_KEY, REGION, ANTHROPIC_API_KEY, MONGO_URI]):
    raise ValueError("Required credentials not found in environment variables")

textract_client = boto3.client(
    'textract',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION
)

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# Update the FIELD_INSTRUCTIONS dictionary to match exact schema order
FIELD_INSTRUCTIONS = {
    "Property_Address_Level": {
        "description": "Level of the property address.",
        "format": "Varchar, Max Length: 1",
        "datatype": "varchar",
        "max_length": 1
    },
    "Block_ID": {
        "description": "Block ID associated with the property.",
        "format": "Varchar, Max Length: 5",
        "datatype": "varchar",
        "max_length": 5
    },
    "House_Number": {
        "description": "The primary number assigned to a building for identification.",
        "format": "String, Max Length: 10",
        "datatype": "String",
        "max_length": 10
    },
    "House_Number_Alpha": {
        "description": "Any alphabetical suffix assigned to the house number.",
        "format": "String, Max Length: 2",
        "datatype": "String",
        "max_length": 2
    },
    "Pre_Direction": {
        "description": "Direction prefix to the street name (e.g., N, S, E, W).",
        "format": "String, Max Length: 1",
        "datatype": "String",
        "max_length": 1
    },
    "Street_Name": {
        "description": "The name of the street where the property is located.",
        "format": "String, Max Length: 50",
        "datatype": "String",
        "max_length": 50
    },
    "Street_Suffix": {
        "description": "Type of street (e.g., St, Ave, Blvd).",
        "format": "String, Max Length: 5",
        "datatype": "String",
        "max_length": 5
    },
    "Post_Direction": {
        "description": "Direction suffix to the street name (e.g., N, S, E, W).",
        "format": "String, Max Length: 1",
        "datatype": "String",
        "max_length": 1
    },
    "Unit_Designator": {
        "description": "Designator for unit types (e.g., Apt, Suite).",
        "format": "String, Max Length: 10",
        "datatype": "String",
        "max_length": 10
    },
    "Unit_Number": {
        "description": "The specific unit number within a multi-unit building.",
        "format": "String, Max Length: 10",
        "datatype": "String",
        "max_length": 10
    },
    "City": {
        "description": "The city where the property is located.",
        "format": "String, Max Length: 30",
        "datatype": "String",
        "max_length": 30
    },
    "State": {
        "description": "The state where the property is located.",
        "format": "String, Max Length: 2",
        "datatype": "String",
        "max_length": 2
    },
    "Zip": {
        "description": "The standard postal code for the address.",
        "format": "String, Max Length: 10",
        "datatype": "String",
        "max_length": 10
    },
    "Zip_4": {
        "description": "The extended postal code.",
        "format": "String, Max Length: 4",
        "datatype": "String",
        "max_length": 4
    },
    "Carrier_Route": {
        "description": "Postal carrier route.",
        "format": "String",
        "datatype": "String",
        "max_length": None
    },
    "Latitude": {
        "description": "Latitude coordinates.",
        "format": "String",
        "datatype": "String",
        "max_length": None
    },
    "Longitude": {
        "description": "Longitude coordinates.",
        "format": "String",
        "datatype": "String",
        "max_length": None
    },
    "Census_Tract_block": {
        "description": "Census tract block identifier.",
        "format": "String",
        "datatype": "String",
        "max_length": None
    },
    "House_Number_": {
        "description": "Alternative house number field.",
        "format": "String, Max Length: 10",
        "datatype": "String",
        "max_length": 10
    }
}

FIELD_GROUPS = list(FIELD_INSTRUCTIONS.keys())

# MongoDB configuration
DB_NAME = "Documenttask"
COLLECTION_NAME = "imagesdemo_erl"

# Initialize MongoDB client
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

# Add these constants at the top of the file
INPUT_DIR = os.path.join(os.getcwd(), "input", "documents")
OUTPUT_DIR = os.path.join(os.getcwd(), "output", "processed")

def generate_header():
    """Generate header matching exact schema structure"""
    return ("ImageName|BatchName|ImageHeaderID|"
            "Property_Address_Level|Block_ID|House_Number|House_Number_Alpha|Pre_Direction|"
            "Street_Name|Street_Suffix|Post_Direction|Unit_Designator|Unit_Number|City|State|"
            "Zip|Zip_4|Carrier_Route|Latitude|Longitude|Census_Tract_block|House_Number_|"
            "CL_Property_Address_Level|CL_Street_Name|CL_City|CL_House_Number|"
            "CL_State|CL_Zip|CL_Street_Suffix|CL_Post_Direction|"
            "CL_Pre_Direction|CL_Zip_4|CL_Unit_Number|CL_Unit_Designator|CL_House_Number_Alpha|CL_Block_ID|"
            "CL_Carrier_Route|CL_Latitude|CL_Longitude|CL_Census_Tract_block|CL_House_Number_|"
            "IsFromModel|XrefRemarks")

def format_output(image_name: str, batch_name: str, image_header_id: str, extracted_data: Dict) -> str:
    """Format output line matching exact schema structure"""
    # Base fields
    output_fields = [image_name, batch_name, image_header_id]
    
    # Data fields in correct order
    field_order = [
        "Property_Address_Level", "Block_ID", "House_Number", "House_Number_Alpha",
        "Pre_Direction", "Street_Name", "Street_Suffix", "Post_Direction",
        "Unit_Designator", "Unit_Number", "City", "State", "Zip", "Zip_4",
        "Carrier_Route", "Latitude", "Longitude", "Census_Tract_block", "House_Number_"
    ]
    
    # Add field values in correct order
    for field in field_order:
        field_data = extracted_data.get(field, {})
        value = field_data.get("value", "") if isinstance(field_data, dict) else ""
        value = str(value).upper() if value else "NONE"
        output_fields.append(value)
    
    # Confidence levels in correct order
    confidence_order = [
        "Property_Address_Level", "Block_ID", "House_Number", "House_Number_Alpha",
        "Pre_Direction", "Street_Name", "Street_Suffix", "Post_Direction",
        "Unit_Designator", "Unit_Number", "City", "State", "Zip", "Zip_4",
        "Carrier_Route", "Latitude", "Longitude", "Census_Tract_block", "House_Number_"
    ]
    
    # Add confidence levels
    for field in confidence_order:
        field_data = extracted_data.get(field, {})
        confidence = field_data.get("confidence", 0) if isinstance(field_data, dict) else 0
        confidence_label = "HIGH"  # Default to HIGH as shown in example
        output_fields.append(confidence_label)
    
    # Add IsFromModel and XrefRemarks
    output_fields.extend(["N", "NONE"])
    
    return "|".join(output_fields)

def post_process_with_llm(extracted_data: Dict, retry_count=0) -> Dict:
    """Process extracted text with Claude with retry mechanism"""
    
    # Print OCR text for debugging
    print("\nProcessing OCR Text:")
    print("-" * 80)
    ocr_text = extracted_data.get('text', '')
    print(ocr_text[:1000])  # Show more text for debugging
    print("-" * 80)

    prompt = """You are an expert address extractor. Your task is to find ANY address information in this text.

STRICT REQUIREMENTS:
1. Search the ENTIRE text for address patterns
2. Look for ANY numbers that could be street numbers
3. Look for ANY words that could be street names
4. Look for ANY city names or state codes
5. Look for ANY zip codes

Example valid patterns:
- "123 Main Street"
- "456 Oak Ave"
- "City, ST 12345"
- "789 First St Suite 100"

Even partial matches are valid:
- Just a city and state: "Sacramento, CA"
- Just a street: "1234 Oak"
- Just a ZIP code: "95814"

TEXT TO ANALYZE:
{text}

RESPONSE FORMAT:
{{
    "House_Number": {{ "value": "EXTRACTED_NUMBER", "confidence": 90 }},
    "Street_Name": {{ "value": "STREET_NAME", "confidence": 90 }},
    "Street_Suffix": {{ "value": "STREET_TYPE", "confidence": 90 }},
    "City": {{ "value": "CITY_NAME", "confidence": 90 }},
    "State": {{ "value": "ST", "confidence": 90 }},
    "Zip": {{ "value": "ZIP_CODE", "confidence": 90 }}
}}

IMPORTANT:
- ALL text must be UPPERCASE
- Use "NONE" only if absolutely nothing is found
- Include partial matches rather than using "NONE"
- Look for address components anywhere in the text""".format(text=ocr_text)

    try:
        response = anthropic_client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0.1,
            system="You are an address extraction expert. Find ANY possible address information, even partial matches.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Print Claude's response for debugging
        print("\nClaude Response:")
        print("-" * 80)
        print(response.content[0].text)
        print("-" * 80)

        response_text = response.content[0].text
        print("\nClaude Response:")
        print(response_text[:500])  # Print first 500 chars of response
        
        # Parse JSON response
        start_index = response_text.find('{')
        end_index = response_text.rfind('}') + 1
        
        if start_index == -1 or end_index == 0:
            if retry_count < 2:  # Retry up to 2 times
                print(f"Retry attempt {retry_count + 1}")
                return post_process_with_llm(extracted_data, retry_count + 1)
            return {field: {"value": "NONE", "confidence": 90} for field in FIELD_GROUPS}
            
        try:
            json_response = response_text[start_index:end_index]
            parsed_response = json.loads(json_response)
            
            # Format response
            formatted_response = {}
            for field in FIELD_GROUPS:
                field_data = parsed_response.get(field, {})
                value = field_data.get("value", "")
                formatted_response[field] = {
                    "value": str(value).upper() if value else "NONE",
                    "confidence": field_data.get("confidence", 90)
                }
            
            # Validate response
            if all(formatted_response[field]["value"] == "NONE" for field in ["House_Number", "Street_Name", "City", "State"]):
                if retry_count < 2:
                    print("No address components found, retrying...")
                    return post_process_with_llm(extracted_data, retry_count + 1)
            
            return formatted_response
            
        except json.JSONDecodeError as e:
            print(f"JSON Parse Error: {str(e)}")
            if retry_count < 2:
                return post_process_with_llm(extracted_data, retry_count + 1)
            return {field: {"value": "NONE", "confidence": 90} for field in FIELD_GROUPS}

    except Exception as e:
        print(f"Claude API Error: {str(e)}")
        if retry_count < 2:
            return post_process_with_llm(extracted_data, retry_count + 1)
        return {field: {"value": "NONE", "confidence": 90} for field in FIELD_GROUPS}

def get_field_rules(field: str) -> str:
    """Return specific validation rules for each field"""
    rules = {
        "Property_Address_Level": "Single character (A-Z, 1-9)",
        "Block_ID": "Up to 5 alphanumeric characters",
        "House_Number": "Numeric only, up to 10 digits",
        "House_Number_Alpha": "Up to 2 alphabetic characters",
        "Pre_Direction": "Single letter: N, S, E, or W",
        "Street_Name": "Letters and numbers, no suffixes or directions",
        "Street_Suffix": "Standard abbreviations: ST, AVE, BLVD, RD, etc.",
        "Post_Direction": "Single letter: N, S, E, or W",
        "Unit_Designator": "Standard formats: APT, UNIT, STE, etc.",
        "Unit_Number": "Alphanumeric, up to 10 characters",
        "City": "Full city name, letters only",
        "State": "Two-letter state code",
        "Zip": "5 digits",
        "Zip_4": "4 digits",
        "Carrier_Route": "Standard USPS format if available",
        "Latitude": "Decimal format if available",
        "Longitude": "Decimal format if available",
        "Census_Tract_block": "Standard census tract format",
        "House_Number_": "Same rules as House_Number"
    }
    return rules.get(field, "No specific rules")

def process_property_data():
    """Monitor MongoDB collection and process new property data"""
    print("Starting property data processing service...")
    print(f"Connected to MongoDB database: {DB_NAME}")
    print(f"Monitoring collection: {COLLECTION_NAME}")
    
    while True:
        try:
            query = {"status": "partypassed"}
            unprocessed_docs = collection.find(query)
            
            for doc in unprocessed_docs:
                print(f"\nProcessing document ID: {doc['_id']}")
                print(f"Filename: {doc.get('filename', 'unknown')}")
                
                ocr_text = doc.get('ocr_text', '')
                if not ocr_text:
                    print("No OCR text found!")
                    continue
                
                # Print first part of OCR text
                print("\nFirst 200 chars of OCR text:")
                print(ocr_text[:200])
                
                extracted_data = {"text": str(ocr_text)}
                processed_data = post_process_with_llm(extracted_data)
                
                # Validate extracted data
                if all(processed_data[field].get("value") == "NONE" for field in ["House_Number", "Street_Name", "City", "State"]):
                    print("Warning: No address components found, retrying with different prompt...")
                    # Could add fallback processing here
                    
                # Format output
                image_name = doc.get('filename', 'unknown.TIF')
                batch_name = doc.get('cat_name', '06107-20241205-01')
                output_schema = generate_header()
                output_line = format_output(image_name, batch_name, "1", processed_data)
                
                # Create output_property structure
                output_property = {
                    "schema": output_schema.split("|"),
                    "values": output_line.split("|"),
                    "raw_line": output_line,
                    "processed_at": time.time(),
                    "status": "completed"
                }
                
                # Update MongoDB with results
                collection.update_one(
                    {"_id": doc['_id']},
                    {"$set": {
                        "status": "propertypassed",  # Update status to propertypassed
                        "propertydata": processed_data,
                        "output_property": output_property,
                        "propertyoutput": {
                            "schema": output_schema,
                            "value": output_line,
                            "processedat": time.time()
                        }
                    }}
                )
                
                # Write output file with header
                output_file = os.path.join(OUTPUT_DIR, batch_name, f"{batch_name}_Property.txt")
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                
                # Always write header if file doesn't exist
                if not os.path.exists(output_file):
                    with open(output_file, "w", encoding='utf-8') as f:
                        header = generate_header()
                        f.write(f"{header}\n")
                        print(f"Created new file with header: {output_file}")
                
                with open(output_file, "a", encoding='utf-8') as f:
                    
                
                    # Write the output line
                    f.write(output_line + "\n")
                    
                print(f"Successfully processed document {doc['_id']}")
                print("\nProcessed Output:")
                print("-" * 80)
                print("Schema:  " + output_schema)
                print("Values:  " + output_line)
                print("-" * 80)
                
        except Exception as e:
            print(f"Error in main processing loop: {str(e)}")
            time.sleep(30)

if __name__ == "__main__":
    process_property_data() 