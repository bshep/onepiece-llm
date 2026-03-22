import os
from dotenv import load_dotenv
from src.rag.pipeline import OnePieceRAG
from src.utils.one_piece_data import ONE_PIECE_ARCS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory

# Load environment variables
load_dotenv()

class OnePieceAgent:
    def __init__(self, model_name="gpt-4o-mini"):
        """Initializes the One Piece Agent with RAG, History, and Spoiler Control."""
        self.rag = OnePieceRAG(model_name=model_name)
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.history = ChatMessageHistory()
        self.current_arc = None # No filter by default
        
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

    def set_progress(self, arc_name):
        """Sets the user's current progress."""
        if arc_name in ONE_PIECE_ARCS:
            self.current_arc = arc_name
            print(f"Progress updated: You are currently at the {arc_name}.")
        else:
            print(f"Error: Arc '{arc_name}' not found in chronological list.")

    def chat(self):
        """Starts an interactive chat loop."""
        print("="*50)
        print("Welcome to the One Piece Lore Agent (Spoiler-Free Edition)!")
        print("Commands:")
        print("  - set arc [Arc Name]: Update your progress (e.g., 'set arc Skypiea Arc')")
        print("  - arcs: List all arcs in order")
        print("  - status: Check current progress")
        print("  - exit/quit: End the session")
        print("="*50)
        
        while True:
            user_input = input("\nYou: ")
            
            # Handle commands
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye! See you on the Grand Line!")
                break
            
            if user_input.lower().startswith("set arc "):
                arc_name = user_input[8:].strip()
                self.set_progress(arc_name)
                continue
                
            if user_input.lower() == "arcs":
                print("One Piece Arcs in order:")
                for i, arc in enumerate(ONE_PIECE_ARCS):
                    print(f"  {i+1}. {arc}")
                continue
                
            if user_input.lower() == "status":
                print(f"Current Arc: {self.current_arc or 'Full Access (No Filter)'}")
                continue
            
            # 1. Get RAG answer (with arc filtering)
            rag_answer = self.rag.answer_question(user_input, current_arc=self.current_arc)
            
            # 2. Formulate conversational response
            current_arc_info = self.current_arc if self.current_arc else "The user is caught up (Full Access)."
            
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

def main():
    agent = OnePieceAgent()
    agent.chat()

if __name__ == "__main__":
    main()
