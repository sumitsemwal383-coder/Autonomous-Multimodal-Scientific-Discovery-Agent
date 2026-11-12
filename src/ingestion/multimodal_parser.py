
    def ingest_visual_evidence(
        self,
        figures: list,
        vector_db,
        paper_metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Convert visual evidence into chunks and store them for RAG."""
        chunks = self.synthesize_visual_chunks(
            figures,
            paper_metadata
        )

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
                logger.exception(
                    "Failed to index visual chunk %s",
                    chunk["id"]
                )
                failed.append({
                    "id": chunk["id"],
                    "error": str(exc)
                })

        return {
            "total_chunks": len(chunks),
            "inserted": inserted,
            "failed": failed
        }
