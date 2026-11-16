"""
Literature Retriever for Grounded RAG.
Retrieves scientific literature, checks citation metadata consistency,
and formats citation-grounded context.
"""

import re
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from .vector_db import VectorDatabase


class LiteratureRetriever:
    def __init__(self, vector_db: VectorDatabase):
        self.vector_db = vector_db

    def retrieve_grounding_context(
        self,
        research_topic: str,
        top_k: int = 4,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """Retrieve relevant papers and build citation-grounded context."""
        if top_k <= 0:
            return "top_k must be greater than zero.", []

        results = self.vector_db.search(research_topic, top_k=top_k)

        if not results:
            return "No relevant literature found in vector store.", []

        context_lines = [
            f"=== GROUNDED SCIENTIFIC LITERATURE FOR: '{research_topic}' ==="
        ]
        citations: List[Dict[str, Any]] = []

        for idx, match in enumerate(results, 1):
            meta = match.get("metadata") or {}
            doc_id = str(match.get("id") or "").strip()
            title = str(meta.get("title") or "").strip()

            authors_data = meta.get("authors") or []
            if isinstance(authors_data, str):
                authors = authors_data
            else:
                authors = ", ".join(str(author) for author in authors_data[:3])

            pub_date = str(meta.get("published") or "Unknown")
            abstract = str(meta.get("abstract") or match.get("text") or "")
            url = str(meta.get("url") or "").strip()
            score = match.get("score", 0.0)

            provenance = self._check_provenance(
                doc_id=doc_id,
                title=title,
                url=url,
                metadata=meta,
            )

            citation = {
                "ref_key": f"Ref_{idx}",
                "doc_id": doc_id,
                "title": title or "Untitled",
                "authors": authors,
                "published": pub_date,
                "url": url,
                "score": score,
                "source": meta.get("source", "unknown"),
                "doi": meta.get("doi", ""),
                "provenance_verified": provenance["verified"],
                "provenance_status": provenance["status"],
                "provenance_issues": provenance["issues"],
            }
            citations.append(citation)

            context_lines.append(
                f"[Ref_{idx}] Title: {title or 'Untitled'}\n"
                f"       Authors: {authors or 'Unknown'} ({pub_date})\n"
                f"       ID: {doc_id or 'Missing'} | Relevance Score: {score}\n"
                f"       URL: {url or 'Missing'}\n"
                f"       Provenance: {provenance['status']}\n"
                f"       Findings/Abstract: {abstract}\n"
            )

        context_lines.append(
            "=== INSTRUCTION: Every generated hypothesis must cite at least "
            "one supplied [Ref_X]. Use only the supplied literature as evidence. "
            "Do not invent citations. ==="
        )
        return "\n".join(context_lines), citations

    @staticmethod
    def _check_provenance(
        doc_id: str,
        title: str,
        url: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Check internal consistency; this is not live-source verification."""
        issues: List[str] = []

        if not doc_id:
            issues.append("Missing document ID")
        if not title or title.lower() == "untitled":
            issues.append("Missing paper title")

        if not url:
            issues.append("Missing source URL")
        else:
            parsed_url = urlparse(url)
            if parsed_url.scheme != "https" or not parsed_url.netloc:
                issues.append("Source URL must be a valid HTTPS URL")
            else:
                host = parsed_url.netloc.lower().split(":")[0]
                path = parsed_url.path.lower()
                normalized_id = doc_id.lower().strip()

                if normalized_id.startswith("pmid:"):
                    pmid = normalized_id.split(":", 1)[1].strip()
                    if not re.fullmatch(r"\d+", pmid):
                        issues.append("Invalid PubMed identifier")
                    elif host not in {
                        "pubmed.ncbi.nlm.nih.gov",
                        "eutils.ncbi.nlm.nih.gov",
                    } or pmid not in path:
                        issues.append("PubMed ID does not match the source URL")

                elif normalized_id.startswith("arxiv:"):
                    arxiv_id = normalized_id.split(":", 1)[1].strip()
                    url_id = path.rstrip("/").split("/")[-1]
                    if host not in {"arxiv.org", "export.arxiv.org"} or url_id.lower() != arxiv_id.lower():
                        issues.append("ArXiv ID does not match the source URL")
                elif normalized_id and not metadata.get("source"):
                    issues.append("Source type is missing for this document ID")

        metadata_id = (
            metadata.get("id")
            or metadata.get("paper_id")
            or metadata.get("doc_id")
        )
        if metadata_id and str(metadata_id).strip() != doc_id:
            issues.append("Document ID conflicts with metadata ID")

        return {
            "verified": len(issues) == 0,
            "status": "consistent" if not issues else "needs_review",
            "issues": issues,
        }

    def verify_grounding(
        self,
        hypothesis_text: str,
        citations: List[Dict[str, Any]],
    ) -> bool:
        """Require a cited reference with internally consistent metadata."""
        if not hypothesis_text or not citations:
            return False

        for citation in citations:
            ref_key = str(citation.get("ref_key") or "").strip()
            if not ref_key:
                continue

            if not re.search(r"\[" + re.escape(ref_key) + r"\]", hypothesis_text):
                continue

            provenance = self._check_provenance(
                doc_id=str(citation.get("doc_id") or "").strip(),
                title=str(citation.get("title") or "").strip(),
                url=str(citation.get("url") or "").strip(),
                metadata=citation,
            )
            if provenance["verified"]:
                return True

        return False
