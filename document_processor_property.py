import os
from dotenv import load_dotenv
import boto3
import json
from typing import List, Dict
import fitz  # PyMuPDF
from PIL import Image
import io
from anthropic import Anthropic
import concurrent.futures
import logging
from datetime import datetime
from property_processor import format_output, generate_header, FIELD_INSTRUCTIONS, FIELD_GROUPS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('processing.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Initialize AWS clients
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
REGION = os.getenv('AWS_REGION')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

textract_client = boto3.client(
    'textract',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION
)

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)

# System prompt and field instructions remain the same as in your code
# ... (keep your existing FIELD_INSTRUCTIONS and FIELD_GROUPS)

def post_process_with_llm(extracted_data: Dict) -> Dict:
    field_instructions_text = "\n".join([
        f"- {field}:\n"
        f"  Description: {details['description']}\n"
        f"  Format: {details.get('format', 'No specific format')}\n"
        f"  Max Length: {details.get('max_length', 'Not specified')}"
        for field, details in FIELD_INSTRUCTIONS.items()
    ])

    prompt = f"""Analyze the following document text and extract the specified fields. Here are the field specifications:

{field_instructions_text}

Document Text:
{extracted_data.get('text', '')}

EXTRACTION RULES:
1. ALL VALUES MUST BE IN UPPERCASE
2. If a field is not found, set its confidence to 0 and add appropriate flags
3. If a field is found but doesn't match the format specifications, flag it

Return the analysis in JSON format with field_name, value, confidence (0-100), and flags."""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            temperature=0.2,
            system="You are an expert in document analysis and metadata extraction for legal and real estate documents.",
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse the response
        response_text = response.content[0].text
        
        # Extract JSON from response
        start_index = response_text.find('{')
        end_index = response_text.rfind('}') + 1
        
        if start_index == -1 or end_index == 0:
            logging.error("No valid JSON found in response")
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
            logging.error(f"Error parsing JSON: {str(e)}")
            return {field: {"value": None, "confidence": 0, "flags": ["JSON_PARSING_ERROR"]} for field in FIELD_GROUPS}

    except Exception as e:
        logging.error(f"Error calling Claude: {str(e)}")
        return {field: {"value": None, "confidence": 0, "flags": ["CLAUDE_API_ERROR"]} for field in FIELD_GROUPS}

def process_batch(file_paths: List[str], output_file: str):
    """Process a batch of documents concurrently"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_documents, file_path): file_path for file_path in file_paths}
        
        with open(output_file, "a") as f:
            for future in concurrent.futures.as_completed(futures):
                file_path = futures[future]
                try:
                    result = future.result()
                    image_name = os.path.basename(file_path)
                    batch_name = os.path.basename(os.path.dirname(file_path))
                    output_line = format_output(image_name, batch_name, "1", result)
                    f.write(output_line + "\n")
                    logging.info(f"Successfully processed {image_name}")
                except Exception as e:
                    logging.error(f"Error processing {file_path}: {str(e)}")
                    error_output = f"{os.path.basename(file_path)}|{os.path.basename(os.path.dirname(file_path))}|1" + "|ERROR" * (len(FIELD_GROUPS) * 2)
                    f.write(error_output + "\n")

def process_documents(input_directory: str, output_directory: str, batch_size: int = 100):
    """Process all documents in batches"""
    os.makedirs(output_directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_directory, f"processed_documents_{timestamp}.txt")
    
    # Write header
    with open(output_file, "w") as f:
        f.write(generate_header() + "\n")


    # Get all document files
    files = [os.path.join(input_directory, f) for f in os.listdir(input_directory) 
             if f.lower().endswith(('.tif', '.tiff', '.pdf'))]
    
    # Process in batches
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        logging.info(f"Processing batch {i//batch_size + 1} of {len(files)//batch_size + 1}")
        process_batch(batch, output_file)

# Keep your existing helper functions (convert_document_to_images, extract_text_with_textract, 
# format_output, generate_header) as they are

if __name__ == "__main__":
    input_directory = "input/documents"
    output_directory = "output/processed"
    process_documents(input_directory, output_directory, batch_size=100) 