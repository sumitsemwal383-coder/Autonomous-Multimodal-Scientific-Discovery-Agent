"""
Multimodal Parser
Processes visual evidence such as charts, figures,
and experimental plots for the RAG pipeline.
"""

import logging
import uuid
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class MultimodalParser:
    def __init__(self):
        self.processed_figures = 0

    def synthesize_visual_chunks(
        self,
        figures: List[Dict[str, Any]],
        paper_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Convert visual evidence into searchable text chunks."""
        chunks = []
        paper_metadata = paper_metadata or {}

        for figure in figures:
            if not isinstance(figure, dict):
                continue

            caption = figure.get("caption", "Untitled Figure")
            interpretation = figure.get(
                "interpretation", "No interpretation available"
            )
            quantitative_summary = figure.get(
                "quantitative_summary", "No quantitative data available"
            )

            text = (
                f"Figure: {caption}\n"
                f"Interpretation: {interpretation}\n"
                f"Quantitative Summary: {quantitative_summary}"
            )

            metadata = {
                **paper_metadata,
                "caption": str(caption),
                "type": "visual_evidence"
            }

            chunks.append({
                "id": str(uuid.uuid4()),
                "text": text,
                "metadata": metadata
            })

        self.processed_figures += len(chunks)
        return chunks

    def ingest_visual_evidence(
        self,
        figures: List[Dict[str, Any]],
        vector_db,
        paper_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Convert visual evidence into chunks and store them in vector DB."""
        chunks = self.synthesize_visual_chunks(figures, paper_metadata)
        inserted = 0
        failed = []

        for chunk in chunks:
            try:
                vector_db.insert(
                    doc_id=chunk["id"],
                    text=chunk["text"],
                    metadata=chunk["metadata"]
                )
                inserted += 1
            except Exception as exc:
                logger.exception("Failed to index visual chunk %s", chunk["id"])
                failed.append({"id": chunk["id"], "error": str(exc)})

        return {
            "total_chunks": len(chunks),
            "inserted": inserted,
            "failed": failed
        }
