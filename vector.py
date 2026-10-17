"""
Vector store and retriever module for Dubai Trip Query Chatbot.
Provides backwards-compatible retriever interface with graceful fallback.
"""
import os
from pathlib import Path
from src.retrieval.store import TripKnowledgeStore
from src.core.schemas import RetrievedDocument

WORKSPACE_ROOT = Path(__file__).resolve().parent
csv_path = WORKSPACE_ROOT / "Dubai_trip.csv"

# Attempt LangChain + Chroma import if available
retriever = None
try:
    from langchain_ollama import OllamaEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    import pandas as pd

    df = pd.read_csv(csv_path)
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    db_location = "./chrome_lamgchain_db"
    add_documents = not os.path.exists(db_location)

    if add_documents:
        documents = []
        ids = []
        for i, row in df.iterrows():
            highlights = row.get("Highlights") if "Highlights" in row else row.get("Attractions / Details", "")
            document = Document(
                page_content=f"{row.get('Date', '')} {row.get('Activity', '')}",
                metadata={
                    "timing": row.get("Timing", ""),
                    "location": row.get("Location", ""),
                    "transport": row.get("Transport / Flight", ""),
                    "attractions": highlights,
                    "meals_hotel": row.get("Meals / Hotel", "")
                },
                id=str(i)
            )
            ids.append(str(i))
            documents.append(document)

    vector_store = Chroma(
        collection_name="Dubai_Trip",
        persist_directory=db_location,
        embedding_function=embeddings
    )

    if add_documents:
        vector_store.add_documents(documents, ids=ids)

    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

except Exception:
    # Graceful fallback: lightweight standalone retriever using TripKnowledgeStore
    class FallbackRetriever:
        def __init__(self, store: TripKnowledgeStore):
            self.store = store

        def invoke(self, query: str):
            docs = self.store.retrieve(query, k=4)
            # Wrap in minimal Document-like interface
            class DocWrapper:
                def __init__(self, doc: RetrievedDocument):
                    self.page_content = doc.page_content
                    self.metadata = doc.metadata

                def __repr__(self):
                    return f"Document(page_content='{self.page_content}', metadata={self.metadata})"

            return [DocWrapper(d) for d in docs]

    _store = TripKnowledgeStore(csv_path)
    retriever = FallbackRetriever(_store)