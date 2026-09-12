import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
from pipeline import run_pipeline

from extract import extract_from_report

st.set_page_config(page_title="earKART AI Audiogram Prototype", layout="wide")
st.title("AI-Assisted Audiogram Prototype")
st.caption("Enter thresholds manually to simulate a completed hearing test.")

FREQUENCIES = [500, 1000, 2000, 4000]

st.info(
    "Enter the softest volume (in dB HL) at which the patient could just barely hear each tone. "
    "Lower numbers mean better hearing (0-25 dB HL is normal). Higher numbers mean the sound had "
    "to be louder for the patient to notice it, indicating hearing loss. Typical range: -10 to 120."
)

PRESETS = {
    "Normal hearing": {"ac": {500: 10, 1000: 10, 2000: 15, 4000: 15}, "bc": {500: 5, 1000: 5, 2000: 10, 4000: 10}},
    "Mild sensorineural": {"ac": {500: 20, 1000: 25, 2000: 30, 4000: 35}, "bc": {500: 15, 1000: 20, 2000: 20, 4000: 25}},
    "Conductive loss": {"ac": {500: 45, 1000: 50, 2000: 50, 4000: 55}, "bc": {500: 10, 1000: 10, 2000: 15, 4000: 15}},
    "Severe mixed": {"ac": {500: 75, 1000: 80, 2000: 85, 4000: 90}, "bc": {500: 45, 1000: 50, 2000: 55, 4000: 60}},
}

st.markdown("**Quick fill (optional):**")
preset_cols = st.columns(len(PRESETS))
for i, (name, values) in enumerate(PRESETS.items()):
    if preset_cols[i].button(name):
        for freq in FREQUENCIES:
            st.session_state[f"r_ac_{freq}"] = values["ac"][freq]
            st.session_state[f"r_bc_{freq}"] = values["bc"][freq]
            st.session_state[f"l_ac_{freq}"] = values["ac"][freq]
            st.session_state[f"l_bc_{freq}"] = values["bc"][freq]
        st.rerun()

def threshold_inputs(label, key_prefix, default=25):
    st.subheader(label)
    cols = st.columns(4)
    values = {}
    for i, freq in enumerate(FREQUENCIES):
        values[freq] = cols[i].number_input(
            f"{freq} Hz", min_value=-10, max_value=120,
            value=default, step=5, key=f"{key_prefix}_{freq}",
            help="dB HL - lower is better hearing"
        )
    return values

st.markdown("### Auto-fill from an old report (optional)")
uploaded = st.file_uploader("Upload a report (PDF or image)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded is not None:
    temp_path = f"temp_{uploaded.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded.getbuffer())

    result = extract_from_report(
        temp_path,
        right_bc_template="assets/bc_template_right.png",
        left_bc_template="assets/bc_template_left.png",
    )

    for freq, val in result["right_ac"].items():
        st.session_state[f"r_ac_{freq}"] = val
    for freq, val in result["left_ac"].items():
        st.session_state[f"l_ac_{freq}"] = val
    for freq, val in result["right_bc"].items():
        st.session_state[f"r_bc_{freq}"] = val
    for freq, val in result["left_bc"].items():
        st.session_state[f"l_bc_{freq}"] = val

    st.success("All four series (AC + BC, both ears) auto-filled from the report.")

with st.form("audiogram_form"):
    st.markdown("### Right Ear")
    right_ac = threshold_inputs("Air Conduction (AC)", "r_ac", default=20)
    right_bc = threshold_inputs("Bone Conduction (BC)", "r_bc", default=15)

    st.markdown("### Left Ear")
    left_ac = threshold_inputs("Air Conduction (AC)", "l_ac", default=20)
    left_bc = threshold_inputs("Bone Conduction (BC)", "l_bc", default=15)

    submitted = st.form_submit_button("Generate Audiogram + Report")

if submitted:
    result = run_pipeline(right_ac, right_bc, left_ac, left_bc)

    st.markdown("---")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.pyplot(result["chart"])

    with col2:
        st.subheader("Right Ear")
        st.write(f"PTA: {result['right']['pta']} dB")
        st.write(f"Degree: {result['right']['degree']}")
        st.write(f"Type: {result['right']['type']}")

        st.subheader("Left Ear")
        st.write(f"PTA: {result['left']['pta']} dB")
        st.write(f"Degree: {result['left']['degree']}")
        st.write(f"Type: {result['left']['type']}")

    st.markdown("---")
    st.subheader("Provisional Diagnosis")
    st.write(result["report"]["Provisional Diagnosis"])

    st.subheader("Recommendation")
    st.write(result["report"]["Recommendation"])