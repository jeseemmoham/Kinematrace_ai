"""
test_master_multiagent_workflow.py

KinemaTrace AI — Master Multi-Agent Workflow, Data Consistency & Integration Test Suite.
Executes all 8 mandatory clinical system test scenarios:
1. TEST 1: Normal Custom Video -> Low Risk (No contradiction)
2. TEST 2: Abnormal Custom Video -> High/Medium Risk (Exact triggered risk factors)
3. TEST 3: Video Quality Failure -> FAIL blocks downstream analysis
4. TEST 4: Old vs New Video Comparison -> Agent 4 side-by-side analysis (IMPROVED/STABLE/WORSENED)
5. TEST 5: Chatbot Progression -> Reads stored Old & New results (No "I don't have the old video")
6. TEST 6: Chatbot PDF Report -> Generates downloadable PDF report
7. TEST 7: Patient Data Isolation -> Patient A vs Patient B separation
8. TEST 8: Demo Case Isolation -> Demo case vs Custom video isolation
"""

import os
import sys
from typing import Dict, Any, Union, Optional
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

import pandas as pd
from fastapi.testclient import TestClient
from backend.main import app
from backend.video_quality_agent import validate_video_quality
from backend.clinical_math import calculate_joint_angles, evaluate_gait_risk
from backend.cv_engine import extract_pose_data
from backend.agents import (
    analyze_biomechanics,
    assess_clinical_risk,
    compare_gait_progress,
    process_clinical_assistant_query,
    process_empathetic_translator,
)
from backend.pdf_generator import generate_clinical_pdf_report

client = TestClient(app)
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
def clean_str(obj: Any) -> str:
    s = str(obj)
    return (
        s.replace("≥", ">=")
        .replace("≤", "<=")
        .replace("°", " deg")
        .replace("—", "-")
        .replace("→", "->")
        .replace("✓", "PASS")
        .encode("ascii", "replace")
        .decode("ascii")
    )


def test_1_normal_custom_video():
    print("\n========================================================")
    print("TEST 1 -- NORMAL CUSTOM VIDEO")
    print("========================================================")
    normative_video = os.path.join(WORKSPACE_DIR, "demo_normative.mp4")
    normative_csv = os.path.join(WORKSPACE_DIR, "demo_normative.csv")
    assert os.path.exists(normative_video), f"Missing {normative_video}"

    # Agent 1 Validation
    quality = validate_video_quality(normative_video)
    print(clean_str(f"Agent 1 Status: {quality['status']} (Score: {quality.get('video_quality_score')}/100)"))
    assert quality["status"] in ["PASS", "WARNING"]

    # Agent 2 Gait Analysis
    df_pose = pd.read_csv(normative_csv, index_col="frame") if os.path.exists(normative_csv) else extract_pose_data(normative_video)
    angles_df = calculate_joint_angles(df_pose)
    risk_eval = evaluate_gait_risk(df_pose)
    bio_result = analyze_biomechanics(angles_df, risk_eval)
    metrics = bio_result["metrics"]

    print(clean_str(f"Agent 2 Gait Symmetry: {100.0 - metrics['mean_symmetry_index_pct']:.1f}%"))
    print(clean_str(f"Agent 2 Left Knee ROM: {metrics['left_rom_deg']:.1f}°, Right Knee ROM: {metrics['right_rom_deg']:.1f}°"))

    # Agent 3 Risk Assessment
    risk_result = assess_clinical_risk(gait_analysis_result=bio_result)
    print(clean_str(f"Agent 3 Risk Level: {risk_result['risk_level']} (Severity: {risk_result['severity']})"))

    # Assertions
    assert risk_result["risk_level"] == "LOW", f"Expected LOW RISK, got {risk_result['risk_level']}"
    assert risk_result["affected_side"] == "NONE"
    print("PASS: Normal video evaluated as LOW RISK with clean data consistency!")


def test_2_abnormal_custom_video():
    print("\n========================================================")
    print("TEST 2 -- ABNORMAL CUSTOM VIDEO")
    print("========================================================")
    asymmetric_video = os.path.join(WORKSPACE_DIR, "demo_asymmetric.mp4")
    asymmetric_csv = os.path.join(WORKSPACE_DIR, "demo_asymmetric.csv")
    assert os.path.exists(asymmetric_video), f"Missing {asymmetric_video}"

    quality = validate_video_quality(asymmetric_video)
    assert quality["status"] in ["PASS", "WARNING"]

    df_pose = pd.read_csv(asymmetric_csv, index_col="frame") if os.path.exists(asymmetric_csv) else extract_pose_data(asymmetric_video)
    angles_df = calculate_joint_angles(df_pose)
    risk_eval = evaluate_gait_risk(df_pose)
    bio_result = analyze_biomechanics(angles_df, risk_eval)

    risk_result = assess_clinical_risk(gait_analysis_result=bio_result)
    print(clean_str(f"Agent 2 Asymmetry: {bio_result['metrics']['mean_symmetry_index_pct']:.1f}%"))
    print(clean_str(f"Agent 3 Risk Level: {risk_result['risk_level']} (Triggered: {risk_result['triggered_measurements']})"))

    assert risk_result["risk_level"] in ["HIGH", "MEDIUM"]
    assert len(risk_result["triggered_measurements"]) > 0
    print("PASS: Asymmetric video correctly triggered HIGH/MEDIUM risk with specific risk factors!")


def test_3_video_quality_failure():
    print("\n========================================================")
    print("TEST 3 -- VIDEO QUALITY FAILURE")
    print("========================================================")
    invalid_video_path = os.path.join(WORKSPACE_DIR, "invalid_corrupt_test_file.mp4")
    with open(invalid_video_path, "wb") as f:
        f.write(b"not a real video file content")

    quality = validate_video_quality(invalid_video_path)
    print(clean_str(f"Agent 1 Status for Invalid Video: {quality['status']} (Issues: {quality.get('issues')})"))

    if os.path.exists(invalid_video_path):
        os.remove(invalid_video_path)

    assert quality["status"] == "FAIL"
    assert len(quality.get("issues", [])) > 0
    print("PASS: Poor quality video returned FAIL and prevented unreliable gait analysis!")


def test_4_old_vs_new_video_comparison():
    print("\n========================================================")
    print("TEST 4 -- OLD VS NEW VIDEO COMPARISON (AGENT 4)")
    print("========================================================")
    asymmetric_csv = os.path.join(WORKSPACE_DIR, "demo_asymmetric.csv")
    normative_csv = os.path.join(WORKSPACE_DIR, "demo_normative.csv")

    df_old = pd.read_csv(asymmetric_csv, index_col="frame")
    df_new = pd.read_csv(normative_csv, index_col="frame")

    bio_old = analyze_biomechanics(calculate_joint_angles(df_old), evaluate_gait_risk(df_old))
    bio_new = analyze_biomechanics(calculate_joint_angles(df_new), evaluate_gait_risk(df_new))

    risk_old = assess_clinical_risk(bio_old)
    risk_new = assess_clinical_risk(bio_new)

    quality_stub = {"status": "PASS", "video_quality_score": 95}

    comp = compare_gait_progress(
        old_gait_result=bio_old,
        new_gait_result=bio_new,
        old_risk_result=risk_old,
        new_risk_result=risk_new,
        old_quality_result=quality_stub,
        new_quality_result=quality_stub,
        old_file_name="demo_asymmetric.mp4",
        new_file_name="demo_normative.mp4"
    )

    print(clean_str(f"Agent 4 Progress Classification: {comp['overall_progress']}"))
    print(clean_str(f"Agent 4 Key Findings: {comp['key_findings']}"))

    assert comp["overall_progress"] == "IMPROVED"
    assert "old_video" in comp
    assert "new_video" in comp
    print("PASS: Agent 4 compared OLD vs NEW side-by-side and correctly classified IMPROVED!")
    return comp


def test_5_chatbot_progression(comp_data):
    print("\n========================================================")
    print("TEST 5 -- CHATBOT PROGRESSION (AGENT 5)")
    print("========================================================")
    context = {
        "patient_id": "KT-2026-P902",
        "has_two_videos": True,
        "old_video": comp_data["old_video"],
        "new_video": comp_data["new_video"],
        "comparison": comp_data["comparison"],
        "patient_progress": comp_data
    }

    res = process_clinical_assistant_query("Has the patient improved?", context)
    text = res["response"]
    print(clean_str("Agent 5 Chatbot Response:\n" + text[:300] + "..."))

    assert "IMPROVED" in text
    assert "I don't have the old video" not in text
    assert "Gait Symmetry:" in text
    print("PASS: Agent 5 chatbot successfully read Agent 4 stored OLD and NEW results!")


def test_6_chatbot_pdf_report(comp_data):
    print("\n========================================================")
    print("TEST 6 -- CHATBOT REPORT & PDF GENERATION")
    print("========================================================")
    context = {
        "patient_id": "KT-2026-P902",
        "patient_info": {"id": "KT-2026-P902", "age": "7 y/o", "case": "Outpatient Gait Tracking"},
        "patient_progress": comp_data
    }

    res = process_clinical_assistant_query("Generate a full clinical report", context)
    text = res["response"]
    print(clean_str("Agent 5 Report Generation Response:\n" + text[:350] + "..."))

    assert "CLINICAL EKG & GAIT KINEMATIC E-REPORT" in text or "GAIT KINEMATIC" in text
    assert "Download PDF Report" in text or "generate-pdf" in text

    # HTTP API Endpoint Check
    pdf_res = client.get("/api/generate-pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000
    print(clean_str(f"Generated PDF Size: {len(pdf_res.content)} bytes"))
    print("PASS: Downloadable PDF report successfully generated from backend API!")


def test_7_patient_data_isolation():
    print("\n========================================================")
    print("TEST 7 -- PATIENT DATA ISOLATION")
    print("========================================================")
    ctx_patient_a = {
        "patient_id": "PATIENT_A_101",
        "patient_info": {"id": "PATIENT_A_101", "age": "5 y/o"},
        "metrics": {"gait_symmetry_pct": 98.5, "mean_symmetry_index_pct": 1.5, "left_rom_deg": 120.0, "right_rom_deg": 120.0}
    }

    ctx_patient_b = {
        "patient_id": "PATIENT_B_202",
        "patient_info": {"id": "PATIENT_B_202", "age": "11 y/o"},
        "metrics": {"gait_symmetry_pct": 72.0, "mean_symmetry_index_pct": 28.0, "left_rom_deg": 80.0, "right_rom_deg": 115.0}
    }

    res_a = process_clinical_assistant_query("Summarize patient metrics", ctx_patient_a)
    res_b = process_clinical_assistant_query("Summarize patient metrics", ctx_patient_b)

    assert "PATIENT_A_101" in res_a["response"]
    assert "PATIENT_B_202" in res_b["response"]
    assert "PATIENT_A_101" not in res_b["response"]
    assert "PATIENT_B_202" not in res_a["response"]
    print("PASS: Patient A and Patient B data sessions strictly isolated!")


def test_8_demo_case_isolation():
    print("\n========================================================")
    print("TEST 8 -- DEMO CASE ISOLATION")
    print("========================================================")
    preset_ctx = {
        "source": "preset",
        "case_id": "case1",
        "patient_info": {"id": "KT-PRESET-CASE1", "case": "Case 1 -- Normative Control"},
        "metrics": {"mean_symmetry_index_pct": 3.2}
    }

    custom_ctx = {
        "source": "custom_upload",
        "video_id": "custom_video_scan_99.mp4",
        "patient_info": {"id": "KT-CUSTOM-99", "case": "Uploaded Video Scan"},
        "metrics": {"mean_symmetry_index_pct": 14.8}
    }

    res_preset = process_clinical_assistant_query("What is the gait symmetry?", preset_ctx)
    res_custom = process_clinical_assistant_query("What is the gait symmetry?", custom_ctx)

    print("PRESET RESPONSE:", clean_str(res_preset["response"]))
    print("CUSTOM RESPONSE:", clean_str(res_custom["response"]))

    assert "KT-PRESET-CASE1" in res_preset["response"]
    assert "KT-CUSTOM-99" in res_custom["response"]
    assert "KT-PRESET-CASE1" not in res_custom["response"]
    print("PASS: Demo case values do not leak into custom patient uploads!")


if __name__ == "__main__":
    test_1_normal_custom_video()
    test_2_abnormal_custom_video()
    test_3_video_quality_failure()
    comp_data = test_4_old_vs_new_video_comparison()
    test_5_chatbot_progression(comp_data)
    test_6_chatbot_pdf_report(comp_data)
    test_7_patient_data_isolation()
    test_8_demo_case_isolation()
    print("\n========================================================")
    print("ALL 8 MANDATORY SYSTEM TESTS PASSED CLEANLY!")
    print("========================================================")
