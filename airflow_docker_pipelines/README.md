# Airflow Docker Pipelines README

This README provides information about setting up and running the Airflow Docker Pipelines for the Assignment4-End-to-End-Research-Tool project. These pipelines automate scraping publications, setting up Snowflake, loading data into Snowflake, and processing PDFs into chunks for indexing in Pinecone.

## Project Structure

📂 **airflow_docker_pipelines**  
├── **Dockerfile**  
├── **docker-compose.yaml**  
├── **requirements.txt**  
├── **dags**  
│   ├── **scrape_cfa_publications_dag.py** - Scrapes CFA Institute publications and uploads metadata to S3  
│   ├── **snowflake_setup_dag.py** - Sets up Snowflake warehouse, database, schema, and table  
│   ├── **snowflake_load_dag.py** - Loads publication data from S3 into Snowflake  
│   └── **pdf_processing_pipeline_dag.py** - Processes PDFs, chunks content using Docling, and indexes it in Pinecone  


## Setup Instructions

1. **Prerequisites**

- **Docker**: Ensure Docker and Docker Compose are installed.
- **API Credentials**: Set up AWS, Snowflake, NVIDIA, and Pinecone credentials in the `.env` file.

2. **Setup Steps**

- Clone the Repository:
```bash
git clone https://github.com/your-repo/Assignment4-End-to-End-Research-Tool.git
cd Assignment4-End-to-End-Research-Tool/airflow_docker_pipelines
```
- Build Docker Image for Airflow:
```bash
docker build -t airflow-a4:latest .
```
- Run Airflow Initialization:
Replace placeholder values with your credentials before running.
```bash
AIRFLOW_IMAGE_NAME=airflow-a4:latest AIRFLOW_UID=0 _AIRFLOW_WWW_USER_USERNAME=admin _AIRFLOW_WWW_USER_PASSWORD=admin123 AWS_ACCESS_KEY_ID='<YOUR_AWS_ACCESS_KEY>' AWS_SECRET_ACCESS_KEY='<YOUR_AWS_SECRET_KEY>' AWS_REGION='<YOUR_AWS_REGION>' S3_BUCKET_NAME='<YOUR_S3_BUCKET>' SNOWFLAKE_ACCOUNT='<YOUR_SNOWFLAKE_ACCOUNT>' SNOWFLAKE_USER='<YOUR_SNOWFLAKE_USER>' SNOWFLAKE_PASSWORD='<YOUR_SNOWFLAKE_PASSWORD>' SNOWFLAKE_ROLE='<YOUR_SNOWFLAKE_ROLE>' NVIDIA_API_KEY='<YOUR_NVIDIA_API_KEY>' PINECONE_API_KEY='<YOUR_PINECONE_API_KEY>' docker-compose up airflow-init
```

## Pipelines Overview

1. **Scrape CFA Publications DAG** (`scrape_cfa_publications_dag.py`): Scrapes selected research publications from the CFA Institute website, including title, summary, publication date, author, and download link. Uploads metadata to S3.
2. **Snowflake Setup DAG** (`snowflake_setup_dag.py`): Sets up a Snowflake warehouse, database, schema, and the `PUBLICATION_LIST` table for storing publication metadata.
3. **Snowflake Load DAG** (`snowflake_load_dag.py`): Loads publication metadata from the S3 bucket into Snowflake, handling merges to update or insert records as needed.
4. **PDF Processing Pipeline DAG** (`pdf_processing_pipeline_dag.py`): Downloads PDFs, converts content to Markdown with Docling, chunks it, and indexes the content in Pinecone for query-ready document indexing.

## Running the Pipelines
To run the pipelines, start each task from the Airflow UI or schedule them based on your requirements. The DAGs are configured to run in the following order:

1. Scrape CFA Publications
2. Snowflake Setup
3. Snowflake Load
4. PDF Processing Pipeline