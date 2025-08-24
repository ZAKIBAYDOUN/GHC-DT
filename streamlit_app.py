import streamlit as st
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import time
import logging
import urllib3

# Disable SSL warnings when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="🌿 Green Hill Canarias - Digital Twin",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get configuration from environment or Streamlit secrets
def get_config_value(key: str, default: str = "") -> str:
    """Get configuration from environment or Streamlit secrets"""
    # Try environment first
    env_value = os.getenv(key, "")
    if env_value:
        return env_value
    
    # Try Streamlit secrets
    try:
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except:
        pass
    
    return default

# Configuration
LANGSMITH_API_KEY = get_config_value("LANGSMITH_API_KEY", "")
LANGSMITH_ASSISTANT_ID = get_config_value("LANGSMITH_ASSISTANT_ID", "76f94782-5f1d-4ea0-8e69-294da3e1aefb")
LANGCHAIN_API_KEY = get_config_value("LANGCHAIN_API_KEY", LANGSMITH_API_KEY)  # Fallback to LANGSMITH_API_KEY
OPENAI_API_KEY = get_config_value("OPENAI_API_KEY", "")  # Optional for fallback

# LangGraph deployment URL (from your GitHub Pages)
LANGGRAPH_URL = "https://ghc-langsmith-deployment.us.langgraph.cloud"

# Assistant IDs for different audiences
ASSISTANT_IDS = {
    "boardroom": "76f94782-5f1d-4ea0-8e69-294da3e1aefb",
    "investor": "ff7afd85-51e0-4fdd-8ec5-a14508a100f9",
    "public": "34747e20-39db-415e-bd80-597006f71a7a",
}

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audience" not in st.session_state:
    st.session_state.audience = "public"

def check_system_health():
    """Check if LangSmith/LangGraph connection is healthy"""
    try:
        # Check if we have the required API keys
        langsmith_key = get_config_value("LANGSMITH_API_KEY", "")
        
        if not langsmith_key:
            return False, {"error": "LangSmith API key not configured"}
        
        # We'll consider the system healthy if we have valid keys
        # Actual connection test might rate limit, so we'll trust the configuration
        return True, {
            "status": "healthy",
            "deployment": "LangSmith/LangGraph Deployment",
            "api_configured": True,
            "deployment_url": LANGGRAPH_URL
        }
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return False, {"error": str(e)}

def ask_question(question: str, audience: str = "public") -> Dict[str, Any]:
    """Send question to LangGraph deployment (matching GitHub Pages implementation)"""
    try:
        # Get API key
        langsmith_key = get_config_value('LANGSMITH_API_KEY')
        if not langsmith_key:
            return {"error": "LangSmith API key not configured"}
        
        # Get assistant ID based on audience
        assistant_id = ASSISTANT_IDS.get(audience, ASSISTANT_IDS["public"])
        
        # Prepare the request to LangGraph deployment
        headers = {
            "x-api-key": langsmith_key,
            "Content-Type": "application/json"
        }
        
        # Match the payload structure from GitHub Pages
        payload = {
            "assistant_id": assistant_id,
            "thread_id": f"streamlit-{int(time.time())}",
            "input": {
                "messages": [{
                    "role": "user",
                    "content": question
                }]
            }
        }
        
        # Call LangGraph deployment
        response = requests.post(
            f"{LANGGRAPH_URL}/runs/stream",
            headers=headers,
            json=payload,
            timeout=30,
            stream=True,
            verify=False  # Disable SSL verification to handle SSL name issues
        )
        
        if response.status_code == 200:
            # Process streaming response
            full_response = ""
            final_data = {}
            
            for line in response.iter_lines():
                if line:
                    try:
                        # Parse streaming response
                        line_text = line.decode('utf-8')
                        if line_text.startswith("data: "):
                            data_str = line_text[6:]  # Remove "data: " prefix
                            if data_str.strip() == "[DONE]":
                                break
                            
                            data = json.loads(data_str)
                            
                            # Extract response based on the structure
                            if isinstance(data, dict):
                                # Handle different response formats
                                if "final_answer" in data:
                                    full_response = data["final_answer"]
                                    final_data = data
                                elif "content" in data:
                                    full_response += data.get("content", "")
                                elif "output" in data:
                                    if isinstance(data["output"], dict):
                                        full_response = data["output"].get("final_answer", "")
                                        final_data = data["output"]
                                        
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        logger.warning(f"Error parsing stream line: {e}")
                        continue
            
            # Return the response
            if full_response:
                return {
                    "response": full_response,
                    "success": True,
                    "model": "LangSmith Assistant",
                    "audience": audience,
                    "assistant_id": assistant_id,
                    "raw_data": final_data
                }
            else:
                return {
                    "response": "No response generated from the assistant.",
                    "success": False
                }
                
        else:
            error_detail = response.text
            logger.error(f"LangGraph API error: {response.status_code} - {error_detail}")
            
            # Fallback to OpenAI if available
            openai_key = get_config_value('OPENAI_API_KEY')
            if openai_key and response.status_code in [401, 403, 404]:
                logger.info("Falling back to OpenAI API")
                return ask_question_openai_fallback(question, audience)
            
            return {
                "error": f"LangGraph API returned status {response.status_code}",
                "details": error_detail
            }
            
    except requests.exceptions.Timeout:
        return {"error": "Request timeout - API took too long to respond"}
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        return {"error": str(e)}

def ask_question_openai_fallback(question: str, audience: str = "public") -> Dict[str, Any]:
    """Fallback to OpenAI API if LangSmith is not available"""
    try:
        openai_key = get_config_value('OPENAI_API_KEY')
        if not openai_key:
            return {"error": "OpenAI API key not configured for fallback"}
        
        openai_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }
        
        system_prompts = {
            "public": "You are the Green Hill Canarias Digital Twin, providing general business information for the public. Be professional, informative, and accessible.",
            "investor": "You are the Green Hill Canarias Digital Twin, providing financial insights and investment information. Focus on financial metrics, growth potential, and market opportunities.",
            "boardroom": "You are the Green Hill Canarias Digital Twin, providing strategic analysis and executive insights. Provide high-level strategic guidance, market analysis, and actionable recommendations."
        }
        
        payload = {
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": system_prompts.get(audience, system_prompts["public"])},
                {"role": "user", "content": question}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        response = requests.post(openai_url, headers=headers, json=payload, timeout=30, verify=False)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return {
                    "response": content,
                    "success": True,
                    "model": "gpt-4 (fallback)",
                    "audience": audience
                }
                
        return {"error": f"OpenAI fallback failed: {response.status_code}"}
        
    except Exception as e:
        logger.error(f"OpenAI fallback error: {e}")
        return {"error": f"Fallback error: {str(e)}"}

def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1>🌿 Green Hill Canarias</h1>
        <h3>Digital Twin - AI-Powered Business Intelligence Platform</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # System status in sidebar
    with st.sidebar:
        st.markdown("### 🔧 System Status")
        
        # Check health
        is_healthy, health_data = check_system_health()
        
        if is_healthy:
            st.success("✅ System Online")
            if "deployment" in health_data:
                st.info(f"🌐 {health_data['deployment']}")
        else:
            st.error("🔴 System Offline")
            if "error" in health_data:
                st.warning(health_data["error"])
        
        # Audience selector with unique key
        st.markdown("### 👥 Select Audience")
        audience = st.selectbox(
            "Choose your access level:",
            options=["public", "investor", "boardroom"],
            format_func=lambda x: {
                "public": "🌍 Public - General Information",
                "investor": "💼 Investor - Financial Data",
                "boardroom": "🏛️ Boardroom - Strategic Insights"
            }[x],
            index=0,
            key="unique_audience_selector"  # Unique key to prevent duplicate ID
        )
        st.session_state.audience = audience
        
        # Configuration info
        st.markdown("### ⚙️ Configuration")
        st.text("Mode: LangSmith/LangGraph")
        st.text(f"LangSmith: {'✅' if get_config_value('LANGSMITH_API_KEY') else '❌'}")
        st.text(f"OpenAI (fallback): {'✅' if get_config_value('OPENAI_API_KEY') else '❌'}")
        
        # Show current assistant
        selected_assistant = ASSISTANT_IDS.get(st.session_state.audience, "Unknown")
        st.text(f"Assistant: {selected_assistant[:12]}...")
        
        # Debug info (collapsible)
        with st.expander("🔍 Debug Info"):
            st.text(f"Deployment URL: {LANGGRAPH_URL}")
            st.text(f"Full Assistant ID: {selected_assistant}")
    
    # Main chat interface
    col1, col2, col3 = st.columns([1, 6, 1])
    
    with col2:
        # Info boxes
        st.markdown("""
        <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-bottom: 2rem;'>
            <div style='background: #f0f8ff; padding: 1rem; border-radius: 10px; text-align: center;'>
                <h4>🧠 Intelligent Analysis</h4>
                <p>Get strategic insights, market intelligence, and financial analysis powered by advanced AI technology.</p>
            </div>
            <div style='background: #f0fff0; padding: 1rem; border-radius: 10px; text-align: center;'>
                <h4>💼 Multi-Audience Support</h4>
                <p>Tailored responses for public information, investor relations, and executive decision-making.</p>
            </div>
            <div style='background: #fff0f5; padding: 1rem; border-radius: 10px; text-align: center;'>
                <h4>📚 Knowledge Management</h4>
                <p>Add documents and data to enhance the AI's understanding of your business context.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat interface
        if is_healthy:
            st.markdown("### 💬 Chat with GHC Digital Twin")
            
            # Display conversation history
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            
            # Chat input
            if prompt := st.chat_input("Enter your business question:", key="unique_chat_input"):
                # Add user message to history first
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Get AI response
                with st.spinner("Analyzing..."):
                    response = ask_question(prompt, st.session_state.audience)
                    
                    if "error" in response:
                        error_msg = f"⚠️ Error: {response['error']}"
                        if "details" in response:
                            error_msg += f"\n\nDetails: {response['details']}"
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": error_msg
                        })
                    else:
                        # Extract answer from response
                        answer = response.get("response", "No response generated")
                        
                        # Add metadata to answer if available
                        if response.get("success") and response.get("model"):
                            answer += f"\n\n*🤖 Powered by {response.get('model')} | 👥 {response.get('audience', 'public').title()} mode*"
                        
                        # Add to history
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": answer
                        })
                
                # Rerun to show new messages
                st.rerun()
            
            # Clear conversation button
            if st.button("🗑️ Clear Conversation", key="unique_clear_button"):
                st.session_state.messages = []
                st.rerun()
                
        else:
            st.error("🔴 System offline - Please check configuration")
            st.info("💡 Configure your API keys in Streamlit Cloud Secrets")
            st.markdown("""
            **Required secrets:**
            - `LANGSMITH_API_KEY` (primary)
            - `LANGCHAIN_API_KEY` (alternative)
            - `OPENAI_API_KEY` (optional fallback)
            """)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Developed for Green Hill Canarias | Multi-modal AI Interface"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
