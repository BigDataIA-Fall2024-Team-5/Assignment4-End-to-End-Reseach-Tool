# export_router.py

import os
import markdown2  # Ensure markdown2 is installed
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pdfkit  # Ensure pdfkit is installed and wkhtmltopdf is accessible
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        logger.info("PDF generated successfully. Returning PDF file response.")
        # Return the generated PDF as a file response
        return FileResponse(
            pdf_file_path, 
            media_type="application/pdf", 
            filename="research_draft.pdf"
        )
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
