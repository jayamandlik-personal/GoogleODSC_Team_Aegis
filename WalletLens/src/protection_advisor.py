"""Rule-based protection advisor - maps signals/classification to recommended protections."""

from typing import List, Set

# Handle both relative and absolute imports
try:
    from .protection_models import Protection, Signal, DataQuality
except ImportError:
    from protection_models import Protection, Signal, DataQuality


# Classification → default protections mapping
CLASSIFICATION_PROTECTIONS = {
    "Exploiter": [
        "AVOID_SIGNING_APPROVALS",
        "SUGGEST_TEST_AMOUNT",
        "SHOW_WARNING_BANNER",
        "REQUIRE_EXPLICIT_CONFIRMATION",
        "LIMIT_TX_AMOUNT",
        "REVOKE_APPROVALS_CHECK"
    ],
    "Compromised Wallet": [
        "AVOID_SIGNING_APPROVALS",
        "SUGGEST_TEST_AMOUNT",
        "SHOW_WARNING_BANNER",
        "REQUIRE_EXPLICIT_CONFIRMATION",
        "REVOKE_APPROVALS_CHECK",
        "USE_SEPARATE_SPENDING_WALLET"
    ],
    "Merchant/Exchange": [
        "REVIEW_TX_SIMULATION",
        "SUGGEST_TEST_AMOUNT"
    ],
    "Bot/MEV": [
        "REVIEW_TX_SIMULATION",
        "LIMIT_VELOCITY",
        "COOLDOWN_PERIOD"
    ],
    "Whale/Treasury": [
        "SUGGEST_HARDWARE_WALLET_FOR_SAVINGS",
        "SUGGEST_SMART_WALLET_MULTISIG",
        "SUGGEST_TIME_DELAY",
        "SPLIT_TREASURY_AND_OPERATIONAL",
        "REQUIRE_PASSKEY_OR_2FA"
    ]
}


# Signal → protection mapping
SIGNAL_PROTECTIONS = {
    "SHORT_LIVED": ["SUGGEST_TEST_AMOUNT", "SHOW_WARNING_BANNER"],
    "NEW_ADDRESS": ["SUGGEST_TEST_AMOUNT", "REVIEW_TX_SIMULATION"],
    "BURST_ACTIVITY": ["LIMIT_VELOCITY", "COOLDOWN_PERIOD"],
    "HIGH_VALUE_FLOW": ["SUGGEST_TEST_AMOUNT", "LIMIT_TX_AMOUNT", "REQUIRE_EXPLICIT_CONFIRMATION"],
    "OUTFLOW_DOMINANT": ["SHOW_WARNING_BANNER", "AVOID_SIGNING_APPROVALS"],
    "APPROVAL_PATTERN": ["AVOID_SIGNING_APPROVALS", "REVOKE_APPROVALS_CHECK", "BLOCK_APPROVAL_FUNCTIONS"],
    "TOKEN_DUMP_PATTERN": ["SHOW_WARNING_BANNER", "AVOID_SIGNING_APPROVALS", "REQUIRE_EXPLICIT_CONFIRMATION"],
    "HIGH_CONTRACT_INTERACTION": ["REVIEW_TX_SIMULATION", "AVOID_SIGNING_APPROVALS"],
    "BYTES_LIMITED": ["LIMITED_CONFIDENCE_NOTICE"],
    "PARTIAL_DATA": ["LIMITED_CONFIDENCE_NOTICE"],
    "MISSING_MV": ["SUGGEST_RETRY_WITH_AGGREGATES"]
}


# Verdict → base protections
VERDICT_PROTECTIONS = {
    "HIGH RISK": [
        "SHOW_WARNING_BANNER",
        "REQUIRE_EXPLICIT_CONFIRMATION",
        "AVOID_SIGNING_APPROVALS",
        "SUGGEST_TEST_AMOUNT"
    ],
    "CAUTION": [
        "SHOW_WARNING_BANNER",
        "SUGGEST_TEST_AMOUNT",
        "REVIEW_TX_SIMULATION"
    ],
    "SAFE": [
        "REVIEW_TX_SIMULATION"
    ]
}


# Protection definitions
PROTECTION_DEFINITIONS = {
    "SHOW_WARNING_BANNER": Protection(
        code="SHOW_WARNING_BANNER",
        title="Show warning banner",
        description="Show a clear caution banner before interacting.",
        priority="P1"
    ),
    "REQUIRE_EXPLICIT_CONFIRMATION": Protection(
        code="REQUIRE_EXPLICIT_CONFIRMATION",
        title="Require explicit confirmation",
        description="Ask user to confirm they understand the risk before proceeding.",
        priority="P1"
    ),
    "SUGGEST_TEST_AMOUNT": Protection(
        code="SUGGEST_TEST_AMOUNT",
        title="Use small test transfer",
        description="Use a small test transfer first; avoid moving large funds.",
        priority="P1"
    ),
    "AVOID_SIGNING_APPROVALS": Protection(
        code="AVOID_SIGNING_APPROVALS",
        title="Avoid token approvals",
        description="Avoid token approvals / blind signatures with this address or dApp.",
        priority="P1"
    ),
    "REVIEW_TX_SIMULATION": Protection(
        code="REVIEW_TX_SIMULATION",
        title="Review transaction simulation",
        description="Use transaction simulation (if available) before signing.",
        priority="P1"
    ),
    "REVOKE_APPROVALS_CHECK": Protection(
        code="REVOKE_APPROVALS_CHECK",
        title="Review and revoke approvals",
        description="Review and revoke existing token approvals regularly.",
        priority="P2"
    ),
    "USE_SEPARATE_SPENDING_WALLET": Protection(
        code="USE_SEPARATE_SPENDING_WALLET",
        title="Use separate spending wallet",
        description="Use a separate hot wallet for dApps; keep main funds isolated.",
        priority="P1"
    ),
    "LIMIT_TX_AMOUNT": Protection(
        code="LIMIT_TX_AMOUNT",
        title="Apply transfer amount limits",
        description="Apply transfer amount limits for high-signal interactions.",
        priority="P1"
    ),
    "LIMIT_VELOCITY": Protection(
        code="LIMIT_VELOCITY",
        title="Apply rate limits",
        description="Apply rate limits (transactions/day) for suspicious patterns.",
        priority="P1"
    ),
    "COOLDOWN_PERIOD": Protection(
        code="COOLDOWN_PERIOD",
        title="Add cooldown delay",
        description="Add a cooldown delay (e.g., 24h) for approvals or large transfers.",
        priority="P2"
    ),
    "ALLOWLIST_RECIPIENTS": Protection(
        code="ALLOWLIST_RECIPIENTS",
        title="Restrict to allowlisted recipients",
        description="Restrict transfers to allowlisted recipient addresses.",
        priority="P1"
    ),
    "BLOCK_APPROVAL_FUNCTIONS": Protection(
        code="BLOCK_APPROVAL_FUNCTIONS",
        title="Restrict approval-like calls",
        description="Disallow approval-like calls in risky contexts.",
        priority="P1"
    ),
    "SUGGEST_HARDWARE_WALLET_FOR_SAVINGS": Protection(
        code="SUGGEST_HARDWARE_WALLET_FOR_SAVINGS",
        title="Use hardware wallet for savings",
        description="Store long-term funds in a hardware wallet (cold storage).",
        priority="P1"
    ),
    "SUGGEST_SMART_WALLET_MULTISIG": Protection(
        code="SUGGEST_SMART_WALLET_MULTISIG",
        title="Use multisig/smart wallet",
        description="Use a multisig/smart wallet for treasury custody.",
        priority="P1"
    ),
    "SUGGEST_TIME_DELAY": Protection(
        code="SUGGEST_TIME_DELAY",
        title="Use time delay for large transfers",
        description="Use a time delay for large transfers (treasury-grade control).",
        priority="P2"
    ),
    "SPLIT_TREASURY_AND_OPERATIONAL": Protection(
        code="SPLIT_TREASURY_AND_OPERATIONAL",
        title="Separate treasury and operational wallets",
        description="Separate treasury vault wallet from operational spending wallet.",
        priority="P1"
    ),
    "REQUIRE_PASSKEY_OR_2FA": Protection(
        code="REQUIRE_PASSKEY_OR_2FA",
        title="Require strong authentication",
        description="Require strong authentication for high-impact actions (enterprise).",
        priority="P1"
    ),
    "ADD_TO_WATCHLIST": Protection(
        code="ADD_TO_WATCHLIST",
        title="Monitor for future interactions",
        description="Monitor for future interactions with this address.",
        priority="P2"
    ),
    "ALERT_ON_LARGE_OUTFLOW": Protection(
        code="ALERT_ON_LARGE_OUTFLOW",
        title="Alert on large outflows",
        description="Alert if large outflows happen within X minutes/hours of interaction.",
        priority="P2"
    ),
    "ALERT_ON_NEW_COUNTERPARTIES": Protection(
        code="ALERT_ON_NEW_COUNTERPARTIES",
        title="Alert on new counterparties",
        description="Alert if counterparties spike suddenly.",
        priority="P3"
    ),
    "LIMITED_CONFIDENCE_NOTICE": Protection(
        code="LIMITED_CONFIDENCE_NOTICE",
        title="Explain partial analysis",
        description="Explain that analysis is partial due to query limits.",
        priority="P1"
    ),
    "SUGGEST_RETRY_WITH_AGGREGATES": Protection(
        code="SUGGEST_RETRY_WITH_AGGREGATES",
        title="Enable materialized views",
        description="Recommend enabling materialized views / aggregates for better coverage.",
        priority="P3"
    )
}


def recommend_protections(
    signals: List[Signal],
    classification: str,
    verdict: str,
    data_quality: DataQuality
) -> List[Protection]:
    """
    Generate recommended protections based on signals, classification, and verdict.
    
    Args:
        signals: List of observed signals
        classification: Wallet classification
        verdict: Safety verdict (SAFE, CAUTION, HIGH RISK)
        data_quality: Data quality flags
        
    Returns:
        List of Protection objects (prioritized)
    """
    protection_codes: Set[str] = set()
    
    # Add verdict-based protections
    verdict_key = verdict.upper() if verdict else "SAFE"
    if verdict_key in VERDICT_PROTECTIONS:
        protection_codes.update(VERDICT_PROTECTIONS[verdict_key])
    
    # Add classification-based protections
    if classification:
        # Try exact match first
        if classification in CLASSIFICATION_PROTECTIONS:
            protection_codes.update(CLASSIFICATION_PROTECTIONS[classification])
        else:
            # Try partial match (e.g., "Merchant/Exchange" -> "Merchant/Exchange")
            for key, codes in CLASSIFICATION_PROTECTIONS.items():
                if key.lower() in classification.lower() or classification.lower() in key.lower():
                    protection_codes.update(codes)
                    break
    
    # Add signal-based protections
    for signal in signals:
        if signal.code in SIGNAL_PROTECTIONS:
            protection_codes.update(SIGNAL_PROTECTIONS[signal.code])
    
    # Add data quality protections
    if data_quality.bytes_limited or data_quality.partial:
        protection_codes.add("LIMITED_CONFIDENCE_NOTICE")
    
    if data_quality.missing_views:
        protection_codes.add("SUGGEST_RETRY_WITH_AGGREGATES")
    
    # Convert codes to Protection objects
    protections = []
    for code in protection_codes:
        if code in PROTECTION_DEFINITIONS:
            protections.append(PROTECTION_DEFINITIONS[code])
    
    # Sort by priority (P1 first, then P2, then P3)
    priority_order = {"P1": 1, "P2": 2, "P3": 3}
    protections.sort(key=lambda p: priority_order.get(p.priority, 99))
    
    # Limit to top 6 protections
    return protections[:6]

