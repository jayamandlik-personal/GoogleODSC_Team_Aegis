import os
from dotenv import load_dotenv
from google.cloud import bigquery
import pandas as pd

load_dotenv()

def query_blockchain(sql_query: str) -> str: # <--- Note return type is str
    """
    Executes a SQL query on the Ethereum blockchain.
    """
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    if not project_id:
        return "Error: GOOGLE_CLOUD_PROJECT not found in .env."

    try:
        # Initialize Client
        client = bigquery.Client(project=project_id)
        
        # Security Check
        if "crypto_ethereum" not in sql_query and "bigquery-public-data" not in sql_query:
            return "Error: Only 'bigquery-public-data.crypto_ethereum' is allowed."

        # Run Query
        print(f"Executing SQL: {sql_query[:100]}...") # Debug log
        query_job = client.query(sql_query)
        
        # Wait for the job to complete and handle errors
        try:
            result = query_job.result()
            df = result.to_dataframe()
            
            if df.empty:
                return "No results found."

            return df.head(20).to_markdown(index=False)
        except Exception as query_error:
            # Get more detailed error information
            error_msg = str(query_error)
            if hasattr(query_job, 'errors') and query_job.errors:
                error_details = '; '.join([str(err) for err in query_job.errors])
                error_msg = f"{error_msg}. Details: {error_details}"
            return f"SQL Error: {error_msg}"
    except Exception as e:
        # Handle any other errors (client initialization, etc.)
        return f"Error: {str(e)}"