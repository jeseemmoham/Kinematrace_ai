"""
create_demo_assets.py

Generates demo MP4 videos with drawn human skeletons and pre-processed DataFrames
for the Streamlit KinemaTrace AI app using imageio libx264 yuv420p H.264 encoding.
"""

import os
import cv2
import numpy as np
import pandas as pd
import imageio
from clinical_math import calculate_joint_angles, compute_symmetry_index, evaluate_gait_risk
from cv_engine import generate_annotated_video, stream_annotated_frames


def generate_gait_video_and_df(
    output_video_path: str,
    asymmetric: bool = False,
    num_frames: int = 90,
    fps: int = 30,
    width: int = 640,
    height: int = 480
):
    """
    Creates an H.264 yuv420p MP4 video of a moving human skeleton and returns the corresponding DataFrame.
    """
    rgb_frames = []
    rows = []

    for t in range(num_frames):
        # Create dark medical grid background
        frame = np.ones((height, width, 3), dtype=np.uint8) * 18
        for y in range(0, height, 40):
            cv2.line(frame, (0, y), (width, y), (30, 35, 45), 1)
        for x in range(0, width, 40):
            cv2.line(frame, (x, 0), (x, height), (30, 35, 45), 1)

        # Gait phase angle (1 Hz gait frequency)
        phase = 2 * np.pi * (t / fps)

        # Hip locations
        hip_center_x, hip_center_y = width // 2, height // 2 - 40
        left_hip_x, left_hip_y, left_hip_z = hip_center_x - 30, hip_center_y, 0.0
        right_hip_x, right_hip_y, right_hip_z = hip_center_x + 30, hip_center_y, 0.0

        # Thigh & shank lengths
        l1, l2 = 80.0, 80.0

        # Left leg dynamics (normative)
        alpha_l = 0.3 * np.sin(phase)
        beta_l = alpha_l + 0.6 * np.sin(phase + np.pi / 4) + 0.5

        left_knee_x = left_hip_x + l1 * np.sin(alpha_l)
        left_knee_y = left_hip_y + l1 * np.cos(alpha_l)
        left_knee_z = 0.0

        left_ankle_x = left_knee_x + l2 * np.sin(beta_l)
        left_ankle_y = left_knee_y + l2 * np.cos(beta_l)
        left_ankle_z = 0.0

        # Right leg dynamics
        if not asymmetric:
            alpha_r = 0.3 * np.sin(phase + np.pi)
            beta_r = alpha_r + 0.6 * np.sin(phase + np.pi + np.pi / 4) + 0.5
        else:
            alpha_r = 0.08 * np.sin(phase + np.pi)
            beta_r = alpha_r + 0.15 * np.sin(phase + np.pi) + 0.1

        right_knee_x = right_hip_x + l1 * np.sin(alpha_r)
        right_knee_y = right_hip_y + l1 * np.cos(alpha_r)
        right_knee_z = 0.0

        right_ankle_x = right_knee_x + l2 * np.sin(beta_r)
        right_ankle_y = right_knee_y + l2 * np.cos(beta_r)
        right_ankle_z = 0.0

        # Draw Torso & Head
        head_center = (hip_center_x, hip_center_y - 120)
        cv2.circle(frame, head_center, 22, (0, 210, 255), -1, cv2.LINE_AA)
        cv2.line(frame, head_center, (hip_center_x, hip_center_y), (0, 210, 255), 4, cv2.LINE_AA)
        cv2.line(frame, (int(left_hip_x), int(left_hip_y)), (int(right_hip_x), int(right_hip_y)), (0, 210, 255), 4, cv2.LINE_AA)

        # Draw Left Leg (Cyan)
        cv2.line(frame, (int(left_hip_x), int(left_hip_y)), (int(left_knee_x), int(left_knee_y)), (255, 200, 0), 4, cv2.LINE_AA)
        cv2.line(frame, (int(left_knee_x), int(left_knee_y)), (int(left_ankle_x), int(left_ankle_y)), (255, 200, 0), 4, cv2.LINE_AA)
        cv2.circle(frame, (int(left_hip_x), int(left_hip_y)), 7, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (int(left_knee_x), int(left_knee_y)), 7, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (int(left_ankle_x), int(left_ankle_y)), 7, (255, 255, 255), -1, cv2.LINE_AA)

        # Draw Right Leg (Magenta / Orange-Red)
        cv2.line(frame, (int(right_hip_x), int(right_hip_y)), (int(right_knee_x), int(right_knee_y)), (50, 100, 255), 4, cv2.LINE_AA)
        cv2.line(frame, (int(right_knee_x), int(right_knee_y)), (int(right_ankle_x), int(right_ankle_y)), (50, 100, 255), 4, cv2.LINE_AA)
        cv2.circle(frame, (int(right_hip_x), int(right_hip_y)), 7, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (int(right_knee_x), int(right_knee_y)), 7, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (int(right_ankle_x), int(right_ankle_y)), 7, (255, 255, 255), -1, cv2.LINE_AA)

        # Add HUD Text
        mode_label = "CASE 2: ASYMMETRICAL LIMP" if asymmetric else "CASE 1: NORMATIVE GAIT"
        label_color = (80, 80, 255) if asymmetric else (80, 255, 120)
        cv2.putText(frame, f"KinemaTrace AI - {mode_label}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, label_color, 2, cv2.LINE_AA)
        cv2.putText(frame, f"FRAME: {t:03d}/{num_frames}", (width - 170, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1, cv2.LINE_AA)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frames.append(frame_rgb)

        # Save normalized coordinates in DataFrame format
        rows.append({
            "frame": t,
            "left_hip_x": left_hip_x / width,
            "left_hip_y": left_hip_y / height,
            "left_hip_z": left_hip_z,
            "left_hip_visibility": 0.99,
            "left_knee_x": left_knee_x / width,
            "left_knee_y": left_knee_y / height,
            "left_knee_z": left_knee_z,
            "left_knee_visibility": 0.99,
            "left_ankle_x": left_ankle_x / width,
            "left_ankle_y": left_ankle_y / height,
            "left_ankle_z": left_ankle_z,
            "left_ankle_visibility": 0.99,
            "right_hip_x": right_hip_x / width,
            "right_hip_y": right_hip_y / height,
            "right_hip_z": right_hip_z,
            "right_hip_visibility": 0.99,
            "right_knee_x": right_knee_x / width,
            "right_knee_y": right_knee_y / height,
            "right_knee_z": right_knee_z,
            "right_knee_visibility": 0.99,
            "right_ankle_x": right_ankle_x / width,
            "right_ankle_y": right_ankle_y / height,
            "right_ankle_z": right_ankle_z,
            "right_ankle_visibility": 0.99,
        })

    if os.path.exists(output_video_path):
        try:
            os.remove(output_video_path)
        except Exception:
            pass

    writer = imageio.get_writer(
        output_video_path,
        fps=fps,
        codec="libx264",
        pixelformat="yuv420p",
        macro_block_size=None
    )
    for rgb_frame in rgb_frames:
        writer.append_data(rgb_frame)
    writer.close()

    df = pd.DataFrame(rows).set_index("frame")
    return df


if __name__ == "__main__":
    print("Generating H.264 yuv420p demo assets with imageio...")
    df_norm = generate_gait_video_and_df("demo_normative.mp4", asymmetric=False)
    df_asym = generate_gait_video_and_df("demo_asymmetric.mp4", asymmetric=True)

    df_norm.to_csv("demo_normative.csv")
    df_asym.to_csv("demo_asymmetric.csv")

    generate_annotated_video("demo_normative.mp4", "demo_normative_annotated.mp4")
    generate_annotated_video("demo_asymmetric.mp4", "demo_asymmetric_annotated.mp4")

    # Also generate browser-native WebM videos (VP9) for the Streamlit live player
    print("Generating WebM VP9 annotated videos for browser-native playback...")
    for _ in stream_annotated_frames("demo_normative.mp4", "demo_normative_annotated.webm"):
        pass
    for _ in stream_annotated_frames("demo_asymmetric.mp4", "demo_asymmetric_annotated.webm"):
        pass

    print("All demo assets (MP4 + WebM) generated successfully!")

