import os
import snowflake.connector
import boto3
import pandas as pd
from io import StringIO
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

def load_data_into_snowflake():
    """Reads CSV from S3 and loads it into Snowflake table using a merge operation."""
    
    # Establish Snowflake connection
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "WH_PUBLICATIONS_ETL"),
        role=os.getenv("SNOWFLAKE_ROLE")
    )
    cursor = conn.cursor()

    # Set up database, schema, and table details
    database_name = os.getenv("SNOWFLAKE_DATABASE", "RESEARCH_PUBLICATIONS")
    schema_name = os.getenv("SNOWFLAKE_SCHEMA", "RESEARCH_PUBLICATIONS")
    table_name = os.getenv("SNOWFLAKE_TABLE", "PUBLICATION_LIST")

    # Set up S3 details
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    s3_key = "raw/publications_data.csv"
    aws_region = os.getenv("AWS_REGION")

    s3_client = boto3.client(
        's3',
        region_name=aws_region,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

    def read_csv_from_s3(bucket, key):
        """Read CSV content from S3 and load it into a pandas DataFrame."""
        print(f"Reading CSV from S3 bucket '{bucket}', key '{key}'...")
        response = s3_client.get_object(Bucket=bucket, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        return pd.read_csv(StringIO(csv_content))

    # Load data from S3
    df = read_csv_from_s3(s3_bucket, s3_key)
    df = df.where(pd.notnull(df), None)  # Replace NaN with None

    try:
        print("Starting data merge operation in Snowflake...")
        for _, row in df.iterrows():
            merge_query = f"""
            MERGE INTO {database_name}.{schema_name}.{table_name} AS target
            USING (SELECT '{row['title']}' AS TITLE,
                         '{row['summary']}' AS BRIEF_SUMMARY,
                         '{row['date']}' AS DATE,
                         '{row['authors']}' AS AUTHOR,
                         '{row['cover_path']}' AS IMAGE_LINK,
                         '{row['publication_path']}' AS PDF_LINK,
                         CURRENT_TIMESTAMP AS CREATED_DATE) AS source
            ON target.TITLE = source.TITLE
               AND target.AUTHOR = source.AUTHOR
               AND target.DATE = source.DATE
            WHEN MATCHED THEN
              UPDATE SET target.BRIEF_SUMMARY = source.BRIEF_SUMMARY,
                         target.IMAGE_LINK = source.IMAGE_LINK,
                         target.PDF_LINK = source.PDF_LINK
            WHEN NOT MATCHED THEN
              INSERT (TITLE, BRIEF_SUMMARY, DATE, AUTHOR, IMAGE_LINK, PDF_LINK, CREATED_DATE)
              VALUES (source.TITLE, source.BRIEF_SUMMARY, source.DATE, source.AUTHOR, source.IMAGE_LINK, source.PDF_LINK, source.CREATED_DATE);
            """
            cursor.execute(merge_query)
        print(f"Data loaded successfully into table '{table_name}'.")
        
    except snowflake.connector.errors.ProgrammingError as e:
        print(f"Error during data merge: {e}")
    finally:
        cursor.close()
        conn.close()
        print("Snowflake connection closed.")

if __name__ == "__main__":
    print("Starting the Snowflake data load script...")
    load_data_into_snowflake()
    print("Data load script completed.")
