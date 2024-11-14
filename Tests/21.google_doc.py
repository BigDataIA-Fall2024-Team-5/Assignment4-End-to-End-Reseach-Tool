import os
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Path to your service account JSON key file
SERVICE_ACCOUNT_FILE = 'credentials.json'
SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']

# Initialize the Google Docs API
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('docs', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)

# Folder ID where the document will be saved
FOLDER_ID = '1Ob3hcXe-BKJzlHAjw-9Ib_Fd8hv8Xthh'  # Replace with your actual folder ID

# The content to format and add to Google Docs
content = """
# Snow in Kashmir: A Winter Wonderland

Kashmir, often referred to as "Paradise on Earth," transforms into a breathtaking winter wonderland during the snowfall season, which typically spans from December to February. This period is characterized by heavy snowfall that blankets the picturesque landscapes, creating a stunning visual feast for visitors and locals alike.

## Seasonal Overview
The snowfall season in Kashmir begins in December, with the first snowflakes delicately touching the ground. January is usually the coldest month, with temperatures dropping as low as -6.1°C or even lower. The iconic Dal Lake, Mughal Gardens, and historic sites like the Shankaracharya Temple are adorned with a thick layer of snow, offering postcard-perfect scenes that attract tourists from around the globe.

## Impact on Tourism
Kashmir's snowfall not only enhances its natural beauty but also significantly boosts its tourism industry. Popular destinations like Gulmarg and Pahalgam become hotspots for winter sports enthusiasts, offering activities such as skiing and snowboarding. 

### Gulmarg Ski Resort and Gondola
The Gulmarg Ski Resort, in particular, is renowned for its pristine slopes and attracts skiing enthusiasts from around the world. The Gulmarg Gondola, one of the highest cable cars globally, provides breathtaking views of the snow-covered peaks, further enhancing the tourist experience.

## Recent Trends and Concerns
However, recent winters have raised concerns among experts and locals alike. Reports indicate a rare snowless winter, which could lead to water scarcity and negatively impact the economy, particularly in farming and water supply sectors. 

### Link to Climate Change
The absence of snowfall has been linked to climate change, with experts noting a significant rise in temperatures and a decrease in snowfall over the years. This trend poses a threat to the region's ecology and economy, as the tourism sector accounts for a substantial portion of Jammu and Kashmir's GDP.

## Conclusion
The snowfall in Kashmir is not just a seasonal phenomenon; it is a vital aspect of the region's identity and economy. While the winter months offer a magical experience for visitors, the challenges posed by climate change and the potential for snowless winters highlight the need for sustainable practices to preserve this beautiful region for future generations.
"""

def create_google_doc(content):
    # Create a new Google Doc with folder ID for location
    doc_metadata = {
        "name": "Formatted Codelabs Document",
        "mimeType": "application/vnd.google-apps.document",
        "parents": [FOLDER_ID]
    }
    doc = drive_service.files().create(body=doc_metadata, fields="id").execute()
    document_id = doc.get("id")
    print(f"Created Google Doc with ID: {document_id}")

    # Prepare the requests to format the content
    requests = []
    lines = content.strip().splitlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Determine the heading level based on `#` symbols
        if line.startswith("### "):  # Heading 2
            text = line[4:]
            requests.extend(insert_text_request(text, "HEADING_2"))
        elif line.startswith("## ") or line.startswith("# "):  # Heading 1
            text = line.lstrip("# ").strip()
            requests.extend(insert_text_request(text, "HEADING_1"))
        else:
            # Normal text
            requests.extend(insert_text_request(line, "NORMAL_TEXT"))
        
        # Add a newline after each line to separate paragraphs
        requests.append({"insertText": {"location": {"index": 1}, "text": "\n"}})

    # Execute the requests to format the document
    service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
    print("Document formatted successfully.")
    return f"https://docs.google.com/document/d/{document_id}"

def insert_text_request(text, style):
    """Helper function to create a request for inserting text with a specific style."""
    return [
        {
            "insertText": {
                "location": {
                    "index": 1,
                },
                "text": text
            }
        },
        {
            "updateParagraphStyle": {
                "range": {
                    "startIndex": 1,
                    "endIndex": 1 + len(text)
                },
                "paragraphStyle": {
                    "namedStyleType": style
                },
                "fields": "namedStyleType"
            }
        }
    ]

# Run the script
doc_link = create_google_doc(content)
print(f"Google Doc link: {doc_link}")
