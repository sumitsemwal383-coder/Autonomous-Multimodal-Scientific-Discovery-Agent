
def _parse_atom(self, xml_bytes: bytes) -> List[Dict[str, Any]]:
    """Parse an arXiv Atom feed and extract paper metadata safely."""
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        logger.error("Failed to parse arXiv Atom XML: %s", exc)
        return []

    papers: List[Dict[str, Any]] = []

    for entry in root.findall("atom:entry", ns):
        def get_text(path: str, default: str = "") -> str:
            element = entry.find(path, ns)
            if element is None or not element.text:
                return default
            return " ".join(element.text.split())

        arxiv_id = get_text("atom:id")
        title = get_text("atom:title", "Untitled")
        abstract = get_text("atom:summary")
        published = get_text("atom:published")

        authors = [
            " ".join(name.text.split())
            for author in entry.findall("atom:author", ns)
            if (name := author.find("atom:name", ns)) is not None
            and name.text
            and name.text.strip()
        ]

        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if (
                link.attrib.get("title", "").lower() == "pdf"
                or link.attrib.get("type", "").lower() == "application/pdf"
            ):
                pdf_url = link.attrib.get("href", "")
                break

        primary_category = entry.find("arxiv:primary_category", ns)
        category = (
            primary_category.attrib.get("term", "cs.AI")
            if primary_category is not None
            else "cs.AI"
        )

        if not arxiv_id:
            logger.warning("Skipping arXiv entry without an ID")
            continue

        papers.append({
            "source": "arxiv",
            "id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "published": published,
            "category": category,
            "url": pdf_url or arxiv_id,
            "doi": "",
        })

    logger.info("Parsed %d papers from arXiv Atom feed", len(papers))
    return papers
