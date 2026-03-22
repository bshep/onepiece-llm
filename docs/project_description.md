# One Piece LLM Agent

## Project Goal
The goal of this project is to develop a specialized Large Language Model (LLM) agent that can accurately answer questions about the One Piece manga and anime series. The agent will leverage data extracted from the `onepiece_pages_current.xml` dump to provide up-to-date and detailed information about characters, plot lines, locations, and other lore elements of the series.

## Project Scope
- **Data Ingestion:** Process and index the One Piece wiki dump (`onepiece_pages_current.xml`).
- **Retrieval Augmented Generation (RAG):** Implement a RAG pipeline to retrieve relevant context from the data for the LLM.
- **Agentic Behavior:** Develop an agent that can handle complex queries, possibly by breaking them down into sub-queries or searching for multiple sources of information.
- **Evaluation:** Create a set of test questions and answers to evaluate the agent's performance.

## Key Features
- **Accurate Information:** Provide reliable information based on the official manga/anime data.
- **Contextual Understanding:** Answer questions that require connecting multiple pieces of information (e.g., character relationships, historical events).
- **Source Attributions:** Cite sources or specific wiki pages used to generate answers.
