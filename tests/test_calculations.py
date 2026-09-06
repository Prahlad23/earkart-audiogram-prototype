import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from calculations import calculate_pta, classify_degree, classify_type


def test_pta_calculation():
    thresholds = {500: 20, 1000: 20, 2000: 20, 4000: 20}
    assert calculate_pta(thresholds) == 20


def test_degree_normal():
    assert classify_degree(10) == "Normal"


def test_degree_mild():
    assert classify_degree(30) == "Mild"


def test_degree_moderate():
    assert classify_degree(50) == "Moderate"


def test_degree_severe():
    assert classify_degree(70) == "Severe"


def test_degree_profound():
    assert classify_degree(90) == "Profound"


def test_type_normal():
    assert classify_type(ac_pta=15, bc_pta=10) == "Normal"


def test_type_sensorineural():
    assert classify_type(ac_pta=40, bc_pta=35) == "Sensorineural"


def test_type_conductive():
    assert classify_type(ac_pta=45, bc_pta=15) == "Conductive"


def test_type_mixed():
    assert classify_type(ac_pta=60, bc_pta=35) == "Mixed"


def test_asymmetric_case_right_worse():
    # Right ear much worse than left — checks each ear is judged independently
    right_pta = 75
    left_pta = 15
    assert classify_degree(right_pta) == "Severe"
    assert classify_degree(left_pta) == "Normal"