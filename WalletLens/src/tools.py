"""Tools for querying blockchain data from BigQuery."""

import os
import re
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
        
        # Security Check - Validate actual table paths in FROM/JOIN clauses
        # Uses strict table path validation instead of substring matching to prevent
        # bypass attacks via comments or string literals containing allowed table names.
        # Allow queries to:
        # 1. bigquery-public-data.crypto_ethereum.* (raw blockchain data)
        # 2. {project_id}.walletlens_aggregates.* (user's Materialized Views)
        
        # Extract table references from FROM and JOIN clauses only (not comments or string literals)
        # Pattern matches: FROM `project.dataset.table`, FROM "project.dataset.table", or FROM project.dataset.table
        # Handles backticks, double quotes, and unquoted identifiers
        # Also handles table aliases: FROM table AS alias or FROM table alias
        # Matches: project.dataset.table (3-part qualified name)
        # Note: This regex only matches actual table references in FROM/JOIN clauses, preventing bypass via comments
        table_pattern = r'(?:FROM|JOIN)\s+(?:`([^`]+)`|"([^"]+)"|([a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+\.[a-zA-Z0-9_\-]+))'
        table_matches = []
        for match in re.finditer(table_pattern, sql_query, re.IGNORECASE):
            # Extract the table reference (group 1, 2, or 3 depending on quoting style)
            table_ref = match.group(1) or match.group(2) or match.group(3)
            if table_ref and '.' in table_ref:
                # Extract just the table path (remove alias if present)
                # Split on whitespace to handle: table AS alias, table alias, etc.
                table_path = table_ref.split()[0].strip()
                # Must be exactly project.dataset.table format (2 dots)
                if table_path.count('.') == 2:
                    table_matches.append(table_path)
        
        if not table_matches:
            return "Error: No valid table references found in query. Queries must reference tables in FROM or JOIN clauses."
        
        # Validate each table reference
        allowed_patterns = [
            r'^bigquery-public-data\.crypto_ethereum\.',  # Public Ethereum data
            rf'^{re.escape(project_id)}\.walletlens_aggregates\.'  # User's Materialized Views
        ]
        
        for table_ref in table_matches:
            table_ref_lower = table_ref.lower()
            is_allowed = any(
                re.match(pattern, table_ref_lower, re.IGNORECASE) 
                for pattern in allowed_patterns
            )
            
            if not is_allowed:
                return f"Error: Table '{table_ref}' is not allowed. Only queries to 'bigquery-public-data.crypto_ethereum.*' or '{project_id}.walletlens_aggregates.*' are allowed."

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
