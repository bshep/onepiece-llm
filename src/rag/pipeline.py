import os
import argparse
from src.rag.retriever import OnePieceRetriever
from src.rag.generator import OnePieceGenerator

class OnePieceRAG:
    def __init__(self, persist_directory="chroma_db", collection_name="one_piece_lore", model_name="gpt-4o-mini"):
        """Initializes the RAG pipeline."""
        self.retriever = OnePieceRetriever(persist_directory, collection_name)
        self.generator = OnePieceGenerator(model_name)

    def answer_question(self, question: str, k: int = 5, filter_metadata: dict = None):
        """Retrieves and generates an answer."""
        print(f"Retrieving context for: {question}...")
        docs = self.retriever.retrieve(question, k=k, filter_metadata=filter_metadata)
        
        print(f"Generating answer based on {len(docs)} retrieved chunks...")
        answer = self.generator.generate(question, docs)
        
        return answer

def main():
    parser = argparse.ArgumentParser(description="Ask questions about One Piece using the RAG pipeline.")
    parser.add_argument("--question", required=True, help="The question to ask.")
    parser.add_argument("--k", type=int, default=5, help="Number of chunks to retrieve.")
    parser.add_argument("--arc", help="Filter by arc (optional).")
    parser.add_argument("--type", help="Filter by page type (optional, e.g., 'chapter', 'character').")

    args = parser.parse_args()
    
    # Prepare metadata filter if needed
    filter_metadata = {}
    if args.arc:
        filter_metadata["arc"] = args.arc
    if args.type:
        filter_metadata["page_type"] = args.type
    
    rag = OnePieceRAG()
    answer = rag.answer_question(args.question, k=args.k, filter_metadata=filter_metadata if filter_metadata else None)
    
    print("\n" + "="*50)
    print(f"QUESTION: {args.question}")
    print("="*50)
    print(f"ANSWER:\n{answer}")
    print("="*50)

if __name__ == "__main__":
    main()
