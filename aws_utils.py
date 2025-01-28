import boto3

def upload_to_s3(file_path, bucket_name):
    """
    Upload file to S3 bucket.
    :param file_path: Path to the file
    :param bucket_name: S3 bucket name
    """
    try:
        s3_client = boto3.client('s3')
        s3_client.upload_file(file_path, bucket_name, file_path)
        print(f"File uploaded to S3: {file_path}")
    except Exception as e:
        print(f"Error uploading to S3: {str(e)}")

def analyze_with_textract(text):
    """
    Analyze text with AWS Textract.
    :param text: Text to analyze
    :return: Textract analysis results
    """
    try:
        textract_client = boto3.client('textract')
        response = textract_client.analyze_document(
            Document={'Text': text},
            FeatureTypes=['FORMS']
        )
        return response
    except Exception as e:
        print(f"Error analyzing text with Textract: {str(e)}")
        return {}
