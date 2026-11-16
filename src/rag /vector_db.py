"""
Vector Database Module
Stores and retrieves scientific research documents using ChromaDB.

The public API is intentionally compatible with:
- LiteratureReviewerAgent: insert_batch(papers)
- MultimodalParser: insert(doc_id, text, metadata)
- LiteratureRetriever: search(query, top_k=...)
"""

import json
from typing import Any, Dict, Iterable, List, Optional

import chromadb
from chromadb.utils import embedding_functions


class VectorDatabase:
    def __init__(
        self,
        collection_name: str = "scientific_research",
        persist_directory: str = "./data/chroma_db",
    ):
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )

    @staticmethod
    def _metadata_value(value: Any) -> Any:
        """Convert metadata values to ChromaDB-supported scalar values."""
        if value is None:
            return ""
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, (list, tuple, dict)):
            return json.dumps(value, ensure_ascii=False, default=str)
        return str(value)

    @classmethod
    def _clean_metadata(cls, metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        metadata = metadata or {}
        cleaned = {
            str(key): cls._metadata_value(value)
            for key, value in metadata.items()
            if value is not None
        }
        # ChromaDB requires non-empty metadata values in some versions.
        return cleaned or {"source": "unknown"}

    def insert(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Insert or update one document."""
        if not str(doc_id).strip():
            raise ValueError("doc_id must be a non-empty string")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        self.collection.upsert(
            ids=[str(doc_id)],
            documents=[text],
            metadatas=[self._clean_metadata(metadata)],
        )
        return True

    def insert_batch(self, papers: Iterable[Dict[str, Any]]) -> int:
        """Insert or update paper records returned by ingestion pipelines."""
        papers = list(papers or [])
        if not papers:
            return 0

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for index, paper in enumerate(papers):
            if not isinstance(paper, dict):
                continue

            doc_id = str(
                paper.get("id")
                or paper.get("paper_id")
                or paper.get("doc_id")
                or f"paper_{self.collection.count() + index}"
            ).strip()

            abstract = str(paper.get("abstract") or paper.get("text") or "").strip()
            title = str(paper.get("title") or "Untitled").strip()
            document = (
                f"Title: {title}\n\nAbstract: {abstract}"
                if abstract
                else title
            )
            if not document.strip():
                continue

            metadata = dict(paper)
            metadata.pop("text", None)

            # Preserve authors in a readable form for LiteratureRetriever.
            authors = metadata.get("authors", [])
            if isinstance(authors, (list, tuple)):
                metadata["authors"] = ", ".join(str(a) for a in authors)

            ids.append(doc_id)
            documents.append(document)
            metadatas.append(self._clean_metadata(metadata))

        if not ids:
            return 0

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    def add_documents(
        self,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """Compatibility helper for adding plain text documents."""
        if not documents:
            return 0

        if ids is None:
            start = self.collection.count()
            ids = [f"doc_{start + i}" for i in range(len(documents))]

        if len(ids) != len(documents):
            raise ValueError("ids and documents must have the same length")

        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in documents]

        if len(metadatas) != len(documents):
            raise ValueError("metadatas and documents must have the same length")

        self.collection.upsert(
            ids=[str(item) for item in ids],
            documents=[str(item) for item in documents],
            metadatas=[self._clean_metadata(item) for item in metadatas],
        )
        return len(documents)

    def search(
        self,
        query: str,
        top_k: int = 3,
        n_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search documents and return a list of normalized match dictionaries.

        Supports both `top_k` (used by LiteratureRetriever) and `n_results`
        (used by earlier versions of this project).
        """
        if not isinstance(query, str) or not query.strip():
            return []

        count = self.collection.count()
        if count == 0:
            return []

        requested = n_results if n_results is not None else top_k
        try:
            requested = max(1, int(requested))
        except (TypeError, ValueError):
            requested = 3

        result = self.collection.query(
            query_texts=[query],
            n_results=min(requested, count),
            include=["documents", "metadatas", "distances"],
        )

        ids_by_query = result.get("ids") or [[]]
        docs_by_query = result.get("documents") or [[]]
        metas_by_query = result.get("metadatas") or [[]]
        distances_by_query = result.get("distances") or [[]]

        ids = ids_by_query[0] if ids_by_query else []
        docs = docs_by_query[0] if docs_by_query else []
        metas = metas_by_query[0] if metas_by_query else []
        distances = distances_by_query[0] if distances_by_query else []

        matches: List[Dict[str, Any]] = []
        for index, doc_id in enumerate(ids):
            distance = distances[index] if index < len(distances) else None
            # Chroma distances are lower for closer matches.
            score = (1.0 - float(distance)) if distance is not None else 0.0

            matches.append(
                {
                    "id": str(doc_id),
                    "text": docs[index] if index < len(docs) else "",
                    "metadata": (
                        metas[index]
                        if index < len(metas) and metas[index]
                        else {}
                    ),
                    "score": score,
                    "distance": distance,
                }
            )

        return matches

    def clear_database(self) -> None:
        """Delete and recreate the configured collection."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"},
        )
