
from pathlib import Path

# ============================================================
# PROJECT DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

CACHE_DIR = DATA_DIR / "cache"

HOLDOUT_DIR = DATA_DIR / "holdout_papers"

VECTOR_STORE_DIR = DATA_DIR / "vector_store"


# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

CACHE_DIR.mkdir(parents=True, exist_ok=True)
HOLDOUT_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# ARXIV API CONFIGURATION
# ============================================================

ARXIV_API_URL = "https://export.arxiv.org/api/query"


# ============================================================
# PUBMED API CONFIGURATION
# ============================================================

PUBMED_ESEARCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
)

PUBMED_ESUMMARY_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
)

PUBMED_EFETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
)
