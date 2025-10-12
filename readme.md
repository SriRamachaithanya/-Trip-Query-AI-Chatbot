# Trip Query AI Chatbot

This project is a complete Retrieval-Augmented Generation (RAG) system that functions as a command-line chatbot for answering questions about a trip to Dubai. The project is composed of two main Python scripts: one that processes a trip itinerary from a CSV file and stores it in a vector database, and another that runs the interactive chatbot, using the database to provide contextually accurate answers.

---

## How It Works 💡

The system works in two stages:

1.  **Data Ingestion:** A script reads a `Dubai_trip.csv` file, converts each itinerary item into a numerical representation (embedding) using the `mxbai-embed-large` model, and stores these embeddings in a persistent Chroma DB vector store. This process only needs to be run once.
2.  **Question Answering:** The main chatbot script takes a user's question, uses the same embedding model to search the Chroma DB for the most relevant itinerary information, and then passes this information along with the original question to a powerful Language Model (`llama3.2`). The LLM uses this context to generate an informed answer.

---

## Project Components 📂

This project consists of two core Python files:

### 1. Vector Store Creation (`vector.py`)

This script is responsible for setting up the knowledge base.
* **Loads Data:** Reads the trip itinerary from `Dubai_trip.csv`.
* **Generates Embeddings:** Uses the `OllamaEmbeddings` with the `mxbai-embed-large` model to convert text data into vectors.
* **Builds Database:** Creates a `Chroma` vector database in a local directory (`./chrome_lamgchain_db`) and populates it with the itinerary documents.
* **Creates Retriever:** Exports a `retriever` object configured to fetch the single most relevant document for a given query.

### 2. Chatbot Application (`main.py`)

This is the interactive user-facing script.
* **User Input:** Prompts the user for questions in a continuous loop.
* **Retrieval:** Takes the user's question and uses the `retriever` from `vector.py` to find relevant context from the vector database.
* **Generation:** Feeds the retrieved context and the question into the `OllamaLLM` (`llama3.2` model) using a predefined prompt template.
* **Response:** Prints the LLM's generated answer to the console.

---

## Setup and Installation ⚙️

Follow these steps to get the project running.

1.  **Install Ollama:** You must have [Ollama](https://ollama.com/) installed and running on your system.

2.  **Download LLM Models:** Open your terminal and pull the necessary models:
    ```bash
    # For generating answers
    ollama pull llama3.2

    # For creating text embeddings
    ollama pull mxbai-embed-large
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install pandas langchain-ollama langchain-chroma langchain-core
    ```

4.  **Prepare Data:** Make sure the `Dubai_trip.csv` file is present in the same directory as your Python scripts.

---

## Usage Instructions ▶️

1.  **Create the Vector Database:**
    First, run the data processing script to build the knowledge base.
    ```bash
    python vector.py
    ```
    This will create a new folder named `chrome_lamgchain_db` in your directory. You only need to run this script once.

2.  **Run the Chatbot:**
    Once the database is created, start the chatbot.
    ```bash
    python main.py
    ```
    You can now start asking questions about your Dubai trip. Type `q` and press Enter to quit the application.

---

## Assumptions 📝

For this project to function correctly, the following assumptions are made:

* **Ollama Environment:** **Ollama is installed and the service is running** on the local machine.
* **Model Availability:** Both the `llama3.2` and `mxbai-embed-large` models have been successfully **downloaded via Ollama**.
* **CSV File:** A CSV file named **`Dubai_trip.csv` exists** in the root project directory and contains the expected columns (`Date`, `Activity`, `Timing`, `Location`, etc.).
* **File Structure:** The two scripts (`vector.py` and `main.py`) are in the same directory. The main script correctly imports the `retriever` object from the vector script.
* **Write Permissions:** The script has the necessary **permissions to create and write to the `./chrome_lamgchain_db` directory**.
* **Interactive Terminal:** The chatbot script is run in an **interactive command-line environment** that supports user input.