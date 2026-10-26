from pathlib import Path

from typing import Dict, Any, List

from typing import Dict, Any


import jinja2

from config.settings import TEMPLATES_DIR, SYNTHESIS_DIR


class LatexPaperGenerator:

    """Render academic manuscripts and compile BibTeX references."""

    """Render academic manuscripts using LaTeX and Jinja2."""

    def __init__(
        self,
        template_dir: Path = TEMPLATES_DIR,
        output_dir: Path = SYNTHESIS_DIR,
    ):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=False,
        )

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> str:
        """Render a LaTeX template using the supplied context."""
        template = self.env.get_template(template_name)
        return template.render(**context)

    def save_manuscript(self, content: str) -> str:
        """Save the rendered manuscript to a LaTeX file."""
        output_path = self.output_dir / "research_paper.tex"
        output_path.write_text(content, encoding="utf-8")
        return str(output_path)


    @staticmethod
    def _escape_bibtex(value: str) -> str:
        """Escape characters that can cause issues in BibTeX fields."""
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
        }

        for char, replacement in replacements.items():
            value = value.replace(char, replacement)

        return value

    def generate_bibtex(
        self,
        citations: List[Dict[str, Any]],
    ) -> str:
        """Convert literature citation records into BibTeX entries."""
        bib_entries = []

        for idx, citation in enumerate(citations, start=1):
            key = f"ref_{idx}"

            authors = citation.get("authors", "Unknown Author")
            if isinstance(authors, list):
                authors = " and ".join(str(author) for author in authors)
            else:
                authors = str(authors).replace(",", " and")

            title = str(citation.get("title", "Untitled Publication"))
            published = str(citation.get("published", "2024"))
            year = published[:4] if published else "2024"
            url = str(citation.get("url", ""))

            fields = [
                f"  author = {{{self._escape_bibtex(authors)}}}",
                f"  title = {{{self._escape_bibtex(title)}}}",
                f"  journal = {{arXiv preprint / PubMed}}",
                f"  year = {{{self._escape_bibtex(year)}}}",
            ]

            if url:
                fields.append(
                    f"  url = {{{self._escape_bibtex(url)}}}"
                )

            entry = (
                f"@article{{{key},\n"
                + ",\n".join(fields)
                + "\n}"
            )

            bib_entries.append(entry)

        return "\n\n".join(bib_entries)

    def save_bibliography(
        self,
        citations: List[Dict[str, Any]],
    ) -> str:
        """Generate and save the BibTeX bibliography."""
        bib_content = self.generate_bibtex(citations)

        bib_path = self.output_dir / "references.bib"
        bib_path.write_text(bib_content, encoding="utf-8")

        return str(bib_path)

