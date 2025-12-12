"""Setup script to create Materialized Views and pre-aggregated summary tables for WalletLens.

This script creates optimized views/tables that pre-compute wallet statistics to avoid
scanning petabytes of data on every query.

Run this once to set up the optimized data structures in your BigQuery project.
"""

import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv(override=True)

def create_dataset_if_not_exists(client: bigquery.Client, dataset_id: str):
    """Create a dataset if it doesn't exist."""
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_id} already exists")
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        dataset = client.create_dataset(dataset, exists_ok=True)
        print(f"Created dataset {dataset_id}")

def setup_materialized_views(client: bigquery.Client, project_id: str, dataset_id: str = "walletlens_aggregates"):
    """Create Materialized Views for pre-aggregated wallet statistics."""
    
    # Create dataset
    create_dataset_if_not_exists(client, dataset_id)
    
    # Materialized View 1: Daily wallet aggregations (transactions) - sent
    mv_transactions_sent = f"""
    CREATE MATERIALIZED VIEW IF NOT EXISTS `{project_id}.{dataset_id}.mv_wallet_tx_sent_daily`
    PARTITION BY DATE(day)
    CLUSTER BY address
    AS
    SELECT 
        DATE(block_timestamp) as day,
        LOWER(from_address) as address,
        COUNT(*) as tx_count_sent,
        SUM(value)/1e18 as eth_sent,
        COUNT(DISTINCT to_address) as unique_receivers
    FROM `bigquery-public-data.crypto_ethereum.transactions`
    WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
    GROUP BY day, address
    """
    
    # Materialized View 1b: Daily wallet aggregations (transactions) - received
    mv_transactions_received = f"""
    CREATE MATERIALIZED VIEW IF NOT EXISTS `{project_id}.{dataset_id}.mv_wallet_tx_received_daily`
    PARTITION BY DATE(day)
    CLUSTER BY address
    AS
    SELECT 
        DATE(block_timestamp) as day,
        LOWER(to_address) as address,
        COUNT(*) as tx_count_received,
        SUM(value)/1e18 as eth_received,
        COUNT(DISTINCT from_address) as unique_senders
    FROM `bigquery-public-data.crypto_ethereum.transactions`
    WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
    GROUP BY day, address
    """
    
    # Materialized View 2: Token transfer aggregations
    mv_token_transfers = f"""
    CREATE MATERIALIZED VIEW IF NOT EXISTS `{project_id}.{dataset_id}.mv_wallet_token_transfers_daily`
    PARTITION BY DATE(day)
    CLUSTER BY address
    AS
    SELECT 
        DATE(block_timestamp) as day,
        LOWER(from_address) as address,
        COUNT(DISTINCT token_address) as unique_tokens_sent,
        COUNT(*) as token_tx_count
    FROM `bigquery-public-data.crypto_ethereum.token_transfers`
    WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
    GROUP BY day, address
    """
    
    # Summary Table: Wallet-level aggregations (updated daily)
    summary_table = f"""
    CREATE TABLE IF NOT EXISTS `{project_id}.{dataset_id}.wallet_summary_1y`
    (
        address STRING,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP,
        total_tx_count INT64,
        total_eth_received FLOAT64,
        total_eth_sent FLOAT64,
        unique_receivers INT64,
        unique_senders INT64,
        unique_tokens_sent INT64,
        last_updated TIMESTAMP
    )
    PARTITION BY DATE(last_updated)
    CLUSTER BY address
    """
    
    queries = [
        ("Materialized View: Daily Transactions (Sent)", mv_transactions_sent),
        ("Materialized View: Daily Transactions (Received)", mv_transactions_received),
        ("Materialized View: Token Transfers", mv_token_transfers),
        ("Summary Table: Wallet Aggregations", summary_table)
    ]
    
    for name, query in queries:
        try:
            print(f"\nCreating {name}...")
            job = client.query(query)
            job.result()  # Wait for completion
            print(f"✅ {name} created successfully")
        except Exception as e:
            print(f"❌ Error creating {name}: {str(e)}")
            # Continue with other views even if one fails

def main():
    """Main setup function."""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if not project_id:
        print("Error: GOOGLE_CLOUD_PROJECT not found in .env")
        return
    
    print(f"Setting up aggregations for project: {project_id}")
    print("⚠️  Note: Materialized Views may take time to build initially (scanning 365 days of data)")
    print("    This is a one-time cost. Subsequent queries will be much faster!\n")
    
    client = bigquery.Client(project=project_id)
    
    setup_materialized_views(client, project_id)
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Check BigQuery Console to verify Materialized Views were created")
    print("2. Materialized Views will auto-refresh periodically")
    print("3. The planner will automatically use these views when available")
    print("4. For production, set up scheduled refreshes via BigQuery Scheduled Queries")
    print("\n💡 Tip: First query may be slow while Materialized View builds. Subsequent queries will be fast!")

if __name__ == "__main__":
    main()

