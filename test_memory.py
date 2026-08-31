from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import uuid

def test_approved_post_storage():
    print("1. Initializing Embedder and ChromaDB...")
    embedder = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    
    # Use the collection name you specifically use for storing approved posts
    vector_store = Chroma(
        collection_name="approved_posts", 
        embedding_function=embedder,
        persist_directory="./chroma_db"
    )
    
    print("2. Simulating an approved post save...")
    post_id = str(uuid.uuid4())
    final_post_text = (
        "Quantum experiments have finally let us watch a system run backwards. "
        "The arrow of time has been a philosophical staple, but in the lab we can now treat it as a controllable parameter."
    )
    
    # We store the tone and metadata alongside the post so the Generator can filter by it later
    vector_store.add_texts(
        texts=[final_post_text],
        metadatas=[{
            "tone": "Direct, punchy, and technical", 
            "craft_score": 8.0,
            "type": "completed_post"
        }],
        ids=[post_id]
    )
    print("✅ Post and tone successfully embedded and saved.")
    
    print("\n3. Querying for a stylistic match for the next post...")
    # Simulate the Generator asking for past examples with a similar technical tone
    search_query = "Looking for examples of highly technical and punchy posts."
    
    # We can use a metadata filter to ensure we only pull approved posts
    results = vector_store.similarity_search(
        search_query, 
        k=1,
        filter={"type": "completed_post"}
    )
    
    print("\n--- RESULTS ---")
    if results:
        print("✅ Retrieval Passed! Found the matching approved post:")
        print(f"   -> Tone: {results[0].metadata.get('tone')}")
        print(f"   -> Post Preview: {results[0].page_content[:75]}...")
    else:
        print("❌ Search failed to retrieve the approved post.")

if __name__ == "__main__":
    test_approved_post_storage()