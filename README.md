# WalletLens - Predictive On-Chain Analysis Agent (Team Aegis)

An AI-powered blockchain forensic agent that profiles Ethereum wallet addresses and assesses interaction safety using Google Gemini 2.5 and BigQuery. WalletLens classifies addresses into personas (Bot, Whale, Exploiter, Compromised Wallet, etc.) and provides safety verdicts to help users make informed decisions before interacting with unknown addresses.

## Features

- **Persona Classification**: Identifies wallet types (Merchant/Exchange, Bot/MEV, Whale/Treasury, Exploiter, Compromised Wallet)
- **Safety Assessment**: Provides clear safety verdicts (🟢 SAFE, 🟡 CAUTION, 🔴 HIGH RISK)
- **1-Year Historical Analysis**: Analyzes the last 365 days of transaction history
- **Pattern Detection**: Detects exploit patterns, drain events, and suspicious activity
- **Analysis History**: Stores last 5 analyses for quick reference
- **Full Observability**: Detailed execution logs for transparency

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

## Running the Application

Start the Streamlit application:

```bash
streamlit run src/main.py
```

The application will be available at `http://localhost:8501`

## Usage

1. Enter an Ethereum wallet address (0x followed by 40 hex characters)
2. Click "Analyze Wallet"
3. Review the classification and safety verdict
4. Check execution logs for detailed analysis steps

## Project Structure

```
WalletLens/
├── src/
│   ├── main.py          # Streamlit UI
│   ├── executor.py      # Gemini agent executor
│   ├── planner.py       # System instructions and classification logic
│   ├── tools.py         # BigQuery query tool
│   └── memory.py        # Logging and history management
├── requirements.txt     # Python dependencies
├── env.template        # Environment variable template
└── README.md          # This file
```

## Technologies

- **Google Gemini 2.5 Flash**: AI model for classification and analysis
- **Google BigQuery**: On-chain data queries from public Ethereum dataset
- **Streamlit**: Web interface
- **Python**: Core implementation

## License

Apache 2.0

## Authors

- **Jaya Mandlik** - jaya.ashok.mandlik@gmail.com
- **Katie Li** - katiem3749@gmail.com

## Team

**Team Aegis** - Google ODSC Hackathon 2025 - Dec 12. 2025
