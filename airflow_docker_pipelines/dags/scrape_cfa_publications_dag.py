import os
import pandas as pd
import boto3
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from io import StringIO, BytesIO
from datetime import datetime
from dotenv import load_dotenv
from airflow import DAG
from airflow.operators.python import PythonOperator

load_dotenv()

# Load environment variables for AWS credentials
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')
s3_bucket_name = os.getenv('S3_BUCKET_NAME')

# Function to initialize Selenium WebDriver
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Function to download files and upload them to S3 using an in-memory buffer
def download_and_upload_file(url, s3_dir, s3_bucket_name, aws_region, s3):
    if url:
        file_name = os.path.basename(url.split('?')[0])
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            file_buffer = BytesIO(response.content)
            s3_key = f"{s3_dir}/{file_name}"
            s3.upload_fileobj(file_buffer, s3_bucket_name, s3_key)
            s3_url = f"https://{s3_bucket_name}.s3.{aws_region}.amazonaws.com/{s3_key}"
            return s3_url
    return None

# Function to handle PDF extraction
def extract_pdf_link(pdf_soup):
    primary_link = pdf_soup.find('a', class_='content-asset--primary', href=True)
    if primary_link and '.pdf' in primary_link['href']:
        return primary_link['href'] if primary_link['href'].startswith('http') else f"https://rpc.cfainstitute.org{primary_link['href']}"
    
    secondary_pdf_tag = pdf_soup.find('a', class_='items__item', href=True)
    if secondary_pdf_tag and '.pdf' in secondary_pdf_tag['href']:
        return secondary_pdf_tag['href'] if secondary_pdf_tag['href'].startswith('http') else f"https://rpc.cfainstitute.org{secondary_pdf_tag['href']}"
    
    return None

# Function to scrape publications using Selenium and save data as a pandas DataFrame
def scrape_publications_with_selenium(**kwargs):
    print("Starting publication scraping process...")
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=aws_region)
    driver = init_driver()
    all_data = []

    # Titles to filter for
    target_titles = {
        'Overcoming the Notion of a Single Reference Currency: A Currency Basket Approach',
        'Risk Profiling through a Behavioral Finance Lens',
        'The Evolution of Asset/Liability Management'
    }

    for page_num in range(0, 100, 10):
        base_url = f"https://rpc.cfainstitute.org/en/research-foundation/publications#first={page_num}&sort=%40officialz32xdate%20descending"
        print(f"Loading page {page_num // 10 + 1}...")
        driver.get(base_url)
        time.sleep(5)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        publications = soup.find_all('div', class_='coveo-list-layout CoveoResult')

        for pub in publications:
            title_tag = pub.find('a', class_='CoveoResultLink')
            title = title_tag.text.strip() if title_tag else None

            # Check if the title is in the target list
            if title not in target_titles:
                continue

            print(f"Scraping publication: {title}")
            href = title_tag['href'] if title_tag else None
            href = f"https://rpc.cfainstitute.org{href}" if href and href.startswith('/') else href

            image_tag = pub.find('img', class_='coveo-result-image')
            image_url = image_tag['src'] if image_tag else None
            image_url = f"https://rpc.cfainstitute.org{image_url}" if image_url and image_url.startswith('/') else image_url

            summary_tag = pub.find('div', class_='result-body')
            summary = summary_tag.text.strip() if summary_tag else None

            pdf_link = None
            if href:
                driver.get(href)
                time.sleep(5)
                pdf_soup = BeautifulSoup(driver.page_source, 'html.parser')
                pdf_link = extract_pdf_link(pdf_soup)

            date_tag = pub.find('span', class_='date')
            date = date_tag.text.strip() if date_tag else None

            authors_tag = pub.find('span', class_='author')
            authors = authors_tag.text.strip() if authors_tag else None

            s3_image_url = download_and_upload_file(image_url, 'raw/publication_covers', s3_bucket_name, aws_region, s3) if image_url else "NA"
            s3_pdf_url = download_and_upload_file(pdf_link, 'raw/publications', s3_bucket_name, aws_region, s3) if pdf_link else "NA"

            all_data.append({
                'title': title or "NA",
                'summary': summary or "NA",
                'date': date or "NA",
                'authors': authors or "NA",
                'cover_path': s3_image_url,
                'publication_path': s3_pdf_url
            })

    driver.quit()
    print("Scraping process complete. Creating DataFrame...")
    df = pd.DataFrame(all_data)
    print("DataFrame created.")
    
    # Push the DataFrame to XCom for the next task
    kwargs['ti'].xcom_push(key='scraped_data', value=df.to_json(orient='records'))

# Function to save the scraped data as a CSV file and upload to S3
def save_and_upload_csv(**kwargs):
    print("Saving DataFrame as CSV and uploading to S3...")
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=aws_region)
    csv_buffer = StringIO()

    # Pull the data from XCom
    data_json = kwargs['ti'].xcom_pull(task_ids='scrape_publications_task', key='scraped_data')
    df = pd.read_json(data_json)
    
    df.to_csv(csv_buffer, index=False)
    s3_key = "raw/publications_data.csv"
    s3.put_object(Body=csv_buffer.getvalue(), Bucket=s3_bucket_name, Key=s3_key)
    print(f'CSV uploaded to S3 at: s3://{s3_bucket_name}/{s3_key}')

# Define the DAG
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 11, 11),
    'retries': 1,
}

with DAG(
    dag_id='scrape_and_upload_publications_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False
) as dag:

    # Task to scrape publications
    scrape_publications_task = PythonOperator(
        task_id='scrape_publications_task',
        python_callable=scrape_publications_with_selenium,
        provide_context=True
    )

    # Task to save and upload CSV
    save_and_upload_csv_task = PythonOperator(
        task_id='save_and_upload_csv_task',
        python_callable=save_and_upload_csv,
        provide_context=True
    )

    # Define task dependencies
    scrape_publications_task >> save_and_upload_csv_task
