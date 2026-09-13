import os
import uuid
from typing import List, Dict

# Using the correct LangChain 0.3.x compatible imports
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

class VectorStoreManager:
    """
    Manages the local ChromaDB instance to act as a Semantic Digital Twin.
    Stores high-scoring posts and retrieves them via semantic search to mimic the user's voice.
    """
    
    def __init__(self, persist_directory: str = "data/chroma_db"):
        # Ensure the data directory exists
        os.makedirs(persist_directory, exist_ok=True)
        self.persist_directory = persist_directory
        
        # 1. Initialize the embedding model
        # Using a blazingly fast, lightweight model (~80MB) optimized for CPU
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}, 
            encode_kwargs={'normalize_embeddings': True} # Normalization improves cosine similarity
        )
        
        # 2. Initialize ChromaDB
        # It automatically creates a local SQLite database in the persist_directory
        self.vector_store = Chroma(
            collection_name="linkedin_golden_posts",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def save_golden_post(self, topic: str, final_post: str, craft_score: float) -> str:
        """
        Embeds and saves a high-quality post into the database.
        The topic acts as the semantic anchor (the text that is embedded and searched against).
        """
        doc_id = str(uuid.uuid4())
        
        # Create a LangChain Document
        document = Document(
            page_content=topic, # We search against the topic
            metadata={
                "post": final_post,
                "score": craft_score,
                "type": "golden_sample"
            }
        )
        
        # Add to ChromaDB (it persists automatically in langchain-chroma)
        self.vector_store.add_documents(documents=[document], ids=[doc_id])
        return doc_id

    def get_similar_style(self, current_topic: str, k: int = 2) -> List[Dict]:
        """
        Queries the database for past posts related to the current topic.
        Returns the raw post text to inject into the Generator's prompt.
        """
        # Fetch the top k most similar posts based on topic similarity
        results = self.vector_store.similarity_search(query=current_topic, k=k)
        
        past_posts = []
        for doc in results:
            past_posts.append({
                "past_topic": doc.page_content,
                "post_text": doc.metadata.get("post", ""),
                "score": doc.metadata.get("score", 0.0)
            })
            
        return past_posts

# Global singleton instance for easy import across the app
vector_store = VectorStoreManager()