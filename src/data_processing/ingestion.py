import os
import requests
import subprocess
import argparse
from tqdm import tqdm

DEFAULT_URL = "https://s3.amazonaws.com/wikia_xml_dumps/o/on/onepiece_pages_current.xml.7z"
DEFAULT_DUMP_PATH = "dumps/onepiece_pages_current.xml.7z"
DEFAULT_EXTRACT_PATH = "dumps/onepiece_pages_current.xml"

def download_dump(url: str, dest_path: str):
    """Downloads the One Piece wiki dump from the provided URL."""
    print(f"Downloading dump from {url}...")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(dest_path, "wb") as f, tqdm(
        desc=dest_path,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                bar.update(len(chunk))
    print(f"Download complete: {dest_path}")

def extract_dump(source_path: str, dest_path: str):
    """Extracts the .7z archive using the 7z command-line tool."""
    if not os.path.exists(source_path):
        print(f"Error: Source file {source_path} not found.")
        return

    print(f"Extracting {source_path} to {dest_path}...")
    # 7z x source_path -o<output_dir> -aoa (overwrite all)
    output_dir = os.path.dirname(dest_path)
    try:
        # Use -y to assume Yes on all queries (including overwrite)
        subprocess.run(["7z", "x", source_path, f"-o{output_dir}", "-aoa", "-y"], check=True)
        print(f"Extraction complete.")
    except subprocess.CalledProcessError as e:
        print(f"Error during extraction: {e}")
    except FileNotFoundError:
        print("Error: '7z' command not found. Please install p7zip (e.g., 'brew install p7zip' on macOS or 'sudo apt install p7zip-full' on Linux).")

def main():
    parser = argparse.ArgumentParser(description="Download and extract the One Piece wiki dump.")
    parser.add_argument("--url", default=DEFAULT_URL, help="URL to download the dump from.")
    parser.add_argument("--dest", default=DEFAULT_DUMP_PATH, help="Path to save the downloaded .7z file.")
    parser.add_argument("--extract-path", default=DEFAULT_EXTRACT_PATH, help="Path for the extracted .xml file.")
    parser.add_argument("--force-download", action="store_true", help="Force download even if the file exists.")
    parser.add_argument("--skip-extraction", action="store_true", help="Skip extraction after download.")

    args = parser.parse_args()

    if args.force_download or not os.path.exists(args.dest):
        download_dump(args.url, args.dest)
    else:
        print(f"Dump already exists at {args.dest}. Use --force-download to redownload.")

    if not args.skip_extraction:
        extract_dump(args.dest, args.extract_path)

if __name__ == "__main__":
    main()
