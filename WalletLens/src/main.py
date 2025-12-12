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
    page_title="WalletLens",
    page_icon="🔍",
    layout="wide"
)

# Title
st.title("🔍 WalletLens")
st.markdown("### Ethereum Wallet Classification Tool")
st.markdown("Analyze Ethereum wallet addresses to identify **Who is this?** and assess **Is it safe to interact?**")
st.markdown("Classifications: **Merchant/Exchange**, **Bot/MEV**, **Whale/Treasury**, **Exploiter**, or **Compromised/Drained Wallet**")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
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
    
    # Show analysis history
    st.header("📜 Recent Analyses")
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

# Main content
address_input = st.text_input(
    "Enter Ethereum Wallet Address:",
    placeholder="0x...",
    help="Enter a valid Ethereum address (0x followed by 40 hex characters)"
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
        r'(Compromised|Drained Wallet|Victim)'
    ]
    for pattern in classification_patterns:
        match = re.search(pattern, result_text, re.IGNORECASE)
        if match:
            classification = match.group(1)
            break
    
    return classification, safety_verdict

if st.button("Analyze Wallet", type="primary"):
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
            st.success("Analysis Complete!")
            
            # Main result
            st.header("📊 Analysis Result")
            if safety_verdict:
                st.markdown(f"### {safety_verdict}")
            if classification:
                st.markdown(f"**Classification:** {classification}")
            st.markdown("---")
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
st.markdown("**WalletLens** - Powered by Google Gemini AI and BigQuery")

