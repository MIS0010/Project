from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import fitz
from PIL import Image
from field_definitions import FIELD_GROUPS
import multiprocessing

# Number of worker threads (adjust based on your CPU)
MAX_WORKERS = multiprocessing.cpu_count() * 2

def process_document_batch(docs, processor, batch_name):
    """Process a batch of documents in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_doc = {
            executor.submit(process_single_document, doc, processor): doc 
            for doc in docs
        }
        
        for future in as_completed(future_to_doc):
            doc = future_to_doc[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"Error processing document {doc['_id']}: {str(e)}")
    
    return results

def process_single_document(doc, processor):
    """Process a single document."""
    ocr_text = doc.get('ocr_text', '')
    extracted_data = {"text": str(ocr_text)}
    processed_data = processor.post_process_with_llm(extracted_data)
    
    image_name = doc.get('filename', 'unknown.TIF')
    batch_name = doc.get('cat_name', '06107-20241205-01')
    image_header_id = "1"
    
    output_line = format_output(image_name, batch_name, image_header_id, processed_data)
    
    return {
        "doc_id": doc['_id'],
        "output_line": output_line,
        "processed_data": processed_data,
        "image_name": image_name,
        "batch_name": batch_name
    }
process_single_document
def convert_document_to_images(file_path: str) -> List[Image.Image]:
    """Convert document to list of images."""
    if file_path.lower().endswith(('.tif', '.tiff')):
        images = []
        with Image.open(file_path) as img:
            n_frames = getattr(img, 'n_frames', 1)
            for frame in range(n_frames):
                try:
                    img.seek(frame)
                    frame_image = img.convert('RGB') if img.mode not in ('RGB', 'L') else img.copy()
                    images.append(frame_image)
                except EOFError:
                    break
        return images
    else:
        raise ValueError("Unsupported file format. Please provide a TIFF file.")

def format_output(image_name: str, batch_name: str, image_header_id: str, extracted_data: Dict) -> str:
    output = f"{image_name}|{batch_name}|{image_header_id}"
    
    # Format field values
    for field in FIELD_GROUPS:
        field_data = extracted_data.get(field, {})
        value = field_data.get("value", "") if isinstance(field_data, dict) else ""
        value = str(value) if value is not None else ""
        output += f"|{value}"
    
    # Format confidence levels
    for field in FIELD_GROUPS:
        field_data = extracted_data.get(field, {})
        confidence = field_data.get("confidence", 0) if isinstance(field_data, dict) else 0
        confidence_label = "HIGH" if confidence >= 90 else "LOW"
        output += f"|{confidence_label}"
    
    # Add empty fields for IsFromModel and XrefRemarks
    output += "||"
    
    return output

def generate_header():
    """Generate the complete header schema."""
    # Define field headers first
    field_header = "|".join(FIELD_GROUPS)
    confidence_header = "|".join([f"CL_{field}" for field in FIELD_GROUPS])
    
    # Combine into final header
    header = f"ImageName|BatchName|ImageHeaderID|{field_header}|{confidence_header}|IsFromModel|XrefRemarks"
    print("Generated Header:")
    print(header)
    return header 