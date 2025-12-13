"""Render protection reports for different stakeholder views."""

from typing import Dict, Any

# Handle both relative and absolute imports
try:
    from .protection_models import ProtectionReport, Signal, Protection
except ImportError:
    from protection_models import ProtectionReport, Signal, Protection


def render_user_view(report: ProtectionReport, safety_mode: bool = True) -> Dict[str, Any]:
    """
    Render user-friendly view with plain English.
    
    Args:
        report: Protection report
        safety_mode: If True, show warnings + protections; if False, facts only
        
    Returns:
        Dictionary with rendered content
    """
    # Get top 3 signals (exclude technical ones unless affecting confidence)
    user_signals = [
        s for s in report.observed_signals
        if s.code not in ["MISSING_MV", "BYTES_LIMITED", "PARTIAL_DATA"]
    ]
    top_signals = sorted(user_signals, key=lambda s: {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(s.severity, 0), reverse=True)[:3]
    
    # Get top 3 protections
    top_protections = report.recommended_protections[:3]
    
    content = {
        "summary": f"This wallet shows signals consistent with {report.classification or 'unknown type'}.",
        "persona": report.classification,  # Add persona/classification info
        "verdict": report.verdict,  # Add verdict info
        "confidence": report.confidence_level,
        "signals_observed": [
            {
                "title": s.title,
                "detail": s.detail
            }
            for s in top_signals
        ],
        "protect_yourself": [
            {
                "title": p.title,
                "description": p.description
            }
            for p in top_protections
        ] if safety_mode else []
    }
    
    if not safety_mode:
        # Facts-only mode
        content["classification"] = report.classification
        content["verdict"] = report.verdict
        content["data_quality"] = {
            "complete": report.data_quality.complete,
            "partial": report.data_quality.partial,
            "notes": report.data_quality.notes
        }
    
    return content


def render_customer_view(report: ProtectionReport) -> Dict[str, Any]:
    """
    Render customer/treasury business view with setup guidance.
    
    Returns:
        Dictionary with treasury-focused content
    """
    # Filter treasury-relevant protections
    treasury_protections = [
        p for p in report.recommended_protections
        if any(keyword in p.code for keyword in [
            "HARDWARE", "MULTISIG", "TIME_DELAY", "TREASURY", "OPERATIONAL", "PASSKEY", "2FA"
        ])
    ]
    
    # Setup guidance
    setup_guidance = []
    if "Whale/Treasury" in (report.classification or ""):
        setup_guidance.append("Use a dedicated treasury vault wallet separate from operational wallets")
        setup_guidance.append("Implement multisig with time delays for large transfers")
        setup_guidance.append("Store long-term funds in hardware wallet (cold storage)")
    
    # Controls checklist
    controls = []
    for p in treasury_protections:
        controls.append({
            "control": p.title,
            "description": p.description,
            "priority": p.priority
        })
    
    # Training tips
    training_tips = [
        "Never reuse treasury wallet to connect to dApps",
        "Use separate hot wallet for DeFi interactions",
        "Regularly review and revoke token approvals",
        "Implement allowlists for known counterparties"
    ]
    
    return {
        "classification": report.classification,
        "setup_guidance": setup_guidance,
        "controls_checklist": controls,
        "training_tips": training_tips,
        "confidence": report.confidence_level
    }


def render_vasp_view(report: ProtectionReport) -> Dict[str, Any]:
    """
    Render VASP/Wallet provider view (machine-readable JSON-like).
    
    Returns:
        Dictionary suitable for JSON output
    """
    signal_codes = [s.code for s in report.observed_signals]
    protection_codes = [p.code for p in report.recommended_protections]
    
    return {
        "classification": report.classification,
        "confidence": report.confidence_level,
        "signals": signal_codes,
        "recommended_protections": protection_codes,
        "data_quality": {
            "partial": report.data_quality.partial,
            "missing_views": report.data_quality.missing_views,
            "bytes_limited": report.data_quality.bytes_limited,
            "reason": "bytes_billed_limit" if report.data_quality.bytes_limited else None
        },
        "disclaimer_mode": "assistive"
    }


def render_fi_view(report: ProtectionReport) -> Dict[str, Any]:
    """
    Render Financial Institution view with evidence and traceability.
    
    Returns:
        Dictionary with FI-focused content
    """
    # Indicators with evidence
    indicators = []
    for signal in report.observed_signals:
        indicators.append({
            "indicator": signal.code,
            "title": signal.title,
            "detail": signal.detail,
            "evidence_keys": signal.evidence_keys,
            "severity": signal.severity
        })
    
    # Data limitations
    data_limitations = []
    if report.data_quality.bytes_limited:
        data_limitations.append("Bytes billed limit exceeded - some queries skipped")
    if report.data_quality.missing_views:
        data_limitations.append("Materialized views missing - using fallback queries")
    if report.data_quality.partial:
        data_limitations.append("Partial data - not all analysis sections complete")
    if report.data_quality.notes:
        data_limitations.extend(report.data_quality.notes)
    
    # Recommended controls (framed as protections, not decisions)
    recommended_controls = []
    for p in report.recommended_protections:
        # Map to compliance-friendly language
        control_type = "step-up-auth" if "CONFIRMATION" in p.code or "PASSKEY" in p.code else \
                       "velocity-limit" if "VELOCITY" in p.code else \
                       "allowlist" if "ALLOWLIST" in p.code else \
                       "cooldown" if "COOLDOWN" in p.code else \
                       "warning" if "WARNING" in p.code else \
                       "other"
        
        recommended_controls.append({
            "control_type": control_type,
            "title": p.title,
            "description": p.description,
            "priority": p.priority
        })
    
    # Audit trace
    audit_trace = None
    if report.trace:
        audit_trace = {
            "run_id": report.trace.run_id,
            "timestamp": report.trace.timestamp.isoformat() if report.trace.timestamp else None,
            "model_name": report.trace.model_name,
            "query_outcomes_summary": report.trace.query_outcomes_summary
        }
    
    return {
        "indicators_observed": indicators,
        "data_limitations": data_limitations,
        "recommended_controls": recommended_controls,
        "classification": report.classification,
        "verdict": report.verdict,
        "confidence": report.confidence_level,
        "audit_trace": audit_trace
    }

