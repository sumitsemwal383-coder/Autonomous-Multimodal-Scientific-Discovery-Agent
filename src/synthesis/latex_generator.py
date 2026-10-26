from pathlib import Path
from typing import Dict, Any

import jinja2

from config.settings import TEMPLATES_DIR, SYNTHESIS_DIR


class LatexPaperGenerator:
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
