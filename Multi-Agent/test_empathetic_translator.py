"""
test_empathetic_translator.py

Verification script for Agent 6: The Parent & Caregiver Empathetic Translator:
1. Tests edge case 1: Video-dependency gating (empty payload returns 400 Bad Request).
2. Tests edge case 2: Unlocked execution flow with valid kinematic data.
3. Tests direct python function process_empathetic_translator.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from backend.agents import process_empathetic_translator
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_empathetic_translator_gating_error():
    print("--- Test 1: Video-Dependency Gating (Empty Payload -> HTTP 400) ---")
    response = client.post("/api/agents/empathetic-translator", json={})
    print(f"Status Code: {response.status_code}, Response: {response.json()}")
    assert response.status_code == 400
    assert "No kinematic telemetry provided" in response.json()["detail"]
    print("PASS: Empty request correctly blocked with HTTP 400 Bad Request error!")


def test_empathetic_translator_unlocked_flow():
    print("\n--- Test 2: Unlocked Execution Flow with Kinematic Data ---")
    sample_kinematic_data = {
        "video_id": "upload_1784872958.mp4",
        "gait_analysis": {
            "gait_symmetry": 87.5,
            "left_knee_rom": 64.2,
            "right_knee_rom": 104.2,
            "left_hip_rom": 125.1,
            "rom_difference": 40.0,
            "pose_confidence": 94.2
        },
        "patient_info": {
            "id": "KT-2026-P902",
            "age": "7 y/o",
            "case": "Post-Injury Asymmetric Gait"
        }
    }

    response = client.post(
        "/api/agents/empathetic-translator",
        json={
            "kinematic_data": sample_kinematic_data,
            "user_instruction": "Explain why my child gets tired when running at recess."
        }
    )

    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "empathetic-translator"
    assert "daily_play_explanation" in data
    assert len(data["movement_strengths"]) > 0
    assert len(data["comfort_and_play_tips"]) > 0
    assert "recess" in data["daily_play_explanation"] or "tired" in data["daily_play_explanation"] or "Parent Query" in data["daily_play_explanation"]

    print("PASS: Unlocked empathetic translator returned 3 warm family cards and structured guide!")


def test_python_process_empathetic_translator():
    print("\n--- Test 3: Direct Python Function process_empathetic_translator ---")
    sample_data = {
        "metrics": {
            "left_knee_rom": 60.0,
            "right_knee_rom": 62.0,
            "gait_symmetry": 96.8,
            "left_hip_rom": 120.0,
            "pose_confidence": 98.0
        }
    }
    result = process_empathetic_translator(sample_data, "How can I help my child during playground games?")
    assert result["gait_symmetry"] == 96.8
    assert len(result["movement_strengths"]) >= 3
    assert len(result["comfort_and_play_tips"]) >= 3
    print("PASS: process_empathetic_translator generated family guide successfully!")

if __name__ == "__main__":
    test_empathetic_translator_gating_error()
    test_empathetic_translator_unlocked_flow()
    test_python_process_empathetic_translator()
    print("\n=== ALL EMPATHETIC TRANSLATOR AGENT TESTS PASSED CLEANLY! ===")
