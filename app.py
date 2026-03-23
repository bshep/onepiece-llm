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
# This URL should be set in .streamlit/secrets.toml or Streamlit Cloud Secrets
DB_ZIP_URL = st.secrets.get("DB_ZIP_URL", "https://your-placeholder-url.com/chroma_db.zip")

def download_and_unzip_db():
    """Downloads the vector database from S3 if it doesn't exist locally."""
    if not os.path.exists(DB_PATH):
        with st.status("Initializing Lore Database...", expanded=True) as status:
            st.write("Downloading data from storage...")
            try:
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
                status.update(label="Database Ready!", state="complete", expanded=False)
            except Exception as e:
                status.update(label="Database Error", state="error", expanded=True)
                st.error(f"Failed to download database: {e}")
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
    
    # Arc Selection
    current_arc = st.selectbox(
        "Where are you in the story?",
        options=["Select an Arc"] + ONE_PIECE_ARCS + ["Caught Up"],
        index=0
    )
    
    if current_arc == "Select an Arc":
        st.warning("Please select your current arc to enable chat.")
        st.session_state.current_arc = None
    elif current_arc == "Caught Up":
        st.session_state.current_arc = ONE_PIECE_ARCS[-1]
    else:
        st.session_state.current_arc = current_arc

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
if prompt := st.chat_input("What is Gear 5?"):
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
