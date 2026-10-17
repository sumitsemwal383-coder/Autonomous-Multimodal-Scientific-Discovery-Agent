import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import logging

from typing import List, Dict, Any, Optional
from pathlib import Path

from config.settings import ARXIV_API_URL, CACHE_DIR

logger = logging.getLogger(__name__)


class ArxivPipeline:

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the pipeline and configure its cache location."""

        self.cache_dir = Path(cache_dir or CACHE_DIR)
        self.cache_file = self.cache_dir / "arxiv_papers_cache.json"

    # ==========================================================================
    # DAY 2: ARXIV API SEARCH
    # ==========================================================================

    def search(
        self,
        query: str,
        max_results: int = 5,
        categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search ArXiv, falling back to cached or demo papers if needed."""

        if max_results < 1:
            raise ValueError("max_results must be at least 1")

        search_query = query

        if categories:
            cat_filter = " OR ".join(
                f"cat:{category}" for category in categories
            )
            search_query = f"({query}) AND ({cat_filter})"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

        logger.info("Querying ArXiv API: %s", url)

        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "AutonomousScientificAgent/1.0 (academic-research)"
                    )
                },
            )

            with urllib.request.urlopen(request, timeout=15) as response:
                content = response.read()

            # DAY 3: Parse the Atom XML response.
            papers = self._parse_atom(content)

            # DAY 4: Save successfully retrieved papers to local cache.
            self._cache_papers(papers)

            return papers[:max_results]

        except Exception as error:
            logger.warning(
                "Live ArXiv query failed: %s. Trying local cache.",
                error,
            )

        # DAY 4: Use cached papers if the live API is unavailable.
        papers = self._load_cached_papers()

        if papers:
            logger.info("Loaded %s papers from local cache.", len(papers))
        else:
            # DAY 4: Use curated fallback papers when no cache is available.
            logger.warning(
                "No cached papers available; using demo fallback papers."
            )
            papers = self._load_fallback_papers(query)

        return papers[:max_results]

    # ==========================================================================
    # DAY 3: ATOM XML PARSING AND METADATA EXTRACTION
    # ==========================================================================

    def _parse_atom(self, xml_bytes: bytes) -> List[Dict[str, Any]]:
        """Parse Atom XML and extract structured ArXiv paper metadata."""

        namespaces = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }

        root = ET.fromstring(xml_bytes)
        papers = []

        for entry in root.findall("atom:entry", namespaces):

            id_element = entry.find("atom:id", namespaces)
            title_element = entry.find("atom:title", namespaces)
            summary_element = entry.find("atom:summary", namespaces)
            published_element = entry.find("atom:published", namespaces)

            paper_id = (
                id_element.text.strip()
                if id_element is not None and id_element.text
                else ""
            )

            if not paper_id:
                continue

            title = (
                " ".join(title_element.text.split())
                if title_element is not None and title_element.text
                else "Untitled"
            )

            abstract = (
                " ".join(summary_element.text.split())
                if summary_element is not None and summary_element.text
                else ""
            )

            published = (
                published_element.text.strip()
                if published_element is not None and published_element.text
                else ""
            )

            authors = []

            for author in entry.findall("atom:author", namespaces):
                name = author.find("atom:name", namespaces)

                if name is not None and name.text:
                    authors.append(name.text.strip())

            pdf_url = ""

            for link in entry.findall("atom:link", namespaces):
                if (
                    link.attrib.get("title") == "pdf"
                    or link.attrib.get("type") == "application/pdf"
                ):
                    pdf_url = link.attrib.get("href", "")
                    break

            primary_category = entry.find(
                "arxiv:primary_category",
                namespaces,
            )

            category = (
                primary_category.attrib.get("term", "")
                if primary_category is not None
                else ""
            )

            papers.append({
                "source": "arxiv",
                "id": paper_id,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "published": published,
                "category": category,
                "url": pdf_url or paper_id,
                "doi": "",
            })

        return papers

    # ==========================================================================
    # DAY 4: LOAD PAPERS FROM LOCAL CACHE
    # ==========================================================================

    def _load_cached_papers(self) -> List[Dict[str, Any]]:
        """Load valid paper records from the local JSON cache."""

        try:
            if not self.cache_file.exists():
                return []

            with open(
                self.cache_file,
                "r",
                encoding="utf-8",
            ) as file:
                cached = json.load(file)

            if not isinstance(cached, list):
                logger.warning("Cache must contain a JSON list.")
                return []

            return [
                paper
                for paper in cached
                if isinstance(paper, dict) and paper.get("id")
            ]

        except (OSError, json.JSONDecodeError) as error:
            logger.warning("Could not read ArXiv cache: %s", error)
            return []

    # ==========================================================================
    # DAY 4: CURATED OFFLINE FALLBACK PAPERS
    # ==========================================================================

    def _load_fallback_papers(
        self,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Return curated demonstration papers when no cache is available."""

        fallback_data = [
            {
                "source": "arxiv",
                "id": "http://arxiv.org/abs/2403.09629v1",
                "title": (
                    "Quiet-STaR: Language Models Can Teach Themselves "
                    "to Think Before Speaking"
                ),
                "abstract": (
                    "We introduce Quiet-STaR, a method that trains language "
                    "models to generate thoughts at every token to explain "
                    "future text, improving reasoning performance."
                ),
                "authors": [
                    "Eric Zelikman",
                    "Georges Harik",
                    "Yijia Shao",
                    "Varuna Jayasiri",
                    "Nick Haber",
                    "Noah D. Goodman",
                ],
                "published": "2024-03-14T17:59:12Z",
                "category": "cs.AI",
                "url": "https://arxiv.org/pdf/2403.09629",
                "doi": "10.48550/arXiv.2403.09629",
            },
            {
                "source": "arxiv",
                "id": "http://arxiv.org/abs/2305.18290v2",
                "title": (
                    "Direct Preference Optimization: Your Language Model "
                    "is Secretly a Reward Model"
                ),
                "abstract": (
                    "Direct Preference Optimization (DPO) optimizes language "
                    "models using preference data without requiring a "
                    "separately trained reward model."
                ),
                "authors": [
                    "Rafael Rafailov",
                    "Archit Sharma",
                    "Eric Mitchell",
                    "Stefano Ermon",
                    "Christopher D. Manning",
                    "Chelsea Finn",
                ],
                "published": "2023-05-29T18:21:40Z",
                "category": "cs.LG",
                "url": "https://arxiv.org/pdf/2305.18290",
                "doi": "10.48550/arXiv.2305.18290",
            },
            {
                "source": "arxiv",
                "id": "http://arxiv.org/abs/2310.03744v1",
                "title": (
                    "Self-RAG: Learning to Retrieve, Generate, "
                    "and Critique through Self-Reflection"
                ),
                "abstract": (
                    "Self-RAG uses adaptive retrieval and self-critique "
                    "to improve retrieval-augmented generation."
                ),
                "authors": [
                    "Akari Asai",
                    "Zeqiu Wu",
                    "Yizhong Wang",
                    "Avirup Sil",
                    "Hannaneh Hajishirzi",
                ],
                "published": "2023-10-05T17:48:29Z",
                "category": "cs.CL",
                "url": "https://arxiv.org/pdf/2310.03744",
                "doi": "10.48550/arXiv.2310.03744",
            },
            {
                "source": "arxiv",
                "id": "http://arxiv.org/abs/2303.11366v3",
                "title": (
                    "Reflexion: Language Agents with Verbal "
                    "Reinforcement Learning"
                ),
                "abstract": (
                    "Reflexion equips agents with verbal feedback and "
                    "self-reflection to improve subsequent attempts "
                    "without updating model parameters."
                ),
                "authors": [
                    "Noah Shinn",
                    "Federico Cassano",
                    "Edward Berman",
                    "Ashwin Gopinath",
                    "Karthik Narasimhan",
                    "Shunyu Yao",
                ],
                "published": "2023-03-20T17:33:04Z",
                "category": "cs.AI",
                "url": "https://arxiv.org/pdf/2303.11366",
                "doi": "10.48550/arXiv.2303.11366",
            },
        ]

        return fallback_data

    # ==========================================================================
    # DAY 4: SAVE PAPERS TO LOCAL DISK CACHE
    # ==========================================================================

    def _cache_papers(
        self,
        papers: List[Dict[str, Any]],
    ) -> None:
        """Save papers to disk without duplicating their IDs."""

        try:
            # Create the cache directory if it does not exist.
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            # Read any existing valid cache entries.
            cached = self._load_cached_papers()

            # Use IDs as keys to avoid duplicate records.
            papers_by_id = {
                paper["id"]: paper
                for paper in cached
            }

            for paper in papers:
                paper_id = paper.get("id")

                if paper_id:
                    papers_by_id[paper_id] = paper

            with open(
                self.cache_file,
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    list(papers_by_id.values()),
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

            logger.info(
                "Cached %s unique ArXiv papers.",
                len(papers_by_id),
            )

        except OSError as error:
            logger.error("Error caching ArXiv papers: %s", error)
