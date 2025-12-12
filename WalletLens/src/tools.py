"""Tools for querying blockchain data from BigQuery."""

import os
from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd

load_dotenv(override=True)

def query_blockchain(sql_query: str) -> str:
    """
    Executes a SQL query on the Ethereum blockchain.
    """
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    if not project_id:
        return "Error: GOOGLE_CLOUD_PROJECT not found in .env."

    try:
        # Initialize Client
        client = bigquery.Client(project=project_id)
        
        # Security Check - BOTH strings must be present
        # Using OR: blocks if EITHER is missing (requires BOTH to be present)
        if "crypto_ethereum" not in sql_query or "bigquery-public-data" not in sql_query:
            return "Error: Only 'bigquery-public-data.crypto_ethereum' dataset is allowed. Query must contain both 'bigquery-public-data' and 'crypto_ethereum'."

        # CONFIGURATION FIX: Increase the safety limit
        # We allow up to 100 GB (100 * 1024^3 bytes) per query.
        # This prevents the "Query exceeded limit for bytes billed" error for 1-year scans.
        job_config = bigquery.QueryJobConfig(
            maximum_bytes_billed=100 * 1024 * 1024 * 1024  # 100 GB limit
        )

        print(f"Executing SQL: {sql_query[:50]}...") 
        
        # Pass the config here
        query_job = client.query(sql_query, job_config=job_config)
        result = query_job.result()
        df = result.to_dataframe()
        
        if df.empty:
            return "No results found."

        return df.head(20).to_markdown(index=False)

    except Exception as e:
        return f"SQL Error: {str(e)}"
