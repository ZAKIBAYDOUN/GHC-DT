import streamlit as st
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import time

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="🌿 Green Hill Canarias - Digital Twin",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get configuration from environment
API_BASE_URL = os.getenv("GHC_API_BASE_URL", "http://localhost:8003")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_ASSISTANT_ID = os.getenv("LANGSMITH_ASSISTANT_ID", "76f94782-5f1d-4ea0-8e69-294da3e1aefb")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")

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
    """Check if the backend API is healthy"""
    try:
        # Try different possible API endpoints
        api_endpoints = [API_BASE_URL, "http://localhost:8003", "http://localhost:8002", "http://localhost:8001"]
        
        for endpoint in api_endpoints:
            try:
                response = requests.get(f"{endpoint}/api/health", timeout=2)
                if response.status_code == 200:
                    return True, response.json()
            except:
                continue
        
        return False, {"error": "API not reachable"}
    except Exception as e:
        return False, {"error": str(e)}

def ask_question(question: str, audience: str = "public") -> Dict[str, Any]:
    """Send question to the backend API"""
    try:
        # Determine the API endpoint based on audience
        endpoint = f"{API_BASE_URL}/api/ask"
        
        payload = {
            "question": question,
            "audience": audience
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned status {response.status_code}",
                "details": response.text
            }
            
    except requests.exceptions.Timeout:
        return {"error": "Request timeout - please try again"}
    except Exception as e:
        return {"error": str(e)}

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
            st.warning("Please ensure the backend API is running")
        
        # Audience selector
        st.markdown("### 👥 Select Audience")
        audience = st.selectbox(
            "Choose your access level:",
            options=["public", "investor", "boardroom"],
            format_func=lambda x: {
                "public": "🌍 Public - General Information",
                "investor": "💼 Investor - Financial Data",
                "boardroom": "🏛️ Boardroom - Strategic Insights"
            }[x],
            index=0
        )
        st.session_state.audience = audience
        
        # Configuration info
        st.markdown("### ⚙️ Configuration")
        st.text(f"API: {API_BASE_URL}")
        st.text(f"OpenAI: {'✅' if OPENAI_API_KEY else '❌'}")
        st.text(f"LangSmith: {'✅' if LANGSMITH_API_KEY else '❌'}")
    
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
            if prompt := st.chat_input("Enter your business question:"):
                # Add user message to history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Get AI response
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing..."):
                        response = ask_question(prompt, st.session_state.audience)
                        
                        if "error" in response:
                            st.error(f"⚠️ {response['error']}")
                            if "details" in response:
                                with st.expander("Error details"):
                                    st.code(response['details'])
                        else:
                            # Extract answer from response
                            answer = response.get("answer", response.get("response", "No response generated"))
                            citations = response.get("citations", [])
                            
                            # Display answer
                            st.markdown(answer)
                            
                            # Display citations if available
                            if citations:
                                with st.expander(f"📚 Sources ({len(citations)})"):
                                    for i, citation in enumerate(citations):
                                        st.markdown(f"**{i+1}.** {citation.get('source', 'Unknown source')}")
                                        if citation.get('url'):
                                            st.markdown(f"   🔗 [{citation['url']}]({citation['url']})")
                            
                            # Add to history
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": answer
                            })
            
            # Clear conversation button
            if st.button("🗑️ Clear Conversation"):
                st.session_state.messages = []
                st.rerun()
                
        else:
            st.error("🔴 System offline - Please check back later")
            st.info("💡 Make sure the backend API is running on " + API_BASE_URL)
    
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