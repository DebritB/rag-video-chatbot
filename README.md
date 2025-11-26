# Video Grading RAG System - Setup & Usage Guide

## Overview

Complete AI pipeline for video transcript analysis and grading with two deployment options:

### Local Setup
1. **Extract & Transcribe** → Extract audio from videos, transcribe with GPU Whisper
2. **Grade** → Use Ollama/Mistral to grade transcripts against custom rubric
3. **Semantic Search** → Load graded data into MongoDB with vector embeddings
4. **Interactive UI** → Streamlit app for searching and analyzing results (local Ollama)

### Cloud Deployment (Recommended for Production)
1. **Retrieve** → MongoDB Atlas Vector Search for semantic retrieval
2. **Generate** → AWS Bedrock (Claude 3 Haiku) for intelligent responses
3. **Deploy** → AWS Lambda + Streamlit Cloud
4. **Secure** → Environment variables + AWS Secrets Manager for credentials

---

## 🚀 Live Deployment (Cloud - Production Ready)

**App is live and deployed!**

### Access the App
👉 **[https://rag-video-chatbot-dqqnj9ftvygvocemy69qkw.streamlit.app/](https://rag-video-chatbot-dqqnj9ftvygvocemy69qkw.streamlit.app/)**

The app is deployed on Streamlit Cloud with AWS Lambda backend:
- ✅ Queries MongoDB Atlas (244 videos indexed)
- ✅ Uses AWS Bedrock (Claude 3 Haiku) for AI responses
- ✅ No local resources needed - fully cloud-hosted
- ✅ 24/7 availability

### For Local Development
See **[DEPLOYMENT_GUIDE.md](aws_deployment/DEPLOYMENT_GUIDE.md)** for full instructions.

**To run locally:**
```bash
# 1. Clone repo
git clone https://github.com/DebritB/rag-video-chatbot.git && cd rag-video-chatbot

# 2. Copy env template
cp .env.example .env
# Edit .env and add your Lambda API endpoint (from AWS Console)

# 3. Run locally (uses same cloud backend)
streamlit run streamlit_app.py

# 4. Or modify to use local Ollama instead of Lambda
cd aws_deployment
streamlit run streamlit_app_local.py  # (requires local Ollama setup)
```

### Architecture
```
User Query (Streamlit Cloud)
    ↓
AWS Lambda (Python 3.11)
    ↓
AWS Bedrock (Claude 3 Haiku)
    ↓
MongoDB Atlas (Vector Search)
    ↓
Response ✓
```

---

## ✅ System Status

| Component | Status | Details |
|-----------|--------|---------|
| **Streamlit Cloud** | 🟢 LIVE | https://rag-video-chatbot-dqqnj9ftvygvocemy69qkw.streamlit.app/ |
| **AWS Lambda** | 🟢 ACTIVE | `rag-bedrock-handler` (Python 3.11) |
| **API Gateway** | 🟢 RUNNING | `/prod/chat` endpoint live |
| **MongoDB Atlas** | 🟢 READY | 244 videos indexed with Vector Search |
| **Bedrock (Claude 3)** | 🟢 CONNECTED | Ready for inference |
| **GitHub Repo** | 🟢 SECURE | No credentials exposed, clean history |

---

## Quick Start (Cloud - Already Deployed)

### Just Use It! 🎉
Simply visit: **[https://rag-video-chatbot-dqqnj9ftvygvocemy69qkw.streamlit.app/](https://rag-video-chatbot-dqqnj9ftvygvocemy69qkw.streamlit.app/)**

No setup needed - ask questions about videos:
- "What videos do I have?"
- "Tell me about Q-learning"
- "Find videos on grid world RL"

### Local Development (Optional)

**Prerequisites** (for local testing):
- ✅ Python 3.11+
- ✅ `.env` file with `LAMBDA_API_ENDPOINT` (uses cloud Lambda)
- ✅ Internet connection

**To modify the app locally:**
```bash
# Clone and setup
git clone https://github.com/DebritB/rag-video-chatbot.git
cd rag-video-chatbot
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your LAMBDA_API_ENDPOINT

# Run locally (still uses cloud backend)
streamlit run streamlit_app.py
```

### Original Local Pipeline (For Reference)

If you want to re-transcribe/re-grade videos locally (requires GPU):

**Prerequisites**:
- ✅ Python 3.12 environment
- ✅ NVIDIA GPU with CUDA 12.1
- ✅ Ollama with Mistral 7B
- ✅ 20+ GB free disk space

**Step 1: Transcribe Videos**
```powershell
python extract_and_transcribe.py
# Output: transcriptions.xlsx
```

**Step 2: Grade Transcripts**
```powershell
python grade_transcripts.py
# Output: graded_videos.xlsx (color-coded)
```

**Step 3: Upload to MongoDB**
```powershell
python rag_mongodb.py
# Generates embeddings & uploads to MongoDB Atlas
# Takes ~3-5 minutes
```

**Step 4: Start Local UI (uses local Ollama)**
```powershell
streamlit run streamlit_app_local.py
# Opens: http://localhost:8501
```

---

## Tools Used & Why

### HuggingFace Embeddings (`all-MiniLM-L6-v2`)
- **Purpose**: Convert text to vectors for semantic similarity
- **Runs on**: CPU (lightweight, ~80MB)
- **Used in**: `rag_mongodb.py`, `streamlit_app.py`
- **Why NOT Ollama**: Ollama generates text, not embeddings

### Ollama/Mistral 7B
- **Purpose**: Generate insights and grade videos
- **Runs on**: GPU (RTX 4060)
- **Used in**: `grade_transcripts.py`, `streamlit_app.py` (AI Analysis)
- **Why NOT HuggingFace**: HuggingFace embeddings can't generate text

### MongoDB Atlas
- **Purpose**: Cloud vector database
- **Stores**: Video data + embeddings
- **Note**: All AI processing is LOCAL (HuggingFace CPU + Ollama GPU). MongoDB just stores data.

### LangChain
- **Purpose**: RAG framework that orchestrates embeddings + vector search
- **Simplifies**: MongoDB integration, vector operations

---

## File Descriptions

| File | Purpose | Input | Output |
|------|---------|-------|--------|
| `extract_and_transcribe.py` | Extract audio, transcribe with GPU | `videos/` folder | `transcriptions.xlsx` |
| `grade_transcripts.py` | Grade using Ollama + custom rubric | `transcriptions.xlsx` | `graded_videos.xlsx` |
| `rag_mongodb.py` | Load Excel → embeddings → MongoDB | `graded_videos.xlsx` | MongoDB (video_grading.videos) |
| `streamlit_app.py` | Web UI for search & analytics | MongoDB | Browser UI (http://localhost:8501) |

---

## Streamlit UI Features

### 1. Natural Language Search
- Enter queries like: "Q-learning videos with good grades"
- Uses vector similarity to find relevant videos
- Shows top results with Ollama-generated insights

### 2. Filter Results
- Filter by Criteria 1 (Grid World): Full / No marks
- Filter by Criteria 2 (Algorithm & Params): Full / Average / Fair / No marks
- Displays matching videos in table format

### 3. Analytics
- Total videos in database
- Grade distribution for both criteria
- Quick statistics dashboard

---

## Grading Criteria Explained

### Criteria 1: Grid World RL Problem
- **Full**: Video discusses 2D grid-based reinforcement learning
- **No marks**: Doesn't explicitly mention grid world RL problem

### Criteria 2: Algorithm & Parameters
- **Full**: Clearly explains both algorithm selection AND relevant parameters
- **Average**: Mentions algorithm but parameters vague/incomplete
- **Fair**: Only mentions algorithm OR parameters, not both
- **No marks**: Neither algorithm nor parameters explained

**Accepted Parameters** (depends on algorithm):
- **PassiveDUEAgent**: gamma, U(s)
- **PassiveTDAgent**: alpha, gamma, U(s)
- **PassiveADPAgent**: alpha, gamma, mdp, U(s)
- **QLearningAgent**: alpha, gamma, epsilon, Q(s,a)

---

## Troubleshooting

### MongoDB Connection Fails
- Check internet connection
- **Security**: Never commit MongoDB URIs or credentials to GitHub
- Credentials must be stored in `.env` files (excluded via `.gitignore`) or AWS Secrets Manager
- Try whitelist IP at MongoDB Atlas → Security → Network Access
- Connection strings use SSL workarounds for compatibility

### Ollama Not Running
- Check if Ollama process is active
- Start with: `$env:CUDA_VISIBLE_DEVICES = "0"; & "C:\Users\User\AppData\Local\Programs\Ollama\ollama.exe" serve`
- Keep terminal open while using system

### Embeddings Download Takes Long
- First run downloads `all-MiniLM-L6-v2` model (~100MB)
- Cached after first use (~3-5 minutes first time, <1 minute after)

### Streamlit Shows "Module not found"
- Reinstall dependencies: `pip install -r requirements_rag.txt`
- Restart Streamlit: `Ctrl+C` then `streamlit run streamlit_app.py`

---

## Performance Notes

- **Transcription**: ~2-3 seconds per video on GPU (311 videos ≈ 10-15 mins total)
- **Grading**: ~5-10 seconds per video (Ollama inference)
- **Embedding**: ~1-2 seconds per video (HuggingFace)
- **MongoDB Upload**: ~2 seconds per video
- **Vector Search**: <100ms per query (MongoDB optimized)

---

## GPU Memory Usage

| Process | GPU Memory | Device |
|---------|-----------|--------|
| Whisper (transcribe) | 1.5 GB | RTX 4060 |
| Ollama/Mistral (grade) | 4 GB | RTX 4060 |
| HuggingFace embeddings | <500 MB | CPU |
| Total | ~4-5 GB | Fits in RTX 4060 (8GB) |

Note: Don't run transcription and grading simultaneously on RTX 4060 (only 8GB total).

---

## Next Steps

1. **Monitor rag_mongodb.py**: Check if it completes successfully
2. **Launch Streamlit UI**: `streamlit run streamlit_app.py`
3. **Test vector search**: Try queries like:
   - "grid world RL"
   - "Q-learning"
   - "temporal difference learning"
4. **Check analytics**: View grade distributions
5. **Export results**: Use Streamlit filters to find specific videos

---

## Architecture Diagram

```
Videos (D:\HELP\videos)
    ↓
[extract_and_transcribe.py] --GPU Whisper--> transcriptions.xlsx
    ↓
[grade_transcripts.py] --Ollama/GPU--> graded_videos.xlsx (color-coded)
    ↓
[rag_mongodb.py] --HuggingFace/CPU--> MongoDB Atlas (vectors + metadata)
    ↓
[streamlit_app.py] --Web UI--> User Queries
    ↓
Vector Search (MongoDB) + Ollama Insights (GPU) = Results
```

---

## API Endpoints Used

| Tool | Endpoint | Purpose |
|------|----------|---------|
| Ollama | http://localhost:11434/api/generate | Text generation |
| Ollama | http://localhost:11434/api/tags | Check running models |
| MongoDB | mongodb+srv://... | Vector search + metadata |
| HuggingFace Hub | huggingface.co | Download embeddings model |

---

## Files Modified Today

```
d:\HELP\
├── extract_and_transcribe.py      (transcription, ready to run)
├── grade_transcripts.py           (grading, fully tested)
├── rag_mongodb.py                 (NEW: loads to MongoDB with LangChain)
├── streamlit_app.py               (NEW: web UI with LangChain)
├── requirements_rag.txt           (dependencies for RAG)
├── TOOLS_EXPLANATION.md           (this file)
├── test_mongodb_connection.py     (debugging tool)
├── test_rag_ready.py              (component health check)
├── transcriptions.xlsx            (from step 1)
└── graded_videos.xlsx             (from step 2, color-coded)
```

---

## Support

For issues, check:
1. Terminal output for error messages
2. MongoDB connection string format
3. Ollama service status
4. GPU VRAM availability
5. Internet connectivity for first-time embedding download

All local processing runs on your machine (CPU/GPU). Only vector storage happens in cloud (MongoDB).
