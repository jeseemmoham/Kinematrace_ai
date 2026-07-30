"""
test_single_agent.py

Automated Test Suite for KinemaTrace Single-Agent Implementation.
Verifies that one single autonomous agent successfully completes the end-to-end workflow:
1. Video Quality Validation
2. Pose Extraction & Biomechanical Calculation
3. Clinical Risk Assessment
4. Longitudinal Progress Tracking
5. Clinical PDF Report Generation
6. Natural Language Conversational Q&A
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from single_agent import KinemaTraceSingleAgent

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def test_single_agent_end_to_end_normative():
    agent = KinemaTraceSingleAgent()
    video_path = os.path.join(SCRIPT_DIR, "demo_normative.mp4")
    assert os.path.exists(video_path), f"Missing demo video at {video_path}"

    result = agent.run_complete_pipeline(
        video_path=video_path,
        patient_id="TEST-SINGLE-001",
        patient_name="Normative Test Child",
        patient_age="2"
    )

    assert result["status"] == "SUCCESS"
    assert result["video_quality"]["status"] in ["PASS", "WARNING"]
    assert result["biomechanical_metrics"]["gait_symmetry_pct"] >= 80.0
    assert result["clinical_risk"]["risk_level"] in ["LOW", "MEDIUM"]
    assert os.path.exists(result["generated_pdf_report"])


def test_single_agent_end_to_end_asymmetric():
    agent = KinemaTraceSingleAgent()
    video_path = os.path.join(SCRIPT_DIR, "demo_asymmetric.mp4")
    assert os.path.exists(video_path), f"Missing demo video at {video_path}"

    result = agent.run_complete_pipeline(
        video_path=video_path,
        patient_id="TEST-SINGLE-002",
        patient_name="Asymmetric Test Child",
        patient_age="2"
    )

    assert result["status"] == "SUCCESS"
    assert result["clinical_risk"]["risk_level"] in ["MEDIUM", "HIGH"]
    assert len(result["clinical_risk"]["triggered_risk_factors"]) > 0


def test_single_agent_qa_query():
    agent = KinemaTraceSingleAgent()
    dummy_context = {
        "biomechanical_metrics": {
            "gait_symmetry_pct": 92.5,
            "left_knee_rom_deg": 58.0,
            "right_knee_rom_deg": 56.5,
            "rom_difference_deg": 1.5
        },
        "clinical_risk": {
            "risk_level": "LOW",
            "severity_score": 0.5,
            "clinical_recommendation": "Routine monitoring."
        }
    }

    ans_sym = agent.answer_clinical_query("What is the gait symmetry?", dummy_context)
    assert "92.5%" in ans_sym

    ans_risk = agent.answer_clinical_query("What is the risk level?", dummy_context)
    assert "LOW" in ans_risk


if __name__ == "__main__":
    print("=== Running Single-Agent Verification Suite ===")
    test_single_agent_end_to_end_normative()
    print("PASS Test 1: Normative video pipeline")
    test_single_agent_end_to_end_asymmetric()
    print("PASS Test 2: Asymmetric video pipeline")
    test_single_agent_qa_query()
    print("PASS Test 3: Conversational Q&A engine")
    print("\nALL SINGLE-AGENT VERIFICATION TESTS PASSED SUCCESSFULLY.")
