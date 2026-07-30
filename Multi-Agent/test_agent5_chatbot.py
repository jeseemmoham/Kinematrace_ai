"""
test_agent5_chatbot.py

Comprehensive verification suite for Agent 5 — Clinical AI Assistant / Patient Insight Chatbot.
Tests:
1. Patient Summary Intent
2. Risk Explanation Intent (Agent 3 integration)
3. Normative / Reference Comparison Intent
4. Progression Analysis Intent (Agent 4 integration)
5. PDF Report Generation Intent & PDF File Output
6. Missing Data Handling & Error Messages
7. Custom Patient Data Isolation (No demo data leak)
"""

import os
import sys

# Ensure backend directory is in python path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from agents import process_clinical_assistant_query
from pdf_generator import generate_clinical_pdf_report


def test_agent5_preset_cases():
    print("\n--- Test 1: Agent 5 Preset Demo Cases (Case 1 & Case 2) ---")
    
    # Case 1: Normative Control
    ctx1 = {"case_id": "case1", "patient_info": {"id": "PED-2026-001", "age": "7 y/o", "case": "Normative Control"}}
    res1_sum = process_clinical_assistant_query("Summarize this patient.", ctx1)
    assert "PED-2026-001" in res1_sum["response"]
    assert "LOW RISK" in res1_sum["response"]
    print("[PASS] Case 1 Summary test passed.")

    # Case 2: Asymmetric Gait Risk Explanation
    ctx2 = {"case_id": "case2", "patient_info": {"id": "KT-2026-P902", "age": "7 y/o", "case": "Post-Injury Asymmetric Gait"}}
    res2_risk = process_clinical_assistant_query("Why is this patient high risk?", ctx2)
    assert "HIGH RISK" in res2_risk["response"]
    assert "20.9%" in res2_risk["response"]
    assert "15.0%" in res2_risk["response"]
    assert "MEDICAL SAFETY DISCLAIMER" in res2_risk["response"]
    print("[PASS] Case 2 Risk Explanation test passed.")


def test_agent5_normative_comparison():
    print("\n--- Test 2: Agent 5 Normative / Reference Comparison ---")
    ctx2 = {"case_id": "case2"}
    res_norm = process_clinical_assistant_query("Compare the patient with normal values", ctx2)
    assert "Normative Reference Comparison" in res_norm["response"]
    assert "Mean Asymmetry Index" in res_norm["response"]
    assert "Left Knee ROM" in res_norm["response"]
    assert "Right Knee ROM" in res_norm["response"]
    assert "Bilateral ROM Deficit" in res_norm["response"]
    print("[PASS] Reference Comparison test passed.")


def test_agent5_progression_analysis():
    print("\n--- Test 3: Agent 5 Progression Analysis (Agent 4 Integration) ---")
    
    # Complete comparison context with Agent 4 data
    comp_context = {
        "patient_info": {"id": "PED-LONGITUDINAL-01", "age": "8 y/o"},
        "patient_progress": {
            "overall_progress": "IMPROVED",
            "old_video": {
                "file_name": "baseline_scan.mp4",
                "gait_asymmetry": 25.5,
                "left_rom": 60.0,
                "right_rom": 61.5,
                "rom_deficit_deg": 1.5,
            },
            "new_video": {
                "file_name": "latest_scan.mp4",
                "gait_asymmetry": 12.8,
                "left_rom": 88.5,
                "right_rom": 89.2,
                "rom_deficit_deg": 0.7,
            },
            "summary": "Asymmetry decreased significantly with enhanced right knee ROM."
        }
    }

    res_prog = process_clinical_assistant_query("Has the patient improved?", comp_context)
    assert "gait asymmetry decreased from **25.5%** to **12.8%**" in res_prog["response"]
    assert "IMPROVED" in res_prog["response"]
    assert "baseline_scan.mp4" in res_prog["response"]
    assert "latest_scan.mp4" in res_prog["response"]
    print("[PASS] Progression Analysis test passed.")


def test_agent5_missing_data_rules():
    print("\n--- Test 4: Agent 5 Missing Data Handling ---")
    
    # Custom patient with incomplete Agent 4 progress
    custom_ctx = {
        "source_type": "custom",
        "patient_info": {"id": "KT-CUSTOM-99", "age": "6 y/o"},
        "video_quality": {"status": "PASS", "video_quality_score": 90},
        "telemetry": {"gait_symmetry_pct": 92.0, "left_rom": 90.0, "right_rom": 88.0},
        "clinical_risk": {"risk_level": "LOW", "severity": "NORMAL"}
    }

    res_no_prog = process_clinical_assistant_query("Has the patient improved?", custom_ctx)
    assert "Progress comparison requires both a baseline and latest assessment" in res_no_prog["response"]
    print("[PASS] Missing Agent 4 Progress handling passed.")


def test_agent5_pdf_report():
    print("\n--- Test 5: Agent 5 PDF Report Generation ---")
    ctx = {
        "case_id": "case2",
        "patient_info": {"id": "KT-2026-P902", "age": "7 y/o", "case": "Post-Injury Asymmetric Gait"}
    }
    res_rep = process_clinical_assistant_query("Generate a clinical report PDF", ctx)
    assert res_rep.get("has_pdf_report") is True
    assert "PEDIATRIC GAIT SCREENING REPORT" in res_rep["response"]

    pdf_bytes = generate_clinical_pdf_report(ctx)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")
    print(f"[PASS] PDF Report byte generation passed ({len(pdf_bytes)} bytes).")


def test_custom_patient_isolation():
    print("\n--- Test 6: Custom Patient Data Isolation (No Demo Leakage) ---")
    custom_ctx = {
        "source_type": "custom",
        "patient_info": {"id": "KT-CUSTOM-4444", "age": "5 y/o", "case": "User Custom Video"},
        "filename": "custom_patient_walking.mp4",
        "video_quality": {"status": "PASS", "video_quality_score": 95},
        "telemetry": {
            "gait_symmetry_pct": 91.5,
            "mean_si_pct": 8.5,
            "left_rom": 105.0,
            "right_rom": 102.0,
            "peak_knee_flexion": 102.0,
            "hip_flexion_rom_deg": 122.0
        },
        "clinical_risk": {
            "risk_level": "LOW",
            "severity": "NORMAL",
            "affected_side": "NONE",
            "reasoning": "Custom gait scan reveals mild 8.5% asymmetry well within normal 15% threshold."
        }
    }

    res = process_clinical_assistant_query("Summarize this patient", custom_ctx)
    assert "KT-CUSTOM-4444" in res["response"]
    assert "91.5%" in res["response"]
    # Ensure Case 2 demo values (20.9%, 58.2°) DO NOT leak into custom patient
    assert "20.9%" not in res["response"]
    assert "58.2°" not in res["response"]
    print("[PASS] Custom patient context isolation passed.")


if __name__ == "__main__":
    test_agent5_preset_cases()
    test_agent5_normative_comparison()
    test_agent5_progression_analysis()
    test_agent5_missing_data_rules()
    test_agent5_pdf_report()
    test_custom_patient_isolation()
    print("\n==================================================")
    print("ALL AGENT 5 CLINICAL ASSISTANT TESTS PASSED 100%!")
    print("==================================================")
