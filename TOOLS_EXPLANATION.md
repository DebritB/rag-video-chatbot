# Tools Used in Video Grading RAG System

## Quick Answer
**Yes, we use Ollama!** But not for embeddings. Here's what each tool does:

---

## Tool Breakdown

### 1. **HuggingFace Embeddings** (`all-MiniLM-L6-v2`)
- **What it does**: Converts text to 384-dimensional vectors
- **Purpose**: Enables semantic search (finds "similar" videos)
- **Runs on**: CPU (lightweight, ~80MB)
- **Used in**: `rag_mongodb.py` and `streamlit_app.py`
- **Why NOT Ollama**: Ollama is for generating text, not understanding similarity

### 2. **Ollama/Mistral 7B**
- **What it does**: Generates natural language text and insights
- **Purpose**: Analyzes search results and creates human-readable explanations
- **Runs on**: Your GPU (RTX 4060)
- **Used in**: `streamlit_app.py` (AI Insights tab)
- **Why NOT HuggingFace**: HuggingFace embeddings only understand text, can't generate new text

### 3. **MongoDB Atlas**
- **What it does**: Cloud vector database
- **Purpose**: Stores the video embeddings created by HuggingFace
- **Runs on**: Cloud (AWS Sydney)
- **Data flow**: HuggingFace → embeddings → MongoDB → stored
- **Note**: All AI processing is LOCAL (HuggingFace on CPU, Ollama on GPU). MongoDB just stores the results.

### 4. **LangChain**
- **What it does**: Orchestration framework
- **Purpose**: Simplifies integration between HuggingFace embeddings and MongoDB
- **Provides**: `MongoDBAtlasVectorSearch` for easy semantic search

---

## Why BOTH HuggingFace AND Ollama?

**Analogy**: 
- **HuggingFace**: Like a librarian who understands which books are similar
- **Ollama**: Like a book reviewer who reads the books and writes reviews

You need both:
1. Librarian (HuggingFace) finds the right books → vectors → MongoDB
2. Reviewer (Ollama) reads the found books → generates insights

---

## Complete Data Flow

```
User enters search query
    ↓
HuggingFace embeddings convert query to vector
    ↓
Vector search in MongoDB (finds similar videos)
    ↓
Results displayed in Streamlit
    ↓
User clicks "AI Analysis"
    ↓
Ollama reads the search results
    ↓
Ollama generates insights on GPU
    ↓
Insights displayed in Streamlit
```

---

## Where Each Tool is Used

| File | HuggingFace | Ollama | MongoDB | LangChain |
|------|-------------|--------|---------|-----------|
| `rag_mongodb.py` | ✅ (embedding) | ❌ | ✅ (storage) | ✅ |
| `streamlit_app.py` | ✅ (vector search) | ✅ (insights) | ✅ (queries) | ✅ |
| `grade_transcripts.py` | ❌ | ✅ (grading) | ❌ | ❌ |
| `extract_and_transcribe.py` | ❌ | ❌ | ❌ | ❌ |

---

## Hardware Usage

- **CPU**: HuggingFace embeddings (lightweight, always available)
- **GPU (RTX 4060)**: Ollama/Mistral for text generation (fast, optional)
- **Cloud**: MongoDB Atlas (just storage, no processing)

---

## Can We Use ONLY Ollama?

**No, because:**
- Ollama is great for text generation but terrible for understanding similarity
- HuggingFace embeddings are small, fast, and perfect for semantic search
- Different tools for different jobs = better performance

**You could:**
- Use Ollama to generate embeddings (but much slower, uses more GPU memory)
- Not use HuggingFace (but search would be much slower)

**Best choice:** Keep current setup - HuggingFace for search, Ollama for insights.

---

## Summary

✅ **We DO use Ollama** (for generating insights on your GPU)
✅ **We ALSO use HuggingFace** (for semantic search on CPU)
✅ **We use MongoDB** (to store the vectors created by HuggingFace)
✅ **All AI processing is LOCAL** (nothing sent to cloud except storage)
