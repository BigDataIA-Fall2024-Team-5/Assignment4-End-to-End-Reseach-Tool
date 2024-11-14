# export_router.py

import os
import markdown2  # Ensure markdown2 is installed
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import pdfkit  # Ensure pdfkit is installed and wkhtmltopdf is accessible
import logging
from openai import OpenAI  # Import the OpenAI client
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set your OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# Initialize the OpenAI client
openai_client = OpenAI(api_key=openai_api_key)

# Google API setup
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
FOLDER_ID = '1Ob3hcXe-BKJzlHAjw-9Ib_Fd8hv8Xthh'  # Replace with your actual folder ID

# Initialize Google Docs and Drive API clients
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
docs_service = build('docs', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)

# Create a router for export-related endpoints
router = APIRouter()

# Define a request model for the draft content
class DraftRequest(BaseModel):
    draft: str

@router.post("/export/pdf")
async def export_pdf(request: DraftRequest):
    """Convert research draft to PDF and return it as a downloadable file."""
    try:
        # Convert draft Markdown to HTML
        markdown_content = f"# Research Draft\n\n{request.draft}"
        html_content = markdown2.markdown(markdown_content)

        # Define file paths
        html_file_path = "/tmp/research_draft.html"
        pdf_file_path = "/tmp/research_draft.pdf"

        logger.info("Writing HTML content for PDF generation.")
        # Save HTML content as a file for PDF generation
        with open(html_file_path, "w") as file:
            file.write(html_content)
        
        logger.info("Attempting to generate PDF from HTML content.")
        # Generate PDF from the HTML content
        pdfkit.from_file(html_file_path, pdf_file_path)
        return FileResponse(pdf_file_path, media_type="application/pdf", filename="research_draft.pdf")
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

@router.post("/export/codelabs")
async def export_codelabs(request: DraftRequest):
    """Format research draft as Codelabs using GPT-4 and upload it to Google Docs."""
    prompt = (
        "You are a Codelabs formatting assistant. Format the given document in Codelabs style with the following structure:\n"
        "- Use `#` only once, for the main title of the document.\n"
        "- Use `##` for each major section that should appear in the Table of Contents.\n"
        "- Use `###` for any finer details or sub-sections within each major section, where appropriate.\n"
        "Adjust the structure flexibly depending on the content length, using more `##` headings for longer documents and fewer for shorter ones. "
        "Maintain the original meaning and do not alter the content.\n\n"
        f"Document:\n{request.draft}"
    )

    try:
        logger.info(f"Sending prompt to GPT-4:\n{prompt}")

        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for formatting Codelabs documents."},
                {"role": "user", "content": prompt}
            ]
        )

        formatted_codelabs = response.choices[0].message.content.strip()
        logger.info(f"Formatted Codelabs output:\n{formatted_codelabs}")

        # Upload the formatted content to Google Docs
        doc_link, codelabs_link = create_google_doc(formatted_codelabs)

        return JSONResponse({
            "message": "Codelabs export formatted successfully!",
            "google_doc_link": doc_link,
            "codelabs_link": codelabs_link
        })

    except Exception as e:
        logger.error(f"Error formatting Codelabs with GPT-4: {e}")
        raise HTTPException(status_code=500, detail="Failed to format document as Codelabs.")

def create_google_doc(content):
    """Create a Google Doc with the given content and return the Google Doc and Codelabs preview links."""
    doc_metadata = {
        "name": "Formatted Codelabs Document",
        "mimeType": "application/vnd.google-apps.document",
        "parents": [FOLDER_ID]
    }
    doc = drive_service.files().create(body=doc_metadata, fields="id").execute()
    document_id = doc.get("id")
    logger.info(f"Created Google Doc with ID: {document_id}")

    requests = []
    lines = content.strip().splitlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("### "):  # Heading 2
            text = line[4:]
            requests.extend(insert_text_request(document_id, text, "HEADING_2"))
        elif line.startswith("## ") or line.startswith("# "):  # Heading 1
            text = line.lstrip("# ").strip()
            requests.extend(insert_text_request(document_id, text, "HEADING_1"))
        else:
            requests.extend(insert_text_request(document_id, line, "NORMAL_TEXT"))
        
        docs_service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
        requests = []  # Reset requests for the next line

    google_doc_link = f"https://docs.google.com/document/d/{document_id}"
    codelabs_preview_link = f"https://codelabs-preview.appspot.com/?file_id={document_id}"

    logger.info(f"Google Doc link: {google_doc_link}")
    logger.info(f"Codelabs Preview link: {codelabs_preview_link}")

    return google_doc_link, codelabs_preview_link

def insert_text_request(document_id, text, style):
    end_index = get_document_end_index(document_id)
    return [
        {
            "insertText": {
                "location": {
                    "index": end_index,
                },
                "text": text
            }
        },
        {
            "updateParagraphStyle": {
                "range": {
                    "startIndex": end_index,
                    "endIndex": end_index + len(text)
                },
                "paragraphStyle": {
                    "namedStyleType": style
                },
                "fields": "namedStyleType"
            }
        },
        {
            "insertText": {
                "location": {
                    "index": end_index + len(text)
                },
                "text": "\n"
            }
        }
    ]

def get_document_end_index(document_id):
    doc = docs_service.documents().get(documentId=document_id).execute()
    return doc['body']['content'][-1]['endIndex'] - 1
