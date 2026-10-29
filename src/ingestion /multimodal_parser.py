
    def extract_loss_trend(
        self,
        data_points: list
    ) -> Dict[str, Any]:
        """Summarize supplied training-step and loss measurements."""
        if len(data_points) < 2:
            return {
                "error": "At least two loss measurements are required."
            }

        try:
            points = sorted(
                [
                    {
                        "step": float(point["step"]),
                        "loss": float(point["loss"])
                    }
                    for point in data_points
                ],
                key=lambda point: point["step"]
            )
        except (KeyError, TypeError, ValueError):
            return {"error": "Each point needs numeric step and loss values."}

        if any(point["loss"] < 0 for point in points):
            return {"error": "Loss values cannot be negative."}

        first_loss = points[0]["loss"]
        last_loss = points[-1]["loss"]

        if first_loss > 0:
            reduction_percent = (
                (first_loss - last_loss) / first_loss
            ) * 100
        else:
            reduction_percent = None

        if last_loss < first_loss:
            trend = "decreasing"
        elif last_loss > first_loss:
            trend = "increasing"
        else:
            trend = "unchanged"

        return {
            "figure_type": "Optimization Curve",
            "data_points": points,
            "initial_loss": first_loss,
            "final_loss": last_loss,
            "loss_reduction_percent": (
                round(reduction_percent, 2)
                if reduction_percent is not None else None
            ),
            "overall_trend": trend,
            "data_origin": "provided_measurements"
        }
