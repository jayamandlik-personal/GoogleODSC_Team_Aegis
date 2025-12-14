"""Data models for the Protection Layer - assistive, non-deterministic risk assessment."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Signal:
    """A coded signal derived from facts/metrics."""
    code: str
    title: str
    detail: str
    evidence_keys: List[str] = field(default_factory=list)
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH (not a score, just categorization)


@dataclass
class Protection:
    """A recommended protective action (not a decision)."""
    code: str
    title: str
    description: str
    priority: str  # P1, P2, P3


@dataclass
class DataQuality:
    """Data quality indicators."""
    complete: bool = True
    partial: bool = False
    missing_views: bool = False
    bytes_limited: bool = False
    notes: List[str] = field(default_factory=list)


@dataclass
class Trace:
    """Audit trace information."""
    run_id: str
    timestamp: datetime
    model_name: str
    query_outcomes_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProtectionReport:
    """Unified protection report structure."""
    address: str
    chain: str = "ethereum"
    time_window_days: int = 365
    classification: Optional[str] = None
    verdict: Optional[str] = None  # SAFE, CAUTION, HIGH RISK
    confidence_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    observed_signals: List[Signal] = field(default_factory=list)
    interpretation: str = ""
    recommended_protections: List[Protection] = field(default_factory=list)
    data_quality: DataQuality = field(default_factory=DataQuality)
    trace: Optional[Trace] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "address": self.address,
            "chain": self.chain,
            "time_window_days": self.time_window_days,
            "classification": self.classification,
            "verdict": self.verdict,
            "confidence_level": self.confidence_level,
            "observed_signals": [
                {
                    "code": s.code,
                    "title": s.title,
                    "detail": s.detail,
                    "evidence_keys": s.evidence_keys,
                    "severity": s.severity
                }
                for s in self.observed_signals
            ],
            "interpretation": self.interpretation,
            "recommended_protections": [
                {
                    "code": p.code,
                    "title": p.title,
                    "description": p.description,
                    "priority": p.priority
                }
                for p in self.recommended_protections
            ],
            "data_quality": {
                "complete": self.data_quality.complete,
                "partial": self.data_quality.partial,
                "missing_views": self.data_quality.missing_views,
                "bytes_limited": self.data_quality.bytes_limited,
                "notes": self.data_quality.notes
            },
            "trace": {
                "run_id": self.trace.run_id,
                "timestamp": self.trace.timestamp.isoformat() if self.trace else None,
                "model_name": self.trace.model_name if self.trace else None,
                "query_outcomes_summary": self.trace.query_outcomes_summary if self.trace else {}
            } if self.trace else None
        }

