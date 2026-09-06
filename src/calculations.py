def calculate_pta(thresholds: dict) -> float:
    """
    thresholds: a dictionary like {500: 20, 1000: 25, 2000: 30, 4000: 35}
    Each key is a frequency in Hz, each value is the dB level
    the patient could just barely hear at that frequency.

    Returns the Pure Tone Average (PTA) — the standard summary number
    used to describe overall hearing at these 4 key frequencies.
    """
    key_frequencies = [500, 1000, 2000, 4000]
    values = [thresholds[freq] for freq in key_frequencies]
    return sum(values) / len(values)


def classify_degree(pta: float) -> str:
    """
    Takes a PTA number and returns the WHO-standard hearing loss category.
    """
    if pta <= 25:
        return "Normal"
    elif pta <= 40:
        return "Mild"
    elif pta <= 60:
        return "Moderate"
    elif pta <= 80:
        return "Severe"
    else:
        return "Profound"

def calculate_air_bone_gap(ac_pta: float, bc_pta: float) -> float:
    """
    Returns the gap between air conduction and bone conduction PTA.
    """
    return ac_pta - bc_pta


def classify_type(ac_pta: float, bc_pta: float, gap_threshold: float = 10) -> str:
    """
    Classifies the type of hearing loss based on AC and BC PTA values.
    """
    ac_normal = ac_pta <= 25
    bc_normal = bc_pta <= 25
    gap = calculate_air_bone_gap(ac_pta, bc_pta)

    if ac_normal:
        return "Normal"
    elif gap >= gap_threshold:
        return "Conductive" if bc_normal else "Mixed"
    else:
        return "Sensorineural"

if __name__ == "__main__":
    ac_sample = {500: 20, 1000: 25, 2000: 30, 4000: 35}
    bc_sample = {500: 15, 1000: 20, 2000: 20, 4000: 25}

    ac_pta = calculate_pta(ac_sample)
    bc_pta = calculate_pta(bc_sample)

    print("AC PTA:", ac_pta)
    print("BC PTA:", bc_pta)
    print("Degree:", classify_degree(ac_pta))
    print("Type:", classify_type(ac_pta, bc_pta))