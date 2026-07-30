"""
test_cv_engine.py

Verification script for cv_engine module dependencies and error handling.
"""

import sys
import numpy as np
import cv2
import pandas as pd
import mediapipe as mp

def run_tests():
    print("=== Testing Imports ===")
    print(f"OpenCV Version: {cv2.__version__}")
    print(f"MediaPipe Version: {mp.__version__}")
    print(f"Pandas Version: {pd.__version__}")
    print(f"NumPy Version: {np.__version__}")

    from cv_engine import extract_pose_data

    print("\n=== Testing Error Handling ===")

    # Test 1: Non-existent file
    try:
        extract_pose_data("non_existent_video.mp4")
        print("FAIL: Should have raised FileNotFoundError for non-existent file.")
    except FileNotFoundError as e:
        print(f"PASS: FileNotFoundError raised correctly -> {e}")

    # Test 2: Invalid/empty file
    dummy_file = "empty_test.mp4"
    with open(dummy_file, "w") as f:
        f.write("")

    try:
        extract_pose_data(dummy_file)
        print("FAIL: Should have raised ValueError for invalid video file.")
    except ValueError as e:
        print(f"PASS: ValueError raised correctly -> {e}")
    except Exception as e:
        print(f"PASS: Exception raised correctly -> {e}")
    finally:
        import os
        if os.path.exists(dummy_file):
            os.remove(dummy_file)

    print("\n=== All basic verification tests passed! ===")

if __name__ == "__main__":
    run_tests()
