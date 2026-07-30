import os
import sys
import time
from typing import Any
from fastapi.testclient import TestClient

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(WORKSPACE_DIR, "backend")
if backend_dir in sys.path:
    sys.path.remove(backend_dir)
sys.path.insert(0, backend_dir)

from main import app, VIDEO_ANALYSIS_CACHE
from agents import (
    process_clinical_assistant_query,
    process_empathetic_translator,
    assess_clinical_risk,
)

client = TestClient(app)

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

def run_performance_and_persistence_tests():
    print("\n========================================================")
    print("RUNNING STATE MANAGEMENT & PERFORMANCE OPTIMIZATION TESTS")
    print("========================================================")

    test_video_path = os.path.join(WORKSPACE_DIR, "demo_normative.mp4")
    if not os.path.exists(test_video_path):
        print(f"Error: test video {test_video_path} not found.")
        sys.exit(1)

    # 1. Initial Analysis & Cache Population
    t0 = time.time()
    res1 = client.post("/api/analyze-custom-video", json={"file_path": test_video_path})
    t_initial = (time.time() - t0) * 1000.0

    assert res1.status_code == 200, f"Analysis failed: {res1.text}"
    data1 = res1.json()
    video_id_1 = data1.get("video_id")

    assert video_id_1 is not None and "vid_" in video_id_1, f"Invalid video_id: {video_id_1}"
    print(f"Initial Analysis Execution Time: {t_initial:.1f}ms")
    print(f"Generated Unique video_id: {video_id_1}")

    # 2. Performance Caching Verification (< 100ms response)
    t1 = time.time()
    res2 = client.post("/api/analyze-custom-video", json={"file_path": test_video_path})
    t_cached = (time.time() - t1) * 1000.0

    assert res2.status_code == 200
    data2 = res2.json()
    video_id_2 = data2.get("video_id")

    assert video_id_1 == video_id_2, "Video IDs must match for identical video cached request!"
    assert t_cached < 100.0, f"Cached response took too long: {t_cached:.1f}ms (Expected < 100ms)"
    print(f"Cached Analysis Execution Time: {t_cached:.1f}ms (Speedup: {t_initial / max(1, t_cached):.1f}x fast!)")
    print("PASS: Performance Caching verified (< 100ms response)!")

    # 3. Downstream Agent Data Integrity Verification via video_id
    risk_result = data1.get("risk_assessment", {})
    assert risk_result.get("video_id") == video_id_1, "Agent 3 Risk Assessment video_id mismatch!"
    print("PASS: Agent 3 Risk Assessment video_id verified!")

    # 4. Chatbot Fast Execution with Stored Session Context
    t2 = time.time()
    chat_res = process_clinical_assistant_query("What is the patient risk level?", data1)
    t_chat = (time.time() - t2) * 1000.0

    assert chat_res.get("response") is not None
    assert t_chat < 50.0, f"Chatbot execution took too long: {t_chat:.1f}ms"
    print(f"Agent 5 Chatbot Response Time: {t_chat:.1f}ms")
    print("PASS: Agent 5 Chatbot executes instantly from stored results!")

    # 5. Empathetic Translator Fast Execution with Stored Session Context
    t3 = time.time()
    trans_res = process_empathetic_translator(data1, user_instruction="")
    t_trans = (time.time() - t3) * 1000.0

    assert trans_res.get("daily_play_explanation") is not None
    assert t_trans < 50.0, f"Empathetic Translator execution took too long: {t_trans:.1f}ms"
    print(f"Agent 6 Empathetic Translator Response Time: {t_trans:.1f}ms")
    print("PASS: Agent 6 Empathetic Translator executes instantly from stored results!")

    print("\n========================================================")
    print("ALL PERFORMANCE & STATE MANAGEMENT TESTS PASSED CLEANLY!")
    print("========================================================\n")

if __name__ == "__main__":
    run_performance_and_persistence_tests()
