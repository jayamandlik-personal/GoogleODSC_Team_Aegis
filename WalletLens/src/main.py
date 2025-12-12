"""Streamlit UI for WalletLens application."""

import streamlit as st
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from executor import WalletAgentExecutor

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="WalletLens",
    page_icon="🔍",
    layout="wide"
)

# Title
st.title("🔍 WalletLens")
st.markdown("### Ethereum Wallet Classification Tool")
st.markdown("Analyze Ethereum wallet addresses and classify them as **Bot**, **Merchant**, or **Whale**")

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

# Main content
address_input = st.text_input(
    "Enter Ethereum Wallet Address:",
    placeholder="0x...",
    help="Enter a valid Ethereum address (0x followed by 40 hex characters)"
)

if st.button("Analyze Wallet", type="primary"):
    if not address_input:
        st.error("Please enter a wallet address")
    elif not address_input.startswith("0x") or len(address_input) != 42:
        st.error("Invalid Ethereum address format. Address should start with 0x and be 42 characters long.")
    else:
        # Initialize executor
        try:
            with st.spinner("Initializing WalletLens agent..."):
                executor = WalletAgentExecutor()
            
            # Run analysis
            with st.spinner("Analyzing wallet address... This may take a moment."):
                result = executor.run(address_input)
            
            # Display results
            st.success("Analysis Complete!")
            
            # Main result
            st.header("📊 Analysis Result")
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

