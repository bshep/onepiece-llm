import os
import json
import argparse
from tqdm import tqdm
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Load environment variables (API keys)
load_dotenv()

def populate_db(input_path: str, persist_directory: str, collection_name: str, batch_size: int):
    """Reads chunks from JSONL and adds them to ChromaDB."""
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    # Initialize embeddings model
    # Ensure OPENAI_API_KEY is in your .env file or environment
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Initialize Chroma
    vector_db = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory
    )

    print(f"Loading chunks from {input_path} and indexing into ChromaDB (collection: {collection_name})...")
    
    documents = []
    with open(input_path, "r", encoding="utf-8") as f:
        # Read lines and wrap in LangChain Document objects
        for line in tqdm(f, desc="Reading chunks"):
            data = json.loads(line)
            
            # Create Document with metadata
            doc = Document(
                page_content=data["content"],
                metadata={
                    "title": data["title"],
                    "page_type": data["page_type"] or "other",
                    "arc": data["arc"] or "unknown",
                    "chunk_index": data["chunk_index"],
                    "total_chunks": data["total_chunks"]
                }
            )
            documents.append(doc)
            
            # Add to DB in batches to avoid memory issues or API limits
            if len(documents) >= batch_size:
                vector_db.add_documents(documents)
                documents = []
        
        # Add remaining documents
        if documents:
            vector_db.add_documents(documents)

    print(f"Indexing complete. Database persisted at {persist_directory}")

def main():
    parser = argparse.ArgumentParser(description="Populate ChromaDB with One Piece chunks.")
    parser.add_argument("--input-path", default="dumps/onepiece_chunks.jsonl", help="Path to the chunks JSONL file.")
    parser.add_argument("--persist-directory", default="chroma_db", help="Directory to persist ChromaDB data.")
    parser.add_argument("--collection-name", default="one_piece_lore", help="Name of the ChromaDB collection.")
    parser.add_argument("--batch-size", type=int, default=500, help="Number of documents per batch.")

    args = parser.parse_args()
    populate_db(args.input_path, args.persist_directory, args.collection_name, args.batch_size)

if __name__ == "__main__":
    main()
