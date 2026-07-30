"""
test_clinical_math.py

Verification script with mock data for clinical_math.py functions.
"""

import numpy as np
import pandas as pd
from clinical_math import calculate_joint_angles, compute_symmetry_index, evaluate_gait_risk


def test_joint_angle_math():
    print("--- Test 1: Joint Angle Vector Math ---")
    # Frame 0: Left side 90 deg, Right side 180 deg (straight leg)
    # Frame 1: Left side 180 deg, Right side 90 deg
    mock_data = {
        "left_hip_x": [0.0, 0.0],
        "left_hip_y": [1.0, 1.0],
        "left_hip_z": [0.0, 0.0],
        "left_knee_x": [0.0, 0.0],
        "left_knee_y": [0.0, 0.0],
        "left_knee_z": [0.0, 0.0],
        "left_ankle_x": [1.0, 0.0],
        "left_ankle_y": [0.0, -1.0],
        "left_ankle_z": [0.0, 0.0],
        "right_hip_x": [0.0, 0.0],
        "right_hip_y": [1.0, 1.0],
        "right_hip_z": [0.0, 0.0],
        "right_knee_x": [0.0, 0.0],
        "right_knee_y": [0.0, 0.0],
        "right_knee_z": [0.0, 0.0],
        "right_ankle_x": [0.0, 1.0],
        "right_ankle_y": [-1.0, 0.0],
        "right_ankle_z": [0.0, 0.0],
    }

    df = pd.DataFrame(mock_data)
    angles = calculate_joint_angles(df)

    print("Calculated Angles:")
    print(angles)

    np.testing.assert_allclose(angles["left_knee_angle"].values, [90.0, 180.0], atol=1e-5)
    np.testing.assert_allclose(angles["right_knee_angle"].values, [180.0, 90.0], atol=1e-5)
    print("PASS: Joint angle calculations match expected geometric values!")


def test_symmetry_index():
    print("\n--- Test 2: Symmetry Index Formula ---")
    left_angles = pd.Series([100.0, 90.0])
    right_angles = pd.Series([80.0, 90.0])

    # Frame 0: |100 - 80| / ((100 + 80)/2) * 100 = 20 / 90 * 100 = 22.2222%
    # Frame 1: |90 - 90| / 90 * 100 = 0%
    si = compute_symmetry_index(left_angles, right_angles)
    print("Calculated SI:")
    print(si)

    expected_si = [22.2222222, 0.0]
    np.testing.assert_allclose(si.values, expected_si, atol=1e-4)
    print("PASS: Symmetry Index formula match expected values!")


def test_evaluate_gait_risk():
    print("\n--- Test 3: Evaluate Gait Risk ---")

    # Case A: Normative Gait (SI = 0%)
    normative_data = pd.DataFrame({
        "left_knee_angle": [90.0, 90.0],
        "right_knee_angle": [90.0, 90.0]
    })
    risk_normative = evaluate_gait_risk(normative_data)
    print("Normative Evaluation Result:", risk_normative)
    assert risk_normative["status"] == "NORMATIVE GAIT"
    assert risk_normative["color"] == "green"

    # Case B: High Asymmetry (Mean SI = (22.22 + 22.22) / 2 = 22.22% > 15%)
    asymmetric_data = pd.DataFrame({
        "left_knee_angle": [100.0, 100.0],
        "right_knee_angle": [80.0, 80.0]
    })
    risk_asymmetric = evaluate_gait_risk(asymmetric_data)
    print("High Asymmetry Evaluation Result:", risk_asymmetric)
    assert risk_asymmetric["status"] == "HIGH ASYMMETRY DETECTED"
    assert risk_asymmetric["color"] == "red"
    assert risk_asymmetric["risk_score"] > 15.0

    print("PASS: Gait risk evaluations returned correct status and risk scores!")


if __name__ == "__main__":
    test_joint_angle_math()
    test_symmetry_index()
    test_evaluate_gait_risk()
    print("\n=== ALL CLINICAL MATH TESTS PASSED SUCCESSFULLY! ===")
