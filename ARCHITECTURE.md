# Architecture Overview

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                      (Streamlit - main.py)                       │
│                                                                   │
│  ┌──────────────┐                                                │
│  │ Wallet Input │ ───────────────────────────────────────────┐  │
│  └──────────────┘                                              │  │
│                                                                 │  │
└─────────────────────────────────────────────────────────────────┘  │
                                                                     │
                                                                     │
┌─────────────────────────────────────────────────────────────────┐ │
│                      EXECUTOR (executor.py)                      │ │
│                    "The Engine"                                  │ │
│                                                                   │ │
│  ┌─────────────────────────────────────────────────────────┐   │ │
│  │ 1. Initialize Gemini Model (2.5 Flash)                  │   │ │
│  │ 2. Configure Function Calling (query_blockchain tool)   │   │ │
│  │ 3. Manage Function Call Loop (max 10 iterations)        │   │ │
│  │ 4. Handle Model Fallback Logic                          │   │ │
│  └─────────────────────────────────────────────────────────┘   │ │
│                            │                                     │ │
│                            │ System Instructions                 │ │
│                            ▼                                     │ │
└─────────────────────────────────────────────────────────────────┘ │
                                                                     │
┌─────────────────────────────────────────────────────────────────┐ │
│                      PLANNER (planner.py)                        │ │
│                      "The Brain"                                 │ │
│                                                                   │ │
│  ┌─────────────────────────────────────────────────────────┐   │ │
│  │ • Persona Classification Rules                          │   │ │
│  │ • Safety Assessment Logic                                │   │ │
│  │ • SQL Query Templates (1-year optimized)                │   │ │
│  │ • Exploit Detection Patterns                             │   │ │
│  │ • Drain Detection Logic                                  │   │ │
│  └─────────────────────────────────────────────────────────┘   │ │
│                            │                                     │ │
│                            │ Function Call                       │ │
│                            ▼                                     │ │
└─────────────────────────────────────────────────────────────────┘ │
                                                                     │
┌─────────────────────────────────────────────────────────────────┐ │
│                      TOOLS (tools.py)                           │ │
│                      "The Hands"                                 │ │
│                                                                   │ │
│  ┌─────────────────────────────────────────────────────────┐   │ │
│  │ • BigQuery Client Initialization                        │   │ │
│  │ • Security Validation (crypto_ethereum + MVs)          │   │ │
│  │ • Query Execution (100GB limit)                         │   │ │
│  │ • Result Formatting (Markdown tables)                   │   │ │
│  └─────────────────────────────────────────────────────────┘   │ │
│                            │                                     │ │
│                            │ SQL Query                           │ │
│                            ▼                                     │ │
└─────────────────────────────────────────────────────────────────┘ │
                                                                     │
┌─────────────────────────────────────────────────────────────────┐ │
│              BIGQUERY DATA SOURCES                                 │ │
│                                                                   │ │
│  ┌─────────────────────────────────────────────────────────┐   │ │
│  │ OPTIMIZED (Priority):                                   │   │ │
│  │ • Materialized Views (walletlens_aggregates)           │   │ │
│  │   - mv_wallet_tx_sent_daily                             │   │ │
│  │   - mv_wallet_tx_received_daily                         │   │ │
│  │   - mv_wallet_token_transfers_daily                     │   │ │
│  └─────────────────────────────────────────────────────────┘   │ │
│                            │                                     │ │
│                            │ (Fallback if MVs unavailable)      │ │
│                            ▼                                     │ │
│  ┌─────────────────────────────────────────────────────────┐   │ │
│  │ RAW TABLES:                                              │   │ │
│  │ • bigquery-public-data.crypto_ethereum                  │   │ │
│  │   - transactions (ETH transfers)                         │   │ │
│  │   - traces (internal calls)                              │   │ │
│  │   - token_transfers (ERC-20)                             │   │ │
│  └─────────────────────────────────────────────────────────┘   │ │
│                                                                   │ │
└─────────────────────────────────────────────────────────────────┘ │
                                                                     │
┌─────────────────────────────────────────────────────────────────┐ │
│                    MEMORY (memory.py)                            │ │
│                    "The Black Box"                               │ │
│                                                                   │ │
│  ┌─────────────────────────────────────────────────────────┐   │ │
│  │ • Step-by-step execution logging                         │   │ │
│  │ • SQL query logging                                      │   │ │
│  │ • Error tracking                                         │   │ │
│  │ • Analysis history (last 5)                              │   │ │
│  └─────────────────────────────────────────────────────────┘   │ │
│                            │                                     │ │
│                            │ Logs                                │ │
│                            ▼                                     │ │
└─────────────────────────────────────────────────────────────────┘ │
                                                                     │
                            ┌─────────────┐                         │
                            │   USER UI   │                         │
                            │  (Display)  │                         │
                            └─────────────┘                         │
```

## Core Modules

### 1. Planner (`planner.py`) - "The Brain"

**Purpose**: Stores the system instructions and classification logic that guide the Gemini model.

**Key Responsibilities**:
- Defines persona classification rules (Merchant, Bot, Whale, Exploiter, Compromised Wallet)
- Establishes safety assessment criteria (🟢 SAFE, 🟡 CAUTION, 🔴 HIGH RISK)
- Provides optimized SQL query templates for 1-year lookback analysis
- Contains exploit detection patterns (new address + massive funds)
- Implements drain detection logic (sudden multi-token dumps)
- Enforces performance rules (no SELECT *, specific column selection)

**Key Features**:
- 1-year timestamp filtering: `block_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)`
- Column-specific queries to minimize data scanned
- Monthly activity breakdowns for pattern detection
- **Materialized View Priority**: Prefers pre-aggregated Materialized Views for faster queries
- **Smart Fallback**: Falls back to raw tables if Materialized Views unavailable

### 2. Executor (`executor.py`) - "The Engine"

**Purpose**: Initializes and manages the Gemini model with function calling capabilities.

**Key Responsibilities**:
- Initializes Gemini 2.5 Flash model with system instructions from Planner
- Configures function calling with `query_blockchain` tool
- Manages the function call loop (up to 10 iterations)
- Handles model fallback logic (tries multiple model names)
- Processes function responses and sends them back to the model
- Extracts final text response from the model

**Key Features**:
- Model fallback: Tries multiple Gemini model names for compatibility
- Function call loop: Handles multiple tool invocations in sequence
- Error handling: Gracefully handles model initialization failures
- Memory integration: Logs all execution steps

### 3. Memory (`memory.py`) - "The Black Box"

**Purpose**: Provides observability through step-by-step logging and analysis history.

**Key Responsibilities**:
- Logs every execution step with timestamps
- Tracks SQL query generation and execution
- Records errors and exceptions
- Stores analysis history (last 5 analyses)
- Provides execution logs for user transparency

**Key Features**:
- `WalletMemory`: Step-by-step execution logging
- `AnalysisHistory`: Stores last 5 analyses with classification and safety verdict
- Timestamp tracking for all operations
- Session-based history storage (Streamlit)

### 4. Tools (`tools.py`) - "The Hands"

**Purpose**: Connects to BigQuery and executes SQL queries on the Ethereum public dataset.

**Key Responsibilities**:
- Initializes BigQuery client with project credentials
- Validates SQL queries (security check: only `crypto_ethereum` dataset)
- Executes queries with 100GB billing limit
- Formats results as Markdown tables
- Handles errors and returns user-friendly messages

**Key Features**:
- Security validation: Only allows queries to `bigquery-public-data.crypto_ethereum` or Materialized Views in user's project
- Billing protection: `maximum_bytes_billed=100GB` prevents overspending
- Result formatting: Returns Markdown tables (max 20 rows)
- Error handling: Returns descriptive error messages
- **Materialized View Support**: Allows queries to optimized pre-aggregated tables

## Data Flow

1. **User Input** → Streamlit UI receives wallet address
2. **Executor Initialization** → Creates Gemini model with Planner's system instructions
3. **Prompt Generation** → Executor sends analysis prompt to Gemini
4. **Function Call** → Gemini requests `query_blockchain` tool
5. **Query Execution** → Tools module executes SQL on BigQuery
6. **Result Processing** → Tools formats result as Markdown
7. **Response Loop** → Executor sends result back to Gemini, repeats if needed
8. **Final Analysis** → Gemini generates classification and safety verdict
9. **Memory Logging** → All steps logged to Memory module
10. **UI Display** → Results shown to user with execution logs

## Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **AI Model**: Google Gemini 2.5 Flash (with native function calling)
- **Data Source**: Google BigQuery Public Dataset (`crypto_ethereum`) + Materialized Views
- **Language**: Python 3.8+
- **Key Libraries**: 
  - `google-generativeai`: Gemini API
  - `google-cloud-bigquery`: BigQuery client
  - `google-cloud-bigquery-storage`: Fast gRPC-based data retrieval
  - `streamlit`: Web UI
  - `pandas`: Data processing

## Performance Architecture

### Query Optimization Strategy

1. **Materialized Views (Priority)**: Pre-aggregated daily transaction and token transfer data
   - Partitioned by date for fast time-range queries
   - Clustered by address for fast address lookups
   - Automatically refreshed daily
   - Reduces query time from 30-60 seconds to 2-5 seconds
   - Reduces data scanned from GB/TB to MB/GB

2. **Raw Tables (Fallback)**: Direct queries to `bigquery-public-data.crypto_ethereum`
   - Used when Materialized Views unavailable
   - Optimized with 1-year timestamp filtering
   - Specific column selection (no SELECT *)
   - Aggregation-first approach

3. **BigQuery Storage API**: gRPC-based data retrieval
   - Faster than REST API
   - Better for large result sets
   - Enabled via `google-cloud-bigquery-storage` package

### Setup Script

The `setup_aggregations.py` script creates Materialized Views:
- `mv_wallet_tx_sent_daily`: Daily outgoing transaction aggregations
- `mv_wallet_tx_received_daily`: Daily incoming transaction aggregations
- `mv_wallet_token_transfers_daily`: Daily token transfer aggregations

See `OPTIMIZATION_SETUP.md` for detailed setup instructions.
