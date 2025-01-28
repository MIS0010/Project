import boto3
from anthropic import Anthropic
from PIL import Image
import io
import json
from typing import List, Dict
from config import *
from field_definitions import FIELD_INSTRUCTIONS, FIELD_GROUPS

class LegalDocumentProcessor:
    def __init__(self):
        self.textract_client = boto3.client(
            'textract',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        self.anthropic = Anthropic(api_key=ANTHROPIC_API_KEY)

    def extract_text_with_textract(self, images: List[Image.Image]) -> Dict:
        """Process images with AWS Textract and return combined text."""
        combined_text = ""
        
        for page_num, image in enumerate(images, start=1):
            image_byte_array = io.BytesIO()
            image.save(image_byte_array, format="PNG")
            image_bytes = image_byte_array.getvalue()

            response = self.textract_client.analyze_document(
                Document={'Bytes': image_bytes},
                FeatureTypes=['TABLES', 'FORMS']
            )

            combined_text += f"\n=== PAGE {page_num} ===\n"
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    combined_text += block['Text'] + "\n"
        
        return {"text": combined_text}

    def post_process_with_llm(self, extracted_data: Dict) -> Dict:
        # Add document structure hints
        text = extracted_data.get('text', '')
        structured_text = f"""DOCUMENT ANALYSIS REQUEST:

Document Content:
{text}

Please analyze this legal document and extract all required fields.
Pay special attention to:
1. Document type indicators in the header
2. Legal description sections
3. Property identifiers
4. Map references
5. Recording information

"""
        field_instructions_text = "\n".join([
            f"- {field}:\n"
            f"  Description: {details['description']}\n"
            f"  Format: {details.get('format', 'No specific format')}\n"
            f"  Max Length: {details.get('max_length', 'Not specified')}\n"
            f"  Required Format Examples: {details.get('examples', 'N/A')}"
            for field, details in FIELD_INSTRUCTIONS.items()
        ])

        prompt = get_extraction_prompt(structured_text, field_instructions_text)
        
        try:
            message = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4096,
                temperature=0.1,
                top_p=0.9,
                top_k=50,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            print(897,response_text)
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            
            if start_index == -1 or end_index == 0:
                return {field: {"value": None, "confidence": 0, "flags": ["EXTRACTION_FAILED"]} 
                        for field in FIELD_GROUPS}
            
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

        except Exception as e:
            print(f"Error in LLM processing: {str(e)}")
            return {field: {"value": None, "confidence": 0, "flags": ["LLM_PROCESSING_ERROR"]}
                    for field in FIELD_GROUPS} 
            