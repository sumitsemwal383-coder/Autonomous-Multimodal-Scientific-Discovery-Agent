
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
HOLDOUT_DIR = DATA_DIR / "holdout_papers"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# Create directories if missing
for directory in (CACHE_DIR, HOLDOUT_DIR, VECTOR_STORE_DIR):
    directory.mkdir(parents=True, exist_ok=True)

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
