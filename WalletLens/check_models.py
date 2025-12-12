"""Quick script to check available Gemini models."""

import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("Error: GEMINI_API_KEY not found")
    exit(1)

genai.configure(api_key=api_key)

print("Listing available models...")
try:
    models = genai.list_models()
    print("\nAvailable models:")
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"  - {model.name}")
            print(f"    Supported methods: {model.supported_generation_methods}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\nTrying to create model with 'gemini-pro'...")
try:
    model = genai.GenerativeModel('gemini-pro')
    print("✓ Successfully created gemini-pro model")
except Exception as e:
    print(f"✗ Error: {e}")

