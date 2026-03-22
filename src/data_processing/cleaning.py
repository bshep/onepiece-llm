import os
import lxml.etree as ET
import json
import argparse
import re
from tqdm import tqdm

def parse_xml_to_jsonl(xml_path: str, output_path: str):
    """Parses the MediaWiki XML dump and extracts page titles, text content, and arc metadata."""
    if not os.path.exists(xml_path):
        print(f"Error: XML file {xml_path} not found.")
        return

    print(f"Parsing {xml_path} to {output_path}...")
    
    # Namespaces for MediaWiki XML export-0.11
    namespaces = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    
    # Regex to find arc information like {{Wano Country Arc}} or {{Romance Dawn Arc}}
    arc_pattern = re.compile(r"\{\{([A-Za-z0-9\s]+ Arc)\}\}")

    # List of regexes to exclude certain pages based on title
    # e.g., File:, Category:, Template:, MediaWiki:, User:, Talk:, etc.
    exclude_patterns = [
        re.compile(r"^File:.*"),
        re.compile(r"^File talk:.*"),
        re.compile(r"^Category:.*"),
        re.compile(r"^Template:.*"),
        re.compile(r"^Template talk:.*"),
        re.compile(r"^MediaWiki:.*"),
        re.compile(r"^User:.*"),
        re.compile(r"^User talk:.*"),
        re.compile(r"^Talk:.*"),
        re.compile(r"^Help:.*"),
        re.compile(r"^Help talk:.*"),
        re.compile(r"^Module:.*"),
        re.compile(r"^User blog:.*"),
        re.compile(r"^User blog comment:.*"),
        re.compile(r"^Forum:.*"),
        re.compile(r"^Forum talk:.*"),
        re.compile(r"^Category talk:.*"),
        re.compile(r"^One Piece Wiki talk:.*"),
        re.compile(r"^One Piece Wiki:.*"),
    ]
    
    context = ET.iterparse(xml_path, events=('end',), tag='{http://www.mediawiki.org/xml/export-0.11/}page')
    
    count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for event, elem in tqdm(context, desc="Processing pages"):
            title_elem = elem.find('mw:title', namespaces)
            revision_elem = elem.find('mw:revision', namespaces)
            
            if title_elem is not None and revision_elem is not None:
                title = title_elem.text
                
                # Skip excluded pages based on title patterns
                if any(pattern.match(title) for pattern in exclude_patterns):
                    elem.clear()
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]
                    continue

                text_elem = revision_elem.find('mw:text', namespaces)
                if text_elem is not None and text_elem.text:
                    text = text_elem.text
                    
                    # Robust check for redirects (stripping whitespace and case-insensitive)
                    if not text.strip().upper().startswith("#REDIRECT"):
                        # Determine page type and arc info
                        page_type = None
                        arc = None
                        
                        if title.startswith("Chapter "):
                            page_type = "chapter"
                            arc_match = arc_pattern.search(text)
                            arc = arc_match.group(1) if arc_match else "Unknown Arc"
                        elif title.startswith("Episode "):
                            page_type = "episode"
                            # Episodes also often have arc templates at the bottom
                            arc_match = arc_pattern.search(text)
                            arc = arc_match.group(1) if arc_match else "Unknown Arc"
                        elif title.endswith(" Arc"):
                            page_type = "arc"
                        elif title.endswith(" Saga"):
                            page_type = "saga"
                        
                        page_data = {
                            "title": title,
                            "page_type": page_type,
                            "arc": arc,
                            "content": text
                        }
                        f.write(json.dumps(page_data) + "\n")
                        count += 1
            
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
                
    print(f"Finished parsing {count} pages.")

def main():
    parser = argparse.ArgumentParser(description="Parse the One Piece wiki XML dump into JSONL.")
    parser.add_argument("--xml-path", default="dumps/onepiece_pages_current.xml", help="Path to the extracted XML file.")
    parser.add_argument("--output-path", default="dumps/onepiece_pages.jsonl", help="Path to save the output JSONL file.")

    args = parser.parse_args()
    parse_xml_to_jsonl(args.xml_path, args.output_path)

if __name__ == "__main__":
    main()
