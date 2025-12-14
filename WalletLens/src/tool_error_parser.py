"""Parse execution logs to extract tool errors and data quality issues."""

from typing import List, Dict, Any
import re


def parse_logs_for_errors(logs: List[str]) -> Dict[str, Any]:
    """
    Parse execution logs to extract error patterns.
    
    Args:
        logs: List of log strings from memory
        
    Returns:
        Dictionary with error counts and flags:
        {
            "missing_mv": bool,
            "bytes_limited": bool,
            "other_errors": int,
            "error_details": List[str]
        }
    """
    result = {
        "missing_mv": False,
        "bytes_limited": False,
        "other_errors": 0,
        "error_details": []
    }
    
    # Patterns to detect
    mv_patterns = [
        r'Table.*mv_wallet.*was not found',
        r'Table.*mv_wallet.*not found',
        r'404.*mv_wallet',
        r'materialized view.*not found',
        r'Materialized view.*does not exist'
    ]
    
    bytes_patterns = [
        r'bytes billed limit exceeded',
        r'bytesBilledLimitExceeded',
        r'bytes billed.*exceeded',
        r'Query exceeded limit for bytes billed',
        r'bytes limit exceeded'
    ]
    
    error_patterns = [
        r'Error:',
        r'SQL Error:',
        r'Query error:'
    ]
    
    for log in logs:
        log_lower = log.lower()
        
        # Check for missing materialized views
        for pattern in mv_patterns:
            if re.search(pattern, log_lower, re.IGNORECASE):
                result["missing_mv"] = True
                result["error_details"].append(log)
                break
        
        # Check for bytes billed exceeded
        for pattern in bytes_patterns:
            if re.search(pattern, log_lower, re.IGNORECASE):
                result["bytes_limited"] = True
                result["error_details"].append(log)
                break
        
        # Count other errors
        for pattern in error_patterns:
            if re.search(pattern, log_lower):
                # Don't double-count if already captured above
                if not any(mv_p in log_lower for mv_p in ['mv_wallet', 'materialized view']):
                    if not any(bytes_p in log_lower for bytes_p in ['bytes', 'billed', 'limit']):
                        result["other_errors"] += 1
                        result["error_details"].append(log)
                        break
    
    return result


def get_query_outcomes_summary(logs: List[str]) -> Dict[str, Any]:
    """
    Extract summary of query outcomes from logs.
    
    Args:
        logs: List of log strings
        
    Returns:
        Dictionary with query statistics:
        {
            "total_queries": int,
            "successful_queries": int,
            "failed_queries": int,
            "rows_returned": int (approximate)
        }
    """
    summary = {
        "total_queries": 0,
        "successful_queries": 0,
        "failed_queries": 0,
        "rows_returned": 0
    }
    
    for log in logs:
        # Count SQL queries
        if "Executing SQL query" in log or "Executing SQL:" in log:
            summary["total_queries"] += 1
        
        # Count successful queries
        if "Query returned results" in log:
            summary["successful_queries"] += 1
            # Try to extract row count
            row_match = re.search(r'(\d+)\s+rows', log)
            if row_match:
                summary["rows_returned"] += int(row_match.group(1))
        
        # Count failed queries
        if "Query error:" in log or "SQL Error:" in log:
            summary["failed_queries"] += 1
    
    return summary

