# Backend README

## Introduction

This backend directory contains the core implementation of the research assistant application, managing document handling, chat and search functionalities, and RAG (Retrieval-Augmented Generation) querying from Snowflake and Pinecone. The backend API is built using FastAPI and supports various functionalities including document download, query response, Arxiv search, and exporting research drafts to Google Docs and Codelabs format.

## Project Structure

📂 backend  
├── Dockerfile  
├── credentials.json  
├── poetry.lock  
├── pyproject.toml  
└── research_canvas  
    ├── __init__.py  
    ├── agent.py  
    ├── arxiv_search.py  
    ├── chat.py  
    ├── delete.py  
    ├── demo.py  
    ├── document_selection.py  
    ├── download.py  
    ├── export_router.py  
    ├── model.py  
    ├── rag.py  
    ├── search.py  
    └── state.py  

## Setup Instructions

### Prerequisites
- Docker & Docker Compose: Required for containerization.
- Python 3.12: Ensure Python 3.12 compatibility.
- API Credentials: Place required credentials in the `.env` file for AWS, Snowflake, NVIDIA, Pinecone, and OpenAI.
- Poetry: Used for dependency management.
- Google credentials.json: Required for accessing Google Drive and Google Docs.

## Application Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-repo/Assignment4-End-to-End-Research-Tool.git
   cd Assignment4-End-to-End-Research-Tool/backend
   ```

2. **Setup .env File**:
   Create a `.env` file in the backend directory with your credentials:
   ```plaintext
   AWS_ACCESS_KEY_ID='your_aws_access_key'
   AWS_SECRET_ACCESS_KEY='your_aws_secret_key'
   AWS_REGION='your_aws_region'
   S3_BUCKET_NAME='your_s3_bucket_name'
   SNOWFLAKE_ACCOUNT='your_snowflake_account'
   SNOWFLAKE_USER='your_snowflake_user'
   SNOWFLAKE_PASSWORD='your_snowflake_password'
   SNOWFLAKE_ROLE='your_snowflake_role'
   NVIDIA_API_KEY='your_nvidia_api_key'
   PINECONE_API_KEY='your_pinecone_api_key'
   OPENAI_API_KEY='your_openai_api_key'
   TAVILY_API_KEY='your_tavily_api_key'
   ```

3. **Install Dependencies and Run Backend**:
   ```bash
   poetry install
   sudo apt install wkhtmltopdf
   poetry run demo
   ```
   The backend will be available at `http://localhost:8000`, and you can view the FastAPI documentation at `http://localhost:8000/docs`.

4. **Alternatively, Using Docker Compose**:
   Run the backend using Docker Compose with the following commands:
   ```bash
   docker-compose up --build
   ```
   For Docker setup, ensure `REMOTE_ACTION_URL='http://backend:8000'` in the UI's .env file.