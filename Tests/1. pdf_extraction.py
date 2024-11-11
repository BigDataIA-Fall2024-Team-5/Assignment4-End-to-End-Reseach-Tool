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

load_dotenv()

# Load environment variables for AWS credentials
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
aws_region = os.getenv('AWS_REGION')
s3_bucket_name = os.getenv('S3_BUCKET_NAME')

# Function to initialize Selenium WebDriver
def init_driver():
    print("Initializing Selenium WebDriver...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("WebDriver initialized.")
    return driver

# Function to download files and upload them to S3 using an in-memory buffer
def download_and_upload_file(url, s3_dir, s3_bucket_name, aws_region, s3):
    if url:
        print(f"Downloading file from {url}...")
        file_name = os.path.basename(url.split('?')[0])
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            file_buffer = BytesIO(response.content)
            s3_key = f"{s3_dir}/{file_name}"
            print(f"Uploading {file_name} to S3 bucket {s3_bucket_name}...")
            s3.upload_fileobj(file_buffer, s3_bucket_name, s3_key)
            s3_url = f"https://{s3_bucket_name}.s3.{aws_region}.amazonaws.com/{s3_key}"
            print(f"File uploaded successfully: {s3_url}")
            return s3_url
        else:
            print(f"Failed to download file from {url}. Status code: {response.status_code}")
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
def scrape_publications_with_selenium():
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
        time.sleep(10)

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
    return df

# Function to save the scraped data as a CSV file and upload to S3
def save_and_upload_csv(df):
    print("Saving DataFrame as CSV and uploading to S3...")
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key, region_name=aws_region)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)

    s3_key = "raw/publications_data.csv"
    s3.put_object(Body=csv_buffer.getvalue(), Bucket=s3_bucket_name, Key=s3_key)
    print(f'CSV uploaded to S3 at: s3://{s3_bucket_name}/{s3_key}')

# Main execution
if __name__ == "__main__":
    # Step 1: Scrape Publications
    publications_df = scrape_publications_with_selenium()
    print("Scraping complete. DataFrame created.")

    # Step 2: Save and upload the scraped data as a CSV
    save_and_upload_csv(publications_df)
    print("CSV uploaded successfully.")
