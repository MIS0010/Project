from PIL import Image
import pytesseract

def extract_text_from_image(image_data):
    """
    Extract text from image using Tesseract.
    :param image_data: Binary image data
    :return: Extracted text
    """
    try:
        image = Image.open(io.BytesIO(image_data))
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting text from image: {str(e)}")
        return ""
