from calculations import calculate_pta, classify_degree, classify_type
from chart import plot_audiogram
from report import generate_full_report


def run_pipeline(right_ac, right_bc, left_ac, left_bc):
    """
    Takes raw threshold dicts for both ears (air + bone conduction)
    and returns everything a report needs: chart, diagnosis, recommendation.
    """
    # Step 1: Calculate PTA for each ear/mode
    right_ac_pta = calculate_pta(right_ac)
    right_bc_pta = calculate_pta(right_bc)
    left_ac_pta = calculate_pta(left_ac)
    left_bc_pta = calculate_pta(left_bc)

    # Step 2: Classify degree and type for each ear
    right = {
        "pta": right_ac_pta,
        "degree": classify_degree(right_ac_pta),
        "type": classify_type(right_ac_pta, right_bc_pta),
    }
    left = {
        "pta": left_ac_pta,
        "degree": classify_degree(left_ac_pta),
        "type": classify_type(left_ac_pta, left_bc_pta),
    }

    # Step 3: Generate the chart
    fig = plot_audiogram(right_ac, right_bc, left_ac, left_bc)

    # Step 4: Generate the report text
    report = generate_full_report(right, left)

    return {
        "right": right,
        "left": left,
        "chart": fig,
        "report": report,
    }


if __name__ == "__main__":
    right_ac = {500: 20, 1000: 25, 2000: 30, 4000: 35}
    right_bc = {500: 15, 1000: 20, 2000: 20, 4000: 25}
    left_ac = {500: 45, 1000: 55, 2000: 65, 4000: 75}
    left_bc = {500: 40, 1000: 45, 2000: 50, 4000: 55}

    result = run_pipeline(right_ac, right_bc, left_ac, left_bc)

    print("Right ear:", result["right"])
    print("Left ear:", result["left"])
    print("\nProvisional Diagnosis:", result["report"]["Provisional Diagnosis"])
    print("Recommendation:", result["report"]["Recommendation"])

    import matplotlib.pyplot as plt
    plt.show()