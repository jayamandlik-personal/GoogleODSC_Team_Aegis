"""Executor class that sets up and runs the Gemini chat model with tools."""

import os
from dotenv import load_dotenv
import google.generativeai as genai
from typing import Dict, Any, List

# Handle both relative and absolute imports
try:
    from .tools import query_blockchain
    from .planner import WalletLensPlanner
    from .memory import WalletMemory
except ImportError:
    # Fallback to absolute imports when running as script
    from tools import query_blockchain
    from planner import WalletLensPlanner
    from memory import WalletMemory

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
        
        # Get system instruction from planner
        system_instruction = WalletLensPlanner.get_system_instruction()
        
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
        prompt = f"Analyze the Ethereum wallet address: {address}. Classify it as Bot, Merchant, or Whale and provide detailed reasoning."
        
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
                
                # Process each function call
                for function_call in function_calls:
                    function_name = function_call.name
                    
                    if function_name == "query_blockchain":
                        sql = function_call.args.get('sql_query', '')
                        self.memory.log_step(f"Executing SQL query: {sql[:100]}...")
                        
                        # Execute the query (now returns a string/markdown)
                        result = query_blockchain(sql)
                        
                        # Log the result
                        if isinstance(result, str):
                            # Check if it's an error
                            if result.startswith("Error:") or result.startswith("SQL Error:"):
                                # Log full error for debugging (truncate only for display)
                                error_preview = result[:200] + "..." if len(result) > 200 else result
                                self.memory.log_step(f"Query error: {error_preview}")
                            else:
                                # Count approximate rows from markdown (rough estimate)
                                row_count = result.count('\n') - 1  # Subtract header row
                                self.memory.log_step(f"Query returned results ({row_count} rows shown)")
                        else:
                            self.memory.log_step(f"Query returned results")
                        
                        # Prepare function response for Gemini
                        # The result is now a string (markdown table)
                        function_response = genai.protos.FunctionResponse(
                            name=function_name,
                            response={"result": result}  # Wrap in dict for FunctionResponse
                        )
                        
                        # Send function response back to model
                        response = self.chat.send_message(function_response)
            
            # Get the final text response
            if response.candidates and len(response.candidates) > 0:
                final_response = response.text if hasattr(response, 'text') else str(response)
            else:
                final_response = "No response generated"
            
            self.memory.log_step("Analysis completed successfully")
            
            return {
                'result': final_response,
                'memory_logs': self.memory.get_logs()
            }
            
        except Exception as e:
            error_msg = f"Error during analysis: {str(e)}"
            self.memory.log_step(error_msg)
            return {
                'result': f"Error: {error_msg}",
                'memory_logs': self.memory.get_logs()
            }

