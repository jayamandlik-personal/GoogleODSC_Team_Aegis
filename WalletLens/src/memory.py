"""Simple memory class to log execution steps."""

from typing import List
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

