def generate_diagnosis(degree: str, hearing_type: str, ear: str) -> str:
    """
    Builds one sentence describing the diagnosis for a single ear.
    """
    if degree == "Normal":
        return f"{ear} ear: Hearing within normal limits."
    return f"{ear} ear: {degree} degree {hearing_type.lower()} hearing loss."


def generate_recommendation(degree: str, hearing_type: str) -> str:
    """
    Picks a generic, safe recommendation based on degree + type.
    These are intentionally generic — the audiologist will review and finalize.
    """
    if degree == "Normal":
        return "No intervention required. Routine monitoring advised."

    if hearing_type == "Conductive":
        return "ENT evaluation recommended to assess middle ear pathology."

    if hearing_type == "Mixed":
        return "ENT evaluation and hearing aid assessment recommended."

    # Sensorineural
    if degree in ["Mild", "Moderate"]:
        return "Hearing aid evaluation recommended."
    else:  # Severe or Profound
        return "Comprehensive audiological evaluation and hearing aid/cochlear implant assessment recommended."


def generate_full_report(right, left) -> dict:
    diagnosis_lines = [
        generate_diagnosis(right["degree"], right["type"], "Right"),
        generate_diagnosis(left["degree"], left["type"], "Left"),
    ]

    right_rec = generate_recommendation(right["degree"], right["type"])
    left_rec = generate_recommendation(left["degree"], left["type"])

    if right_rec == left_rec:
        recommendation_text = right_rec
    else:
        recommendation_text = f"Right ear: {right_rec} Left ear: {left_rec}"

    return {
        "Provisional Diagnosis": " ".join(diagnosis_lines),
        "Recommendation": recommendation_text,
    }


if __name__ == "__main__":
    right = {"pta": 27.5, "degree": "Mild", "type": "Sensorineural"}
    left = {"pta": 60.0, "degree": "Moderate", "type": "Mixed"}

    report = generate_full_report(right, left)
    for section, text in report.items():
        print(f"{section}: {text}")