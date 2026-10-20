import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import logging

from typing import List, Dict, Any, Optional
from pathlib import Path

from config.settings import (
    PUBMED_ESEARCH_URL,
    PUBMED_ESUMMARY_URL,
    CACHE_DIR,
)

try:
    from config.settings import PUBMED_EFETCH_URL
except ImportError:
    PUBMED_EFETCH_URL = None

logger = logging.getLogger(__name__)


class PubMedPipeline:

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = Path(cache_dir or CACHE_DIR)
        self.cache_file = self.cache_dir / "pubmed_papers_cache.json"

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search PubMed and return structured paper records."""

        if max_results < 1:
            raise ValueError("max_results must be at least 1")

        try:
            # Step 1: ESearch retrieves matching PubMed IDs.
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": max_results,
                "sort": "pub_date",
            }

            search_url = (
                f"{PUBMED_ESEARCH_URL}?"
                f"{urllib.parse.urlencode(search_params)}"
            )

            request = urllib.request.Request(
                search_url,
                headers={"User-Agent": "AutonomousScientist/1.0"},
            )

            with urllib.request.urlopen(request, timeout=10) as response:
                search_data = json.loads(
                    response.read().decode("utf-8")
                )

            id_list = (
                search_data
                .get("esearchresult", {})
                .get("idlist", [])
            )

            if not id_list:
                cached = self._load_cached_papers()
                return cached[:max_results] or self._load_fallback_papers()[
                    :max_results
                ]

            # Step 2: ESummary retrieves metadata for those IDs.
            summary_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json",
            }

            summary_url = (
                f"{PUBMED_ESUMMARY_URL}?"
                f"{urllib.parse.urlencode(summary_params)}"
            )

            request = urllib.request.Request(
                summary_url,
                headers={"User-Agent": "AutonomousScientist/1.0"},
            )

            with urllib.request.urlopen(request, timeout=10) as response:
                summary_data = json.loads(
                    response.read().decode("utf-8")
                )

            records = summary_data.get("result", {})
            papers = []

            for pmid in id_list:
                info = records.get(pmid, {})

                if not info or pmid == "uids":
                    continue

                authors = [
                    author.get("name", "")
                    for author in info.get("authors", [])
                    if author.get("name")
                ]

                doi = next(
                    (
                        article_id.get("value", "")
                        for article_id in info.get("articleids", [])
                        if article_id.get("idtype") == "doi"
                    ),
                    "",
                )

                papers.append({
                    "source": "pubmed",
                    "id": f"PMID:{pmid}",
                    "title": info.get("title", "Untitled"),
                    "abstract": "",
                    "authors": authors,
                    "published": info.get("pubdate", ""),
                    "category": "q-bio",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "doi": doi,
                })

            # Step 3: Fetch actual abstracts if EFetch is configured.
            if PUBMED_EFETCH_URL and papers:
                abstracts = self._fetch_abstracts(id_list)

                for paper in papers:
                    pmid = paper["id"].replace("PMID:", "")
                    paper["abstract"] = abstracts.get(pmid, "")

            self._cache_papers(papers)
            return papers[:max_results]

        except Exception as error:
            logger.warning("Live PubMed query failed: %s", error)

            cached = self._load_cached_papers()

            if cached:
                return cached[:max_results]

            return self._load_fallback_papers()[:max_results]

    def _fetch_abstracts(
        self,
        pmids: List[str],
    ) -> Dict[str, str]:
        """Fetch actual abstracts using the NCBI EFetch XML endpoint."""

        if not PUBMED_EFETCH_URL or not pmids:
            return {}

        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
        }

        url = (
            f"{PUBMED_EFETCH_URL}?"
            f"{urllib.parse.urlencode(params)}"
        )

        request = urllib.request.Request(
            url,
            headers={"User-Agent": "AutonomousScientist/1.0"},
        )

        with urllib.request.urlopen(request, timeout=10) as response:
            root = ET.fromstring(response.read())

        abstracts = {}

        for article in root.findall(".//PubmedArticle"):
            pmid_element = article.find(".//PMID")
            if pmid_element is None or not pmid_element.text:
                continue

            abstract_parts = []

            for part in article.findall(".//Abstract/AbstractText"):
                text = "".join(part.itertext()).strip()
                if text:
                    label = part.attrib.get("Label")
                    abstract_parts.append(
                        f"{label}: {text}" if label else text
                    )

            abstracts[pmid_element.text.strip()] = " ".join(
                abstract_parts
            )

        return abstracts

    def _load_cached_papers(self) -> List[Dict[str, Any]]:
        """Load valid paper records from the JSON cache."""

        try:
            if not self.cache_file.exists():
                return []

            with open(self.cache_file, "r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                return []

            return [
                paper for paper in data
                if isinstance(paper, dict) and paper.get("id")
            ]

        except (OSError, json.JSONDecodeError) as error:
            logger.warning("Could not read PubMed cache: %s", error)
            return []

    def _cache_papers(
        self,
        papers: List[Dict[str, Any]],
    ) -> None:
        """Save papers while preventing duplicate IDs."""

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            records = {
                paper["id"]: paper
                for paper in self._load_cached_papers()
            }

            for paper in papers:
                if paper.get("id"):
                    records[paper["id"]] = paper

            with open(self.cache_file, "w", encoding="utf-8") as file:
                json.dump(
                    list(records.values()),
                    file,
                    indent=2,
                    ensure_ascii=False,
                )

        except OSError as error:
            logger.error("Error caching PubMed papers: %s", error)

    def _load_fallback_papers(self) -> List[Dict[str, Any]]:
        """Return the supplied demonstration records for offline use."""

        return [
            {
                "source": "pubmed",
                "id": "PMID:38212450",
                "title": (
                    "Autonomous Artificial Intelligence Agents in "
                    "Biomedical Discovery and Experimental Validation"
                ),
                "abstract": (
                    "Demonstration fallback record. Verify its metadata "
                    "against the original PubMed article before using it."
                ),
                "authors": [],
                "published": "",
                "category": "q-bio.BM",
                "url": "https://pubmed.ncbi.nlm.nih.gov/38212450/",
                "doi": "",
            },
            {
                "source": "pubmed",
                "id": "PMID:37854129",
                "title": (
                    "Statistical Rigor and Reproducibility in Foundation "
                    "Model-Driven Hypothesis Generation"
                ),
                "abstract": (
                    "Demonstration fallback record. Verify its metadata "
                    "against the original PubMed article before using it."
                ),
                "authors": [],
                "published": "",
                "category": "stat.AP",
                "url": "https://pubmed.ncbi.nlm.nih.gov/37854129/",
                "doi": "",
            },
        ]
