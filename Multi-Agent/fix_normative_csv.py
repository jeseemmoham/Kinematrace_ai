"""
fix_normative_csv.py

Script to generate a mathematically clean, symmetric pediatric gait keypoint time series
for demo_normative.csv so Case 1 dynamically evaluates to LOW RISK (Mean SI < 5.0%, Severity: NORMAL, Affected Side: NONE).
"""

import os
import numpy as np
import pandas as pd

def generate_normative_pose_data():
    num_frames = 60
    fps = 30.0
    t = np.linspace(0, 4 * np.pi, num_frames)

    # Symmetric motion profiles
    # Hip centers
    l_hip_x = 0.45 + 0.01 * np.sin(t)
    l_hip_y = 0.45 + 0.005 * np.cos(2 * t)
    l_hip_z = 0.0

    r_hip_x = 0.55 + 0.01 * np.sin(t)
    r_hip_y = 0.45 + 0.005 * np.cos(2 * t)
    r_hip_z = 0.0

    # Shoulders
    l_sh_x = 0.45 + 0.008 * np.sin(t)
    l_sh_y = 0.22 + 0.003 * np.cos(2 * t)
    l_sh_z = 0.0

    r_sh_x = 0.55 + 0.008 * np.sin(t)
    r_sh_y = 0.22 + 0.003 * np.cos(2 * t)
    r_sh_z = 0.0

    # Knee motion: symmetric flexion curves (phase shifted by pi for opposite limb)
    flex_l = 0.12 * np.sin(t)
    flex_r = 0.12 * np.sin(t + np.pi)

    l_knee_x = l_hip_x + flex_l
    l_knee_y = 0.65 - 0.02 * np.abs(np.sin(t))
    l_knee_z = 0.0

    r_knee_x = r_hip_x + flex_r
    r_knee_y = 0.65 - 0.02 * np.abs(np.sin(t + np.pi))
    r_knee_z = 0.0

    # Ankles
    l_ank_x = l_knee_x - 0.02 * np.cos(t)
    l_ank_y = 0.88
    l_ank_z = 0.0

    r_ank_x = r_knee_x - 0.02 * np.cos(t + np.pi)
    r_ank_y = 0.88
    r_ank_z = 0.0

    df = pd.DataFrame({
        "frame": np.arange(num_frames),
        "left_hip_x": l_hip_x, "left_hip_y": l_hip_y, "left_hip_z": l_hip_z, "left_hip_visibility": 0.99,
        "right_hip_x": r_hip_x, "right_hip_y": r_hip_y, "right_hip_z": r_hip_z, "right_hip_visibility": 0.99,
        "left_knee_x": l_knee_x, "left_knee_y": l_knee_y, "left_knee_z": l_knee_z, "left_knee_visibility": 0.99,
        "right_knee_x": r_knee_x, "right_knee_y": r_knee_y, "right_knee_z": r_knee_z, "right_knee_visibility": 0.99,
        "left_ankle_x": l_ank_x, "left_ankle_y": l_ank_y, "left_ankle_z": l_ank_z, "left_ankle_visibility": 0.99,
        "right_ankle_x": r_ank_x, "right_ankle_y": r_ank_y, "right_ankle_z": r_ank_z, "right_ankle_visibility": 0.99,
        "left_shoulder_x": l_sh_x, "left_shoulder_y": l_sh_y, "left_shoulder_z": l_sh_z, "left_shoulder_visibility": 0.99,
        "right_shoulder_x": r_sh_x, "right_shoulder_y": r_sh_y, "right_shoulder_z": r_sh_z, "right_shoulder_visibility": 0.99,
    })

    df.set_index("frame", inplace=True)
    return df

if __name__ == "__main__":
    df_normative = generate_normative_pose_data()
    workspace_csv = os.path.join(os.path.dirname(__file__), "demo_normative.csv")
    backend_csv = os.path.join(os.path.dirname(__file__), "backend", "demo_normative.csv")
    df_normative.to_csv(workspace_csv)
    if os.path.exists(os.path.dirname(backend_csv)):
        df_normative.to_csv(backend_csv)
    print("SUCCESS: demo_normative.csv regenerated with symmetric normative keypoints!")
