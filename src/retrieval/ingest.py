"""
Robust CSV Ingestion and Document Normalization for Dubai Trip Itinerary.
"""
import csv
from pathlib import Path
from typing import List
from src.core.schemas import RetrievedDocument

def load_itinerary_documents(csv_path: Path) -> List[RetrievedDocument]:
    """
    Parses Dubai_trip.csv and builds normalized RetrievedDocument objects
    with rich metadata. Handles column trimming and quote edge-cases.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Itinerary CSV file not found at: {csv_path}")

    documents = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, raw_row in enumerate(reader):
            # Clean keys and values
            row = {k.strip(): (v.strip() if v else "") for k, v in raw_row.items() if k}
            
            date = row.get("Date", "")
            timing = row.get("Timing", "")
            activity = row.get("Activity", "")
            transport = row.get("Transport / Flight", "")
            location = row.get("Location", "")
            highlights = row.get("Highlights", "") or row.get("Attractions / Details", "")
            meals_hotel = row.get("Meals / Hotel", "")

            # Compose informative content
            page_content = f"{date} {timing}: {activity}"
            if highlights:
                page_content += f" ({highlights})"

            metadata = {
                "date": date,
                "timing": timing,
                "activity": activity,
                "transport": transport,
                "location": location,
                "highlights": highlights,
                "meals_hotel": meals_hotel,
                "row_index": idx
            }

            doc = RetrievedDocument(
                id=str(idx),
                page_content=page_content,
                metadata=metadata
            )
            documents.append(doc)

    return documents
