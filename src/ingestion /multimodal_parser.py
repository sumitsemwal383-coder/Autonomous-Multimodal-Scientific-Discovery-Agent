import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MultimodalParser:
    def __init__(self, vision_model: str = "heuristic_vlm"):
        self.vision_model = vision_model

    def parse_figure(self, image_path: Path) -> Dict[str, Any]:
        """Classify a figure using basic filename heuristics."""
        image_path = Path(image_path)

        if not image_path.is_file():
            return {"error": f"Figure file not found: {image_path}"}

        supported_extensions = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}

        if image_path.suffix.lower() not in supported_extensions:
            return {"error": "Unsupported image format"}

        filename = image_path.stem.lower()

        if any(word in filename for word in ("ablation", "bar", "comparison")):
            figure_type = "Comparative Bar Chart"
        elif any(word in filename for word in ("loss", "convergence", "training")):
            figure_type = "Optimization Curve"
        elif any(word in filename for word in ("architecture", "workflow", "diagram")):
            figure_type = "Architecture Diagram"
        else:
            figure_type = "Unknown Figure"

        return {
            "figure_id": image_path.stem,
            "image_path": str(image_path),
            "figure_type": figure_type,
            "classifier": "filename_heuristic",
            "requires_visual_analysis": True
        }
