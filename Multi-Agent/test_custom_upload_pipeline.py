"""
test_custom_upload_pipeline.py

Verification script testing custom video workflow end-to-end:
1. Agent 1 Quality Validation on custom file
2. Agent 2 MediaPipe Pose Extraction & 3D Joint Angles (Knee + Hip)
3. Agent 3 Clinical Risk Assessment on custom metrics
4. Agent 4 Dual Custom Video Progress Comparison
"""

import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.main import _process_agent_request, AgentReportRequest
from backend.video_quality_agent import validate_video_quality
from backend.gait_progress_comparison_agent import compare_gait_progress
from backend.agents import analyze_biomechanics
from backend.clinical_risk_agent import assess_clinical_risk
from backend.clinical_math import calculate_joint_angles, evaluate_gait_risk
from cv_engine import extract_pose_data

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

def test_custom_video_agent_pipeline():
    print("--- Test: Custom Video Processing (Agent 1 -> Agent 2 -> Agent 3) ---")
    custom_video = os.path.join(WORKSPACE_DIR, "demo_asymmetric.mp4")
    assert os.path.exists(custom_video), f"Custom video file not found at {custom_video}"

    # 1. Agent 1 Quality Check
    vq_result = validate_video_quality(custom_video)
    print(f"Agent 1 Score: {vq_result.get('video_quality_score')}, Status: {vq_result.get('status')}")
    assert vq_result.get("status") in ["PASS", "WARNING"]

    # 2. Agent 2 Gait Analysis (Pose Extraction & Angles)
    df_pose = extract_pose_data(custom_video)
    assert not df_pose.empty, "Extracted pose DataFrame should not be empty"
    assert "left_knee_x" in df_pose.columns
    assert "left_shoulder_x" in df_pose.columns, "Shoulder keypoints must be extracted for hip angles"

    angles_df = calculate_joint_angles(df_pose)
    assert "left_knee_angle" in angles_df.columns
    assert "left_hip_angle" in angles_df.columns, "Hip angles must be calculated"

    risk_eval = evaluate_gait_risk(df_pose)
    bio_result = analyze_biomechanics(angles_df, risk_eval)
    assert "hip_flexion_rom_deg" in bio_result["metrics"]
    print(f"Agent 2 Knee ROM: L={bio_result['metrics']['left_rom_deg']}°, R={bio_result['metrics']['right_rom_deg']}°")
    print(f"Agent 2 Hip Flexion ROM: {bio_result['metrics']['hip_flexion_rom_deg']}°")

    # 3. Agent 3 Clinical Risk Assessment
    risk_report = assess_clinical_risk(bio_result)
    print(f"Agent 3 Risk Level: {risk_report['risk_level']}, Affected Side: {risk_report['affected_side']}")
    assert risk_report["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert len(risk_report["triggered_measurements"]) > 0

    # 4. Process Request with custom file_path
    req = AgentReportRequest(
        agent_id="clinical-risk",
        file_path=custom_video,
        source_type="custom"
    )
    report_resp = _process_agent_request("clinical-risk", req)
    assert report_resp["agent_id"] == "clinical-risk"
    assert report_resp["clinical_risk"]["risk_level"] == risk_report["risk_level"]
    print("PASS: Custom video successfully processed through Agent 1 -> Agent 2 -> Agent 3!")


def test_custom_video_comparison():
    print("\n--- Test: Custom Video Dual Comparison (Agent 4) ---")
    video_old = os.path.join(WORKSPACE_DIR, "demo_asymmetric.mp4")
    video_new = os.path.join(WORKSPACE_DIR, "demo_normative.mp4")

    df_old = extract_pose_data(video_old)
    angles_old = calculate_joint_angles(df_old)
    bio_old = analyze_biomechanics(angles_old, evaluate_gait_risk(df_old))
    risk_old = assess_clinical_risk(bio_old)

    df_new = extract_pose_data(video_new)
    angles_new = calculate_joint_angles(df_new)
    bio_new = analyze_biomechanics(angles_new, evaluate_gait_risk(df_new))
    risk_new = assess_clinical_risk(bio_new)

    comp_res = compare_gait_progress(
        old_gait_result=bio_old,
        new_gait_result=bio_new,
        old_risk_result=risk_old,
        new_risk_result=risk_new,
        old_file_name="Old_Custom_Video.mp4",
        new_file_name="New_Custom_Video.mp4"
    )

    print(f"Agent 4 Progress Classification: {comp_res['overall_progress']}")
    print(f"Key Findings: {comp_res['key_findings']}")
    assert comp_res["overall_progress"] in ["IMPROVED", "STABLE", "WORSENED"]
    print("PASS: Agent 4 dual custom video progress comparison succeeded!")

if __name__ == "__main__":
    test_custom_video_agent_pipeline()
    test_custom_video_comparison()
    print("\n=== ALL CUSTOM UPLOAD PIPELINE TESTS PASSED CLEANLY! ===")
