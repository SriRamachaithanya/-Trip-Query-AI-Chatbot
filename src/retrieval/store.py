"""
Knowledge store and hybrid retriever for Dubai trip itinerary.
Provides in-memory keyword-scoring and Chroma integration.
"""
import re
from pathlib import Path
from typing import List, Optional
from src.core.schemas import RetrievedDocument
from src.retrieval.ingest import load_itinerary_documents

class TripKnowledgeStore:
    """Stores and retrieves itinerary documents with configurable k."""

    def __init__(self, csv_path: Path):
        self.csv_path = csv_path
        self.documents: List[RetrievedDocument] = []
        self.load()

    def load(self):
        self.documents = load_itinerary_documents(self.csv_path)

    def retrieve(self, query: str, k: int = 4) -> List[RetrievedDocument]:
        """
        Retrieves the top-k most relevant documents for the query.
        Uses multi-field token scoring (dates, activities, hotels, flights).
        """
        if not self.documents:
            self.load()

        query_tokens = set(re.findall(r"\w+", query.lower()))
        if not query_tokens:
            return self.documents[:k]

        scored_docs = []
        for doc in self.documents:
            score = 0.0
            content_lower = doc.page_content.lower()
            meta = doc.metadata

            # Score matching tokens in content
            for token in query_tokens:
                if token in content_lower:
                    score += 2.0
                if token in meta.get("location", "").lower():
                    score += 1.5
                if token in meta.get("meals_hotel", "").lower():
                    score += 2.5
                if token in meta.get("transport", "").lower():
                    score += 2.5
                if token in meta.get("date", "").lower():
                    score += 3.0

            scored_docs.append((score, doc))

        # Sort descending by score
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # If highest score is 0 and query is broad, return first k docs
        top_docs = [doc for _, doc in scored_docs[:k]]
        return top_docs
