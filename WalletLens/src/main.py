"""Streamlit UI for WalletLens application."""

import streamlit as st
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from executor import WalletAgentExecutor
from memory import AnalysisHistory
import re

# Load environment variables
load_dotenv()

# Initialize session state for history
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = AnalysisHistory(max_size=5)

# Page configuration
st.set_page_config(
    page_title="WalletLens - Predictive On-Chain Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .logo-text {
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .tagline {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    .team-info {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    .integration-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .safety-badge {
        font-size: 1.5rem;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: inline-block;
        margin: 0.5rem 0;
    }
    .safe { background: #d4edda; color: #155724; }
    .caution { background: #fff3cd; color: #856404; }
    .high-risk { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Header with logo
st.markdown("""
<div class="main-header">
    <div class="logo-text">🔍 WalletLens</div>
    <div class="tagline">Predictive On-Chain Analysis Agent</div>
    <div style="margin-top: 1rem; font-size: 0.9rem;">
        Built by <strong>Jaya Mandlik</strong> & <strong>Katie Li</strong> | Team Aegis
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation tabs
tab1, tab2 = st.tabs(["🏠 Home", "ℹ️ About WalletLens"])

with tab1:
    st.markdown("### Ethereum Wallet Classification Tool")
    st.markdown("Analyze Ethereum wallet addresses to identify **Who is this?** and assess **Is it safe to interact?**")
    
    st.info("""
    **Classifications:** Merchant/Exchange • Bot/MEV • Whale/Treasury • Exploiter • Compromised Wallet
    
    **Safety Verdicts:** 🟢 SAFE • 🟡 CAUTION • 🔴 HIGH RISK
    """)

    # Main content
    address_input = st.text_input(
        "Enter Ethereum Wallet Address:",
        placeholder="0x...",
        help="Enter a valid Ethereum address (0x followed by 40 hex characters)",
        key="address_input"
    )
    
    def extract_classification_and_verdict(result_text: str) -> tuple:
        """Extract classification and safety verdict from result text."""
        classification = None
        safety_verdict = None
        
        # Extract safety verdict (🟢 SAFE, 🟡 CAUTION, 🔴 HIGH RISK)
        verdict_pattern = r'(🟢|🟡|🔴)\s*(SAFE|CAUTION|HIGH RISK|DO NOT INTERACT)'
        verdict_match = re.search(verdict_pattern, result_text, re.IGNORECASE)
        if verdict_match:
            emoji = verdict_match.group(1)
            verdict_text = verdict_match.group(2)
            safety_verdict = f"{emoji} {verdict_text}"
        
        # Extract classification
        classification_patterns = [
            r'(Merchant|Exchange)',
            r'(Bot|MEV)',
            r'(Whale|Treasury)',
            r'(Exploiter|Attacker)',
            r'(Compromised Wallet|Victim)'
        ]
        for pattern in classification_patterns:
            match = re.search(pattern, result_text, re.IGNORECASE)
            if match:
                classification = match.group(1)
                break
        
        return classification, safety_verdict
    
    if st.button("🔍 Analyze Wallet", type="primary", use_container_width=True):
        if not address_input:
            st.error("Please enter a wallet address")
        elif not address_input.startswith("0x") or len(address_input) != 42:
            st.error("Invalid Ethereum address format. Address should start with 0x and be 42 characters long.")
        else:
            # Check if we have cached result
            cached = st.session_state.analysis_history.get_by_address(address_input)
            if cached:
                st.info("📋 Showing cached analysis. Re-analyze to get fresh data.")
                use_cache = st.button("Use Cached Result", key="use_cache")
                if use_cache:
                    st.header("📊 Analysis Result")
                    st.markdown(cached['result'])
                    if cached['safety_verdict']:
                        st.markdown(f"**Safety Verdict:** {cached['safety_verdict']}")
                    if cached['classification']:
                        st.markdown(f"**Classification:** {cached['classification']}")
                    st.stop()
            
            # Initialize executor
            try:
                with st.spinner("Initializing WalletLens agent..."):
                    executor = WalletAgentExecutor()
                
                # Run analysis
                with st.spinner("Analyzing wallet address... This may take a moment."):
                    result = executor.run(address_input)
                
                # Extract classification and verdict
                classification, safety_verdict = extract_classification_and_verdict(result['result'])
                
                # Store in history
                st.session_state.analysis_history.add_analysis(
                    address=address_input,
                    result=result['result'],
                    classification=classification,
                    safety_verdict=safety_verdict
                )
                
                # Display results
                st.success("✅ Analysis Complete!")
                
                # Main result with better styling
                st.header("📊 Analysis Result")
                
                # Safety verdict with color coding
                if safety_verdict:
                    if "🟢" in safety_verdict:
                        st.markdown(f'<div class="safety-badge safe">{safety_verdict}</div>', unsafe_allow_html=True)
                    elif "🟡" in safety_verdict:
                        st.markdown(f'<div class="safety-badge caution">{safety_verdict}</div>', unsafe_allow_html=True)
                    elif "🔴" in safety_verdict:
                        st.markdown(f'<div class="safety-badge high-risk">{safety_verdict}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f"### {safety_verdict}")
                
                # Classification badge
                if classification:
                    st.info(f"**Classification:** {classification}")
                
                st.markdown("---")
                
                # Result content
                st.markdown("### 📋 Detailed Analysis")
                st.markdown(result['result'])
                
                # Memory logs
                st.header("📝 Execution Logs")
                with st.expander("View detailed execution logs", expanded=False):
                    for log in result['memory_logs']:
                        st.text(log)
                
            except ValueError as e:
                st.error(f"Configuration Error: {str(e)}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.exception(e)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <strong>WalletLens</strong> - Powered by Google Gemini AI and BigQuery<br>
        Built by <strong>Jaya Mandlik</strong> & <strong>Katie Li</strong> | Team Aegis
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("## About WalletLens")
    
    st.markdown("""
    **WalletLens** is an AI-powered blockchain forensic agent that profiles Ethereum wallet addresses and assesses 
    interaction safety using Google Gemini 2.5 and BigQuery. It helps users make informed decisions before 
    interacting with unknown addresses by providing detailed persona classification and risk assessment.
    """)
    
    st.markdown("### 🎯 Key Features")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - **Persona Classification**: Identifies wallet types
        - **Safety Assessment**: Clear risk verdicts
        - **1-Year Analysis**: Comprehensive historical data
        - **Pattern Detection**: Exploit and drain detection
        """)
    
    with col2:
        st.markdown("""
        - **Analysis History**: Quick access to recent analyses
        - **Full Observability**: Detailed execution logs
        - **Real-time Analysis**: Fast on-chain data queries
        - **Secure**: Validated BigQuery access controls
        """)
    
    st.markdown("### 🔌 Integration Options")
    
    st.markdown("""
    WalletLens can be integrated into various platforms and services:
    """)
    
    integration_options = [
        {
            "name": "Web3 Wallets",
            "description": "MetaMask, WalletConnect, Coinbase Wallet - Add safety checks before transactions",
            "use_case": "Users can verify recipient addresses before sending funds"
        },
        {
            "name": "DeFi Platforms",
            "description": "Uniswap, Aave, Compound - Screen liquidity providers and counterparties",
            "use_case": "Platforms can warn users about risky addresses in their UI"
        },
        {
            "name": "NFT Marketplaces",
            "description": "OpenSea, LooksRare, Blur - Verify seller/buyer addresses",
            "use_case": "Marketplaces can flag suspicious accounts automatically"
        },
        {
            "name": "Crypto Exchanges",
            "description": "Binance, Coinbase, Kraken - Enhanced KYC and risk assessment",
            "use_case": "Exchanges can screen deposit addresses and detect exploiters"
        },
        {
            "name": "Payment Processors",
            "description": "Stripe, PayPal Crypto, Square - Merchant verification",
            "use_case": "Payment processors can verify merchant wallet legitimacy"
        },
        {
            "name": "Mastercard Crypto Credentials",
            "description": "Mastercard's crypto credential system - Enhanced identity verification",
            "use_case": "Integrate with Mastercard Crypto Credentials API to add on-chain analysis layer for verified identities"
        },
        {
            "name": "Blockchain Explorers",
            "description": "Etherscan, Blockscout - Enhanced address information",
            "use_case": "Explorers can add WalletLens analysis as a premium feature"
        },
        {
            "name": "Security Tools",
            "description": "Scam detection, wallet monitoring, transaction screening",
            "use_case": "Security platforms can use WalletLens for automated threat detection"
        },
        {
            "name": "API Integration",
            "description": "REST API or WebSocket for real-time analysis",
            "use_case": "Any application can call WalletLens API to get instant wallet assessments"
        }
    ]
    
    for option in integration_options:
        with st.expander(f"🔗 {option['name']}"):
            st.markdown(f"**Description:** {option['description']}")
            st.markdown(f"**Use Case:** {option['use_case']}")
    
    st.markdown("### 👥 How Users Can Use WalletLens")
    
    st.markdown("""
    #### For Individual Users:
    1. **Before Sending Crypto**: Paste the recipient address to verify it's safe
    2. **Research Wallets**: Analyze any Ethereum address to understand its behavior
    3. **Avoid Scams**: Get instant warnings about exploiters and compromised wallets
    4. **Due Diligence**: Check addresses before interacting with DeFi protocols
    
    #### For Developers:
    1. **API Integration**: Integrate WalletLens into your application via API
    2. **Webhook Support**: Receive real-time alerts for risky addresses
    3. **Batch Analysis**: Analyze multiple addresses programmatically
    4. **Custom Rules**: Configure custom risk thresholds for your use case
    
    #### For Businesses:
    1. **Compliance**: Screen addresses for regulatory compliance
    2. **Risk Management**: Assess counterparty risk before transactions
    3. **Fraud Prevention**: Detect suspicious patterns automatically
    4. **Customer Protection**: Warn users about risky addresses in your platform
    """)
    
    st.markdown("### 🛠️ Technical Stack")
    st.markdown("""
    - **AI Model**: Google Gemini 2.5 Flash
    - **Data Source**: Google BigQuery (Ethereum public dataset)
    - **Framework**: Streamlit
    - **Language**: Python 3.8+
    """)
    
    st.markdown("### 👨‍💻 Team")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Jaya Mandlik**  
        jaya.ashok.mandlik@gmail.com
        """)
    with col2:
        st.markdown("""
        **Katie Li**  
        katiem3749@gmail.com
        """)
    
    st.markdown("### 🏆 Team Aegis - Google ODSC Hackathon 2025 - Dec 12. 2025")

# Sidebar for configuration
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    st.info("Make sure to set your API keys in the .env file")
    
    # Check if API key is set
    api_key = os.getenv('GEMINI_API_KEY')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    if not api_key:
        st.error("⚠️ GEMINI_API_KEY not found in .env file")
    else:
        st.success("✅ GEMINI_API_KEY configured")
    
    if not project_id:
        st.warning("⚠️ GOOGLE_CLOUD_PROJECT not set")
    else:
        st.success(f"✅ Project: {project_id}")
    
    st.markdown("---")
    
    # Show analysis history
    st.markdown("### 📜 Recent Analyses")
    history = st.session_state.analysis_history.get_history()
    if history:
        for i, analysis in enumerate(history):
            with st.expander(f"{analysis['address'][:10]}... ({analysis['timestamp'].strftime('%Y-%m-%d %H:%M')})"):
                if analysis['safety_verdict']:
                    st.markdown(f"**Safety:** {analysis['safety_verdict']}")
                if analysis['classification']:
                    st.markdown(f"**Type:** {analysis['classification']}")
                st.text_area("Result", analysis['result'][:500] + "...", height=100, key=f"hist_{i}", disabled=True)
    else:
        st.info("No analyses yet")
    
    st.markdown("---")
    st.markdown("**Built by Team Aegis**")
    st.markdown("Jaya Mandlik & Katie Li")

