
"""
Vector Database Module
Stores and retrieves scientific research documents
using ChromaDB.
"""

import chromadb
from chromadb.utils import embedding_functions


class VectorDatabase:

    def __init__(self, collection_name="scientific_research"):

        self.client = chromadb.PersistentClient(
            path="./data/chroma_db"
        )

        self.embedding_function = (
            embedding_functions.DefaultEmbeddingFunction()
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function
        )

    def add_documents(self, documents, ids=None):

        if not documents:
            return

        if ids is None:
            ids = [
                f"doc_{self.collection.count() + i}"
                for i in range(len(documents))
            ]

        self.collection.upsert(
            documents=documents,
            ids=ids
        )

    def search(self, query, n_results=3):

        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )

        return results

    def clear_database(self):

        self.client.delete_collection(
            self.collection.name
        )

        self.collection = self.client.get_or_create_collection(
            name="scientific_research",
            embedding_function=self.embedding_function
        )
