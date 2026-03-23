import streamlit as st
import os
import zipfile
import requests
from dotenv import load_dotenv
from src.rag.pipeline import OnePieceRAG
from src.utils.one_piece_data import ONE_PIECE_ARCS

# Load environment variables
load_dotenv()

# Constants
DB_PATH = "chroma_db"
VERSION_FILE = ".db_version"
# This URL and Version should be set in .streamlit/secrets.toml or Streamlit Cloud Secrets
DB_ZIP_URL = st.secrets.get("DB_ZIP_URL", "https://your-placeholder-url.com/chroma_db.zip")
DB_VERSION = st.secrets.get("DB_VERSION", "v1")

def download_and_unzip_db():
    """Downloads the vector database from S3 if it doesn't exist or version is outdated."""
    local_version = ""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            local_version = f.read().strip()

    # Trigger download if DB folder is missing OR version is different
    if not os.path.exists(DB_PATH) or local_version != DB_VERSION:
        with st.status("Updating Lore Database...", expanded=True) as status:
            st.write(f"New version detected ({DB_VERSION}). Downloading...")
            try:
                # Remove old DB if it exists
                if os.path.exists(DB_PATH):
                    import shutil
                    shutil.rmtree(DB_PATH)
                
                response = requests.get(DB_ZIP_URL, stream=True)
                response.raise_for_status()
                zip_path = "chroma_db.zip"
                with open(zip_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                st.write("Extracting files...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(".")
                os.remove(zip_path)
                
                # Update local version file
                with open(VERSION_FILE, "w") as f:
                    f.write(DB_VERSION)
                    
                status.update(label=f"Database Updated to {DB_VERSION}!", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Database Update Failed", state="error", expanded=True)
                st.error(f"Error: {e}")
                return False
    return True

# Initialize RAG Pipeline (Cached so it only runs once per session)
@st.cache_resource(show_spinner=False)
def load_rag_instance():
    if download_and_unzip_db():
        return OnePieceRAG()
    return None

# Page Config
st.set_page_config(page_title="One Piece Lore Agent", page_icon="🏴‍☠️")

# Initialize RAG at the top level (but it's cached)
# This will trigger the download only if the DB is missing
rag = load_rag_instance()

st.title("🏴‍☠️ One Piece Lore Agent")
st.markdown("Ask anything about the world of One Piece! (Spoiler-free)")

# Sidebar for configuration
with st.sidebar:
    st.header("Settings")
    
    # Initialize arc from query params if available
    query_arc = st.query_params.get("arc", "Select an Arc")
    
    # Determine the index for the selectbox
    arc_options = ["Select an Arc"] + ONE_PIECE_ARCS + ["Caught Up"]
    try:
        default_index = arc_options.index(query_arc)
    except ValueError:
        default_index = 0

    # Arc Selection
    selected_arc = st.selectbox(
        "Where are you in the story?",
        options=arc_options,
        index=default_index
    )
    
    # Update query params when selection changes
    if selected_arc != "Select an Arc":
        st.query_params["arc"] = selected_arc
        if selected_arc == "Caught Up":
            st.session_state.current_arc = ONE_PIECE_ARCS[-1]
        else:
            st.session_state.current_arc = selected_arc
    else:
        st.session_state.current_arc = None
        if "arc" in st.query_params:
            del st.query_params["arc"]
    
    if not st.session_state.current_arc:
        st.warning("Please select your current arc to enable chat.")

    st.divider()
    st.info(f"Database Status: {'Connected' if rag else 'Disconnected'}")

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Who is Luffy?"):
    if not st.session_state.get("current_arc"):
        st.error("Please set your current arc in the sidebar before asking questions!")
    elif not rag:
        st.error("The Lore Database is not available. Please check your configuration.")
    else:
        # Display user message
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching the Grand Line..."):
                answer = rag.answer_question(prompt, current_arc=st.session_state.current_arc)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
