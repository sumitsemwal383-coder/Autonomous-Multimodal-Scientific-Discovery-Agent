
    def parse_comparative_chart(
        self,
        data_points: list
    ) -> Dict[str, Any]:
        """Validate comparative measurements and confidence intervals."""
        if not data_points:
            return {"error": "No chart measurements provided."}

        validated = []

        try:
            for point in data_points:
                label = str(point["label"]).strip()
                value = float(point["value"])

                if not label:
                    return {"error": "Every data point needs a label."}

                item = {"label": label, "value": value}

                low = point.get("ci_low")
                high = point.get("ci_high")

                if (low is None) != (high is None):
                    return {
                        "error": f"Incomplete confidence bounds for {label}."
                    }

                if low is not None:
                    low = float(low)
                    high = float(high)

                    if low > high:
                        return {
                            "error": f"Invalid confidence bounds for {label}."
                        }

                    if not low <= value <= high:
                        return {
                            "error": (
                                f"Value for {label} falls outside "
                                "its supplied confidence bounds."
                            )
                        }

                    item["ci_low"] = low
                    item["ci_high"] = high

                validated.append(item)

        except (KeyError, TypeError, ValueError):
            return {
                "error": "Each chart point needs a label and numeric value."
            }

        best = max(validated, key=lambda item: item["value"])

        return {
            "figure_type": "Comparative Bar Chart",
            "key_data_points": validated,
            "highest_value_method": best["label"],
            "highest_value": best["value"],
            "data_origin": "provided_measurements"
        }
