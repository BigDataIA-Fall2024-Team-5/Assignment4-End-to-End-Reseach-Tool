import os
import re
import snowflake.connector
import boto3
from dotenv import load_dotenv
from botocore.config import Config
from research_canvas.state import AgentState  # Assuming AgentState is defined for managing state

# Load environment variables
load_dotenv()

# Initialize S3 client with signature version 's3v4'
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv("AWS_REGION"),
    config=Config(signature_version='s3v4')
)

def extract_bucket_and_key(s3_url):
    """Extract bucket name and key from an S3 URL."""
    match = re.match(r'https://(.+?)\.s3\..*?\.amazonaws\.com/(.+)', s3_url)
    if match:
        bucket = match.group(1)
        key = match.group(2)
        return bucket, key
    else:
        raise ValueError("Invalid S3 URL format")

async def document_selection_agent(state: AgentState, config):
    """
    Retrieves documents from Snowflake and generates presigned URLs for them.
    """

    try:
        # Connect to Snowflake
        conn = snowflake.connector.connect(
            user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"),
            account=os.getenv("SNOWFLAKE_ACCOUNT"),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "WH_PUBLICATIONS_ETL"),
            database=os.getenv("SNOWFLAKE_DATABASE", "RESEARCH_PUBLICATIONS"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "RESEARCH_PUBLICATIONS"),
            role=os.getenv("SNOWFLAKE_ROLE")
        )
        cursor = conn.cursor()

        # Execute the query to retrieve document metadata
        cursor.execute("SELECT id, title, pdf_link FROM PUBLICATION_LIST;")
        publications = cursor.fetchall()

        # Generate presigned URLs for each document
        document_list = []
        for row in publications:
            bucket, key = extract_bucket_and_key(row[2])  # Extract bucket and key from pdf_link
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=3600
            )
            document_list.append({
                "id": row[0],
                "title": row[1],
                "pdf_link": presigned_url
            })

        # Update the agent state with the document list
        state["document_list"] = document_list
        print("Document selection completed successfully with presigned URLs.")

        return state  # Ensure state is returned to keep it updated

    except Exception as e:
        print(f"Error in document_selection_agent: {e}")
        state["error"] = str(e)
        return state
