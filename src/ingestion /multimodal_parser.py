
    def synthesize_visual_chunks(
        self,
        figures: list,
        paper_metadata: Dict[str, Any] = None
    ) -> list:
        """Convert extracted figure evidence into searchable text chunks."""
        paper_metadata = paper_metadata or {}
        chunks = []

        for index, figure in enumerate(figures, start=1):
            figure_id = figure.get("figure_id", f"Fig_{index}")
            caption = figure.get("caption", "")
            figure_type = figure.get("type", figure.get("figure_type", "Unknown"))
            interpretation = figure.get("interpretation", "")
            summary = figure.get("quantitative_summary", "")

            data_points = figure.get(
                "key_data_points",
                figure.get("data_points", [])
            )

            if not any([caption, interpretation, summary, data_points]):
                continue

            point_text = "; ".join(
                str(point) for point in data_points
            )

            text = (
                f"Figure ID: {figure_id}\n"
                f"Figure type: {figure_type}\n"
                f"Caption: {caption}\n"
                f"Interpretation: {interpretation}\n"
                f"Quantitative summary: {summary}\n"
                f"Data points: {point_text}"
            )

            chunks.append({
                "id": (
                    f"{paper_metadata.get('id', 'unknown_paper')}"
                    f"_{figure_id}"
                ),
                "text": text,
                "metadata": {
                    **paper_metadata,
                    "figure_id": figure_id,
                    "figure_type": figure_type,
                    "caption": caption,
                    "content_type": "visual_evidence"
                }
            })

        return chunks
