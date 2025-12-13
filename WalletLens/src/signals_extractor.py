"""Extract coded signals from metrics and query outcomes."""

from typing import Dict, Any, List, Optional

# Handle both relative and absolute imports
try:
    from .protection_models import Signal, DataQuality
    from .tool_error_parser import parse_logs_for_errors
except ImportError:
    from protection_models import Signal, DataQuality
    from tool_error_parser import parse_logs_for_errors


def extract_signals(
    metrics: Dict[str, Any],
    logs: List[str],
    data_quality: DataQuality
) -> List[Signal]:
    """
    Extract coded signals from metrics and errors.
    
    Args:
        metrics: Dictionary with wallet metrics (from analysis result parsing)
        logs: Execution logs
        data_quality: Data quality flags
        
    Returns:
        List of Signal objects
    """
    signals = []
    errors = parse_logs_for_errors(logs)
    
    # Activity & lifecycle signals
    active_days = metrics.get('active_days', 0)
    first_seen = metrics.get('first_seen')
    last_seen = metrics.get('last_seen')
    tx_count = metrics.get('tx_count', 0)
    
    if active_days > 0 and active_days < 30:
        signals.append(Signal(
            code="SHORT_LIVED",
            title="Short active window",
            detail=f"Address active for {active_days} days",
            evidence_keys=["active_days", "first_seen", "last_seen"],
            severity="MEDIUM"
        ))
    
    if active_days > 0 and active_days < 7:
        signals.append(Signal(
            code="NEW_ADDRESS",
            title="Newly created / first-seen recently",
            detail=f"Address first seen {active_days} days ago",
            evidence_keys=["first_seen", "days_since_first_seen"],
            severity="LOW"
        ))
    
    if tx_count > 0 and active_days > 0:
        tx_per_day = tx_count / active_days
        if tx_per_day > 50:  # Burst threshold
            signals.append(Signal(
                code="BURST_ACTIVITY",
                title="Burst of activity in a short time",
                detail=f"{tx_count} transactions in {active_days} days ({tx_per_day:.1f} tx/day)",
                evidence_keys=["tx_count", "active_days", "tx_per_day"],
                severity="MEDIUM"
            ))
    
    # Flow & value movement signals
    eth_in = metrics.get('eth_in_total', 0)
    eth_out = metrics.get('eth_out_total', 0)
    
    if eth_in > 1000 or eth_out > 1000:  # High value threshold (ETH)
        signals.append(Signal(
            code="HIGH_VALUE_FLOW",
            title="High value movement",
            detail=f"Total ETH moved: {eth_in:.2f} in, {eth_out:.2f} out",
            evidence_keys=["eth_in_total", "eth_out_total"],
            severity="HIGH"
        ))
    
    if eth_in > 0 and eth_out > 0:
        out_in_ratio = eth_out / eth_in
        if out_in_ratio > 1.5:  # Outgoing dominates
            signals.append(Signal(
                code="OUTFLOW_DOMINANT",
                title="Outgoing exceeds incoming",
                detail=f"Out/in ratio: {out_in_ratio:.2f}",
                evidence_keys=["eth_in_total", "eth_out_total", "out_in_ratio"],
                severity="MEDIUM"
            ))
        elif out_in_ratio < 0.5:  # Incoming dominates
            signals.append(Signal(
                code="INFLOW_DOMINANT",
                title="Incoming dominates (accumulation)",
                detail=f"In/out ratio: {1/out_in_ratio:.2f}",
                evidence_keys=["eth_in_total", "eth_out_total"],
                severity="LOW"
            ))
    
    # Counterparty patterns
    unique_to = metrics.get('unique_to', 0)
    unique_from = metrics.get('unique_from', 0)
    unique_counterparties = max(unique_to, unique_from)
    
    if unique_counterparties > 100:
        signals.append(Signal(
            code="HIGH_COUNTERPARTY_DIVERSITY",
            title="Many counterparties",
            detail=f"{unique_counterparties} unique counterparties",
            evidence_keys=["unique_to", "unique_from"],
            severity="MEDIUM"
        ))
    elif unique_counterparties < 5 and tx_count > 20:
        signals.append(Signal(
            code="CONCENTRATED_COUNTERPARTY",
            title="Activity concentrated with few addresses",
            detail=f"{unique_counterparties} counterparties for {tx_count} transactions",
            evidence_keys=["top_counterparty_share", "unique_counterparties"],
            severity="MEDIUM"
        ))
    
    # Contract / approvals (if available)
    contract_tx_ratio = metrics.get('contract_tx_ratio', 0)
    if contract_tx_ratio > 0.8:
        signals.append(Signal(
            code="HIGH_CONTRACT_INTERACTION",
            title="High contract interaction",
            detail=f"{contract_tx_ratio*100:.1f}% of transactions are contract calls",
            evidence_keys=["contract_tx_ratio"],
            severity="MEDIUM"
        ))
    
    approval_count = metrics.get('approval_count', 0)
    if approval_count > 10:
        signals.append(Signal(
            code="APPROVAL_PATTERN",
            title="Approval/allowance-like behavior detected",
            detail=f"{approval_count} approval-like calls detected",
            evidence_keys=["approval_like_calls", "token_approval_count"],
            severity="HIGH"
        ))
    
    # Token patterns
    unique_tokens_sent = metrics.get('unique_tokens_sent', 0)
    if unique_tokens_sent > 5:
        signals.append(Signal(
            code="TOKEN_DUMP_PATTERN",
            title="Multi-token outflows / dumping pattern",
            detail=f"{unique_tokens_sent} different tokens sent",
            evidence_keys=["unique_tokens_sent", "token_tx_sent"],
            severity="HIGH"
        ))
    
    # Internal transactions
    internal_tx_count = metrics.get('internal_tx_count', 0)
    if internal_tx_count > 100:
        signals.append(Signal(
            code="INTERNAL_TX_HEAVY",
            title="High internal transaction activity",
            detail=f"{internal_tx_count} internal transactions",
            evidence_keys=["internal_tx_count"],
            severity="MEDIUM"
        ))
    
    # Data quality signals
    if errors["missing_mv"]:
        signals.append(Signal(
            code="MISSING_MV",
            title="Optimized aggregates missing (fallback mode)",
            detail="Materialized views not found; using raw queries",
            evidence_keys=["mv_missing"],
            severity="LOW"
        ))
    
    if errors["bytes_limited"]:
        signals.append(Signal(
            code="BYTES_LIMITED",
            title="Some queries skipped due to BigQuery bytes limit",
            detail="Query limits exceeded; partial analysis",
            evidence_keys=["bytes_limit_errors"],
            severity="MEDIUM"
        ))
    
    if data_quality.partial:
        signals.append(Signal(
            code="PARTIAL_DATA",
            title="Not all signals could be checked",
            detail="Some analysis sections incomplete",
            evidence_keys=["failed_queries", "available_sections"],
            severity="MEDIUM"
        ))
    
    if tx_count == 0:
        signals.append(Signal(
            code="NO_ACTIVITY_FOUND",
            title="No activity found in window",
            detail="No transactions found in the analysis window",
            evidence_keys=["tx_count"],
            severity="LOW"
        ))
    
    return signals


def parse_metrics_from_result(result_text: str, logs: List[str]) -> Dict[str, Any]:
    """
    Parse metrics from analysis result text and logs.
    This is a best-effort parser - extracts what it can find.
    
    Args:
        result_text: The analysis result text from LLM
        logs: Execution logs
        
    Returns:
        Dictionary of extracted metrics
    """
    metrics = {}
    
    # Try to extract numbers from text
    import re
    
    # Extract ETH values
    eth_patterns = [
        r'(\d+\.?\d*)\s*ETH',
        r'(\d+\.?\d*)\s*eth',
        r'value[:\s]+(\d+\.?\d*)',
    ]
    
    for pattern in eth_patterns:
        matches = re.findall(pattern, result_text, re.IGNORECASE)
        if matches:
            try:
                values = [float(m) for m in matches]
                if 'eth_in_total' not in metrics:
                    metrics['eth_in_total'] = max(values) if values else 0
                if 'eth_out_total' not in metrics:
                    metrics['eth_out_total'] = max(values) if values else 0
            except:
                pass
    
    # Extract transaction counts
    tx_patterns = [
        r'(\d+)\s*transactions?',
        r'tx[:\s]+(\d+)',
        r'count[:\s]+(\d+)',
    ]
    
    for pattern in tx_patterns:
        matches = re.findall(pattern, result_text, re.IGNORECASE)
        if matches:
            try:
                metrics['tx_count'] = max([int(m) for m in matches])
            except:
                pass
    
    # Extract days/age
    day_patterns = [
        r'(\d+)\s*days?',
        r'(\d+)\s*day',
        r'age[:\s]+(\d+)',
    ]
    
    for pattern in day_patterns:
        matches = re.findall(pattern, result_text, re.IGNORECASE)
        if matches:
            try:
                metrics['active_days'] = max([int(m) for m in matches])
            except:
                pass
    
    # Extract counterparty counts
    counterparty_patterns = [
        r'(\d+)\s*counterpart',
        r'(\d+)\s*unique',
    ]
    
    for pattern in counterparty_patterns:
        matches = re.findall(pattern, result_text, re.IGNORECASE)
        if matches:
            try:
                metrics['unique_counterparties'] = max([int(m) for m in matches])
            except:
                pass
    
    # Default values if not found
    if 'tx_count' not in metrics:
        metrics['tx_count'] = 0
    if 'active_days' not in metrics:
        metrics['active_days'] = 365  # Default to full window
    if 'eth_in_total' not in metrics:
        metrics['eth_in_total'] = 0
    if 'eth_out_total' not in metrics:
        metrics['eth_out_total'] = 0
    
    return metrics

