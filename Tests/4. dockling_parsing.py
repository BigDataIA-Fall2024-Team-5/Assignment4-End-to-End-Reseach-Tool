import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv
from docling.document_converter import DocumentConverter

# Load environment variables
load_dotenv()

# Initialize the S3 client with Signature Version 4
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv("AWS_REGION"),
    config=Config(signature_version='s3v4')
)

# S3 bucket configuration
bucket_name = os.getenv('S3_BUCKET_NAME')
input_prefix = 'raw/publications/'
output_prefix = 'processed/publications/'

# Function to list PDFs in S3
def list_pdfs_in_s3_folder(prefix):
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    pdf_files = [item['Key'] for item in response.get('Contents', []) if item['Key'].endswith('.pdf')]
    return pdf_files

# Function to generate a presigned URL for an S3 object with a longer expiration
def generate_presigned_url(key):
    return s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket_name, 'Key': key},
        ExpiresIn=3600  # Set expiry time to 1 hour
    )

# Function to process PDFs and upload extracted text to S3 using Docling
def docling_process_and_upload():
    # Initialize Docling DocumentConverter
    converter = DocumentConverter()
    
    # List all PDFs in the input folder
    pdf_files = list_pdfs_in_s3_folder(input_prefix)
    
    # Initialize a counter for processed files
    processed_count = 0

    for pdf_key in pdf_files:
        try:
            # Generate a presigned URL for the PDF file
            presigned_url = generate_presigned_url(pdf_key)

            # Process the PDF with Docling using the presigned URL
            result = converter.convert(presigned_url)
            text_content = result.document.export_to_markdown()  # Export to Markdown

            # Define the output folder and file name
            output_folder = os.path.basename(pdf_key).replace('.pdf', '')
            output_folder_key = f'{output_prefix}{output_folder}/'
            output_txt_key = f'{output_folder_key}{output_folder}.md'  # Save as Markdown file

            # Upload the processed text to S3
            s3.put_object(Bucket=bucket_name, Key=output_txt_key, Body=text_content.encode('utf-8'))
            print(f"Processed and uploaded: {output_txt_key}")
            
            # Increment the counter
            processed_count += 1

        except Exception as e:
            print(f"Error processing {pdf_key}: {str(e)}")

    # Print the total count of processed files
    print(f"Total PDF files processed and uploaded: {processed_count}")

if __name__ == "__main__":
    print("Starting PDF text extraction using Docling...")
    docling_process_and_upload()
    print("PDF text extraction completed.")
