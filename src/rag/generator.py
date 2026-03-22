import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables (API keys)
load_dotenv()

class OnePieceGenerator:
    def __init__(self, model_name="gpt-4o-mini"):
        """Initializes the LLM with OpenAI."""
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        self.output_parser = StrOutputParser()
        
        # System prompt to ensure the LLM stays in character and uses the context
        self.system_prompt = (
            "You are an expert One Piece lore agent. Your goal is to answer questions "
            "accurately based on the provided context. If the answer is not in the context, "
            "say so. Always cite the page titles or arc names from the context in your answer."
            " Do not provide spoilers, limit your answer to the current location in the story as provided by the context."
            "If the question is about future events, only answer based on what is currently known in the provided context."
            "If the question is about a character's current status, only answer based on what is currently known in the provided context."
            "If the question is about a character's current abilities, only answer based on what is currently known in the provided context."
            "Speculation is allowed but must be clearly labeled as such and based on the provided context. Always prioritize accuracy and relevance to the provided context."
            "\n\n"
            "Context:\n{context}"
        )
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("human", "{question}"),
        ])

    def generate(self, question: str, retrieved_docs: list):
        """Generates an answer based on the retrieved context."""
        # Combine retrieved content into a single string
        context_str = "\n\n---\n\n".join([
            f"Source: {doc.metadata['title']} (Arc: {doc.metadata.get('arc', 'N/A')})\nContent: {doc.page_content}"
            for doc in retrieved_docs
        ])
        
        # Build and run the chain
        chain = self.prompt_template | self.llm | self.output_parser
        response = chain.invoke({"question": question, "context": context_str})
        
        return response

if __name__ == "__main__":
    # Test (mocked docs)
    from langchain_core.documents import Document
    generator = OnePieceGenerator()
    mock_docs = [Document(page_content="Gear 5 is the awakened form of Luffy's fruit.", metadata={"title": "Gear 5", "arc": "Wano"})]
    answer = generator.generate("What is Gear 5?", mock_docs)
    print(answer)
