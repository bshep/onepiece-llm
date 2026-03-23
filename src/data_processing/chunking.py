import json
import argparse
import os
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_data(input_path: str, output_path: str, chunk_size: int, chunk_overlap: int):
    """Chunks the text data into smaller segments using RecursiveCharacterTextSplitter."""
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    print(f"Chunking {input_path} to {output_path}...")
    
    # We use a splitter that tries to split by logical separators like headings, then paragraphs, etc.
    # Wikitext often uses == Heading ==, so we can include that if needed, 
    # but RecursiveCharacterTextSplitter handles \n\n and \n well.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n== ", "\n===", "\n\n", "\n", " ", ""]
    )
    
    total_chunks = 0
    with open(input_path, "r", encoding="utf-8") as f_in, \
         open(output_path, "w", encoding="utf-8") as f_out:
        
        # We read line by line (each line is a JSON object representing a page)
        for line in tqdm(f_in, desc="Chunking pages"):
            try:
                page = json.loads(line)
                title = page.get("title", "Unknown")
                page_type = page.get("page_type")
                arc = page.get("arc")
                aliases = page.get("aliases", [])
                content = page.get("content", "")
                
                if not content:
                    continue
                
                chunks = text_splitter.split_text(content)
                
                for i, chunk_text in enumerate(chunks):
                    chunk_data = {
                        "title": title,
                        "page_type": page_type,
                        "arc": arc,
                        "aliases": aliases,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "content": chunk_text
                    }
                    f_out.write(json.dumps(chunk_data) + "\n")
                    total_chunks += 1
            except json.JSONDecodeError:
                continue

    print(f"Finished chunking. Total chunks created: {total_chunks}")

def main():
    parser = argparse.ArgumentParser(description="Chunk the One Piece wiki JSONL data.")
    parser.add_argument("--input-path", default="dumps/onepiece_pages.jsonl", help="Path to the input JSONL file.")
    parser.add_argument("--output-path", default="dumps/onepiece_chunks.jsonl", help="Path to save the output JSONL file.")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Target chunk size in characters.")
    parser.add_argument("--chunk-overlap", type=int, default=100, help="Overlap between chunks in characters.")

    args = parser.parse_args()
    chunk_data(args.input_path, args.output_path, args.chunk_size, args.chunk_overlap)

if __name__ == "__main__":
    main()
