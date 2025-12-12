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
        
        # Security Check - Allow queries to:
        # 1. bigquery-public-data.crypto_ethereum (raw blockchain data)
        # 2. User's own project Materialized Views (walletlens_aggregates dataset)
        sql_lower = sql_query.lower()
        is_public_data = "crypto_ethereum" in sql_lower and "bigquery-public-data" in sql_lower
        is_own_aggregates = project_id.lower() in sql_lower and "walletlens_aggregates" in sql_lower
        
        if not (is_public_data or is_own_aggregates):
            return f"Error: Only queries to 'bigquery-public-data.crypto_ethereum' or '{project_id}.walletlens_aggregates' are allowed."

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
