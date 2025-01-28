import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# AWS Configuration
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')

# Anthropic Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "admin"
COLLECTION_NAME = "images"
OUTPUT_COLLECTION = "output_legal"

if not all([AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, ANTHROPIC_API_KEY, MONGO_URI]):
    raise ValueError("Required credentials not found in environment variables")

# Enhanced system prompt for better field extraction
SYSTEM_PROMPT = '''You are an expert legal document analyzer. Focus on accurate data extraction.

DOCUMENT TYPE STANDARDIZATION:
1. Legal Document Types and Requirements:
   DO = DEED OF TRUST
       Required: APN, Document Number
       Optional: Map Reference
   
   GD = GRANT DEED
       Required: APN or Map Reference, Document Number
       Optional: Tract Number
   
   CL = CERTIFICATE OF LIEN
       Required: APN, Document Number
       Optional: Case Number
   
   ML = MECHANICS LIEN
       Required: APN, Document Number
       Optional: None
   
   RL = RELEASE OF LIEN
       Required: APN, Document Number
       Optional: Reference to original lien
   
   AF = AFFIDAVIT
       Required: Document Number or Case Number
       Optional: APN
   
   TD = TRUST DEED
       Required: APN, Document Number
       Optional: Map Reference
   
   QC = QUITCLAIM DEED
       Required: APN or Map Reference, Document Number
       Optional: None
   
   SD = SUBDIVISION MAP
       Required: Map Book, Map Page
       Optional: Tract Number
   
   CM = CONDOMINIUM MAP
       Required: Map Book, Map Page
       Optional: Unit Numbers

2. Format Standards:
   Document Numbers:
   ✓ DOC-YYYY-XXXXXXX-XX
   ✗ DOC YYYY-XXXXXXX-XX
   ✗ DOC YYYY XXXXXXX XX
   
   Map References:
   ✓ BK-XX (Map_Book)
   ✓ Numeric only (Map_Page)
   ✓ YYYY-MM-DD (Map_Date)
   
   Case Numbers:
   ✓ SC-XXXXXXX
   ✓ CV-XXXXXXX
   ✓ PR-XXXXXXX
   
   APN/Parcel:
   ✓ XXX-XXX-XXX-XXX
   ✓ XXXX-XXX-XXX

3. Legal_Extract_Complete_Flag Rules:
   Set Y when:
   - Legal_Type is correctly standardized AND
   - Legal_Extract_Level is set (L/M) AND
   - Document Number format is correct AND
   - All required fields for document type are present
   
   Set N when:
   - Any required field is missing OR
   - Document Number format is incorrect OR
   - Required fields don't match document type

4. Legal_Extract_Level Rules:
   L (Simple):
   - Single property
   - One APN
   - Basic legal description
   
   M (Multiple/Complex):
   - Multiple properties
   - Multiple APNs
   - Complex legal description
   - Multiple map references

5. Confidence Scoring:
   HIGH (90+):
   - Exact format match
   - Clear document header/footer
   - Multiple confirmations
   - Standard document type
   
   MEDIUM (70-89):
   - Single clear reference
   - Standard format
   - No confirmation needed
   
   LOW (Below 70):
   - Inferred values
   - Non-standard format
   - Uncertain matches
   - Missing required fields

Remember: 
- Standardization is critical
- Document type determines required fields
- Format validation before extraction
- Cross-reference all identifiers
- Better to mark N than accept incorrect format'''

def get_extraction_prompt(extracted_text: str, field_instructions: str) -> str:
    return f"""Analyze this legal document with these specific rules:

DOCUMENT IDENTIFICATION:
1. Legal_Type (DO/MP/BMP/etc):
   - Check document header for type
   - Look for recording information
   - Verify against legal description

2. Legal_Extract_Level:
   - L: Single property, simple description
   - M: Multiple properties or complex description

3. Document Numbers:
   - Recording numbers go in Plat_Document_Number
   - Format: DOC-YYYY-XXXXXXX-XX
   - Cross-reference with header/footer

4. APN/Parcel Numbers:
   - Primary format: XXX-XXX-XXX-XXX
   - Check all sections for APNs
   - Validate format before extraction

5. Legal_Extract_Complete_Flag Rules:
   - Y: When ALL required fields are found:
       * Legal_Type
       * Legal_Extract_Level
       * Document Number
       * APN/Parcel Number
   - N: When any required field is missing

6. Confidence Scoring:
   HIGH (90+):
   - Exact text match
   - Standard format
   - Multiple confirmations
   
   MEDIUM (70-89):
   - Single clear reference
   - Standard format
   - No confirmation
   
   LOW (Below 70):
   - Inferred values
   - Non-standard format
   - Uncertain matches

Document Text:
{extracted_text}

Field Specifications:
{field_instructions}

EXTRACTION REQUIREMENTS:
1. ALL VALUES IN UPPERCASE
2. Validate format before extraction
3. Cross-reference between sections
4. Document numbers must match recording info
5. APNs must match legal description

Return in JSON format:
{{
    "FIELD_NAME": {{
        "value": "EXTRACTED_VALUE",
        "confidence": 0-100,
        "flags": ["EXTRACTION_NOTES"]
    }}
}}""" 