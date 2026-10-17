"""
Prompt templates and formatting utilities for Trip Query AI Chatbot.
"""
from typing import List
from src.core.schemas import RetrievedDocument

SYSTEM_PROMPT = """You are an expert AI Travel Assistant specialized in answering questions about the Dubai trip itinerary.

Instructions:
1. Base your answers strictly on the provided Itinerary Context.
2. If the user asks about destinations, activities, or flights not in the context (e.g. Tokyo, Paris, Rome, general programming/physics), politely state that you can only assist with the Dubai trip itinerary.
3. If the user asks about prices or itemized budgets not explicitly stated in the itinerary, clarify that exact prices are unrecorded or estimates.
4. If the user requests JSON output, return strictly valid JSON matching their requested fields.
5. If the request is ambiguous or missing dates, ask a brief clarifying question or provide the breakdown across all applicable dates.
"""

USER_PROMPT_TEMPLATE = """Itinerary Context:
{context}

User Query:
{question}

Answer:"""

def format_context_documents(docs: List[RetrievedDocument]) -> str:
    """Formats retrieved documents with full metadata into readable text for the LLM."""
    if not docs:
        return "No relevant itinerary records found."
    
    entries = []
    for doc in docs:
        meta = doc.metadata
        entry_parts = [f"• Date: {meta.get('date', 'Unknown')}, Timing: {meta.get('timing', 'Unknown')}"]
        entry_parts.append(f"  Activity: {doc.page_content}")
        if meta.get("location"):
            entry_parts.append(f"  Location: {meta.get('location')}")
        if meta.get("transport") and meta.get("transport") != "—":
            entry_parts.append(f"  Transport/Flight: {meta.get('transport')}")
        if meta.get("highlights"):
            entry_parts.append(f"  Highlights: {meta.get('highlights')}")
        if meta.get("meals_hotel"):
            entry_parts.append(f"  Meals/Hotel: {meta.get('meals_hotel')}")
        entries.append("\n".join(entry_parts))
    
    return "\n\n".join(entries)
