# Technical Explanation

## 1. Agent Workflow

### Step-by-Step Process

1. **Receive User Input**: Streamlit UI captures Ethereum wallet address
2. **Initialize Agent**: Executor creates Gemini model with Planner's system instructions
3. **Generate Analysis Prompt**: Executor sends structured prompt requesting persona classification and safety assessment
4. **Model Reasoning**: Gemini analyzes the prompt and determines it needs blockchain data
5. **Function Call**: Gemini invokes `query_blockchain` tool with SQL query
6. **Query Execution**: Tools module executes SQL on BigQuery public dataset
7. **Result Processing**: Query results formatted as Markdown table and returned to model
8. **Iterative Analysis**: Model may make additional queries if needed (up to 10 iterations)
9. **Final Classification**: Model generates persona classification and safety verdict
10. **Logging**: All steps logged to Memory module for observability
11. **Display Results**: UI shows classification, safety verdict, and execution logs

### Safety-First Protocol

The agent follows a **"Safety First"** reasoning protocol that goes beyond simple balance checks:

#### Flow Direction Analysis
- **Incoming Dominance**: High incoming volume suggests Merchant/Exchange (receiving payments) or Exploiter (receiving stolen funds)
- **Outgoing Dominance**: High outgoing volume suggests Victim (drained wallet) or Payer (normal user)
- **Mixed Patterns**: Balanced flows indicate active trading or business operations

#### Time Concentration Detection
- **Drain Events**: If 90% of volume happens in < 24 hours with multiple tokens → Compromised Wallet
- **Exploit Patterns**: If address is new (< 60 days) and receives massive funds in short window → Exploiter
- **Normal Activity**: Consistent activity over months/years → Legitimate entity

#### Pattern Recognition
- **Multi-Token Dumps**: Sending 3+ different tokens within 1 hour = Drain indicator
- **Sudden Dormancy**: Active address → Zero balance → Dormant = Likely compromised
- **Rapid Fund Movement**: New address + 1000+ ETH in < 30 days = Exploiter pattern

The agent distinguishes "Victims" (compromised wallets) from "Attackers" (exploiters) by analyzing:
- **Address Age**: Victims are established addresses; Attackers are new
- **Activity Window**: Victims show sudden drain; Attackers show rapid accumulation
- **Flow Direction**: Victims send everything out; Attackers receive from multiple sources

## 2. Key Modules

### Planner (`planner.py`)
**Role**: Stores the "Brain" - defines classification logic, safety rules, and SQL templates.

**Key Functions**:
- Provides system instructions to Gemini model
- Defines 5 persona categories with detection patterns
- Establishes safety verdict criteria
- Supplies optimized SQL query templates
- Enforces performance rules (no SELECT *, specific columns only)

**Classification Logic**:
- **Merchant/Exchange**: Constant activity, high incoming volume
- **Bot/MEV**: Extreme frequency (>1000 txs), automated timing
- **Whale/Treasury**: High value, low frequency, long history (>1 year)
- **Exploiter**: New address (<60 days) + massive incoming funds (1000+ ETH)
- **Compromised Wallet**: Established address → sudden drain to zero

### Executor (`executor.py`)
**Role**: The "Engine" - manages Gemini model and function calling loop.

**Key Functions**:
- Initializes Gemini 2.5 Flash model with system instructions
- Configures function calling with `query_blockchain` tool
- Manages iterative function call loop (up to 10 iterations)
- Handles model fallback (tries multiple model names)
- Processes function responses and extracts final analysis

**Function Calling Flow**:
1. Send prompt to Gemini
2. Check for function calls in response
3. Execute function (query_blockchain)
4. Send function result back to model
5. Repeat until final text response

### Memory (`memory.py`)
**Role**: The "Black Box" - provides observability through logging.

**Key Functions**:
- `WalletMemory`: Logs every execution step with timestamps
- `AnalysisHistory`: Stores last 5 analyses for quick reference
- Tracks SQL queries, errors, and execution flow
- Provides logs for user transparency in UI

**Observability Features**:
- Step-by-step execution logging
- SQL query logging (truncated for display)
- Error tracking with full details
- Analysis history with classification and safety verdict

### Tools (`tools.py`)
**Role**: The "Hands" - executes BigQuery queries.

**Key Functions**:
- Connects to BigQuery with project credentials
- Validates SQL queries (security: only `crypto_ethereum` dataset)
- Executes queries with 100GB billing limit
- Formats results as Markdown tables
- Handles errors gracefully

**Security & Performance**:
- Security check: Only allows `bigquery-public-data.crypto_ethereum` queries
- Billing protection: `maximum_bytes_billed=100GB` prevents overspending
- Result limiting: Returns max 20 rows as Markdown

## 3. Tool Integration

### Native Function Calling (Not LangChain)

We use **Gemini's native function calling** (not LangChain) for better reliability and performance:

**Advantages**:
- **Direct Integration**: No abstraction layer, direct API calls
- **Better Error Handling**: Native error messages from Gemini
- **Performance**: Lower latency without middleware
- **Reliability**: Fewer dependencies, fewer failure points

**Implementation**:
```python
# Function declaration in Executor
tools = [{
    "function_declarations": [{
        "name": "query_blockchain",
        "description": "Query Ethereum blockchain data...",
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {"type": "string", ...}
            }
        }
    }]
}]

# Model initialization with tools
model = genai.GenerativeModel(
    model_name='models/gemini-2.5-flash',
    system_instruction=system_instruction,
    tools=tools
)
```

**Function Call Loop**:
- Model generates function call request
- Executor extracts SQL query from function call
- Tools module executes query
- Executor sends result back to model as FunctionResponse
- Model processes result and generates final analysis

## 4. Planning Style: SQL Optimization Strategy

### Partition Filtering

We use **partition filtering** to limit data scanned:

```sql
WHERE block_timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
```

This ensures we only scan the last 365 days of data, dramatically reducing:
- Query execution time
- Data scanned (cost)
- Memory usage

### Specific Column Selection

**Critical Rule**: Never use `SELECT *`

Instead, we only select the columns needed:
```sql
SELECT 
    from_address,
    to_address,
    value,
    block_timestamp
FROM `bigquery-public-data.crypto_ethereum.transactions`
```

**Benefits**:
- Reduces data scanned by 70-80%
- Faster query execution
- Lower BigQuery costs
- Better performance

### Aggregation-First Approach

We use aggregations instead of fetching rows:
```sql
SELECT 
    COUNT(*) as tx_count,
    SUM(value)/1e18 as total_eth,
    MIN(block_timestamp) as first_seen,
    MAX(block_timestamp) as last_seen
```

This approach:
- Processes data in BigQuery (not in Python)
- Returns minimal data (aggregated results)
- Faster than fetching thousands of rows

### Query Templates

The Planner provides optimized SQL templates that:
- Include 1-year timestamp filter
- Select only needed columns
- Use aggregations
- Include monthly breakdowns for pattern detection

## 5. Observability & Testing

### Execution Logging

Every step is logged to Memory:
- Model initialization
- SQL query generation
- Query execution
- Result processing
- Errors and exceptions

Users can view detailed logs in the UI expander.

### Analysis History

Last 5 analyses are stored in session state:
- Address
- Classification
- Safety verdict
- Full result text
- Timestamp

Users can quickly reference previous analyses.

### Error Handling

Comprehensive error handling at each layer:
- **Configuration Errors**: Missing API keys, project IDs
- **Model Errors**: Model initialization failures, function call errors
- **Query Errors**: SQL syntax errors, BigQuery limits, authentication issues
- **Display Errors**: UI rendering issues

All errors are logged and displayed to users with helpful messages.

## 6. Known Limitations

### Data Source Limitations

1. **Public Dataset Latency**: 
   - `bigquery-public-data.crypto_ethereum` may have 1-2 day latency
   - Recent transactions (< 24 hours) may not be available
   - Solution: For real-time data, would need private BigQuery dataset

2. **Ethereum Mainnet Only**:
   - Currently limited to Ethereum mainnet
   - Does not support L2s (Polygon, Arbitrum, etc.) or other chains
   - Solution: Would need additional datasets for other chains

### Performance Limitations

1. **Query Execution Time**:
   - 1-year scans can take 10-30 seconds
   - BigQuery Storage API helps but still has network latency
   - Solution: Could implement query result caching

2. **Model Response Time**:
   - Gemini function calling adds 2-5 seconds per iteration
   - Multiple iterations can add up
   - Solution: Could optimize prompts to reduce iterations

### Classification Limitations

1. **Pattern-Based Detection**:
   - Relies on transaction patterns, not external labels
   - May misclassify sophisticated exploiters
   - Solution: Could integrate with security services (Lookonchain, etc.)

2. **False Positives**:
   - New addresses with legitimate large transfers may be flagged
   - Whales with new addresses may be misclassified
   - Solution: Could add whitelist or manual override

3. **Limited Context**:
   - Only analyzes on-chain data
   - Doesn't consider off-chain context (social media, known entities)
   - Solution: Could integrate external data sources

### Scalability Limitations

1. **Single User Interface**:
   - Streamlit app is single-user by default
   - No authentication or rate limiting
   - Solution: Would need deployment infrastructure for multi-user

2. **Session-Based History**:
   - Analysis history is session-based (lost on refresh)
   - No persistent storage
   - Solution: Could add database for persistent history

### Cost Considerations

1. **BigQuery Costs**:
   - 1-year scans can scan 10-50GB of data
   - Free tier: 1TB/month, then $5/TB
   - Solution: Query optimization and caching reduce costs

2. **Gemini API Costs**:
   - Function calling uses more tokens
   - Multiple iterations increase costs
   - Solution: Prompt optimization to reduce iterations
