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
DB_ZIP_URL = st.secrets.get("DB_ZIP_URL", "https://your-placeholder-url.com/chroma_db.zip") # Placeholder for S3 URL

def download_and_unzip_db():
    """Downloads the vector database from S3 if it doesn't exist locally."""
    if not os.path.exists(DB_PATH):
        st.info("Downloading One Piece Lore Database... This may take a minute.")
        try:
            response = requests.get(DB_ZIP_URL, stream=True)
            zip_path = "chroma_db.zip"
            with open(zip_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_path)
            st.success("Database ready!")
        except Exception as e:
            st.error(f"Failed to download database: {e}")
            st.info("Check if DB_ZIP_URL is correctly set in Streamlit Secrets.")
            return False
    return True

# Page Config
st.set_page_config(page_title="One Piece Lore Agent", page_icon="🏴‍☠️")

st.title("🏴‍☠️ One Piece Lore Agent")
st.markdown("Ask anything about the world of One Piece! (Spoiler-free based on your progress)")

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
    st.markdown("Created by ElBrucio. Data sourced from the One Piece Wiki.")

# Initialize RAG Pipeline (Cached to avoid reloading on every interaction)
@st.cache_resource
def get_rag():
    # Only try to initialize if the DB exists or was successfully downloaded
    if download_and_unzip_db():
        return OnePieceRAG()
    return None

# Session State for Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Who is Luffy?"):
    # Check if arc is set
    if not st.session_state.get("current_arc"):
        st.error("Please set your current arc in the sidebar before asking questions!")
    else:
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        rag = get_rag()
        if rag:
            with st.spinner("Thinking..."):
                # Call RAG pipeline with arc filtering
                answer = rag.answer_question(prompt, current_arc=st.session_state.current_arc)
                
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(answer)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": answer})
        else:
            st.error("RAG Pipeline could not be initialized. Please check database settings.")
