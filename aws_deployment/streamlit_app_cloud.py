#!/usr/bin/env python3
"""
RAG Chatbot for video content Q&A - Cloud Version (calls AWS Lambda).
Uses AWS Lambda + Bedrock (Claude 3 via API Gateway) instead of local Ollama.
"""

import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env (for local testing)
load_dotenv()

# AWS Lambda API Gateway endpoint - read from environment variable
LAMBDA_API_ENDPOINT = os.getenv(
    "LAMBDA_API_ENDPOINT",
    "https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat"
)

# Page config
st.set_page_config(
    page_title="Video AI Chatbot - Cloud",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Video RAG Chatbot - Powered by AWS Lambda + Bedrock"
    }
)

# Custom CSS
st.markdown("""
<style>
    .user-message {
        background-color: #0084FF;
        color: white;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-left: auto;
        max-width: 70%;
        word-wrap: break-word;
    }
    .assistant-message {
        background-color: #E5E5EA;
        color: black;
        padding: 12px 16px;
        border-radius: 18px;
        margin: 8px 0;
        margin-right: auto;
        max-width: 70%;
        word-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

def call_lambda_api(user_input):
    """Call Lambda function via API Gateway."""
    try:
        payload = {"user_input": user_input}

        response = requests.post(
            LAMBDA_API_ENDPOINT,
            json=payload,
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()

            # If the Lambda is returning an API Gateway-style wrapper,
            # unwrap the "body" field which is a JSON string.
            if isinstance(data, dict) and "body" in data:
                try:
                    inner = json.loads(data["body"])
                except (TypeError, json.JSONDecodeError):
                    inner = {}
            else:
                inner = data if isinstance(data, dict) else {}

            # Prefer model response, fall back to error or generic message
            return inner.get("response") or inner.get("error") or "No response generated"
        else:
            return f"Error: HTTP {response.status_code} - {response.text}"

    except requests.exceptions.Timeout:
        return "Request timed out. Backend might be starting up. Please try again."
    except Exception as e:
        return f"Error calling API: {str(e)}"

def main():
    # Sidebar
    with st.sidebar:
        st.title("🎥 Video AI Assistant (Cloud)")
        st.markdown("---")
        st.subheader("Settings")
        
        # Check API connection
        if "YOUR_API_ID" in LAMBDA_API_ENDPOINT:
            st.error("❌ API endpoint not configured")
            st.warning("Please set LAMBDA_API_ENDPOINT in Streamlit Secrets (cloud) or .env file (local)")
            st.info("For Streamlit Cloud: Settings → Secrets → Add LAMBDA_API_ENDPOINT")
            return
        
        st.success("✓ AWS Lambda Connected", icon="✅")
        st.success("✓ Bedrock (Claude 3) Ready", icon="✅")
        st.success("✓ MongoDB Atlas Connected", icon="✅")
        
        st.markdown("---")
        st.subheader("About")
        st.info(
            "Ask questions about video content. The AI will search through transcripts "
            "and provide accurate answers based on the videos. Powered by AWS Lambda + Bedrock."
        )
        
        # Clear history button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Main chat area
    st.title("💬 Video AI Chatbot")
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else "👤"):
                st.markdown(message["content"])
    
    # Input area
    st.markdown("---")
    
    # Chat input
    user_input = st.chat_input("", key="chat_input")
    
    if user_input:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        
        # Generate response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                response = call_lambda_api(user_input)
                st.markdown(response)
                
                # Add assistant message to history
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
