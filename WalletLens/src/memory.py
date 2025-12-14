"""Simple memory class to log execution steps and store analysis history."""

from typing import List, Dict, Any, Optional
from datetime import datetime


class WalletMemory:
    """Simple class to log steps during wallet analysis."""
    
    def __init__(self):
        """Initialize the memory with empty logs."""
        self.logs: List[str] = []
    
    def log_step(self, step: str):
        """
        Log a step with timestamp.
        
        Args:
            step: Description of the step to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logs.append(f"[{timestamp}] {step}")
    
    def get_logs(self) -> List[str]:
        """
        Get all logged steps.
        
        Returns:
            List of log entries
        """
        return self.logs.copy()
    
    def clear(self):
        """Clear all logs."""
        self.logs = []


class AnalysisHistory:
    """Stores the last N wallet analyses."""
    
    def __init__(self, max_size: int = 5):
        """
        Initialize analysis history.
        
        Args:
            max_size: Maximum number of analyses to store (default: 5)
        """
        self.max_size = max_size
        self.history: List[Dict[str, Any]] = []
    
    def add_analysis(self, address: str, result: str, classification: Optional[str] = None, 
                    safety_verdict: Optional[str] = None, timestamp: Optional[datetime] = None,
                    protection_report: Optional[Any] = None):
        """
        Add an analysis to history.
        
        Args:
            address: Wallet address analyzed
            result: Full analysis result text
            classification: Persona classification (optional, extracted from result)
            safety_verdict: Safety verdict (optional, extracted from result)
            timestamp: Analysis timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        analysis = {
            'address': address,
            'result': result,
            'classification': classification,
            'safety_verdict': safety_verdict,
            'timestamp': timestamp,
            'protection_report': protection_report
        }
        
        # Remove if address already exists
        self.history = [a for a in self.history if a['address'].lower() != address.lower()]
        
        # Add to front
        self.history.insert(0, analysis)
        
        # Keep only last N
        if len(self.history) > self.max_size:
            self.history = self.history[:self.max_size]
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get all stored analyses.
        
        Returns:
            List of analysis dictionaries
        """
        return self.history.copy()
    
    def get_by_address(self, address: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis for a specific address.
        
        Args:
            address: Wallet address to look up
            
        Returns:
            Analysis dict if found, None otherwise
        """
        for analysis in self.history:
            if analysis['address'].lower() == address.lower():
                return analysis
        return None
    
    def clear(self):
        """Clear all history."""
        self.history = []

