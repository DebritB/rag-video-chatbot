#!/usr/bin/env python3
"""
Load graded videos from Excel into MongoDB with LangChain RAG.
Creates a searchable database for video grading results.

TOOLS USED IN THIS SCRIPT:
=========================
1. HuggingFace Embeddings (all-MiniLM-L6-v2):
   - Purpose: Converts video transcripts to 384-dimensional vectors
   - Used for: Semantic search (finding similar videos by meaning)
   - Runs on: CPU (lightweight ~80MB model)
   - Why: Specialized in understanding text similarity, not generating text

2. LangChain:
   - Purpose: Framework that orchestrates embeddings + vector store operations
   - Used for: Simplifies MongoDB vector store integration
   - Runs on: Local machine

3. MongoDB Atlas:
   - Purpose: Cloud vector database that STORES the embeddings
   - Used for: Persisting vectors and enabling fast semantic search
   - Note: MongoDB doesn't do AI processing - it just stores vectors locally generated

4. Ollama (NOT used here):
   - Used in streamlit_app.py for generating insights/responses
   - Runs on: Your GPU
   - Purpose: Generate natural language answers based on search results
"""

import sys
from pathlib import Path
import openpyxl
from pymongo import MongoClient
import logging
import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain.schema import Document

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URI = os.getenv("MONGO_URI", None)  # Must be set in environment variables
DATABASE_NAME = "video_grading"
COLLECTION_NAME = "videos"

class VideoRAGLoader:
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.embeddings = None
        self.vector_store = None
        
    def connect_mongodb(self):
        """Connect to MongoDB Atlas."""
        try:
            logger.info("Connecting to MongoDB Atlas...")
            self.client = MongoClient(MONGO_URI)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[DATABASE_NAME]
            self.collection = self.db[COLLECTION_NAME]
            logger.info("✓ Connected to MongoDB Atlas successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            sys.exit(1)
    
    def init_embeddings(self):
        """
        Initialize embeddings using HuggingFace (all-MiniLM-L6-v2).
        
        WHY HuggingFace (NOT Ollama)?
        - Embeddings model: Converts text to vectors for semantic search
        - Ollama is for generating text responses (different purpose)
        - all-MiniLM-L6-v2: 384-dim vectors, lightweight, fast
        - Runs on CPU, ~80MB model
        """
        try:
            logger.info("Initializing HuggingFace embeddings (all-MiniLM-L6-v2)...")
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            logger.info("✓ Embeddings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            sys.exit(1)
    
    def load_excel_videos(self, excel_path: str) -> list:
        """Load graded videos from Excel file and create LangChain Documents."""
        try:
            logger.info(f"Loading videos from {excel_path}...")
            wb = openpyxl.load_workbook(excel_path)
            ws = wb.active
            
            documents = []
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=False), start=2):
                try:
                    video_name = row[0].value if row[0] else "Unknown"
                    c1_grade = row[1].value if row[1] else "N/A"
                    c2_grade = row[2].value if row[2] else "N/A"
                    duration = row[3].value if row[3] else "0:00"
                    notes = row[4].value if row[4] else ""
                    
                    # Create content for the document
                    content = f"Video: {video_name}\nCriteria 1 (Grid World): {c1_grade}\nCriteria 2 (Algorithm & Params): {c2_grade}\nDuration: {duration}\nNotes: {notes}"
                    
                    # Create LangChain Document
                    doc = Document(
                        page_content=content,
                        metadata={
                            "video_name": str(video_name),
                            "criteria_1": str(c1_grade),
                            "criteria_2": str(c2_grade),
                            "duration": str(duration),
                            "notes": str(notes) if notes else ""
                        }
                    )
                    documents.append(doc)
                except Exception as e:
                    logger.warning(f"Error reading row {row_num}: {e}")
                    continue
            
            logger.info(f"Loaded {len(documents)} videos from Excel")
            return documents
        except Exception as e:
            logger.error(f"Failed to load Excel file: {e}")
            sys.exit(1)
    
    def create_vector_store(self, documents: list):
        """Create MongoDB Atlas vector store from documents."""
        try:
            logger.info("Creating MongoDB Atlas vector store...")
            
            # Clear existing collection
            self.collection.delete_many({})
            logger.info("Cleared existing collection")
            
            # Create vector store
            self.vector_store = MongoDBAtlasVectorSearch.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection=self.collection,
                index_name="vector_index"
            )
            
            logger.info(f"✓ Created vector store with {len(documents)} documents")
        except Exception as e:
            logger.error(f"Failed to create vector store: {e}")
            sys.exit(1)
    
    def run(self):
        """Main pipeline: Load Excel → Create Vector Store → Upload to MongoDB."""
        logger.info("=" * 60)
        logger.info("VIDEO RAG LOADER (LangChain + MongoDB)")
        logger.info("=" * 60)
        
        # Step 1: Connect to MongoDB
        self.connect_mongodb()
        
        # Step 2: Initialize embeddings
        self.init_embeddings()
        
        # Step 3: Load videos from Excel
        excel_path = Path(__file__).parent / "graded_videos.xlsx"
        if not excel_path.exists():
            logger.error(f"Excel file not found: {excel_path}")
            sys.exit(1)
        
        documents = self.load_excel_videos(str(excel_path))
        
        # Step 4: Create vector store in MongoDB
        self.create_vector_store(documents)
        
        logger.info("=" * 60)
        logger.info("✓ RAG Database setup completed successfully!")
        logger.info("=" * 60)
        logger.info(f"\nDatabase: {DATABASE_NAME}")
        logger.info(f"Collection: {COLLECTION_NAME}")
        logger.info(f"Total videos: {len(documents)}")
        logger.info("\nYou can now run the Streamlit app: streamlit run streamlit_app.py")


def main():
    loader = VideoRAGLoader()
    loader.run()


if __name__ == "__main__":
    main()
