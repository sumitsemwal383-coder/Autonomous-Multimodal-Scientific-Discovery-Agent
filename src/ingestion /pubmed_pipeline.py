import urllib.request
import urllib.parse
import json
import logging

from config.settings import PUBMED_ESEARCH_URL

logger = logging.getLogger(__name__)


class PubMedPipeline:

    def search(self, query: str, max_results: int = 5) -> list:
        """Search PubMed and retrieve matching PubMed IDs."""

        if max_results < 1:
            raise ValueError("max_results must be at least 1")

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

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                search_data = json.loads(
                    response.read().decode("utf-8")
                )

            id_list = (
                search_data
                .get("esearchresult", {})
                .get("idlist", [])
            )

            logger.info("Retrieved %s PubMed IDs.", len(id_list))
            return id_list

        except Exception as error:
            logger.warning("PubMed ESearch failed: %s", error)
            return []
