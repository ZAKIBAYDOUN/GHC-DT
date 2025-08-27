"""
Local test script for the GHC Digital Twin
Run this to test the app locally before deployment
"""

import os
import asyncio
from app.ghc_twin import app as langgraph_app

# Set test environment variables
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("VECTOR_STORE_DIR", "test_vector_store")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("INGEST_AUTH_TOKEN", "test-token")

async def test_query():
    """Test a basic query"""
    try:
        initial_state = {
            "question": "What is Green Hill Canarias?",
            "context_docs": None,
            "final_answer": "",
            "error": None
        }
        
        print("Testing Digital Twin query...")
        result = langgraph_app.invoke(initial_state)
        
        print(f"Question: {result['question']}")
        print(f"Answer: {result['final_answer']}")
        if result.get('error'):
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    print("GHC Digital Twin Local Test")
    print("=" * 40)
    
    # Note: This will likely fail without a valid OpenAI API key
    # but it will help verify the structure is correct
    asyncio.run(test_query())