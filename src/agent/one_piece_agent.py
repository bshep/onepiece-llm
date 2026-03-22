import os
from dotenv import load_dotenv
from src.rag.pipeline import OnePieceRAG
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Load environment variables
load_dotenv()

class OnePieceAgent:
    def __init__(self, model_name="gpt-4o-mini"):
        """Initializes the One Piece Agent with RAG and History."""
        self.rag = OnePieceRAG(model_name=model_name)
        self.llm = ChatOpenAI(model=model_name, temperature=0.7)
        self.history = ChatMessageHistory()
        
        self.system_prompt = (
            "You are a friendly and knowledgeable One Piece lore expert. "
            "You have access to a vast database of One Piece information via a RAG pipeline. "
            "Your goal is to have a conversation with the user, helping them understand "
            "the world of One Piece. Always stay in character as a fan and scholar of the series."
        )

    def chat(self):
        """Starts an interactive chat loop."""
        print("="*50)
        print("Welcome to the One Piece Lore Agent!")
        print("Type 'exit' or 'quit' to end the session.")
        print("="*50)
        
        while True:
            user_input = input("\nYou: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye! See you on the Grand Line!")
                break
            
            # 1. Get RAG answer
            rag_answer = self.rag.answer_question(user_input)
            
            # 2. Formulate conversational response
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", f"Based on this factual info: {rag_answer}\n\nUser Question: {user_input}")
            ])
            
            # Get history
            history_messages = self.history.messages
            
            chain = prompt | self.llm
            response = chain.invoke({"chat_history": history_messages})
            
            # 3. Update history
            self.history.add_user_message(user_input)
            self.history.add_ai_message(response.content)
            
            print(f"\nAgent: {response.content}")

def main():
    agent = OnePieceAgent()
    agent.chat()

if __name__ == "__main__":
    main()
