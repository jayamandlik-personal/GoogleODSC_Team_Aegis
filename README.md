# WalletLens - Predictive On-Chain Analysis Agent (Team Aegis)

An AI-powered blockchain forensic agent that profiles on-chain wallet addresses and assesses interaction safety using Google Gemini 2.5 and BigQuery. WalletLens classifies addresses into personas (Bot, Whale, Exploiter, Compromised Wallet, etc.) and provides safety verdicts to help users make informed decisions before interacting with unknown addresses.

## Features

- **Persona Classification**: Identifies wallet types (Merchant/Exchange, Bot/MEV, Whale/Treasury, Exploiter, Compromised Wallet)
- **Safety Assessment**: Provides clear safety verdicts (🟢 SAFE, 🟡 CAUTION, 🔴 HIGH RISK)
- **Protection Layer**: Assistive risk assessment with signals, confidence, and protective actions (no scores, no blocking decisions)
- **1-Year Historical Analysis**: Analyzes the last 365 days of transaction history
- **Pattern Detection**: Detects exploit patterns, drain events, and suspicious activity
- **Analysis History**: Stores last 5 analyses for quick reference
- **Full Observability**: Detailed execution logs for transparency
- **Performance Optimized**: Uses BigQuery Materialized Views for fast queries (optional setup)
- **Multi-Stakeholder Views**: Different output formats for Users, Customers/Treasury, VASPs, and Financial Institutions

## Setup

### Prerequisites

- Python 3.8+
- Google Cloud Project with BigQuery API enabled
- Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd WalletLens
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the `WalletLens/` directory:
   ```bash
   cp env.template .env
   ```
   
   Edit `.env` and add your credentials:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id_here
   ```

4. **Authenticate with Google Cloud** (Critical Step)
   
   For BigQuery access, you must authenticate:
   ```bash
   gcloud auth application-default login
   ```
   
   This command will open a browser window for authentication. Follow the prompts to complete the setup.

5. **Enable BigQuery API**
   
   Ensure BigQuery API is enabled for your project:
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/library/bigquery.googleapis.com)
   - Select your project
   - Click "Enable"

6. **Optional: Setup Performance Optimization (Recommended)**
   
   For faster queries and lower costs, set up Materialized Views:
   ```bash
   cd WalletLens
   python setup_aggregations.py
   ```
   
   This creates pre-aggregated tables that dramatically improve query performance. See `OPTIMIZATION_SETUP.md` for details.

## Running the Application

Start the Streamlit application:

```bash
streamlit run src/main.py
```

The application will be available at `http://localhost:8501`

## Usage

1. Enter an on-chain wallet address (0x followed by 40 hex characters for Ethereum)
2. Click "Analyze Wallet"
3. Review the classification and safety verdict
4. Explore different stakeholder views (User, Customer/Treasury, VASP, Financial Institution)
5. Toggle AI Recommendations in the sidebar to show/hide warnings and protections
6. Click buttons to load additional views on-demand (Customer/Treasury, VASP, FI, Logs)
7. Check execution logs for detailed analysis steps

## Protection Layer (Assistive Mode)

WalletLens includes a **Protection Layer** that provides assistive risk assessment without making deterministic decisions or blocking actions. This layer follows core principles:

### Core Principles

- **No Numeric Risk Scores**: We don't output risk scores that could be misinterpreted as guarantees
- **No Blocking Decisions**: We don't output deterministic decisions like BLOCK, ALLOW, or STEP_UP_AUTH
- **Signals → Confidence → Protective Actions**: We provide observed signals, confidence levels, and recommended protective actions
- **Low-Claim Language**: Uses soft language like "signals observed", "may be consistent with", avoiding definitive claims
- **User-Controlled**: AI Recommendations toggle lets users choose whether to see warnings and protections

### What the Protection Layer Provides

1. **Observed Signals**: Coded signals derived from facts/metrics (e.g., SHORT_LIVED, HIGH_VALUE_FLOW, OUTFLOW_DOMINANT)
2. **Interpretation**: Soft-language interpretation of what signals may indicate
3. **Confidence / Data Quality**: Transparent about data limitations (missing MVs, bytes billed exceeded, partial data)
4. **Protection Recommendations**: Suggested protective actions (e.g., SUGGEST_TEST_AMOUNT, AVOID_SIGNING_APPROVALS, USE_SEPARATE_SPENDING_WALLET)

### AI Recommendations

- **ON (default)**: Shows warnings, signals, and protective recommendations
- **OFF**: Shows only facts, classification, verdict, and data quality

### Stakeholder Views

The Protection Layer provides different views for different stakeholders:

- **User View**: Plain English summary with top 3 signals and protections
- **Customer/Treasury View**: Setup guidance, controls checklist, and training tips
- **VASP/Wallet Provider View**: Machine-readable JSON output for integration
- **Financial Institution View**: Evidence-based indicators, data limitations, recommended controls, and audit trace

### Data Quality Handling

The Protection Layer explicitly handles:
- **Missing Materialized Views**: Detects when optimized aggregates are unavailable
- **Bytes Billed Exceeded**: Detects BigQuery query limits and adjusts confidence accordingly
- **Partial Data**: Flags when analysis is incomplete due to query failures

See the codebook in the codebase for the complete signal and protection code definitions.

## Integration Options

WalletLens can be integrated into your platform through multiple methods:

### REST API

HTTP REST API endpoints for synchronous wallet analysis:

- `POST /api/v1/analyze` - Analyze a single wallet address
- `GET /api/v1/analysis/{address}` - Retrieve cached analysis
- `POST /api/v1/batch` - Analyze multiple addresses
- Returns JSON with ProtectionReport structure
- Supports all stakeholder views (User, VASP, FI, Customer)

**Example Request:**
```bash
curl -X POST https://api.walletlens.com/v1/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "address": "0x...",
    "view": "user",
    "ai_recommendations": true
  }'
```

**Example Response:**
```json
{
  "address": "0x...",
  "classification": "Exploiter",
  "verdict": "HIGH RISK",
  "confidence_level": "HIGH",
  "observed_signals": [...],
  "recommended_protections": [...],
  "data_quality": {...}
}
```

### Webhook Integration

Event-driven webhooks for asynchronous analysis and alerts:

- Subscribe to wallet analysis events
- Receive notifications when risky addresses are detected
- Custom webhook endpoints for your application
- Retry mechanism for failed deliveries
- Payload includes full ProtectionReport

**Use Cases:**
- Real-time monitoring and alerting
- Integration with incident response systems
- Automated compliance workflows

**Example Webhook Payload:**
```json
{
  "event": "wallet.analysis.complete",
  "address": "0x...",
  "protection_report": {...},
  "timestamp": "2025-12-12T10:00:00Z"
}
```

### WebSocket API

Real-time bidirectional communication for live analysis:

- Stream analysis results as they're generated
- Subscribe to multiple addresses simultaneously
- Low-latency updates for real-time applications
- Connection management and reconnection handling

**Use Cases:**
- Live transaction monitoring
- Real-time dashboards
- Interactive wallet screening tools

### SDK / Client Libraries

Language-specific SDKs for easy integration:

- **Python SDK**: `pip install walletlens-python`
- **JavaScript/TypeScript SDK**: `npm install @walletlens/sdk`
- **Go SDK**: `go get github.com/walletlens/go-sdk`
- Type-safe interfaces for ProtectionReport
- Built-in error handling and retries
- Local caching support

**Example Python SDK:**
```python
from walletlens import WalletLensClient

client = WalletLensClient(api_key="YOUR_API_KEY")
report = client.analyze("0x...", view="user", ai_recommendations=True)
print(f"Classification: {report.classification}")
print(f"Verdict: {report.verdict}")
```

### Platform Integration Examples

#### Web3 Wallets (MetaMask, WalletConnect, etc.)
- **Integration**: API call before transaction confirmation
- **Implementation**: Show ProtectionReport in transaction UI
- **Use Case**: Users verify recipient addresses before sending funds

#### DeFi Platforms (Uniswap, Aave, etc.)
- **Integration**: API integration to check addresses
- **Implementation**: Display warnings based on ProtectionReport
- **Use Case**: Warn users about risky addresses in UI

#### Crypto Exchanges (Binance, Coinbase, etc.)
- **Integration**: API for deposit address screening
- **Implementation**: Webhook alerts for high-risk addresses
- **Use Case**: Screen deposit addresses and detect exploiters

#### Financial Institutions
- **Integration**: API for compliance workflows
- **Implementation**: Financial Institution view for audit trails
- **Use Case**: Screen addresses for regulatory compliance, generate audit reports

#### Treasury Management
- **Integration**: API integration with Customer/Treasury view
- **Implementation**: Setup guidance and controls checklist
- **Use Case**: Verify counterparties, implement treasury controls

## Project Structure

```
WalletLens/
├── src/
│   ├── main.py              # Streamlit UI
│   ├── executor.py          # Gemini agent executor
│   ├── planner.py           # System instructions and classification logic
│   ├── tools.py             # BigQuery query tool
│   ├── memory.py            # Logging and history management
│   ├── protection_models.py # Protection report data models
│   ├── signals_extractor.py # Signal extraction from metrics
│   ├── tool_error_parser.py # Error parsing from logs
│   ├── protection_advisor.py # Rule-based protection recommendations
│   └── stakeholder_views.py # Stakeholder-specific rendering
├── setup_aggregations.py    # BigQuery Materialized Views setup script
├── OPTIMIZATION_SETUP.md    # Performance optimization guide
├── requirements.txt         # Python dependencies
├── env.template            # Environment variable template
└── README.md               # This file
```

## Technologies

- **Google Gemini 2.5 Flash**: AI model for classification and analysis
- **Google BigQuery**: On-chain data queries from public Ethereum dataset
- **BigQuery Materialized Views**: Pre-aggregated tables for performance optimization
- **Streamlit**: Web interface
- **Python**: Core implementation

## Performance

WalletLens is optimized for fast queries and cost efficiency:

- **Query Optimization**: 1-year lookback with partition filtering, specific column selection, and aggregations
- **Materialized Views**: Optional pre-aggregated tables reduce query time from 30-60 seconds to 2-5 seconds
- **BigQuery Storage API**: Faster data retrieval using gRPC protocol
- **Smart Fallback**: Automatically uses Materialized Views when available, falls back to raw tables otherwise

## License

Apache 2.0

## Authors

- **Jaya Mandlik** - jaya.ashok.mandlik@gmail.com
- **Katie Li** - katiem3749@gmail.com

## Team

**Team Aegis** - Google ODSC Hackathon 2025 - Dec 12. 2025
