# WalletLens Optimization Setup - Materialized Views

This guide explains how to set up Materialized Views and pre-aggregated tables to dramatically improve query performance and reduce costs.

## Why Materialized Views?

Instead of scanning petabytes of raw transaction data on every query, Materialized Views pre-compute and store aggregated results. This means:
- **Faster queries**: Query pre-aggregated data instead of raw transactions
- **Lower costs**: Scan much less data per query
- **Better scalability**: Can handle full historical data across multiple chains

## Setup Instructions

### Step 1: Run the Setup Script

```bash
cd WalletLens
source ../venv/bin/activate  # or your virtual environment
python setup_aggregations.py
```

This will create:
- **Materialized Views**: `mv_wallet_tx_sent_daily` and `mv_wallet_tx_received_daily` - Daily transaction aggregations
- **Materialized View**: `mv_wallet_token_transfers_daily` - Daily token transfer aggregations

### Step 2: Verify Setup

Check in BigQuery Console:
1. Go to your project in [BigQuery Console](https://console.cloud.google.com/bigquery)
2. Look for dataset: `walletlens_aggregates`
3. Verify the Materialized Views were created

### Step 3: Materialized Views Auto-Refresh

Materialized Views automatically refresh in BigQuery. You can:
- Check refresh status in BigQuery Console
- Set up scheduled refreshes if needed (for production)

## How It Works

**Before (Raw Queries):**
- Every analysis scans raw transaction tables
- Scans 365 days of data = ~100GB+ per query
- Slow and expensive

**After (Materialized Views):**
- Queries pre-aggregated daily summaries
- Scans only relevant days for the address
- Much faster and cheaper

## Query Examples

The planner will automatically prefer Materialized Views when available:

```sql
-- This queries the Materialized View (fast!)
SELECT 
    SUM(tx_count_sent) as total_tx_sent,
    SUM(eth_sent) as total_eth_sent,
    MIN(day) as first_seen
FROM `your-project.walletlens_aggregates.mv_wallet_tx_sent_daily`
WHERE address = LOWER('0x...')
```

If Materialized Views don't exist, it falls back to raw tables automatically.

## Production Considerations

For production scaling:
1. **Incremental Updates**: Set up scheduled queries to update Materialized Views daily
2. **Multi-Chain**: Create separate Materialized Views for Polygon, Base, Optimism
3. **Partitioning**: Views are already partitioned by date for optimal performance
4. **Clustering**: Views are clustered by address for fast lookups

## Cost Optimization

Materialized Views:
- **Storage**: Small cost for storing aggregated data (~GB vs PB)
- **Query Cost**: Much lower (scan aggregated data vs raw tables)
- **Refresh Cost**: One-time cost when Materialized View refreshes

**Trade-off**: Higher storage cost, but dramatically lower query costs for repeated analyses.

