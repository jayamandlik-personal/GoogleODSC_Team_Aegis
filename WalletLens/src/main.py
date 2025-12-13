"""Streamlit UI for WalletLens application."""

import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from executor import WalletAgentExecutor
from memory import AnalysisHistory
from stakeholder_views import render_user_view, render_customer_view, render_vasp_view, render_fi_view
import re

# Load environment variables
load_dotenv()

# Initialize session state for history
if 'analysis_history' not in st.session_state:
    st.session_state.analysis_history = AnalysisHistory(max_size=5)

# Initialize AI Recommendations (default ON)
if 'ai_recommendations' not in st.session_state:
    st.session_state.ai_recommendations = True

# Track which additional view to show
if 'show_view' not in st.session_state:
    st.session_state.show_view = None

# Store current analysis result
if 'current_protection_report' not in st.session_state:
    st.session_state.current_protection_report = None

if 'current_analysis_result' not in st.session_state:
    st.session_state.current_analysis_result = None

# Page configuration
st.set_page_config(
    page_title="WalletLens - Predictive On-Chain Analysis",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for sleek Mastercard-style design
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Don't hide header completely - sidebar button is there */
    header {
        background: transparent !important;
        visibility: visible !important;
    }
    
    /* Ensure header button (sidebar toggle) is visible - both when expanded and collapsed */
    header button,
    header button[aria-label*="Close"],
    header button[aria-label*="Open"],
    header button[aria-label*="sidebar"],
    header button[aria-label*="menu"],
    header [data-testid="collapsedControl"],
    header [data-testid="collapsedControl"] button,
    /* Streamlit's sidebar toggle button */
    .stApp header button,
    .stApp header button[aria-label*="Close"],
    .stApp header button[aria-label*="Open"],
    .stApp header [data-testid="collapsedControl"],
    .stApp header [data-testid="collapsedControl"] button,
    /* When sidebar is expanded - collapse button in header */
    section[data-testid="stSidebar"][aria-expanded="true"] ~ header button,
    /* BaseWeb button in header */
    header [data-baseweb="button"],
    header [data-baseweb="button"] button {
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        z-index: 9999 !important;
        position: relative !important;
        cursor: pointer !important;
        pointer-events: auto !important;
    }
    
    /* Ensure the collapse control is always visible when sidebar is collapsed */
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        z-index: 9999 !important;
    }
    
    [data-testid="collapsedControl"] button {
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        cursor: pointer !important;
        pointer-events: auto !important;
    }
    
    /* When sidebar is expanded, ensure collapse button in sidebar header is visible */
    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] [data-baseweb="button"],
    section[data-testid="stSidebar"] header button,
    /* Button at top of sidebar to collapse */
    section[data-testid="stSidebar"] > div > button,
    section[data-testid="stSidebar"] > div > div > button,
    /* First button in sidebar (usually the collapse button) */
    section[data-testid="stSidebar"] button:first-child,
    section[data-testid="stSidebar"] [data-baseweb="button"]:first-child {
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        cursor: pointer !important;
        pointer-events: auto !important;
        color: white !important;
        background: rgba(255, 255, 255, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        margin: 0.5rem !important;
    }
    
    section[data-testid="stSidebar"] button:hover,
    section[data-testid="stSidebar"] [data-baseweb="button"]:hover {
        background: rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Sidebar header collapse button */
    section[data-testid="stSidebar"] [class*="sidebar-header"] button,
    section[data-testid="stSidebar"] [class*="header"] button {
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        cursor: pointer !important;
        pointer-events: auto !important;
    }
    
    /* Ensure all buttons in sidebar are visible (especially collapse button) */
    section[data-testid="stSidebar"] button[aria-label*="Close"],
    section[data-testid="stSidebar"] button[aria-label*="collapse"],
    section[data-testid="stSidebar"] button[aria-label*="Collapse"],
    section[data-testid="stSidebar"] button[aria-label*="sidebar"] {
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        cursor: pointer !important;
        pointer-events: auto !important;
    }
    
    /* Override any rules that might hide buttons when sidebar is expanded */
    section[data-testid="stSidebar"]:not([aria-expanded="false"]) button,
    section[data-testid="stSidebar"][aria-expanded="true"] button {
        visibility: visible !important;
        display: block !important;
    }
    
    /* Ensure sidebar collapse/expand button is always visible - comprehensive selectors */
    /* Streamlit sidebar toggle button */
    button[kind="header"],
    button[aria-label*="sidebar"],
    button[aria-label*="menu"],
    button[aria-label*="Close"],
    button[aria-label*="Open"],
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] button,
    [data-testid="collapsedControl"] > button,
    .stApp button[aria-label*="Close"],
    .stApp button[aria-label*="Open"],
    .stApp button[aria-label*="sidebar"],
    /* BaseWeb button selectors */
    [data-baseweb="button"][aria-label*="sidebar"],
    [data-baseweb="button"][aria-label*="menu"],
    /* Generic button near sidebar */
    section[data-testid="stSidebar"] ~ button,
    /* Sidebar header button */
    header button,
    /* Any button with collapse/expand icon */
    button:has(svg[viewBox*="0 0"]),
    /* Streamlit's specific sidebar control */
    [class*="sidebar"] button,
    [class*="Sidebar"] button {
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        color: #EB001B !important;
        background: white !important;
        border: 2px solid #EB001B !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        box-shadow: 0 2px 8px rgba(235, 0, 27, 0.2) !important;
        z-index: 9999 !important;
        position: relative !important;
    }
    
    button[kind="header"]:hover,
    [data-testid="collapsedControl"] button:hover,
    button[aria-label*="sidebar"]:hover,
    button[aria-label*="menu"]:hover {
        background: #EB001B !important;
        color: white !important;
    }
    
    /* Sidebar collapse button container - ensure it's always visible */
    [data-testid="collapsedControl"] {
        visibility: visible !important;
        display: block !important;
        opacity: 1 !important;
        position: fixed !important;
        left: 0 !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        z-index: 9999 !important;
        width: auto !important;
        height: auto !important;
    }
    
    /* Ensure button icon is visible */
    [data-testid="collapsedControl"] button svg,
    button[kind="header"] svg,
    button[aria-label*="sidebar"] svg,
    button[aria-label*="menu"] svg {
        fill: #EB001B !important;
        color: #EB001B !important;
        stroke: #EB001B !important;
        width: 20px !important;
        height: 20px !important;
    }
    
    [data-testid="collapsedControl"] button:hover svg,
    button[kind="header"]:hover svg,
    button[aria-label*="sidebar"]:hover svg,
    button[aria-label*="menu"]:hover svg {
        fill: white !important;
        color: white !important;
        stroke: white !important;
    }
    
    /* Don't hide any buttons that might be the collapse button */
    button {
        visibility: visible !important;
    }
    
    /* Override any hiding of sidebar controls */
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] *,
    button[kind="header"],
    button[kind="header"] * {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }
    
    /* Mastercard-inspired color scheme */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
    }
    
    /* Reduce top spacing */
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* Reduce tab spacing */
    .stTabs {
        margin-top: 0.5rem !important;
    }
    
    /* Ensure all text is visible */
    .stApp, .main, .block-container {
        color: #1a1a1a !important;
    }
    
    /* Streamlit text elements */
    p, h1, h2, h3, h4, h5, h6, div, span, label {
        color: #1a1a1a !important;
    }
    
    /* Input labels */
    .stTextInput label, .stSelectbox label {
        color: #1a1a1a !important;
    }
    
    /* Markdown text */
    .stMarkdown {
        color: #1a1a1a !important;
    }
    
    /* Info boxes */
    .stInfo, .stSuccess, .stWarning, .stError {
        color: inherit !important;
    }
    
    .main-header {
        background: linear-gradient(135deg, #EB001B 0%, #F79E1B 100%);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 16px rgba(235, 0, 27, 0.15);
    }
    
    .logo-text {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
        letter-spacing: -1px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .tagline {
        font-size: 0.9rem;
        opacity: 0.95;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    
    .team-info {
        margin-top: 1.5rem;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Sleek input styling */
    .stTextInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #EB001B;
        box-shadow: 0 0 0 3px rgba(235, 0, 27, 0.1);
    }
    
    /* Modern button styling */
    .stButton > button {
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        color: white !important;
        background: linear-gradient(135deg, #EB001B 0%, #F79E1B 100%) !important;
        border: none !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
        background: linear-gradient(135deg, #C7001A 0%, #E68A00 100%) !important;
        color: white !important;
    }
    
    /* Ensure all button text is white and visible */
    .stButton > button > div > p,
    .stButton > button > p,
    .stButton > button span,
    .stButton > button div,
    .stButton > button * {
        color: white !important;
    }
    
    /* Card styling */
    .info-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin: 1.5rem 0;
        border: 1px solid #f0f0f0;
    }
    
    .safety-badge {
        font-size: 1.3rem;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        display: inline-block;
        margin: 0.5rem 0;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .safe { 
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
    }
    
    .caution { 
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
    }
    
    .high-risk { 
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white;
    }
    
    /* Sidebar styling - unified gradient background */
    section[data-testid="stSidebar"] {
        background: linear-gradient(135deg, #EB001B 0%, #F79E1B 100%) !important;
        color: white !important;
    }
    
    /* Sidebar text - all white by default */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] div,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Sidebar markdown */
    section[data-testid="stSidebar"] .stMarkdown {
        color: white !important;
    }
    
    /* Sidebar selectbox and toggle labels */
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stToggle label {
        color: white !important;
    }
    
    /* Sidebar selectbox input - white text on semi-transparent background */
    section[data-testid="stSidebar"] .stSelectbox select {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
    }
    
    /* Selected value text in selectbox */
    section[data-testid="stSidebar"] .stSelectbox select,
    section[data-testid="stSidebar"] .stSelectbox select:focus,
    section[data-testid="stSidebar"] .stSelectbox select option:checked {
        color: white !important;
        background: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Dropdown options - dark background with white text */
    section[data-testid="stSidebar"] .stSelectbox option {
        background: rgba(0, 0, 0, 0.95) !important;
        color: white !important;
    }
    
    /* Selectbox container and all nested divs */
    section[data-testid="stSidebar"] .stSelectbox > div,
    section[data-testid="stSidebar"] .stSelectbox > div > div,
    section[data-testid="stSidebar"] .stSelectbox > div > div > div {
        color: white !important;
    }
    
    /* BaseWeb select component - ensure white text */
    section[data-testid="stSidebar"] [data-baseweb="select"],
    section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-baseweb="select"] span {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }
    
    section[data-testid="stSidebar"] [data-baseweb="select"] * {
        color: white !important;
    }
    
    /* Popover menu for dropdown (when open) */
    [data-baseweb="popover"] [data-baseweb="menu"],
    [data-baseweb="popover"] [data-baseweb="menu"] li,
    [data-baseweb="popover"] [data-baseweb="menu"] a {
        background: rgba(0, 0, 0, 0.95) !important;
        color: white !important;
    }
    
    [data-baseweb="popover"] [data-baseweb="menu"] * {
        color: white !important;
    }
    
    /* Sidebar toggle */
    section[data-testid="stSidebar"] .stToggle {
        color: white !important;
    }
    
    /* Sidebar expander */
    section[data-testid="stSidebar"] .streamlit-expanderHeader {
        color: white !important;
        background: rgba(255, 255, 255, 0.1) !important;
    }
    
    section[data-testid="stSidebar"] .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Sidebar expander content */
    section[data-testid="stSidebar"] .streamlit-expanderContent {
        color: white !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    
    section[data-testid="stSidebar"] .streamlit-expanderContent p,
    section[data-testid="stSidebar"] .streamlit-expanderContent div,
    section[data-testid="stSidebar"] .streamlit-expanderContent span {
        color: white !important;
    }
    
    /* Sidebar info boxes - transparent with white text */
    section[data-testid="stSidebar"] .stInfo,
    section[data-testid="stSidebar"] .stSuccess,
    section[data-testid="stSidebar"] .stWarning {
        background: rgba(255, 255, 255, 0.15) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Sidebar caption */
    section[data-testid="stSidebar"] .stCaption {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* Force all sidebar text to be white */
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* But allow specific colored elements to override */
    section[data-testid="stSidebar"] [style*="color: #EB001B"],
    section[data-testid="stSidebar"] [style*="color: #10b981"],
    section[data-testid="stSidebar"] [style*="color: #f59e0b"],
    section[data-testid="stSidebar"] [style*="color: #ef4444"] {
        color: inherit !important;
    }
    
    /* Tooltip/hover text styling - make it white and visible (global) */
    div[data-baseweb="tooltip"],
    [data-baseweb="tooltip"],
    .stTooltipContent,
    [class*="TooltipContent"],
    [class*="tooltip-content"] {
        color: white !important;
        background: rgba(0, 0, 0, 0.95) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    div[data-baseweb="tooltip"] *,
    [data-baseweb="tooltip"] *,
    .stTooltipContent *,
    [class*="TooltipContent"] *,
    [class*="tooltip-content"] * {
        color: white !important;
    }
    
    /* BaseWeb popover (used for tooltips) - global */
    div[data-baseweb="popover"],
    [data-baseweb="popover"] {
        background: rgba(0, 0, 0, 0.95) !important;
        color: white !important;
    }
    
    div[data-baseweb="popover"] *,
    [data-baseweb="popover"] * {
        color: white !important;
    }
    
    /* Streamlit help tooltip text */
    [data-testid="stTooltip"] {
        color: white !important;
    }
    
    [data-testid="stTooltip"] * {
        color: white !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        padding: 1rem 1.5rem;
        font-weight: 600;
    }
    
    /* Feature highlight */
    .feature-box {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        margin: 1rem 0;
        border-left: 4px solid #EB001B;
    }
    
    /* Image container */
    .image-container {
        text-align: center;
        margin: 2rem 0;
    }
    
    .hero-image {
        max-width: 100%;
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
    }
    
    /* BaseWeb button text - ensure all button text is visible */
    [data-baseweb="button"] {
        color: white !important;
    }
    
    [data-baseweb="button"] > div,
    [data-baseweb="button"] > div > div,
    [data-baseweb="button"] p,
    [data-baseweb="button"] span,
    [data-baseweb="button"] * {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Header with logo - Mastercard style
st.markdown("""
<div class="main-header">
    <div class="logo-text">🔍 WalletLens</div>
    <div class="tagline">Intelligent On-Chain Risk Assessment</div>
</div>
""", unsafe_allow_html=True)

# Navigation tabs
tab1, tab2 = st.tabs(["🏠 Home", "ℹ️ About WalletLens"])

with tab1:
    # Main layout - two columns
    col1, col2 = st.columns([2.5, 1])
    
    with col1:
        # Main input section
        st.markdown("""
        <div style="background: white; padding: 1.25rem; border-radius: 12px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); margin-bottom: 1rem;">
            <h2 style="color: #EB001B; margin-bottom: 0.5rem; font-weight: 700; font-size: 1.4rem;">
                🔍 Analyze On-Chain Wallet
            </h2>
            <p style="color: #666; font-size: 0.9rem; margin-bottom: 0; line-height: 1.5;">
                Get instant insights into wallet behavior, risk assessment, and protective recommendations
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Address input
        address_input = st.text_input(
            "Enter Wallet Address:",
            placeholder="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            help="Enter a valid wallet address (Ethereum: 0x followed by 40 hex characters)",
            key="address_input"
        )
        
        # Analyze button - right after input
        analyze_button = st.button(
            "🔍 Analyze Wallet", 
            type="primary", 
            use_container_width=True, 
            key="analyze_button"
        )
    
    with col2:
        # Feature highlights with subtexts
        st.markdown("""
        <div style="background: white; padding: 1.25rem; border-radius: 12px; box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);">
            <h3 style="color: #EB001B; font-size: 1rem; margin-bottom: 1rem; font-weight: 700;">✨ Features</h3>
            <div style="font-size: 0.85rem; color: #333; line-height: 1.8;">
                <div style="margin-bottom: 1rem;">
                    <div style="font-weight: 600; color: #EB001B; margin-bottom: 0.25rem;">🎯 Persona</div>
                    <div style="color: #666; font-size: 0.8rem; line-height: 1.5;">
                        Classify wallet types: Merchant, Bot, Whale, Exploiter, Compromised
                    </div>
                </div>
                <div style="margin-bottom: 1rem;">
                    <div style="font-weight: 600; color: #EB001B; margin-bottom: 0.25rem;">🛡️ Safety</div>
                    <div style="color: #666; font-size: 0.8rem; line-height: 1.5;">
                        Risk assessment: SAFE, CAUTION, or HIGH RISK verdicts
                    </div>
                </div>
                <div>
                    <div style="font-weight: 600; color: #EB001B; margin-bottom: 0.25rem;">🤖 AI</div>
                    <div style="color: #666; font-size: 0.8rem; line-height: 1.5;">
                        Protective recommendations and signal-based insights
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def extract_classification_and_verdict(result_text: str) -> tuple:
        """Extract classification and safety verdict from result text."""
        classification = None
        safety_verdict = None
        
        # Extract safety verdict - look for "Is it safe to interact? 🔴 HIGH RISK" format
        # Also handle standalone verdict patterns
        verdict_patterns = [
            r'Is it safe to interact\?\s*(🟢|🟡|🔴)\s*(SAFE|CAUTION|HIGH RISK|DO NOT INTERACT)',
            r'(🟢|🟡|🔴)\s*(SAFE|CAUTION|HIGH RISK|DO NOT INTERACT)',
            r'\*\*(🟢|🟡|🔴)\s*(SAFE|CAUTION|HIGH RISK|DO NOT INTERACT)\*\*'
        ]
        for pattern in verdict_patterns:
            verdict_match = re.search(pattern, result_text, re.IGNORECASE)
            if verdict_match:
                emoji = verdict_match.group(1)
                verdict_text = verdict_match.group(2)
                safety_verdict = f"{emoji} {verdict_text}"
                break
        
        # Extract classification - look for "Who is this? Compromised Wallet" format
        # Also handle standalone classification patterns
        # Priority order: Check for full phrases first, then individual terms
        classification_patterns = [
            r'Who is this\?\s*(Compromised Wallet|Merchant|Exchange|Bot|MEV|Whale|Treasury|Exploiter|Attacker)',
            r'classified as (?:a |an )?(Compromised Wallet|Merchant|Exchange|Bot|MEV|Whale|Treasury|Exploiter|Attacker)',
            r'(Compromised Wallet)',  # Full phrase - check before individual terms
            r'(Merchant|Exchange)',
            r'(Bot|MEV)',
            r'(Whale|Treasury)',
            r'(Exploiter|Attacker)'
        ]
        for pattern in classification_patterns:
            match = re.search(pattern, result_text, re.IGNORECASE)
            if match:
                classification = match.group(1)
                # Ensure "Compromised Wallet" is captured as full phrase
                if "Compromised Wallet" in result_text and classification != "Compromised Wallet":
                    # Check if "Compromised Wallet" appears in the text
                    if re.search(r'Compromised Wallet', result_text, re.IGNORECASE):
                        classification = "Compromised Wallet"
                break
        
        return classification, safety_verdict
    
    if analyze_button:
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
                
                # Get protection report if available
                protection_report = result.get('protection_report')
                
                # Store in session state so it persists across reruns
                st.session_state.current_protection_report = protection_report
                st.session_state.current_analysis_result = result
                
                # Reset view state for new analysis
                st.session_state.show_view = None
                
                # Store in history (include protection report)
                st.session_state.analysis_history.add_analysis(
                    address=address_input,
                    result=result['result'],
                    classification=classification,
                    safety_verdict=safety_verdict,
                    protection_report=protection_report
                )
                
                # Display results - compact success message
                st.markdown("""
                <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                            color: white; padding: 1rem; border-radius: 10px; 
                            text-align: center; font-weight: 600; font-size: 1rem; 
                            box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3); margin: 1rem 0;">
                    ✅ Analysis Complete!
                </div>
                """, unsafe_allow_html=True)
                
            except ValueError as e:
                st.error(f"Configuration Error: {str(e)}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.exception(e)
    
    # Display protection report views (works for both new and stored analyses)
    if st.session_state.current_protection_report:
        protection_report = st.session_state.current_protection_report
        
        # User View (always shown) - compact header
        st.markdown("""
        <div style="background: white; padding: 1.5rem; border-radius: 12px; 
                    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); margin: 1rem 0;">
            <h1 style="color: #EB001B; font-size: 1.75rem; font-weight: 700; margin-bottom: 0.25rem;">
                👤 User View
            </h1>
            <p style="color: #666; font-size: 0.9rem;">Your personalized wallet analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        user_view = render_user_view(protection_report, st.session_state.ai_recommendations)
        
        st.markdown(f"**Summary:** {user_view['summary']}")
        
        # Add Persona/Classification info
        if user_view.get('persona'):
            persona_emoji = {
                "Exploiter": "🔴",
                "Compromised Wallet": "🔴",
                "Merchant/Exchange": "🟢",
                "Bot/MEV": "🟡",
                "Whale/Treasury": "🟢"
            }.get(user_view['persona'], "⚪")
            st.markdown(f"**Persona:** {persona_emoji} {user_view['persona']}")
        
        if user_view.get('verdict'):
            verdict_emoji = {
                "HIGH RISK": "🔴",
                "CAUTION": "🟡",
                "SAFE": "🟢"
            }.get(user_view['verdict'], "⚪")
            st.markdown(f"**Safety Verdict:** {verdict_emoji} {user_view['verdict']}")
        
        st.markdown(f"**Confidence:** {user_view['confidence']}")
        
        if st.session_state.ai_recommendations:
            st.markdown("### 🛡️ Signals Observed")
            for signal in user_view['signals_observed']:
                st.info(f"**{signal['title']}**: {signal['detail']}")
            
            st.markdown("### 🤖 AI Recommendations")
            for protection in user_view['protect_yourself']:
                st.warning(f"**{protection['title']}**: {protection['description']}")
        else:
            st.markdown("### 📊 Facts Only")
            st.info(f"**Classification:** {user_view.get('classification', user_view.get('persona', 'N/A'))}")
            st.info(f"**Verdict:** {user_view.get('verdict', 'N/A')}")
            if user_view.get('data_quality'):
                dq = user_view['data_quality']
                if dq.get('partial') or dq.get('notes'):
                    st.warning("**Data Quality:** Partial analysis - some sections incomplete")
                    for note in dq.get('notes', []):
                        st.text(f"  • {note}")
        
        # Buttons to load other views on-demand
        st.markdown("---")
        st.markdown("### 📊 Additional Views")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🏢 Customer/Treasury", use_container_width=True, key="btn_customer"):
                st.session_state.show_view = "customer"
                st.rerun()
        
        with col2:
            if st.button("🔌 VASP/Provider", use_container_width=True, key="btn_vasp"):
                st.session_state.show_view = "vasp"
                st.rerun()
        
        with col3:
            if st.button("📋 Financial Institution", use_container_width=True, key="btn_fi"):
                st.session_state.show_view = "fi"
                st.rerun()
        
        with col4:
            if st.button("📝 Logs", use_container_width=True, key="btn_logs"):
                st.session_state.show_view = "logs"
                st.rerun()
        
        # Show selected view on-demand
        if st.session_state.show_view == "customer":
            st.markdown("---")
            st.header("🏢 Customer/Treasury View")
            customer_view = render_customer_view(protection_report)
            
            st.markdown(f"**Classification:** {customer_view['classification']}")
            st.markdown(f"**Confidence:** {customer_view['confidence']}")
            
            if customer_view['setup_guidance']:
                st.markdown("### 📋 Setup Guidance")
                for guidance in customer_view['setup_guidance']:
                    st.info(f"• {guidance}")
            
            if customer_view['controls_checklist']:
                st.markdown("### ✅ Controls Checklist")
                for control in customer_view['controls_checklist']:
                    priority_emoji = "🔴" if control['priority'] == "P1" else "🟡" if control['priority'] == "P2" else "🟢"
                    st.markdown(f"{priority_emoji} **{control['control']}** ({control['priority']})")
                    st.text(f"   {control['description']}")
            
            if customer_view['training_tips']:
                st.markdown("### 💡 Training Tips")
                for tip in customer_view['training_tips']:
                    st.info(f"• {tip}")
        
        elif st.session_state.show_view == "vasp":
            st.markdown("---")
            st.header("🔌 VASP/Wallet Provider View")
            vasp_view = render_vasp_view(protection_report)
            
            st.markdown("**Machine-readable output (JSON format):**")
            st.json(vasp_view)
        
        elif st.session_state.show_view == "fi":
            st.markdown("---")
            st.header("📋 Financial Institution View")
            fi_view = render_fi_view(protection_report)
            
            st.markdown("### 🔍 Indicators Observed")
            for indicator in fi_view['indicators_observed']:
                severity_color = {
                    "HIGH": "🔴",
                    "MEDIUM": "🟡",
                    "LOW": "🟢"
                }.get(indicator['severity'], "⚪")
                st.markdown(f"{severity_color} **{indicator['indicator']}**: {indicator['title']}")
                st.text(f"   {indicator['detail']}")
                if indicator['evidence_keys']:
                    st.caption(f"Evidence: {', '.join(indicator['evidence_keys'])}")
            
            if fi_view['data_limitations']:
                st.markdown("### ⚠️ Data Limitations")
                for limitation in fi_view['data_limitations']:
                    st.warning(f"• {limitation}")
            
            if fi_view['recommended_controls']:
                st.markdown("### 🛡️ Recommended Controls")
                for control in fi_view['recommended_controls']:
                    st.markdown(f"**{control['title']}** ({control['priority']})")
                    st.text(f"   Type: {control['control_type']}")
                    st.text(f"   {control['description']}")
            
            if fi_view['audit_trace']:
                st.markdown("### 📊 Audit Trace")
                st.json(fi_view['audit_trace'])
        
        elif st.session_state.show_view == "logs":
            st.markdown("---")
            st.header("📝 Execution Logs")
            logs = st.session_state.current_analysis_result.get('memory_logs', []) if st.session_state.current_analysis_result else []
            with st.expander("View detailed execution logs", expanded=True):
                for log in logs:
                    st.text(log)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem 1rem; background: white; border-radius: 12px; margin-top: 3rem;">
        <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">
            <strong style="color: #EB001B;">WalletLens</strong>
        </p>
        <p style="color: #9ca3af; font-size: 0.9rem; margin-bottom: 1rem;">
            Powered by Google Gemini AI and BigQuery
        </p>
        <p style="color: #9ca3af; font-size: 0.85rem;">
            Built by <strong style="color: #6b7280;">Jaya Mandlik</strong> & <strong style="color: #6b7280;">Katie Li</strong> | Team Aegis
        </p>
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("## About WalletLens")
    
    st.markdown("""
    **WalletLens** is an AI-powered blockchain forensic agent that profiles on-chain wallet addresses and provides 
    assistive risk assessment using Google Gemini 2.5 and BigQuery. Unlike traditional risk scoring systems, 
    WalletLens focuses on **signals, confidence, and protective actions** rather than deterministic blocking decisions.
    
    Currently supports **Ethereum** with plans to expand to other blockchain networks.
    
    ### What Makes WalletLens Different
    
    - **No Risk Scores**: We don't output numeric scores that could be misinterpreted as guarantees
    - **No Blocking Decisions**: We provide recommendations, not BLOCK/ALLOW commands
    - **Assistive Mode**: Users control what they see with AI Recommendations toggle
    - **Multi-Stakeholder Views**: Different outputs for Users, Businesses, VASPs, and Financial Institutions
    - **Transparent Data Quality**: Clear indicators when analysis is partial or limited
    """)
    
    st.markdown("### 🎯 Key Features")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - **Persona Classification**: Identifies wallet types (Merchant/Exchange, Bot/MEV, Whale/Treasury, Exploiter, Compromised Wallet)
        - **Safety Assessment**: Clear risk verdicts (🟢 SAFE, 🟡 CAUTION, 🔴 HIGH RISK)
        - **Protection Layer**: Signals, confidence levels, and protective action recommendations
        - **1-Year Analysis**: Comprehensive historical data (365 days)
        - **Pattern Detection**: Exploit and drain detection
        """)
    
    with col2:
        st.markdown("""
        - **AI Recommendations**: Toggle to show/hide protective recommendations
        - **Multi-View Output**: User, Customer/Treasury, VASP, and Financial Institution views
        - **Analysis History**: Quick access to recent analyses
        - **Full Observability**: Detailed execution logs
        - **Performance Optimized**: Optional Materialized Views for fast queries
        """)
    
    st.markdown("### 🔌 Integration Options")
    
    st.markdown("""
    WalletLens can be integrated into various platforms and services through multiple integration methods:
    """)
    
    # Integration Methods
    st.markdown("#### 📡 Integration Methods")
    
    integration_methods = [
        {
            "method": "REST API",
            "description": "HTTP REST API endpoints for synchronous wallet analysis",
            "features": [
                "POST /api/v1/analyze - Analyze a single wallet address",
                "GET /api/v1/analysis/{address} - Retrieve cached analysis",
                "POST /api/v1/batch - Analyze multiple addresses",
                "Returns JSON with ProtectionReport structure",
                "Supports all stakeholder views (User, VASP, FI, Customer)"
            ],
            "use_cases": [
                "Real-time wallet checks in applications",
                "Batch processing for compliance screening",
                "Integration into existing backend systems"
            ]
        },
        {
            "method": "Webhook Integration",
            "description": "Event-driven webhooks for asynchronous analysis and alerts",
            "features": [
                "Subscribe to wallet analysis events",
                "Receive notifications when risky addresses are detected",
                "Custom webhook endpoints for your application",
                "Retry mechanism for failed deliveries",
                "Payload includes full ProtectionReport"
            ],
            "use_cases": [
                "Real-time monitoring and alerting",
                "Integration with incident response systems",
                "Automated compliance workflows"
            ]
        },
        {
            "method": "WebSocket API",
            "description": "Real-time bidirectional communication for live analysis",
            "features": [
                "Stream analysis results as they're generated",
                "Subscribe to multiple addresses simultaneously",
                "Low-latency updates for real-time applications",
                "Connection management and reconnection handling"
            ],
            "use_cases": [
                "Live transaction monitoring",
                "Real-time dashboards",
                "Interactive wallet screening tools"
            ]
        },
        {
            "method": "SDK / Client Libraries",
            "description": "Language-specific SDKs for easy integration",
            "features": [
                "Python, JavaScript/TypeScript, Go SDKs available",
                "Type-safe interfaces for ProtectionReport",
                "Built-in error handling and retries",
                "Local caching support"
            ],
            "use_cases": [
                "Quick integration into existing codebases",
                "Type-safe development",
                "Simplified error handling"
            ]
        }
    ]
    
    for method in integration_methods:
        with st.expander(f"🔧 {method['method']}"):
            st.markdown(f"**{method['description']}**")
            st.markdown("**Features:**")
            for feature in method['features']:
                st.markdown(f"- {feature}")
            st.markdown("**Use Cases:**")
            for use_case in method['use_cases']:
                st.markdown(f"- {use_case}")
    
    # Platform Integrations
    st.markdown("#### 🌐 Platform Integrations")
    
    integration_options = [
        {
            "name": "Web3 Wallets",
            "description": "MetaMask, WalletConnect, Coinbase Wallet - Add safety checks before transactions",
            "integration": "API call before transaction confirmation, show ProtectionReport in UI",
            "use_case": "Users can verify recipient addresses before sending funds"
        },
        {
            "name": "DeFi Platforms",
            "description": "Uniswap, Aave, Compound - Screen liquidity providers and counterparties",
            "integration": "API integration to check addresses, display warnings based on ProtectionReport",
            "use_case": "Platforms can warn users about risky addresses in their UI"
        },
        {
            "name": "NFT Marketplaces",
            "description": "OpenSea, LooksRare, Blur - Verify seller/buyer addresses",
            "integration": "Webhook or API to flag suspicious accounts, show Persona classification",
            "use_case": "Marketplaces can flag suspicious accounts automatically"
        },
        {
            "name": "Crypto Exchanges",
            "description": "Binance, Coinbase, Kraken - Enhanced KYC and risk assessment",
            "integration": "API for deposit address screening, webhook alerts for high-risk addresses",
            "use_case": "Exchanges can screen deposit addresses and detect exploiters"
        },
        {
            "name": "Payment Processors",
            "description": "Stripe, PayPal Crypto, Square - Merchant verification",
            "integration": "API integration to verify merchant wallets, return VASP view for compliance",
            "use_case": "Payment processors can verify merchant wallet legitimacy"
        },
        {
            "name": "Mastercard Crypto Credentials",
            "description": "Mastercard's crypto credential system - Enhanced identity verification",
            "integration": "API integration to add on-chain analysis layer, combine with verified identities",
            "use_case": "Add on-chain behavior analysis to verified identity credentials"
        },
        {
            "name": "Blockchain Explorers",
            "description": "Etherscan, Blockscout - Enhanced address information",
            "integration": "API to fetch ProtectionReport, display in address detail pages",
            "use_case": "Explorers can add WalletLens analysis as a premium feature"
        },
        {
            "name": "Security Tools",
            "description": "Scam detection, wallet monitoring, transaction screening",
            "integration": "Webhook subscriptions for alerts, API for batch screening",
            "use_case": "Security platforms can use WalletLens for automated threat detection"
        },
        {
            "name": "Financial Institutions",
            "description": "Banks, compliance platforms - Regulatory compliance and risk assessment",
            "integration": "API for compliance workflows, Financial Institution view for audit trails",
            "use_case": "Screen addresses for regulatory compliance, generate audit reports"
        },
        {
            "name": "Treasury Management",
            "description": "Corporate treasury, DAO treasury management - Operational security",
            "integration": "API integration, Customer/Treasury view for setup guidance",
            "use_case": "Verify counterparties, implement treasury controls, training guidance"
        }
    ]
    
    for option in integration_options:
        with st.expander(f"🔗 {option['name']}"):
            st.markdown(f"**Description:** {option['description']}")
            st.markdown(f"**Integration Method:** {option['integration']}")
            st.markdown(f"**Use Case:** {option['use_case']}")
    
    st.markdown("### 👥 How Users Can Use WalletLens")
    
    st.markdown("""
    #### For Individual Users:
    1. **Before Sending Crypto**: Paste the recipient address to verify it's safe
    2. **Research Wallets**: Analyze any on-chain wallet address to understand its behavior
    3. **Avoid Scams**: Get instant warnings about exploiters and compromised wallets
    4. **Due Diligence**: Check addresses before interacting with DeFi protocols
    5. **AI Recommendations**: Toggle to see protective actions and signals
    
    #### For Developers:
    1. **REST API**: Integrate WalletLens via HTTP API endpoints
    2. **Webhook Integration**: Subscribe to wallet analysis events and alerts
    3. **WebSocket API**: Real-time streaming for live analysis
    4. **SDK Integration**: Use language-specific SDKs (Python, JavaScript, Go)
    5. **Batch Analysis**: Analyze multiple addresses programmatically
    6. **Custom Views**: Access different stakeholder views (User, VASP, FI, Customer)
    
    #### For Businesses:
    1. **Compliance**: Screen addresses for regulatory compliance with audit trails
    2. **Risk Management**: Assess counterparty risk before transactions
    3. **Fraud Prevention**: Detect suspicious patterns automatically via webhooks
    4. **Customer Protection**: Warn users about risky addresses in your platform
    5. **Treasury Management**: Get setup guidance and controls checklist
    6. **Integration**: Easy API/webhook integration into existing systems
    """)
    
    st.markdown("### 🛡️ Protection Layer")
    
    st.markdown("""
    WalletLens includes a **Protection Layer** that provides assistive risk assessment:
    
    - **Observed Signals**: Coded signals derived from facts (SHORT_LIVED, HIGH_VALUE_FLOW, etc.)
    - **Confidence Levels**: Transparent data quality indicators (HIGH/MEDIUM/LOW)
    - **Protective Actions**: Recommended actions (not blocking decisions)
    - **Multi-View Output**: Different formats for Users, Businesses, VASPs, and Financial Institutions
    - **No Risk Scores**: We don't output numeric scores that could be misinterpreted
    - **No Blocking**: We provide recommendations, not BLOCK/ALLOW commands
    
    Toggle **AI Recommendations** in the sidebar to show/hide protective recommendations.
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

# Sidebar - Unified gradient background with white text
with st.sidebar:
    # Settings Header
    st.markdown("""
    <div style="padding: 1rem 0; margin-bottom: 1.5rem; text-align: center;">
        <h2 style="color: white; font-weight: 700; font-size: 1.5rem; margin: 0;">
            ⚙️ Settings
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    blockchain_options = {
        "Ethereum (ETH)": {"enabled": True, "icon": "⛓️"},
        "Bitcoin (BTC)": {"enabled": False, "icon": "₿"},
        "Polygon (MATIC)": {"enabled": False, "icon": "🔷"},
        "BNB Chain (BNB)": {"enabled": False, "icon": "🟡"},
        "Arbitrum (ARB)": {"enabled": False, "icon": "🔵"},
        "Optimism (OP)": {"enabled": False, "icon": "🔴"},
        "Avalanche (AVAX)": {"enabled": False, "icon": "❄️"},
        "Base": {"enabled": False, "icon": "🔵"},
        "Solana (SOL)": {"enabled": False, "icon": "◎"}
    }
    
    # Blockchain Type Selection
    st.markdown("""
    <div style="margin-bottom: 0.75rem;">
        <h3 style="color: white; font-weight: 600; font-size: 0.95rem; margin: 0 0 0.5rem 0;">
            🌐 Blockchain Network
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    selected_blockchain = st.selectbox(
        "",
        options=list(blockchain_options.keys()),
        index=0,
        disabled=False,
        help="Currently only Ethereum is supported. Other networks coming soon!",
        label_visibility="collapsed"
    )
    
    if not blockchain_options[selected_blockchain]["enabled"]:
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.2); color: white; padding: 0.75rem; border-radius: 8px; 
                    border: 1px solid rgba(255, 255, 255, 0.3); margin-top: 0.5rem; font-size: 0.85rem;">
            🚧 {selected_blockchain} support coming soon!
        </div>
        """, unsafe_allow_html=True)
    
    # AI Recommendations
    st.markdown("""
    <div style="margin-top: 1.5rem; margin-bottom: 0.75rem;">
        <h3 style="color: white; font-weight: 600; font-size: 0.95rem; margin: 0 0 0.5rem 0;">
            🤖 AI Recommendations
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    ai_recommendations = st.toggle(
        "Enable AI recommendations",
        value=st.session_state.ai_recommendations,
        help="ON: Shows AI recommendations and protective actions. OFF: Shows facts and classification only."
    )
    st.session_state.ai_recommendations = ai_recommendations
    
    if ai_recommendations:
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.3); color: white; padding: 0.75rem; border-radius: 8px; 
                    text-align: center; font-weight: 600; margin-top: 0.5rem; font-size: 0.9rem; 
                    border: 1px solid rgba(16, 185, 129, 0.5);">
            ✓ Active
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.15); color: white; padding: 0.75rem; 
                    border-radius: 8px; text-align: center; font-weight: 600; margin-top: 0.5rem; 
                    font-size: 0.9rem; border: 1px solid rgba(255, 255, 255, 0.3);">
            Facts Only
        </div>
        """, unsafe_allow_html=True)
    
    # Quick Stats
    st.markdown("""
    <div style="margin-top: 1.5rem; margin-bottom: 0.75rem;">
        <h3 style="color: white; font-weight: 600; font-size: 0.95rem; margin: 0 0 0.5rem 0;">
            📊 Quick Stats
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    history = st.session_state.analysis_history.get_history()
    total_analyses = len(history)
    
    if total_analyses > 0:
        safe_count = sum(1 for a in history if a.get('safety_verdict') and 'SAFE' in a.get('safety_verdict', ''))
        caution_count = sum(1 for a in history if a.get('safety_verdict') and 'CAUTION' in a.get('safety_verdict', ''))
        risk_count = sum(1 for a in history if a.get('safety_verdict') and 'HIGH RISK' in a.get('safety_verdict', ''))
        
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.1); padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border: 1px solid rgba(255, 255, 255, 0.2);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(255, 255, 255, 0.2);">
                <span style="color: white; font-size: 0.9rem;">Total:</span>
                <strong style="color: white; font-size: 0.9rem;">{total_analyses}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: white; font-size: 0.85rem;">🟢 Safe</span>
                <strong style="color: white; font-size: 0.85rem;">{safe_count}</strong>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: white; font-size: 0.85rem;">🟡 Caution</span>
                <strong style="color: white; font-size: 0.85rem;">{caution_count}</strong>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: white; font-size: 0.85rem;">🔴 High Risk</span>
                <strong style="color: white; font-size: 0.85rem;">{risk_count}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.1); padding: 1.5rem; border-radius: 10px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.2);">
            <p style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem; margin: 0;">No analyses yet</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent Analyses
    st.markdown("""
    <div style="margin-top: 1.5rem; margin-bottom: 0.75rem;">
        <h3 style="color: white; font-weight: 600; font-size: 0.95rem; margin: 0 0 0.5rem 0;">
            📜 Recent Analyses
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    if history:
        for i, analysis in enumerate(history[:5]):
            with st.expander(f"🔍 {analysis['address'][:8]}...{analysis['address'][-6:]}", expanded=False):
                if analysis['safety_verdict']:
                    verdict_emoji = "🟢" if "SAFE" in analysis['safety_verdict'] else "🟡" if "CAUTION" in analysis['safety_verdict'] else "🔴"
                    st.markdown(f"""
                    <div style="color: white; margin-bottom: 0.5rem;">
                        <strong>{verdict_emoji} {analysis['safety_verdict']}</strong>
                    </div>
                    """, unsafe_allow_html=True)
                if analysis['classification']:
                    st.markdown(f"""
                    <div style="color: white; margin-bottom: 0.5rem;">
                        <strong>Type:</strong> {analysis['classification']}
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown(f"""
                <div style="color: rgba(255, 255, 255, 0.8); font-size: 0.8rem;">
                    {analysis['timestamp'].strftime('%Y-%m-%d %H:%M')}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.1); padding: 1.5rem; border-radius: 10px; text-align: center; border: 1px solid rgba(255, 255, 255, 0.2);">
            <p style="color: rgba(255, 255, 255, 0.8); font-size: 0.85rem; margin: 0;">No analyses yet</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Help & Support
    st.markdown("""
    <div style="margin-top: 1.5rem; margin-bottom: 0.75rem;">
        <h3 style="color: white; font-weight: 600; font-size: 0.95rem; margin: 0 0 0.5rem 0;">
            💡 Help & Support
        </h3>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📖 How to use", expanded=False):
        st.markdown("""
        <div style="color: white; font-size: 0.9rem; line-height: 1.6;">
        1. Enter a wallet address<br>
        2. Click "Analyze Wallet"<br>
        3. Review User View results<br>
        4. Click buttons for additional views
        </div>
        """, unsafe_allow_html=True)
    
    with st.expander("🔗 Integration", expanded=False):
        st.markdown("""
        <div style="color: white; font-size: 0.9rem; line-height: 1.6;">
        • REST API<br>
        • Webhook Integration<br>
        • WebSocket API<br>
        • SDK Libraries<br><br>
        See About page for details.
        </div>
        """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0; border-top: 1px solid rgba(255, 255, 255, 0.3); margin-top: 2rem;">
        <p style="color: white; font-size: 1rem; font-weight: 700; margin-bottom: 0.5rem;">
            WalletLens
        </p>
        <p style="color: rgba(255, 255, 255, 0.9); font-size: 0.85rem; margin-bottom: 0.25rem;">
            Team Aegis
        </p>
        <p style="color: rgba(255, 255, 255, 0.8); font-size: 0.75rem; margin: 0;">
            Built by <strong style="color: white;">Jaya Mandlik</strong> & <strong style="color: white;">Katie Li</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

