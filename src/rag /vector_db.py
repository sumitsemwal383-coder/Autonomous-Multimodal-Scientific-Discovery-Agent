import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import VECTOR_STORE_DIR
from .embeddings import DenseEmbeddingGenerator

logger = logging.getLogger(__name__)


class VectorDatabase:
    """Persistent vector store for scientific literature."""

    def __init__(
        self,
        collection_name: str = "scientific_literature",
        storage_dir: Optional[Path] = None
    ):
        self.collection_name = collection_name
        self.storage_dir = Path(storage_dir or VECTOR_STORE_DIR)
        self.storage_file = (
            self.storage_dir / f"{collection_name}_store.json"
        )
        self.embedder = DenseEmbeddingGenerator(dimension=128)
        self.records: List[Dict[str, Any]] = []
        self._load()

    def insert(
        self,
        doc_id: str,
        text: str,
        metadata: Dict[str, Any],
        vector: Optional[List[float]] = None
    ) -> None:
        """Insert a document or update an existing document."""
        if vector is None:
            vector = self.embedder.encode(text)

        for record in self.records:
            if record["id"] == doc_id:
                record["text"] = text
                record["vector"] = vector
                record["metadata"] = metadata
                self._save()
                return

        self.records.append({
            "id": doc_id,
            "text": text,
            "vector": vector,
            "metadata": metadata
        })
        self._save()

    def insert_batch(self, items: List[Dict[str, Any]]) -> int:
        """Insert multiple research papers."""
        count = 0

        for item in items:
            doc_id = item["id"]
            text = f"{item.get('title', '')} {item.get('abstract', '')}"
            self.insert(doc_id, text, item)
            count += 1

        return count

    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return the top-k documents ranked by cosine similarity."""
        if top_k <= 0 or not self.records:
            return []

        query_vector = self.embedder.encode(query)
        results = []

        for record in self.records:
            if category_filter:
                category = record.get("metadata", {}).get("category", "")
                if category_filter.lower() not in str(category).lower():
                    continue

            score = self.embedder.cosine_similarity(
                query_vector, record["vector"]
            )

            results.append({
                "id": record["id"],
                "score": round(score, 4),
                "text": record["text"],
                "metadata": record["metadata"]
            })

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

    def count(self) -> int:
        """Return the number of stored documents."""
        return len(self.records)

    def _save(self) -> None:
        """Persist all records to a JSON file."""
        try:
            self.storage_dir.mkdir(parents=True, exist_ok=True)

            with self.storage_file.open("w", encoding="utf-8") as file:
                json.dump(self.records, file, indent=2, ensure_ascii=False)

        except (OSError, TypeError, ValueError):
            logger.exception("Failed to persist vector store")

    def _load(self) -> None:
        """Load previously saved records."""
        if not self.storage_file.exists():
            return

        try:
            with self.storage_file.open("r", encoding="utf-8") as file:
                records = json.load(file)

            if isinstance(records, list):
                self.records = [
                    record for record in records
                    if isinstance(record, dict)
                    and all(
                        key in record
                        for key in ("id", "text", "vector", "metadata")
                    )
                ]
            else:
                logger.warning("Vector store must contain a JSON list.")

        except (OSError, json.JSONDecodeError):
            logger.exception("Failed to load vector store")
            self.records = []
