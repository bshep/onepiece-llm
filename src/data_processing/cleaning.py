import os
import lxml.etree as ET
import json
import argparse
import re
from tqdm import tqdm

def parse_xml_to_jsonl(xml_path: str, output_path: str, alias_output_path: str):
    """
    Parses MediaWiki XML dump with global alias extraction and strict filtering.
    Keeps only: Chapters, Arcs, Sagas.
    Treats REDIRECTS and pipe links [[Target|Alias]] as aliases.
    """
    if not os.path.exists(xml_path):
        print(f"Error: XML file {xml_path} not found.")
        return

    namespaces = {'mw': 'http://www.mediawiki.org/xml/export-0.11/'}
    arc_pattern = re.compile(r"\{\{([A-Za-z0-9\s]+ Arc)\}\}")
    redirect_pattern = re.compile(r"#REDIRECT\s*\[\[(.*?)\]\]", re.IGNORECASE)
    # Pattern for pipe links: [[TargetName|AliasName]]
    pipe_link_pattern = re.compile(r"\[\[([^|\]#]+)(?:#[^|\]]+)?\|([^|\]]+)\]\]")
    
    exclude_prefixes = ["File:", "Category:", "Template:", "MediaWiki:", "User:", "User talk:", "Talk:", "Help:", "Module:"]

    # PASS 1: Build global metadata maps (Scanning ALL content)
    print("Pass 1: Building global Chapter-Arc map and comprehensive Alias map...")
    chapter_arc_map = {}
    alias_map = {} # target_title -> set of aliases
    
    context = ET.iterparse(xml_path, events=('end',), tag='{http://www.mediawiki.org/xml/export-0.11/}page')
    for event, elem in tqdm(context, desc="Scanning for aliases and arcs"):
        title_elem = elem.find('mw:title', namespaces)
        if title_elem is None:
            elem.clear()
            continue
            
        title = title_elem.text
        if any(title.startswith(pref) for pref in exclude_prefixes):
            elem.clear()
            continue

        revision = elem.find('mw:revision', namespaces)
        if revision is not None:
            text_elem = revision.find('mw:text', namespaces)
            if text_elem is not None and text_elem.text:
                text = text_elem.text
                
                # 1. Extract Redirects
                redir_match = redirect_pattern.search(text)
                if redir_match:
                    target = redir_match.group(1).split('#')[0].strip()
                    if target not in alias_map:
                        alias_map[target] = set()
                    alias_map[target].add(title)
                else:
                    # 2. Extract Pipe Link Aliases [[Target|Alias]]
                    for target, alias in pipe_link_pattern.findall(text):
                        target = target.strip()
                        alias = alias.strip()
                        if target != alias and len(alias) > 1:
                            if target not in alias_map:
                                alias_map[target] = set()
                            alias_map[target].add(alias)
                    
                    # 3. Map Chapters to Arcs
                    if title.startswith("Chapter ") and "(" not in title:
                        num_match = re.search(r"Chapter (\d+)", title)
                        if num_match:
                            arc_match = arc_pattern.search(text)
                            if arc_match:
                                chapter_arc_map[int(num_match.group(1))] = arc_match.group(1)

        elem.clear()
        while elem.getprevious() is not None:
            del elem.getparent()[0]

    # Fill Chapter -> Arc gaps
    if chapter_arc_map:
        last_arc = "Romance Dawn Arc"
        for i in range(1, max(chapter_arc_map.keys()) + 1):
            if i in chapter_arc_map:
                last_arc = chapter_arc_map[i]
            else:
                chapter_arc_map[i] = last_arc

    # Save Alias Map for Agent use
    print(f"Saving global alias map to {alias_output_path}...")
    serializable_alias_map = {k: sorted(list(v)) for k, v in alias_map.items()}
    with open(alias_output_path, "w", encoding="utf-8") as f_alias:
        json.dump(serializable_alias_map, f_alias, indent=2)

    # PASS 2: Export strictly filtered pages
    print("Pass 2: Exporting Chapters, Arcs, and Sagas...")
    allowed_types = ["chapter", "arc", "saga"]
    count = 0
    
    context = ET.iterparse(xml_path, events=('end',), tag='{http://www.mediawiki.org/xml/export-0.11/}page')
    with open(output_path, "w", encoding="utf-8") as f:
        for event, elem in tqdm(context, desc="Exporting high-quality pages"):
            title_elem = elem.find('mw:title', namespaces)
            if title_elem is None:
                elem.clear()
                continue
            title = title_elem.text
            
            page_type = None
            if title.startswith("Chapter ") and "(" not in title:
                page_type = "chapter"
            elif title.endswith(" Arc"):
                page_type = "arc"
            elif title.endswith(" Saga"):
                page_type = "saga"
            
            if page_type in allowed_types:
                revision = elem.find('mw:revision', namespaces)
                if revision is not None:
                    text_elem = revision.find('mw:text', namespaces)
                    if text_elem is not None and text_elem.text:
                        text = text_elem.text
                        if not text.strip().upper().startswith("#REDIRECT"):
                            arc = None
                            if page_type == "chapter":
                                num_match = re.search(r"Chapter (\d+)", title)
                                if num_match:
                                    arc = chapter_arc_map.get(int(num_match.group(1)))
                            elif page_type == "arc":
                                arc = title
                            
                            page_aliases = sorted(list(alias_map.get(title, set())))
                            
                            page_data = {
                                "title": title,
                                "page_type": page_type,
                                "arc": arc,
                                "aliases": page_aliases,
                                "content": text
                            }
                            f.write(json.dumps(page_data) + "\n")
                            count += 1
            
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

    print(f"Finished parsing {count} high-quality pages.")

def main():
    parser = argparse.ArgumentParser(description="Parse One Piece wiki XML dump.")
    parser.add_argument("--xml-path", default="dumps/onepiece_pages_current.xml")
    parser.add_argument("--output-path", default="dumps/onepiece_pages.jsonl")
    parser.add_argument("--alias-path", default="dumps/aliases.json")
    args = parser.parse_args()
    parse_xml_to_jsonl(args.xml_path, args.output_path, args.alias_path)

if __name__ == "__main__":
    main()
