"""
test_agents.py

Verification script for agents.py module:
- Agent 1: The Biomechanical Data Analyst
- Agent 2: The Pediatric Physical Therapist
- Agent 3: The Orthopedic Risk Consultant
- Agent 4: The Clinical Report Synthesizer
"""

import numpy as np
import pandas as pd
from agents import (
    AGENT_1_CONFIG,
    AGENT_2_CONFIG,
    AGENT_3_CONFIG,
    AGENT_4_CONFIG,
    analyze_biomechanics,
    analyze_physical_therapy,
    analyze_orthopedic_risk,
    synthesize_clinical_report
)


def test_agent_configurations():
    print("--- Test 1: All 4 Agent Configurations ---")
    assert AGENT_1_CONFIG["name"] == "Agent 1: The Biomechanical Data Analyst"
    assert AGENT_1_CONFIG["role"] == "Lead Pediatric Biomechanical Data Analyst"

    assert AGENT_2_CONFIG["name"] == "Agent 2: The Pediatric Physical Therapist"
    assert AGENT_2_CONFIG["role"] == "Pediatric Physical Therapy & Movement Specialist"

    assert AGENT_3_CONFIG["name"] == "Agent 3: The Orthopedic Risk Consultant"
    assert AGENT_3_CONFIG["role"] == "Pediatric Orthopedic Diagnostic Screening Consultant"

    assert AGENT_4_CONFIG["name"] == "Agent 4: The Clinical Report Synthesizer"
    assert AGENT_4_CONFIG["role"] == "Lead Medical Technical Writer & Clinical Care Planner"
    assert "specialist in pediatric rehabilitation" in AGENT_4_CONFIG["backstory"]
    print("PASS: All 4 agent metadata and system prompt backstories loaded correctly.")


def test_4_agent_pipeline_normative():
    print("\n--- Test 2: Full 4-Agent Pipeline (Normative Case) ---")
    patient_info = {"id": "PED-2026-001", "age": "7 y/o", "case": "Normative Control"}
    frames = np.arange(100)
    left_knee = 130 + 40 * np.sin(frames * 0.1)
    right_knee = 130 + 40 * np.sin(frames * 0.1)

    df_normative = pd.DataFrame({
        "left_knee_angle": left_knee,
        "right_knee_angle": right_knee
    })

    # Pipeline execution
    bio_res = analyze_biomechanics(df_normative)
    pt_res = analyze_physical_therapy(bio_res)
    ortho_res = analyze_orthopedic_risk(bio_res, pt_res)
    synth_res = synthesize_clinical_report(patient_info, bio_res, pt_res, ortho_res)

    print("Agent 4 Executive Summary:", synth_res["executive_summary"])
    assert "fluid bilateral knee flexion/extension symmetry" in synth_res["executive_summary"]
    assert "PROGRESSIVE REHABILITATION EXERCISE ROADMAP" in synth_res["report_text"]
    print("PASS: Full 4-agent normative synthesis completed successfully!")


def test_4_agent_pipeline_asymmetric():
    print("\n--- Test 3: Full 4-Agent Pipeline (Asymmetric Case) ---")
    patient_info = {"id": "PED-2026-002", "age": "6 y/o", "case": "Post-Injury Asymmetric Gait"}
    frames = np.arange(100)
    left_knee = 130 + 40 * np.sin(frames * 0.1)
    right_knee = 110 + 20 * np.sin(frames * 0.1)

    df_asymmetric = pd.DataFrame({
        "left_knee_angle": left_knee,
        "right_knee_angle": right_knee
    })

    # Pipeline execution
    bio_res = analyze_biomechanics(df_asymmetric)
    pt_res = analyze_physical_therapy(bio_res)
    ortho_res = analyze_orthopedic_risk(bio_res, pt_res)
    synth_res = synthesize_clinical_report(patient_info, bio_res, pt_res, ortho_res)

    print("Agent 4 Executive Summary:", synth_res["executive_summary"])
    assert "significant bilateral gait asymmetry" in synth_res["executive_summary"]
    assert "HIGH PRIORITY ORTHOPEDIC REFERRAL" in synth_res["report_text"]
    assert "Phase 1: Foundation & Mobility" in synth_res["report_text"]
    print("PASS: Full 4-agent asymmetric synthesis completed successfully!")


def test_video_quality_validation():
    print("\n--- Test 4: Video Quality Validation Agent ---")
    from agents.video_quality_agent import validate_video_quality
    
    # Test with normative demo video
    res_norm = validate_video_quality("demo_normative.mp4")
    print("Normative Video Quality Score:", res_norm["video_quality_score"], "Status:", res_norm["status"])
    assert res_norm["status"] in ["PASS", "WARNING"]
    assert "video_quality_score" in res_norm
    assert "checks" in res_norm
    assert "metrics" in res_norm
    assert res_norm["checks"]["full_body_visible"] is True
    
    # Test with asymmetric demo video
    res_asym = validate_video_quality("demo_asymmetric.mp4")
    print("Asymmetric Video Quality Score:", res_asym["video_quality_score"], "Status:", res_asym["status"])
    assert res_asym["status"] in ["PASS", "WARNING"]
    
    # Test with non-existent file (should fail gracefully)
    res_err = validate_video_quality("non_existent_file.mp4")
    assert res_err["status"] == "FAIL"
    assert res_err["video_quality_score"] == 0
    assert len(res_err["issues"]) > 0
    print("PASS: Video quality validation checks ran and failed gracefully as expected.")


if __name__ == "__main__":
    test_agent_configurations()
    test_4_agent_pipeline_normative()
    test_4_agent_pipeline_asymmetric()
    test_video_quality_validation()
    print("\n=== ALL PIPELINE AND QUALITY AGENT TESTS PASSED SUCCESSFULLY! ===")
