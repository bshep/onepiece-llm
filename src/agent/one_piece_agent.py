import os
import readline
import json
from dotenv import load_dotenv
from src.rag.pipeline import OnePieceRAG
from src.utils.one_piece_data import ONE_PIECE_ARCS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory

# Load environment variables
load_dotenv()

# Setup history and config files
HISTORY_FILE = os.path.expanduser("~/.one_piece_agent_history")
CONFIG_FILE = os.path.expanduser("~/.one_piece_agent_config")

def setup_readline():
    """Initializes readline with history persistence."""
    if os.path.exists(HISTORY_FILE):
        try:
            readline.read_history_file(HISTORY_FILE)
        except Exception:
            pass
    
    # Register save on exit
    import atexit
    readline.set_history_length(1000)
    atexit.register(readline.write_history_file, HISTORY_FILE)

class OnePieceAgent:
    def __init__(self, model_name="gpt-4o-mini"):
        """Initializes the One Piece Agent with RAG, History, and Spoiler Control."""
        setup_readline()
        self.rag = OnePieceRAG(model_name=model_name)
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.history = ChatMessageHistory()
        self.current_arc = self._load_config().get("current_arc")
        
        self.system_prompt = (
            "You are a friendly and knowledgeable One Piece lore expert. "
            "You have access to a vast database of One Piece information. "
            "IMPORTANT: The user has specified their current progress in the story. "
            "You MUST NOT mention any events, characters, or details that happen AFTER "
            "their current arc. If the user asks about something from the future, "
            "politely explain that you cannot answer that yet to avoid spoilers."
            "\n\n"
            "User's Current Progress: {current_arc_info}"
        )

    def _load_config(self):
        """Loads persistent configuration."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_config(self):
        """Saves current configuration to disk."""
        config = {"current_arc": self.current_arc}
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

    def set_progress(self, arc_name):
        """Sets the user's current progress with partial matching support."""
        search_name = arc_name.lower().strip()
        
        if search_name == "caught up":
            self.current_arc = ONE_PIECE_ARCS[-1]
            self._save_config()
            print(f"Progress updated: You are caught up to the latest arc ({self.current_arc}).")
            return True

        # Find partial matches
        matches = [arc for arc in ONE_PIECE_ARCS if search_name in arc.lower()]
        
        if len(matches) == 1:
            self.current_arc = matches[0]
            self._save_config()
            print(f"Progress updated: You are currently at the {self.current_arc}.")
            return True
        elif len(matches) > 1:
            # If there are multiple, try exact match first
            exact_matches = [arc for arc in matches if arc.lower() == search_name]
            if len(exact_matches) == 1:
                self.current_arc = exact_matches[0]
                self._save_config()
                print(f"Progress updated: You are currently at the {self.current_arc}.")
                return True
            
            print(f"Error: Multiple matches found for '{arc_name}':")
            for m in matches:
                print(f"  - {m}")
            print("Please be more specific.")
            return False
        else:
            print(f"Error: Arc '{arc_name}' not found. Type 'arcs' to see the valid list.")
            return False

    def chat(self):
        """Starts an interactive chat loop."""
        print("="*50)
        print("Welcome to the One Piece Lore Agent!")
        print("="*50)
        
        if self.current_arc:
            print(f"Welcome back! You are currently at: {self.current_arc}")
        else:
            print("To begin, please set your current progress in the story.")
            print("Use: 'set arc [Arc Name]' or 'set arc caught up'")
        
        print("Type 'arcs' to see all available arcs or 'status' to check progress.")
        print("="*50)
        
        try:
            while True:
                user_input = input("\nYou: ").strip()
                
                # Handle exit
                if user_input.lower() in ["exit", "quit"]:
                    print("Goodbye! See you on the Grand Line!")
                    break
                
                if not user_input:
                    continue

                # Handle list arcs
                if user_input.lower() == "arcs":
                    print("One Piece Arcs in order:")
                    for i, arc in enumerate(ONE_PIECE_ARCS):
                        print(f"  {i+1}. {arc}")
                    continue
                
                # Handle setting arc
                if user_input.lower().startswith("set arc "):
                    arc_name = user_input[8:].strip()
                    self.set_progress(arc_name)
                    continue
                
                # Handle status
                if user_input.lower() == "status":
                    if self.current_arc:
                        print(f"Current Arc: {self.current_arc}")
                    else:
                        print("Progress not set yet. Please use 'set arc [Arc Name]'.")
                    continue

                # ENFORCE ARC SETTING
                if not self.current_arc:
                    print("Agent: I'm sorry, I can't answer lore questions until I know where you are in the story to avoid spoilers!")
                    print("Please set your progress using: 'set arc [Arc Name]'")
                    continue
                
                # 1. Get RAG answer (with arc filtering)
                rag_answer = self.rag.answer_question(user_input, current_arc=self.current_arc)
                
                # 2. Formulate conversational response
                current_arc_info = self.current_arc
                
                prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt),
                    MessagesPlaceholder(variable_name="chat_history"),
                    ("human", f"Based on this FACTUAL and FILTERED info: {rag_answer}\n\nUser Question: {user_input}")
                ])
                
                # Get history
                history_messages = self.history.messages
                
                chain = prompt | self.llm
                response = chain.invoke({
                    "chat_history": history_messages,
                    "current_arc_info": current_arc_info
                })
                
                # 3. Update history
                self.history.add_user_message(user_input)
                self.history.add_ai_message(response.content)
                
                print(f"\nAgent: {response.content}")
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! See you on the Grand Line!")

def main():
    agent = OnePieceAgent()
    agent.chat()

if __name__ == "__main__":
    main()
