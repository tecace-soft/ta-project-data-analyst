"""
Setup script for OpenAI API key configuration.

Before running the app, you need to set up your OpenAI API key:

1. Get your API key from: https://platform.openai.com/api-keys

2. RECOMMENDED: Create a .env file in the project root:
   Create a file named ".env" with the following content:
   OPENAI_API_KEY=your_api_key_here
   
   OR set the environment variable manually:
   
   Windows (Command Prompt):
   set OPENAI_API_KEY=your_api_key_here
   
   Windows (PowerShell):
   $env:OPENAI_API_KEY="your_api_key_here"
   
   Mac/Linux:
   export OPENAI_API_KEY=your_api_key_here

3. Then run: python app.py

The .env file approach is recommended as it keeps your API key secure and gitignored.
"""

import os

def check_openai_setup():
    """Check if OpenAI API key is properly configured"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    # Check if .env file exists
    env_file_exists = os.path.exists('.env')
    
    if not api_key:
        print("❌ OpenAI API key not found!")
        if env_file_exists:
            print("📁 .env file exists but OPENAI_API_KEY not found in it.")
            print("Make sure your .env file contains: OPENAI_API_KEY=your_api_key_here")
        else:
            print("💡 Recommended: Create a .env file with: OPENAI_API_KEY=your_api_key_here")
        print("Please set the OPENAI_API_KEY environment variable.")
        print("See setup instructions above.")
        return False
    
    print("✅ OpenAI API key is configured!")
    if env_file_exists:
        print("📁 Using .env file (recommended)")
    else:
        print("🔧 Using environment variable")
    
    return True

if __name__ == "__main__":
    check_openai_setup() 