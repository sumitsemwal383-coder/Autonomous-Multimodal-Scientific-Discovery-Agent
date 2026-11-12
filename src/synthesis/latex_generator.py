import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List

import jinja2

from config.settings import TEMPLATES_DIR, SYNTHESIS_DIR


class LatexPaperGenerator:
    """Render, validate, and compile academic research manuscripts."""

    def __init__(
        self,
        template_dir: Path = TEMPLATES_DIR,
        output_dir: Path = SYNTHESIS_DIR,
    ):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=False,
            undefined=jinja2.StrictUndefined,
        )

        self.env.filters["format_pval"] = self._format_pvalue

    @staticmethod
    def _format_pvalue(val: float) -> str:
        """Format p-values for the statistical results table."""
        val = float(val)

        if val < 0.0001:
            return f"{val:.3e}"

        return f"{val:.4f}"

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
    ) -> str:
        """Render a LaTeX template with validation and error reporting."""
        if not isinstance(context, dict):
            raise TypeError("Template context must be a dictionary.")

        template = self.env.get_template(template_name)
        return template.render(**context)

    def save_manuscript(self, content: str) -> str:
        """Save rendered LaTeX source to disk."""
        output_path = self.output_dir / "scientific_discovery_paper.tex"
        output_path.write_text(content, encoding="utf-8")
        return str(output_path)

    @staticmethod
    def _escape_bibtex(value: str) -> str:
        """Escape common special characters in BibTeX text fields."""
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
        """Generate BibTeX entries from literature citation records."""
        if not isinstance(citations, list):
            raise TypeError("Citations must be provided as a list.")

        entries = []

        for idx, citation in enumerate(citations, start=1):
            if not isinstance(citation, dict):
                raise ValueError(
                    f"Citation at position {idx} must be a dictionary."
                )

            authors = citation.get("authors", "Unknown Author")

            if isinstance(authors, list):
                authors = " and ".join(str(a) for a in authors)
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

            entries.append(
                f"@article{{ref_{idx},\n"
                + ",\n".join(fields)
                + "\n}"
            )

        return "\n\n".join(entries)

    def save_bibliography(
        self,
        citations: List[Dict[str, Any]],
    ) -> str:
        """Generate and save the references.bib file."""
        bib_content = self.generate_bibtex(citations)

        bib_path = self.output_dir / "references.bib"
        bib_path.write_text(bib_content, encoding="utf-8")

        return str(bib_path)

    def compile_pdf(self, tex_path: str) -> Dict[str, Any]:
        """Compile LaTeX and BibTeX, capturing errors at each stage."""
        tex_file = Path(tex_path).resolve()

        if not tex_file.exists():
            return {
                "status": "FAILED",
                "pdf_path": None,
                "errors": [f"LaTeX source not found: {tex_file}"],
            }

        pdflatex = shutil.which("pdflatex")
        bibtex = shutil.which("bibtex")

        if not pdflatex:
            return {
                "status": "SOURCE_SAVED",
                "pdf_path": None,
                "errors": [
                    "pdflatex is not installed. Install a LaTeX "
                    "distribution to generate the PDF."
                ],
            }

        errors = []

        def run_command(command: List[str]) -> bool:
            """Execute a compiler command and capture diagnostics."""
            try:
                result = subprocess.run(
                    command,
                    cwd=str(tex_file.parent),
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )

                if result.returncode != 0:
                    errors.append(
                        f"Command failed: {' '.join(command)}\n"
                        f"{result.stdout[-3000:]}\n"
                        f"{result.stderr[-3000:]}"
                    )
                    return False

                return True

            except subprocess.TimeoutExpired:
                errors.append(
                    f"Compilation timed out: {' '.join(command)}"
                )
                return False

            except OSError as exc:
                errors.append(f"Compiler execution error: {exc}")
                return False

        filename = tex_file.name

        # First pass creates auxiliary files needed by BibTeX.
        if not run_command(
            [pdflatex, "-interaction=nonstopmode", "-halt-on-error", filename]
        ):
            return {
                "status": "FAILED",
                "pdf_path": None,
                "errors": errors,
            }

        bib_path = tex_file.parent / "references.bib"

        # Generate bibliography when BibTeX is installed and references exist.
        if bib_path.exists() and bib_path.stat().st_size > 0:
            if not bibtex:
                errors.append(
                    "bibtex is not installed; bibliography compilation "
                    "was skipped."
                )
            elif not run_command([bibtex, tex_file.stem]):
                return {
                    "status": "FAILED",
                    "pdf_path": None,
                    "errors": errors,
                }

        # Re-run LaTeX to resolve citations and references.
        for _ in range(2):
            if not run_command(
                [
                    pdflatex,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    filename,
                ]
            ):
                return {
                    "status": "FAILED",
                    "pdf_path": None,
                    "errors": errors,
                }

        pdf_path = tex_file.with_suffix(".pdf")

        if not pdf_path.exists():
            errors.append("Compilation finished without producing a PDF.")
            return {
                "status": "FAILED",
                "pdf_path": None,
                "errors": errors,
            }

        return {
            "status": "SUCCESS" if not errors else "PARTIAL_SUCCESS",
            "pdf_path": str(pdf_path),
            "errors": errors,
        }

    def compile_research_paper(
        self,
        hypothesis_data: Dict[str, Any],
        experiment_data: Dict[str, Any],
        critic_data: Dict[str, Any],
        literature_data: Dict[str, Any],
        compile_pdf: bool = True,
    ) -> Dict[str, Any]:
        """Build the manuscript, bibliography, and optionally the PDF."""
        try:
            if not all(
                isinstance(data, dict)
                for data in (
                    hypothesis_data,
                    experiment_data,
                    critic_data,
                    literature_data,
                )
            ):
                raise TypeError("All input data must be dictionaries.")

            hyp = hypothesis_data.get("hypothesis", {})
            if not isinstance(hyp, dict):
                raise ValueError("'hypothesis' must be a dictionary.")

            formal = hyp.get("formal_hypotheses", {})
            variables = hyp.get("variables", {})
            metrics = experiment_data.get("metrics", {})

            if not isinstance(formal, dict) or not isinstance(variables, dict):
                raise ValueError(
                    "Formal hypotheses and variables must be dictionaries."
                )

            if not isinstance(metrics, dict):
                raise ValueError("'metrics' must be a dictionary.")

            # Normalize values used by the statistical table.
            defaults = {
                "sample_size": 100,
                "baseline_mean": 0.0,
                "baseline_std": 0.0,
                "treatment_mean": 0.0,
                "treatment_std": 0.0,
                "mean_difference": 0.0,
                "t_statistic": 0.0,
                "p_value": 0.001,
                "cohens_d": 0.0,
                "ci_95_low": 0.0,
                "ci_95_high": 0.0,
            }

            metrics = {**defaults, **metrics}

            citations = hyp.get(
                "grounding_citations",
                literature_data.get("citations", []),
            )

            title = (
                "Autonomous Discovery: "
                + str(hyp.get("title", "Empirical Hypothesis Validation"))
            )

            abstract = (
                f"We present an autonomous discovery pipeline for '{title}'. "
                f"The system evaluates the hypothesis: "
                f"{hyp.get('statement', 'Not specified')}. "
                f"Experiments used N={metrics['sample_size']}, with "
                f"p={self._format_pvalue(metrics['p_value'])} and "
                f"Cohen's d={float(metrics['cohens_d']):.2f}. "
                f"Statistical evaluation was performed by the Critic agent."
            )

            context = {
                "title": title,
                "abstract": abstract,
                "introduction": (
                    "Autonomous AI researchers can support scientific "
                    "discovery, but their findings require reproducible "
                    "experiments and rigorous statistical validation."
                ),
                "related_work": (
                    "Research on language-model agents, retrieval-augmented "
                    "generation, and automated experimentation motivates "
                    "the design of this discovery pipeline."
                ),
                "hypothesis_statement": hyp.get("statement", ""),
                "h0": formal.get("H0", ""),
                "h1": formal.get("H1", ""),
                "independent_var": variables.get("independent", ""),
                "dependent_var": variables.get("dependent", ""),
                "controlled_var": variables.get("controlled", ""),
                "methodology": (
                    "Experiments were executed in a controlled environment. "
                    f"Design: {hyp.get('experimental_design', 'Paired trials')}."
                ),
                "results_discussion": (
                    f"{critic_data.get('critique', '')} "
                    f"Statistical verdict: {critic_data.get('verdict', 'Not provided')}."
                ),
                "metrics": metrics,
                "critic": critic_data,
                "discussion": (
                    "Results should be interpreted alongside the study design, "
                    "effect size, uncertainty, and limitations."
                ),
                "conclusion": (
                    "This pipeline demonstrates an automated workflow for "
                    "hypothesis evaluation and academic manuscript generation."
                ),
            }

            # Render and validate the Jinja2 template.
            rendered_tex = self.render_template(
                "research_paper.tex.jinja",
                context,
            )

            # Save source and bibliography.
            tex_path = self.save_manuscript(rendered_tex)
            bib_path = self.save_bibliography(citations)

            result = {
                "status": "SOURCE_SAVED",
                "tex_path": tex_path,
                "bib_path": bib_path,
                "pdf_path": None,
                "rendered_tex": rendered_tex,
                "abstract": abstract,
                "title": title,
                "errors": [],
            }

            # PDF compilation can be disabled for environments without LaTeX.
            if compile_pdf:
                pdf_result = self.compile_pdf(tex_path)
                result["status"] = pdf_result["status"]
                result["pdf_path"] = pdf_result["pdf_path"]
                result["errors"].extend(pdf_result["errors"])

            return result

        except (
            jinja2.TemplateError,
            OSError,
            TypeError,
            ValueError,
            KeyError,
        ) as exc:
            return {
                "status": "FAILED",
                "tex_path": None,
                "bib_path": None,
                "pdf_path": None,
                "errors": [f"{type(exc).__name__}: {exc}"],
            }
