import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Load environment variables (API keys)
load_dotenv()

class OnePieceRetriever:
    def __init__(self, persist_directory="chroma_db", collection_name="one_piece_lore"):
        """Initializes the ChromaDB retriever with OpenAI embeddings."""
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vector_db = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory
        )

    def retrieve(self, query: str, k: int = 5, filter_metadata: dict = None):
        """Retrieves the top k most relevant chunks from ChromaDB."""
        # Optional metadata filtering (e.g., {"page_type": "chapter"})
        results = self.vector_db.similarity_search(
            query, 
            k=k, 
            filter=filter_metadata
        )
        return results

if __name__ == "__main__":
    # Quick test (requires DB population)
    retriever = OnePieceRetriever()
    query = "What is Gear 3?"
    docs = retriever.retrieve(query)
    for i, doc in enumerate(docs):
        print(f"Result {i+1}: {doc.metadata['title']} ({doc.metadata['arc']})")
        print(f"Content: {doc.page_content[:200]}...\n")
