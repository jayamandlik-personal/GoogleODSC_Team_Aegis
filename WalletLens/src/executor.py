"""Executor class that sets up and runs the Gemini chat model with tools."""

import os
import re
import uuid
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, Any, List, Optional, Tuple

# Handle both relative and absolute imports
try:
    from .tools import query_blockchain
    from .planner import WalletLensPlanner
    from .memory import WalletMemory
    from .protection_models import ProtectionReport, Signal, DataQuality, Trace
    from .signals_extractor import extract_signals, parse_metrics_from_result
    from .tool_error_parser import parse_logs_for_errors, get_query_outcomes_summary
    from .protection_advisor import recommend_protections
except ImportError:
    # Fallback to absolute imports when running as script
    from tools import query_blockchain
    from planner import WalletLensPlanner
    from memory import WalletMemory
    from protection_models import ProtectionReport, Signal, DataQuality, Trace
    from signals_extractor import extract_signals, parse_metrics_from_result
    from tool_error_parser import parse_logs_for_errors, get_query_outcomes_summary
    from protection_advisor import recommend_protections

# Load environment variables
load_dotenv()


class WalletAgentExecutor:
    """Executes wallet analysis using Gemini with BigQuery tools."""
    
    def __init__(self):
        """Initialize the executor with API key and model setup."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        # Get system instruction from planner and inject project ID
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT', '')
        system_instruction = WalletLensPlanner.get_system_instruction()
        # Replace placeholder with actual project ID
        if project_id:
            system_instruction = system_instruction.replace('{GOOGLE_CLOUD_PROJECT}', project_id)
        
        # Define the tool function for Gemini
        tools = [
            {
                "function_declarations": [
                    {
                        "name": "query_blockchain",
                        "description": "Query Ethereum blockchain data from BigQuery. Use this to gather transaction history, balances, and other on-chain data for wallet addresses.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "sql_query": {
                                    "type": "string",
                                    "description": "SQL query string to execute against bigquery-public-data.crypto_ethereum dataset"
                                }
                            },
                            "required": ["sql_query"]
                        }
                    }
                ]
            }
        ]
        
        # Try different model names in order of preference
        # Try both with and without models/ prefix since library may handle it
        model_names = [
            'models/gemini-2.5-flash',  # Latest flash model
            'models/gemini-2.5-pro',    # Latest pro model
            'models/gemini-pro-latest',  # Latest pro
            'models/gemini-flash-latest',  # Latest flash
            'models/gemini-2.0-flash',   # Stable 2.0 flash
            'gemini-pro',                # Basic pro (library may auto-add prefix)
            'models/gemini-pro'          # Explicit prefix
        ]
        
        self.model = None
        self.supports_tools = False
        last_error = None
        last_tools_error = None
        
        # First, try to create a model without tools to verify API access
        for model_name in model_names:
            try:
                test_model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction
                )
                # If we get here, the model name works
                # Now try with tools
                try:
                    self.model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction,
                        tools=tools
                    )
                    self.supports_tools = True
                    # Found a model with tools support, use it
                    break
                except Exception as tools_error:
                    # Model works but tools don't, save as fallback
                    last_tools_error = tools_error
                    # Only use as fallback if we don't have a model yet
                    if self.model is None:
                        self.model = test_model
                        self.supports_tools = False
                    # Continue to try other models that might support tools
                    continue
            except Exception as e:
                last_error = e
                continue
        
        if self.model is None:
            error_msg = f"Could not initialize any Gemini model. Last error: {str(last_error)}"
            if last_tools_error:
                error_msg += f" Tools error: {str(last_tools_error)}"
            raise ValueError(error_msg)
        
        # Initialize memory
        self.memory = WalletMemory()
        
        # Log which model was successfully initialized
        model_info = f"Initialized model: {self.model._model_name if hasattr(self.model, '_model_name') else 'unknown'}"
        if self.supports_tools:
            model_info += " (with function calling support)"
        else:
            model_info += " (without function calling - tools will be called manually)"
        self.memory.log_step(model_info)
        
        # Initialize chat
        self.chat = self.model.start_chat(history=[])
    
    def _extract_classification_and_verdict(self, result_text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract classification and verdict from result text."""
        classification = None
        verdict = None
        
        # Extract safety verdict
        verdict_patterns = [
            r'Is it safe to interact\?\s*(🟢|🟡|🔴)\s*(SAFE|CAUTION|HIGH RISK|DO NOT INTERACT)',
            r'(🟢|🟡|🔴)\s*(SAFE|CAUTION|HIGH RISK|DO NOT INTERACT)',
            r'\*\*(🟢|🟡|🔴)\s*(SAFE|CAUTION|HIGH RISK|DO NOT INTERACT)\*\*'
        ]
        for pattern in verdict_patterns:
            verdict_match = re.search(pattern, result_text, re.IGNORECASE)
            if verdict_match:
                verdict_text = verdict_match.group(2)
                # Normalize to SAFE, CAUTION, HIGH RISK
                if "HIGH RISK" in verdict_text.upper() or "DO NOT INTERACT" in verdict_text.upper():
                    verdict = "HIGH RISK"
                elif "CAUTION" in verdict_text.upper():
                    verdict = "CAUTION"
                elif "SAFE" in verdict_text.upper():
                    verdict = "SAFE"
                break
        
        # Extract classification
        classification_patterns = [
            r'Who is this\?\s*(Compromised Wallet|Merchant|Exchange|Bot|MEV|Whale|Treasury|Exploiter|Attacker)',
            r'classified as (?:a |an )?(Compromised Wallet|Merchant|Exchange|Bot|MEV|Whale|Treasury|Exploiter|Attacker)',
            r'(Compromised Wallet)',
            r'(Merchant|Exchange)',
            r'(Bot|MEV)',
            r'(Whale|Treasury)',
            r'(Exploiter|Attacker)'
        ]
        for pattern in classification_patterns:
            match = re.search(pattern, result_text, re.IGNORECASE)
            if match:
                classification = match.group(1)
                if "Compromised Wallet" in result_text and classification != "Compromised Wallet":
                    if re.search(r'Compromised Wallet', result_text, re.IGNORECASE):
                        classification = "Compromised Wallet"
                break
        
        return classification, verdict
    
    def _build_protection_report(
        self,
        address: str,
        result_text: str,
        logs: List[str]
    ) -> ProtectionReport:
        """Build protection report from analysis result."""
        # Extract classification and verdict
        classification, verdict = self._extract_classification_and_verdict(result_text)
        
        # Parse errors from logs
        errors = parse_logs_for_errors(logs)
        
        # Build data quality
        data_quality = DataQuality(
            complete=not errors["bytes_limited"] and not errors["missing_mv"],
            partial=errors["bytes_limited"] or errors["other_errors"] > 0,
            missing_views=errors["missing_mv"],
            bytes_limited=errors["bytes_limited"],
            notes=[]
        )
        
        if errors["missing_mv"]:
            data_quality.notes.append("Optimized aggregates unavailable; used fallback/raw queries when possible")
        if errors["bytes_limited"]:
            data_quality.notes.append("Some token/internal patterns could not be checked due to query limits")
        
        # Parse metrics from result
        metrics = parse_metrics_from_result(result_text, logs)
        
        # Extract signals
        signals = extract_signals(metrics, logs, data_quality)
        
        # Determine confidence level
        confidence = "HIGH"
        if data_quality.bytes_limited or data_quality.partial:
            confidence = "MEDIUM"
        if data_quality.bytes_limited and data_quality.partial:
            confidence = "LOW"
        if errors["other_errors"] > 2:
            confidence = "LOW"
        
        # Generate interpretation (soft language)
        interpretation_parts = []
        if classification:
            interpretation_parts.append(f"Signals observed may be consistent with {classification} behavior.")
        if verdict:
            if verdict == "HIGH RISK":
                interpretation_parts.append("Patterns suggest elevated risk indicators.")
            elif verdict == "CAUTION":
                interpretation_parts.append("Some cautionary signals detected.")
            else:
                interpretation_parts.append("No significant risk signals observed.")
        
        if data_quality.partial:
            interpretation_parts.append("Some token/internal patterns could not be checked due to query limits.")
        
        interpretation = " ".join(interpretation_parts) if interpretation_parts else "Analysis completed."
        
        # Recommend protections
        protections = recommend_protections(signals, classification or "", verdict or "", data_quality)
        
        # Build trace
        model_name = self.model._model_name if hasattr(self.model, '_model_name') else 'unknown'
        query_summary = get_query_outcomes_summary(logs)
        trace = Trace(
            run_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            model_name=model_name,
            query_outcomes_summary=query_summary
        )
        
        # Build report
        report = ProtectionReport(
            address=address,
            chain="ethereum",
            time_window_days=365,
            classification=classification,
            verdict=verdict,
            confidence_level=confidence,
            observed_signals=signals,
            interpretation=interpretation,
            recommended_protections=protections,
            data_quality=data_quality,
            trace=trace
        )
        
        return report
    
    def run(self, address: str) -> Dict[str, Any]:
        """
        Run the agent to analyze a wallet address.
        
        Args:
            address: Ethereum wallet address to analyze
            
        Returns:
            Dictionary containing the analysis result and memory logs
        """
        self.memory.log_step(f"Starting analysis for address: {address}")
        
        # Initial prompt to analyze the address
        prompt = f"""Analyze the Ethereum wallet address: {address}. 

You must answer TWO questions:
1. **Who is this?** (Classify as: Merchant/Exchange, Bot/MEV, Whale/Treasury, Exploiter, or Compromised Wallet)
2. **Is it safe to interact?** (Provide Safety Verdict: 🟢 SAFE, 🟡 CAUTION, or 🔴 HIGH RISK)

CRITICAL CHECKS:
- First transaction date (MIN(block_timestamp)) - Calculate address age
- Activity window (MAX - MIN block_timestamp) - Check if concentrated in short period
- Flow direction: Mostly INCOMING (attacker/merchant) or OUTGOING (victim/payer)?
- Token diversity: Did they dump multiple tokens at once? (Drain indicator)
- Total value moved in ETH

Provide your Safety Verdict at the TOP of your response, then detailed reasoning with transaction dates and values."""
        
        try:
            # Send the prompt
            response = self.chat.send_message(prompt)
            
            # Handle function calls if any
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                # Check if response has function calls
                if not response.candidates or len(response.candidates) == 0:
                    break
                
                candidate = response.candidates[0]
                if not candidate.content or not candidate.content.parts:
                    break
                
                # Check all parts for function calls
                function_calls = []
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)
                
                if not function_calls:
                    # No function calls, we have the final response
                    break
                
                # Collect all function responses before sending (fixes multi-function call protocol)
                function_responses = []
                
                # Process each function call and collect results
                for function_call in function_calls:
                    function_name = function_call.name
                    
                    if function_name == "query_blockchain":
                        sql = function_call.args.get('sql_query', '')
                        self.memory.log_step(f"Executing SQL query: {sql[:100]}...")
                        
                        # Execute the query (now returns a string/markdown)
                        result = query_blockchain(sql)
                        
                        # Log the result
                        if isinstance(result, str):
                            # Check if it's an error or empty result
                            if result.startswith("Error:") or result.startswith("SQL Error:"):
                                # Log full error for debugging (truncate only for display)
                                error_preview = result[:200] + "..." if len(result) > 200 else result
                                self.memory.log_step(f"Query error: {error_preview}")
                            elif result.strip() == "No results found.":
                                # Handle empty result case - prevents misleading "-1 rows shown" log
                                self.memory.log_step("Query returned no results")
                            else:
                                # Count approximate rows from markdown (rough estimate)
                                # Only count if it looks like a markdown table (has pipe characters and newlines)
                                if '|' in result and '\n' in result:
                                    row_count = result.count('\n') - 1  # Subtract header row
                                    if row_count >= 0:  # Ensure non-negative count
                                        self.memory.log_step(f"Query returned results ({row_count} rows shown)")
                                    else:
                                        self.memory.log_step("Query returned results")
                                else:
                                    self.memory.log_step("Query returned results")
                        else:
                            self.memory.log_step(f"Query returned results")
                        
                        # Prepare function response for Gemini
                        # The result is now a string (markdown table)
                        function_response = genai.protos.FunctionResponse(
                            name=function_name,
                            response={"result": result}  # Wrap in dict for FunctionResponse
                        )
                        
                        # Collect the response (don't send yet)
                        function_responses.append(function_response)
                
                # Send all function responses together in a single message
                # This ensures the model sees all results at once for proper context
                if function_responses:
                    response = self.chat.send_message(function_responses)
            
            # Get the final text response
            if response.candidates and len(response.candidates) > 0:
                final_response = response.text if hasattr(response, 'text') else str(response)
            else:
                final_response = "No response generated"
            
            self.memory.log_step("Analysis completed successfully")
            
            # Build protection report
            protection_report = self._build_protection_report(
                address=address,
                result_text=final_response,
                logs=self.memory.get_logs()
            )
            
            return {
                'result': final_response,
                'memory_logs': self.memory.get_logs(),
                'protection_report': protection_report
            }
            
        except Exception as e:
            error_msg = f"Error during analysis: {str(e)}"
            self.memory.log_step(error_msg)
            
            # Build minimal protection report even on error
            try:
                protection_report = self._build_protection_report(
                    address=address,
                    result_text=f"Error: {error_msg}",
                    logs=self.memory.get_logs()
                )
            except:
                protection_report = None
            
            return {
                'result': f"Error: {error_msg}",
                'memory_logs': self.memory.get_logs(),
                'protection_report': protection_report
            }

