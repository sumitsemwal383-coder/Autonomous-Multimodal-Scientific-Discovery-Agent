
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Cache directory
CACHE_DIR = BASE_DIR / "data" / "cache"

# Create cache directory if it does not exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# ArXiv API
ARXIV_API_URL = "https://export.arxiv.org/api/query"

# PubMed APIs
PUBMED_ESEARCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
)

PUBMED_ESUMMARY_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
)

PUBMED_EFETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
)
