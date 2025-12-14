# Demo Video

## 📺 Hosted Public Video Link

[Watch Demo Video](https://drive.google.com/file/d/1Mt3gBcvVHFR2qCvk16aRX-SZEjIM-Kf3/view?usp=drive_link)

## Demo Video Timestamps

### 00:00–00:30 — Intro & Setup

- Introduce WalletLens and the problem it solves: identifying who a wallet might be and how to interact safely
- Briefly explain the approach: AI agent + on-chain data (BigQuery Ethereum public dataset)
- Clarify the design choice: assistive, no guarantees, no risk scoring

### 00:30–01:30 — User Input → Planning

- Enter an Ethereum wallet address in the UI
- Explain the planning step:
  - Agent decides which signals to analyze (activity window, value flow, transaction patterns)
  - Applies cost-aware constraints (365-day lookback, aggregation-first queries)
- Mention persona categories and high-level safety verdicts

### 01:30–02:30 — Tool Calls & Memory

- Show the agent making BigQuery tool calls via function calling
- Highlight:
  - Use of optimized materialized views when available
  - Fallback to raw tables when views are missing
  - Hard bytes-billed limit to prevent runaway costs
- Show execution logs and explain the memory/observability layer
- Mention that partial failures are captured, not hidden

### 02:30–03:30 — Final Output & Edge Case Handling

- Show the final classification and safety verdict
- Walk through the Protection Layer:
  - Observed signals
  - Confidence and data quality
  - Recommended protective actions (no blocking, no risk score)
- Highlight edge cases:
  - Missing materialized views
  - Bytes billed exceeded
  - How confidence is adjusted and limitations are communicated
- Mention stakeholder views (user, VASP, FI, customer/treasury) and the Safety Mode toggle

---

# About WalletLens

**WalletLens** is an AI-powered blockchain forensic agent that profiles on-chain wallet addresses and provides assistive risk assessment using Google Gemini 2.5 and BigQuery. Unlike traditional risk scoring systems, WalletLens focuses on **signals, confidence, and protective actions** rather than deterministic blocking decisions.

Currently supports **Ethereum** with plans to expand to other blockchain networks.

## What Makes WalletLens Different

- **No Risk Scores**: We don't output numeric scores that could be misinterpreted as guarantees
- **No Blocking Decisions**: We provide recommendations, not BLOCK/ALLOW commands
- **Assistive Mode**: Users control what they see with AI Recommendations toggle
- **Multi-Stakeholder Views**: Different outputs for Users, Businesses, VASPs, and Financial Institutions
- **Transparent Data Quality**: Clear indicators when analysis is partial or limited

## 🎯 Key Features

### Core Features
- **Persona Classification**: Identifies wallet types (Merchant/Exchange, Bot/MEV, Whale/Treasury, Exploiter, Compromised Wallet)
- **Safety Assessment**: Clear risk verdicts (🟢 SAFE, 🟡 CAUTION, 🔴 HIGH RISK)
- **Protection Layer**: Signals, confidence levels, and protective action recommendations
- **1-Year Analysis**: Comprehensive historical data (365 days)
- **Pattern Detection**: Exploit and drain detection

### User Experience Features
- **AI Recommendations**: Toggle to show/hide protective recommendations
- **Multi-View Output**: User, Customer/Treasury, VASP, and Financial Institution views
- **Analysis History**: Quick access to recent analyses
- **Full Observability**: Detailed execution logs
- **Performance Optimized**: Optional Materialized Views for fast queries

## 🔌 Integration Options

WalletLens can be integrated into various platforms and services through multiple integration methods:

### 📡 Integration Methods

#### 🔧 REST API
**Description:** HTTP REST API endpoints for synchronous wallet analysis

**Features:**
- POST /api/v1/analyze - Analyze a single wallet address
- GET /api/v1/analysis/{address} - Retrieve cached analysis
- POST /api/v1/batch - Analyze multiple addresses
- Returns JSON with ProtectionReport structure
- Supports all stakeholder views (User, VASP, FI, Customer)

**Use Cases:**
- Real-time wallet checks in applications
- Batch processing for compliance screening
- Integration into existing backend systems

#### 🔧 Webhook Integration
**Description:** Event-driven webhooks for asynchronous analysis and alerts

**Features:**
- Subscribe to wallet analysis events
- Receive notifications when risky addresses are detected
- Custom webhook endpoints for your application
- Retry mechanism for failed deliveries
- Payload includes full ProtectionReport

**Use Cases:**
- Real-time monitoring and alerting
- Integration with incident response systems
- Automated compliance workflows

#### 🔧 WebSocket API
**Description:** Real-time bidirectional communication for live analysis

**Features:**
- Stream analysis results as they're generated
- Subscribe to multiple addresses simultaneously
- Low-latency updates for real-time applications
- Connection management and reconnection handling

**Use Cases:**
- Live transaction monitoring
- Real-time dashboards
- Interactive wallet screening tools

#### 🔧 SDK / Client Libraries
**Description:** Language-specific SDKs for easy integration

**Features:**
- Python, JavaScript/TypeScript, Go SDKs available
- Type-safe interfaces for ProtectionReport
- Built-in error handling and retries
- Local caching support

**Use Cases:**
- Quick integration into existing codebases
- Type-safe development
- Simplified error handling

### 🌐 Platform Integrations

#### 🔗 Web3 Wallets
- **Description:** MetaMask, WalletConnect, Coinbase Wallet - Add safety checks before transactions
- **Integration Method:** API call before transaction confirmation, show ProtectionReport in UI
- **Use Case:** Users can verify recipient addresses before sending funds

#### 🔗 DeFi Platforms
- **Description:** Uniswap, Aave, Compound - Screen liquidity providers and counterparties
- **Integration Method:** API integration to check addresses, display warnings based on ProtectionReport
- **Use Case:** Platforms can warn users about risky addresses in their UI

#### 🔗 NFT Marketplaces
- **Description:** OpenSea, LooksRare, Blur - Verify seller/buyer addresses
- **Integration Method:** Webhook or API to flag suspicious accounts, show Persona classification
- **Use Case:** Marketplaces can flag suspicious accounts automatically

#### 🔗 Crypto Exchanges
- **Description:** Binance, Coinbase, Kraken - Enhanced KYC and risk assessment
- **Integration Method:** API for deposit address screening, webhook alerts for high-risk addresses
- **Use Case:** Exchanges can screen deposit addresses and detect exploiters

#### 🔗 Payment Processors
- **Description:** Stripe, PayPal Crypto, Square - Merchant verification
- **Integration Method:** API integration to verify merchant wallets, return VASP view for compliance
- **Use Case:** Payment processors can verify merchant wallet legitimacy

#### 🔗 Mastercard Crypto Credentials
- **Description:** Mastercard's crypto credential system - Enhanced identity verification
- **Integration Method:** API integration to add on-chain analysis layer, combine with verified identities
- **Use Case:** Add on-chain behavior analysis to verified identity credentials

#### 🔗 Blockchain Explorers
- **Description:** Etherscan, Blockscout - Enhanced address information
- **Integration Method:** API to fetch ProtectionReport, display in address detail pages
- **Use Case:** Explorers can add WalletLens analysis as a premium feature

#### 🔗 Security Tools
- **Description:** Scam detection, wallet monitoring, transaction screening
- **Integration Method:** Webhook subscriptions for alerts, API for batch screening
- **Use Case:** Security platforms can use WalletLens for automated threat detection

#### 🔗 Financial Institutions
- **Description:** Banks, compliance platforms - Regulatory compliance and risk assessment
- **Integration Method:** API for compliance workflows, Financial Institution view for audit trails
- **Use Case:** Screen addresses for regulatory compliance, generate audit reports

#### 🔗 Treasury Management
- **Description:** Corporate treasury, DAO treasury management - Operational security
- **Integration Method:** API integration, Customer/Treasury view for setup guidance
- **Use Case:** Verify counterparties, implement treasury controls, training guidance

## 👥 How Users Can Use WalletLens

### For Individual Users:
1. **Before Sending Crypto**: Paste the recipient address to verify it's safe
2. **Research Wallets**: Analyze any on-chain wallet address to understand its behavior
3. **Avoid Scams**: Get instant warnings about exploiters and compromised wallets
4. **Due Diligence**: Check addresses before interacting with DeFi protocols
5. **AI Recommendations**: Toggle to see protective actions and signals

### For Developers:
1. **REST API**: Integrate WalletLens via HTTP API endpoints
2. **Webhook Integration**: Subscribe to wallet analysis events and alerts
3. **WebSocket API**: Real-time streaming for live analysis
4. **SDK Integration**: Use language-specific SDKs (Python, JavaScript, Go)
5. **Batch Analysis**: Analyze multiple addresses programmatically
6. **Custom Views**: Access different stakeholder views (User, VASP, FI, Customer)

### For Businesses:
1. **Compliance**: Screen addresses for regulatory compliance with audit trails
2. **Risk Management**: Assess counterparty risk before transactions
3. **Fraud Prevention**: Detect suspicious patterns automatically via webhooks
4. **Customer Protection**: Warn users about risky addresses in your platform
5. **Treasury Management**: Get setup guidance and controls checklist
6. **Integration**: Easy API/webhook integration into existing systems

## 🛡️ Protection Layer

WalletLens includes a **Protection Layer** that provides assistive risk assessment:

- **Observed Signals**: Coded signals derived from facts (SHORT_LIVED, HIGH_VALUE_FLOW, etc.)
- **Confidence Levels**: Transparent data quality indicators (HIGH/MEDIUM/LOW)
- **Protective Actions**: Recommended actions (not blocking decisions)
- **Multi-View Output**: Different formats for Users, Businesses, VASPs, and Financial Institutions
- **No Risk Scores**: We don't output numeric scores that could be misinterpreted
- **No Blocking**: We provide recommendations, not BLOCK/ALLOW commands

Toggle **AI Recommendations** in the sidebar to show/hide protective recommendations.

## 🛠️ Technical Stack

- **AI Model**: Google Gemini 2.5 Flash
- **Data Source**: Google BigQuery (Ethereum public dataset)
- **Framework**: Streamlit
- **Language**: Python 3.8+

## 👨‍💻 Team

**Jaya Mandlik**  
jaya.ashok.mandlik@gmail.com

**Katie Li**  
katiem3749@gmail.com

## 🏆 Team Aegis - Google ODSC Hackathon 2025 - Dec 12. 2025

---

**License:** Hackathon Project - All Rights Reserved
