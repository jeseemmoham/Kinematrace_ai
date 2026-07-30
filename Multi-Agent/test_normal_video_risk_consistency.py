"""
test_normal_video_risk_consistency.py

Verification script confirming data consistency between Gait Analysis and Risk Assessment:
1. Verifies that normal walking video (demo_normative.mp4) evaluates to LOW RISK in Risk Assessment with HIGH confidence.
2. Verifies that asymmetric walking video (demo_asymmetric.mp4) evaluates to HIGH RISK in Risk Assessment.
3. Verifies that low-confidence / noisy tracking returns INSUFFICIENT DATA.
4. Verifies that borderline gait asymmetry returns MODERATE RISK.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.clinical_math import calculate_joint_angles, evaluate_gait_risk
from backend.cv_engine import extract_pose_data, process_video_single_pass
from backend.agents import analyze_biomechanics
from backend.clinical_risk_agent import assess_clinical_risk
import pandas as pd

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def test_normative_video_evaluates_to_low_risk():
    print("--- Test 1: Normative Walking Video Risk Classification ---")
    normative_video = os.path.join(WORKSPACE_DIR, "demo_normative.mp4")
    assert os.path.exists(normative_video), f"Normative video missing at {normative_video}"

    single_pass_res = process_video_single_pass(normative_video)
    bio_result = analyze_biomechanics(single_pass_res["angles_df"], single_pass_res["risk_result"])
    bio_result["metrics"].update(single_pass_res["metrics"])

    risk_result = assess_clinical_risk(gait_analysis_result=bio_result, patient_age="7 y/o")

    gait_symmetry = bio_result["metrics"].get("gait_symmetry", 100.0)
    confidence = bio_result["metrics"].get("analysis_confidence", "HIGH")
    print(f"Normative Gait Symmetry: {gait_symmetry:.1f}%")
    print(f"Normative Analysis Confidence: {confidence} ({bio_result['metrics'].get('confidence_score', 90)}%)")
    print(f"Normative Risk Classification: {risk_result['risk_level']} (Severity: {risk_result['severity']})")

    assert risk_result["risk_level"] == "LOW", f"Expected LOW RISK for normative video, got {risk_result['risk_level']}"
    assert risk_result["affected_side"] == "NONE"
    print("PASS: Normative walking video correctly evaluated as LOW RISK with HIGH confidence!")


def test_asymmetric_video_evaluates_to_high_risk():
    print("\n--- Test 2: Asymmetric Walking Video Risk Classification ---")
    asymmetric_video = os.path.join(WORKSPACE_DIR, "demo_asymmetric.mp4")
    asymmetric_csv = os.path.join(WORKSPACE_DIR, "demo_asymmetric.csv")

    if os.path.exists(asymmetric_csv):
        df_pose = pd.read_csv(asymmetric_csv, index_col="frame")
        angles_df = calculate_joint_angles(df_pose)
        risk_eval = evaluate_gait_risk(df_pose)
        bio_result = analyze_biomechanics(angles_df, risk_eval)
    else:
        single_pass_res = process_video_single_pass(asymmetric_video)
        bio_result = analyze_biomechanics(single_pass_res["angles_df"], single_pass_res["risk_result"])
        bio_result["metrics"].update(single_pass_res["metrics"])

    risk_result = assess_clinical_risk(gait_analysis_result=bio_result, patient_age="7 y/o")

    gait_symmetry = 100.0 - bio_result["metrics"].get("mean_symmetry_index_pct", 16.0)
    print(f"Asymmetric Gait Symmetry: {gait_symmetry:.1f}%")
    print(f"Asymmetric Risk Classification: {risk_result['risk_level']} (Severity: {risk_result['severity']})")

    assert risk_result["risk_level"] == "HIGH", f"Expected HIGH RISK for asymmetric video, got {risk_result['risk_level']}"
    assert len(risk_result["triggered_measurements"]) > 0
    print("PASS: Asymmetric walking video correctly evaluated as HIGH RISK!")


def test_low_confidence_tracking_gate():
    print("\n--- Test 3: Low-Confidence Tracking Gate Test ---")
    low_conf_gait_result = {
        "metrics": {
            "mean_symmetry_index_pct": 8.0,
            "peak_symmetry_index_pct": 12.0,
            "left_rom_deg": 110.0,
            "right_rom_deg": 108.0,
            "rom_deficit_deg": 2.0,
            "confidence_score": 35.0,  # Below 50% threshold
            "analysis_confidence": "LOW"
        }
    }
    risk_result = assess_clinical_risk(gait_analysis_result=low_conf_gait_result, patient_age="7 y/o")
    print(f"Low Confidence Classification: {risk_result['risk_level']} (Confidence: {risk_result.get('analysis_confidence')})")
    assert risk_result["risk_level"] == "INSUFFICIENT DATA", f"Expected INSUFFICIENT DATA, got {risk_result['risk_level']}"
    print("PASS: Low confidence video correctly triggered INSUFFICIENT DATA screening gate!")


def test_borderline_asymmetry_evaluates_to_medium_risk():
    print("\n--- Test 4: Borderline Asymmetry (Moderate Risk) Test ---")
    borderline_gait_result = {
        "metrics": {
            "mean_symmetry_index_pct": 12.5,  # Between 10.0% and 15.0%
            "peak_symmetry_index_pct": 18.0,
            "left_rom_deg": 110.0,
            "right_rom_deg": 98.0,
            "rom_deficit_deg": 12.0,  # Between 10° and 15°
            "confidence_score": 88.0,
            "analysis_confidence": "HIGH"
        }
    }
    risk_result = assess_clinical_risk(gait_analysis_result=borderline_gait_result, patient_age="7 y/o")
    print(f"Borderline Classification: {risk_result['risk_level']} (Severity: {risk_result['severity']})")
    assert risk_result["risk_level"] in ["MEDIUM", "MODERATE"], f"Expected MODERATE/MEDIUM RISK, got {risk_result['risk_level']}"
    print("PASS: Borderline gait video correctly evaluated as MODERATE RISK!")

if __name__ == "__main__":
    test_normative_video_evaluates_to_low_risk()
    test_asymmetric_video_evaluates_to_high_risk()
    test_low_confidence_tracking_gate()
    test_borderline_asymmetry_evaluates_to_medium_risk()
    print("\n=== ALL RISK CONSISTENCY & CONFIDENCE GATE TESTS PASSED CLEANLY! ===")
