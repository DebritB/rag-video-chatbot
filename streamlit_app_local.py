#!/usr/bin/env python3
"""
RAG Chatbot for video content Q&A.
Ask questions about videos and get answers based on their transcripts.
Professional LLM chatbot interface with conversation history.
"""

import streamlit as st
from pymongo import MongoClient
import requests
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from datetime import datetime

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", None)  # Set in .env file or environment variables
DATABASE_NAME = "video_grading"
COLLECTION_NAME = "videos"

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "neural-chat"

# Page config
st.set_page_config(
    page_title="Video AI Chatbot",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Video RAG Chatbot - Powered by AI"
    }
)

# Custom CSS for better UI
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
    .chat-container {
        display: flex;
        flex-direction: column;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_mongo_client():
    """Get MongoDB connection."""
    return MongoClient(MONGO_URI)

@st.cache_resource
def get_all_videos_with_embeddings():
    """Load all videos with their embeddings from MongoDB."""
    try:
        client = get_mongo_client()
        collection = client[DATABASE_NAME][COLLECTION_NAME]
        videos = list(collection.find(
            {"embedding": {"$exists": True}, "transcript": {"$exists": True}},
            {
                "_id": 1,
                "video_name": 1,
                "transcript": 1,
                "embedding": 1,
                "duration": 1
            }
        ))
        return videos
    except Exception as e:
        st.error(f"Error loading videos: {e}")
        return []

def check_ollama_connection():
    """Check if Ollama is running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

@st.cache_resource
def get_embedding_model():
    """Cache the embedding model."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding_for_query(query_text):
    """Generate embedding for user query."""
    try:
        model = get_embedding_model()
        embedding = model.encode(query_text)
        return embedding
    except:
        return None

def find_relevant_videos(query_embedding, videos, top_k=3):
    """Find most relevant videos using cosine similarity."""
    if query_embedding is None or not videos:
        return []
    
    video_embeddings = [np.array(v["embedding"]) for v in videos]
    similarities = cosine_similarity([query_embedding], video_embeddings)[0]
    
    top_indices = np.argsort(similarities)[::-1][:top_k]
    relevant = [
        {
            **videos[i],
            "similarity": float(similarities[i])
        }
        for i in top_indices
    ]
    return relevant

def query_ollama_with_rag(question, context_videos, total_videos):
    """Query Ollama with video context for RAG."""
    try:
        # Build comprehensive context from videos with metadata
        context_parts = []
        for i, video in enumerate(context_videos, 1):
            transcript = video.get('transcript', '')
            duration = video.get('duration', 'Unknown')
            context_parts.append(f"[Video {i} - Duration: {duration}]\n{transcript}")
        
        context = "\n\n".join(context_parts)
        
        # Build a more helpful prompt
        prompt = f"""You are a helpful assistant analyzing video transcripts.
Your job is to answer questions based on what's discussed in the videos.

VIDEO TRANSCRIPT(S):
{context}

USER QUESTION: {question}

INSTRUCTIONS:
- Answer directly from the transcript content
- If asked "what does this video do/cover/teach?" - provide a clear summary
- If asked a specific question - answer based on the transcript
- Use quotes from the transcript when relevant
- If information is not in the transcript, say so clearly
- Be concise and helpful

ANSWER:"""
        
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.3,
            "num_predict": 500,
            "top_k": 10,
            "top_p": 0.3
        }
        
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=180)
        
        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            if result:
                return result
            return "No response generated. Please try again."
        return f"Error: HTTP {response.status_code}"
    except requests.exceptions.Timeout:
        return "⏱️ Response timed out. Ollama might be busy. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"

def find_video_by_name(query_text, videos):
    """Check if query contains a video name in quotes and return that video if found."""
    # Extract text within quotes
    import re
    match = re.search(r'"([^"]+)"', query_text)
    if not match:
        return None
    
    quoted_name = match.group(1).lower().strip()
    
    # First try exact match with extension
    for video in videos:
        video_name = video.get('video_name', '').lower().strip()
        if video_name == quoted_name:
            return video
    
    # Then try exact match without extension
    for video in videos:
        video_name = video.get('video_name', '').lower().strip()
        video_name_no_ext = video_name.rsplit('.', 1)[0]
        if video_name_no_ext == quoted_name:
            return video
    
    return None

def main():
    # Sidebar
    with st.sidebar:
        st.title("🎥 Video AI Assistant")
        st.markdown("---")
        st.subheader("Settings")
        
        # Check connections
        try:
            client = get_mongo_client()
            client.admin.command('ping')
            st.success("✓ MongoDB Connected", icon="✅")
        except Exception as e:
            st.error(f"❌ MongoDB Error: {e}")
            return
        
        # Check Ollama
        if check_ollama_connection():
            st.success("✓ Ollama Connected", icon="✅")
        else:
            st.error("❌ Ollama not running", icon="❌")
            st.warning("Please start Ollama: `ollama serve`")
            return
        
        # Load videos
        with st.spinner("Loading videos..."):
            videos = get_all_videos_with_embeddings()
        
        st.metric("Videos Loaded", len(videos))
        
        st.markdown("---")
        st.subheader("About")
        st.info(
            "Ask questions about video content. The AI will search through transcripts "
            "and provide accurate answers based on the videos."
        )
        
        # Clear history button
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    if not videos:
        st.error("No videos found in database")
        return
    
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
    user_input = st.chat_input(
        "",
        key="chat_input"
    )
    
    if user_input:
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
        
        # Generate response
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                # Check if query contains a specific video name
                specific_video = find_video_by_name(user_input, videos)
                
                if specific_video:
                    # If user just provided video name in quotes, ask for summary
                    question = user_input
                    # Check if the query is ONLY the video name (just filename in quotes)
                    import re
                    match = re.search(r'"([^"]+)"', user_input)
                    if match and user_input.strip().replace(f'"{match.group(1)}"', '').strip() == '':
                        # User only asked for the video name, provide summary
                        question = f"Summarize the key concepts and content from this video transcript."
                    
                    response = query_ollama_with_rag(question, [specific_video], len(videos))
                else:
                    # Get embedding for query
                    query_embedding = get_embedding_for_query(user_input)
                    
                    if query_embedding is not None:
                        relevant_videos = find_relevant_videos(query_embedding, videos, top_k=3)
                        
                        if relevant_videos:
                            response = query_ollama_with_rag(user_input, relevant_videos, len(videos))
                        else:
                            response = "No relevant information found in the videos. Try asking a different question."
                    else:
                        response = "Error processing your question. Please try again."
                
                st.markdown(response)
                
                # Add assistant message to history
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
