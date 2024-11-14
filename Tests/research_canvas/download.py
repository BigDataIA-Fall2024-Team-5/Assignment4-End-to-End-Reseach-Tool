import boto3
from research_canvas.state import AgentState
from urllib.parse import urlparse

def parse_s3_url(s3_url):
    """Parse an S3 URL into bucket and key."""
    parsed_url = urlparse(s3_url)
    bucket = parsed_url.netloc.split('.')[0]
    key = parsed_url.path.lstrip('/')
    return bucket, key

async def download_node(state: AgentState, config):
    """Download processed Markdown files from S3."""
    
    s3_url = state.get("s3_url")  # Get S3 URL from state
    
    # Ensure s3_url is a string (decode if it's bytes).
    if isinstance(s3_url, bytes):
        s3_url = s3_url.decode('utf-8')  # Decode bytes to string
    
    # Initialize S3 client
    s3 = boto3.client('s3')
    
    # Parse S3 URL to get bucket and key
    bucket, key = parse_s3_url(s3_url)
    
    # Download Markdown file from S3
    markdown_obj = s3.get_object(Bucket=bucket, Key=key)
    
    markdown_content = markdown_obj['Body'].read().decode('utf-8')
    
    # Update state with downloaded content
    state["resources"] = [{"url": s3_url, "content": markdown_content}]
    
    return state