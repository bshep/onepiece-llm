import os
import lxml.etree as ET
import json
import argparse
import re
from tqdm import tqdm

def parse_xml_to_jsonl(xml_path: str, output_path: str):
    """Parses MediaWiki XML dump with chapter-to-arc mapping for strict spoiler control."""
    if not os.path.exists(xml_path):
        print(f"Error: XML file {xml_path} not found.")
        return

    namespaces = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    arc_pattern = re.compile(r"\{\{([A-Za-z0-9\s]+ Arc)\}\}")
    # Pattern to find "first = [[Chapter 123]]"
    first_chapter_pattern = re.compile(r"first\s*=\s*.*?\[\[Chapter\s*(\d+)\]\]", re.IGNORECASE)
    
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
    
    # PASS 1: Build Chapter -> Arc mapping
    print("Pass 1: Building Chapter-to-Arc mapping...")
    chapter_arc_map = {}
    context = ET.iterparse(xml_path, events=('end',), tag='{http://www.mediawiki.org/xml/export-0.11/}page')
    for event, elem in tqdm(context, desc="Mapping chapters"):
        title_elem = elem.find('mw:title', namespaces)
        if title_elem is not None and title_elem.text.startswith("Chapter "):
            try:
                chapter_num = int(title_elem.text.split(" ")[1])
                revision = elem.find('mw:revision', namespaces)
                if revision is not None:
                    text_elem = revision.find('mw:text', namespaces)
                    if text_elem is not None and text_elem.text:
                        arc_match = arc_pattern.search(text_elem.text)
                        if arc_match:
                            chapter_arc_map[chapter_num] = arc_match.group(1)
            except (ValueError, IndexError):
                pass
        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    # Fill in gaps in chapter_arc_map (if a chapter doesn't have an arc tag, use the previous one)
    last_arc = "Romance Dawn Arc"
    if chapter_arc_map:
        for i in range(1, max(chapter_arc_map.keys()) + 1):
            if i in chapter_arc_map:
                last_arc = chapter_arc_map[i]
            else:
                chapter_arc_map[i] = last_arc

    # PASS 2: Process all pages
    print("Pass 2: Processing pages with metadata...")
    context = ET.iterparse(xml_path, events=('end',), tag='{http://www.mediawiki.org/xml/export-0.11/}page')
    count = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for event, elem in tqdm(context, desc="Processing pages"):
            title_elem = elem.find('mw:title', namespaces)
            revision_elem = elem.find('mw:revision', namespaces)
            
            if title_elem is not None and revision_elem is not None:
                title = title_elem.text
                if any(p.match(title) for p in exclude_patterns):
                    elem.clear()
                    while elem.getprevious() is not None:
                        del elem.getparent()[0]
                    continue

                text_elem = revision_elem.find('mw:text', namespaces)
                if text_elem is not None and text_elem.text:
                    text = text_elem.text
                    if not text.strip().upper().startswith("#REDIRECT"):
                        page_type = None
                        arc = None
                        
                        # Type detection
                        if title.startswith("Chapter "):
                            page_type = "chapter"
                            try:
                                num = int(title.split(" ")[1])
                                arc = chapter_arc_map.get(num)
                            except: pass
                        elif title.startswith("Episode "):
                            page_type = "episode"
                            arc_match = arc_pattern.search(text)
                            arc = arc_match.group(1) if arc_match else None
                        elif title.endswith(" Arc"):
                            page_type = "arc"
                            arc = title
                        elif title.endswith(" Saga"):
                            page_type = "saga"
                        elif any(word in title for word in ["Pirates", "Army", "Government", "Family", "Alliance", "Group", "Marines", "Cipher Pol"]):
                            page_type = "group"
                        elif "{{" + title + " Tabs Top}}" in text:
                            page_type = "character"
                        
                        # Infer arc for non-chapter pages (like Pluton)
                        if not arc:
                            first_match = first_chapter_pattern.search(text)
                            if first_match:
                                first_chap_num = int(first_match.group(1))
                                arc = chapter_arc_map.get(first_chap_num)
                        
                        # Last resort: search for ANY arc template
                        if not arc:
                            arc_match = arc_pattern.search(text)
                            arc = arc_match.group(1) if arc_match else None

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
    parser = argparse.ArgumentParser(description="Parse One Piece wiki XML dump.")
    parser.add_argument("--xml-path", default="dumps/onepiece_pages_current.xml")
    parser.add_argument("--output-path", default="dumps/onepiece_pages.jsonl")
    args = parser.parse_args()
    parse_xml_to_jsonl(args.xml_path, args.output_path)

if __name__ == "__main__":
    main()
