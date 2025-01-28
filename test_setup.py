import os
from dotenv import load_dotenv
import boto3
from anthropic import Anthropic
from pymongo import MongoClient

def test_environment():
    """Test if all environment variables are loaded correctly"""
    load_dotenv()
    
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
        'ANTHROPIC_API_KEY',
        'MONGO_URI'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print("❌ Missing environment variables:", missing)
        return False
    print("✅ Environment variables loaded successfully")
    return True

def test_aws_connection():
    """Test AWS Textract connection"""
    try:
        textract = boto3.client(
            'textract',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        textract.list_document_text_detection_jobs()
        print("✅ AWS Textract connection successful")
        return True
    except Exception as e:
        print("❌ AWS Textract connection failed:", str(e))
        return False

def test_claude_connection():
    """Test Claude API connection"""
    try:
        client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'test' only"}]
        )
        print("✅ Claude API connection successful")
        return True
    except Exception as e:
        print("❌ Claude API connection failed:", str(e))
        return False

def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        client = MongoClient(os.getenv('MONGO_URI'))
        db = client.Documenttask
        db.command('ping')
        print("✅ MongoDB connection successful")
        return True
    except Exception as e:
        print("❌ MongoDB connection failed:", str(e))
        return False

def test_output_directory():
    """Test if output directory exists and is writable"""
    output_dir = "Outputs/06107-20241205-01"
    try:
        if not os.path.exists(output_dir):
            print("❌ Output directory doesn't exist")
            return False
            
        # Try to write a test file
        test_file = os.path.join(output_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        
        print("✅ Output directory exists and is writable")
        return True
    except Exception as e:
        print("❌ Output directory test failed:", str(e))
        return False

if __name__ == "__main__":
    print("\nTesting application setup...")
    print("-" * 50)
    
    tests = [
        test_environment,
        test_aws_connection,
        test_claude_connection,
        test_mongodb_connection,
        test_output_directory
    ]
    
    success = True
    for test in tests:
        if not test():
            success = False
            
    print("-" * 50)
    if success:
        print("✅ All tests passed! You can now run the main application.")
        print("\nTo run the application:")
        print("python document_processor_mailing.py")
    else:
        print("❌ Some tests failed. Please fix the issues before running the application.")