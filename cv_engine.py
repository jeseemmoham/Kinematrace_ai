"""
cv_engine.py

Modular Python script for extracting 3D human pose landmarks from video files
and generating professional YOLOv8-Pose style clinical skeleton overlays using OpenCV and MediaPipe.
Uses imageio libx264 / libvpx-vp9 with yuv420p pixel format for HTML5 browser video compatibility.
Optimized for SINGLE-PASS execution and SHA256-based result caching.
"""

import os
import hashlib
from typing import Optional, List, Dict, Tuple, Any
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import imageio

from clinical_math import calculate_joint_angles, compute_symmetry_index, evaluate_gait_risk


JOINTS_OF_INTEREST = {
    "left_shoulder": mp.solutions.pose.PoseLandmark.LEFT_SHOULDER,
    "right_shoulder": mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER,
    "left_hip": mp.solutions.pose.PoseLandmark.LEFT_HIP,
    "right_hip": mp.solutions.pose.PoseLandmark.RIGHT_HIP,
    "left_knee": mp.solutions.pose.PoseLandmark.LEFT_KNEE,
    "right_knee": mp.solutions.pose.PoseLandmark.RIGHT_KNEE,
    "left_ankle": mp.solutions.pose.PoseLandmark.LEFT_ANKLE,
    "right_ankle": mp.solutions.pose.PoseLandmark.RIGHT_ANKLE,
}

# Global in-memory cache for single-pass analysis results keyed by SHA256 hash
SINGLE_PASS_CACHE: Dict[str, Dict[str, Any]] = {}


def calculate_file_sha256(file_path: str) -> str:
    """Computes SHA256 hash of a video file for deterministic caching."""
    if not os.path.exists(file_path):
        return f"hash_missing_{os.path.basename(file_path)}"
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _calculate_knee_angle_3d(hip_lm, knee_lm, ankle_lm) -> float:
    """Calculates 3D interior flexion angle at Knee vertex in degrees."""
    if not (hip_lm and knee_lm and ankle_lm):
        return np.nan

    v_hk = np.array([hip_lm.x - knee_lm.x, hip_lm.y - knee_lm.y, hip_lm.z - knee_lm.z])
    v_ka = np.array([ankle_lm.x - knee_lm.x, ankle_lm.y - knee_lm.y, ankle_lm.z - knee_lm.z])

    norm_hk = np.linalg.norm(v_hk)
    norm_ka = np.linalg.norm(v_ka)

    if norm_hk < 1e-6 or norm_ka < 1e-6:
        return np.nan

    cos_theta = np.dot(v_hk, v_ka) / (norm_hk * norm_ka)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos_theta)))


def process_video_single_pass(
    video_path: str,
    output_webm_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes a SINGLE PASS over the video file:
    1. Initializes MediaPipe Pose ONCE.
    2. Opens Video ONCE.
    3. Extracts landmarks frame-by-frame and computes frame-level joint angles.
    4. Renders YOLOv8-Pose style skeleton overlay onto frames.
    5. Computes all clinical gait metrics (ROM, symmetry, angular velocity, risk status).
    6. Encodes output video ONCE.
    7. Caches and returns all structured results.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    video_hash = calculate_file_sha256(video_path)
    if video_hash in SINGLE_PASS_CACHE:
        cached = SINGLE_PASS_CACHE[video_hash]
        if output_webm_path and not os.path.exists(output_webm_path):
            cached_webm = cached.get("annotated_video_path")
            if cached_webm and os.path.exists(cached_webm):
                import shutil
                try:
                    shutil.copyfile(cached_webm, output_webm_path)
                except Exception:
                    pass
        return cached

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if fps <= 0 or np.isnan(fps):
        fps = 30.0

    columns = ["frame"]
    for joint_name in JOINTS_OF_INTEREST.keys():
        columns.extend([
            f"{joint_name}_x",
            f"{joint_name}_y",
            f"{joint_name}_z",
            f"{joint_name}_visibility"
        ])

    rows: List[Dict[str, float]] = []
    rgb_frames: List[np.ndarray] = []
    frame_idx = 0

    prev_coords: Dict[str, Tuple[float, float, float]] = {}
    alpha = 0.40  # Temporal Exponential Moving Average smoothing factor

    mp_pose = mp.solutions.pose
    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as pose:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            frame_data: Dict[str, float] = {"frame": frame_idx}
            landmarks = None

            if results and results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

            if landmarks is not None:
                for joint_name, landmark_enum in JOINTS_OF_INTEREST.items():
                    idx = landmark_enum.value
                    lm = landmarks[idx]
                    rx, ry, rz = lm.x, lm.y, lm.z
                    vis = getattr(lm, "visibility", 1.0)
                    if joint_name in prev_coords and vis > 0.3:
                        px, py, pz = prev_coords[joint_name]
                        sx = alpha * rx + (1.0 - alpha) * px
                        sy = alpha * ry + (1.0 - alpha) * py
                        sz = alpha * rz + (1.0 - alpha) * pz
                    else:
                        sx, sy, sz = rx, ry, rz
                    prev_coords[joint_name] = (sx, sy, sz)

                    frame_data[f"{joint_name}_x"] = sx
                    frame_data[f"{joint_name}_y"] = sy
                    frame_data[f"{joint_name}_z"] = sz
                    frame_data[f"{joint_name}_visibility"] = vis

                # Draw skeleton overlay
                left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
                left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
                left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
                right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
                right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
                right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]

                angle_l = _calculate_knee_angle_3d(left_hip, left_knee, left_ankle)
                angle_r = _calculate_knee_angle_3d(right_hip, right_knee, right_ankle)

                si_frame = 0.0
                if not (np.isnan(angle_l) or np.isnan(angle_r)):
                    denom = (angle_l + angle_r) / 2.0
                    if denom > 0:
                        si_frame = (abs(angle_l - angle_r) / denom) * 100.0
                is_asymmetric_frame = (si_frame > 15.0)

                valid_coords = [(int(lm.x * width), int(lm.y * height)) for lm in landmarks if getattr(lm, 'visibility', 1.0) > 0.35]
                if valid_coords:
                    xs, ys = [c[0] for c in valid_coords], [c[1] for c in valid_coords]
                    x_min, y_min = max(0, min(xs) - 25), max(0, min(ys) - 35)
                    x_max, y_max = min(width, max(xs) + 25), min(height, max(ys) + 25)
                    bbox_color = (50, 50, 255) if is_asymmetric_frame else (0, 230, 118)
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), bbox_color, 2, cv2.LINE_AA)

                    status_lbl = "HIGH ASYMMETRY" if is_asymmetric_frame else "NORMATIVE"
                    header_text = f"Patient Tracked | MediaPipe 3D [{status_lbl}]"
                    (tw, _), _ = cv2.getTextSize(header_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
                    label_y1 = max(0, y_min - 24)
                    cv2.rectangle(frame, (x_min, label_y1), (x_min + tw + 16, y_min), bbox_color, -1)
                    cv2.putText(frame, header_text, (x_min + 8, y_min - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

                def draw_skel_line(lm1_enum, lm2_enum, color, thickness=3):
                    lm1 = landmarks[lm1_enum.value]
                    lm2 = landmarks[lm2_enum.value]
                    vis1 = getattr(lm1, 'visibility', 1.0)
                    vis2 = getattr(lm2, 'visibility', 1.0)
                    if vis1 > 0.35 and vis2 > 0.35:
                        pt1 = (int(lm1.x * width), int(lm1.y * height))
                        pt2 = (int(lm2.x * width), int(lm2.y * height))
                        if 0 <= pt1[0] <= width and 0 <= pt1[1] <= height and 0 <= pt2[0] <= width and 0 <= pt2[1] <= height:
                            cv2.line(frame, pt1, pt2, color, thickness, cv2.LINE_AA)

                left_leg_color = (6, 119, 217)
                right_leg_color = (11, 158, 245)
                torso_color = (184, 163, 148)

                draw_skel_line(mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_KNEE, left_leg_color, 4)
                draw_skel_line(mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.LEFT_ANKLE, left_leg_color, 4)
                draw_skel_line(mp_pose.PoseLandmark.RIGHT_HIP, mp_pose.PoseLandmark.RIGHT_KNEE, right_leg_color, 4)
                draw_skel_line(mp_pose.PoseLandmark.RIGHT_KNEE, mp_pose.PoseLandmark.RIGHT_ANKLE, right_leg_color, 4)
                draw_skel_line(mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER, torso_color, 2)
                draw_skel_line(mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP, torso_color, 2)
                draw_skel_line(mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_HIP, torso_color, 2)
                draw_skel_line(mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.RIGHT_HIP, left_leg_color, 3)

                for kp in [mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.RIGHT_HIP,
                           mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.RIGHT_KNEE,
                           mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.RIGHT_ANKLE,
                           mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER]:
                    lm_kp = landmarks[kp.value]
                    if getattr(lm_kp, 'visibility', 1.0) > 0.35:
                        pt = (int(lm_kp.x * width), int(lm_kp.y * height))
                        cv2.circle(frame, pt, 7, (9, 83, 180), -1, cv2.LINE_AA)
                        cv2.circle(frame, pt, 3, (11, 158, 245), -1, cv2.LINE_AA)

                hud_x, hud_y = width - 260, 20
                cv2.rectangle(frame, (hud_x, hud_y), (width - 15, hud_y + 85), (18, 20, 23), -1)
                cv2.rectangle(frame, (hud_x, hud_y), (width - 15, hud_y + 85), (40, 48, 58), 1)
                cv2.putText(frame, "LIVE GAIT ANALYSIS", (hud_x + 10, hud_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (11, 158, 245), 1, cv2.LINE_AA)
                cv2.putText(frame, f"L Knee: {angle_l:.1f}deg", (hud_x + 10, hud_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (6, 119, 217), 1, cv2.LINE_AA)
                cv2.putText(frame, f"R Knee: {angle_r:.1f}deg", (hud_x + 10, hud_y + 58), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (11, 158, 245), 1, cv2.LINE_AA)
                si_color = (68, 68, 239) if is_asymmetric_frame else (129, 185, 16)
                cv2.putText(frame, f"SI: {si_frame:.1f}%", (hud_x + 10, hud_y + 76), cv2.FONT_HERSHEY_SIMPLEX, 0.42, si_color, 1, cv2.LINE_AA)
            else:
                for joint_name in JOINTS_OF_INTEREST.keys():
                    frame_data[f"{joint_name}_x"] = np.nan
                    frame_data[f"{joint_name}_y"] = np.nan
                    frame_data[f"{joint_name}_z"] = np.nan
                    frame_data[f"{joint_name}_visibility"] = np.nan

            rows.append(frame_data)
            rgb_frame_annotated = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frames.append(rgb_frame_annotated)
            frame_idx += 1

    cap.release()

    df_pose = pd.DataFrame(rows, columns=columns)
    if not df_pose.empty:
        df_pose.set_index("frame", inplace=True)

    # Compute joint angles & clinical metrics
    angles_df = calculate_joint_angles(df_pose)
    si_series = compute_symmetry_index(angles_df["left_knee_angle"], angles_df["right_knee_angle"])
    risk_result = evaluate_gait_risk(df_pose)

    valid_left = angles_df["left_knee_angle"].dropna()
    valid_right = angles_df["right_knee_angle"].dropna()
    valid_si = si_series.dropna()

    if not valid_left.empty and len(valid_left) > 5:
        l_max = float(np.percentile(valid_left, 95))
        l_min = float(np.percentile(valid_left, 5))
    else:
        l_max = float(valid_left.max()) if not valid_left.empty else 110.0
        l_min = float(valid_left.min()) if not valid_left.empty else 10.0

    if not valid_right.empty and len(valid_right) > 5:
        r_max = float(np.percentile(valid_right, 95))
        r_min = float(np.percentile(valid_right, 5))
    else:
        r_max = float(valid_right.max()) if not valid_right.empty else 110.0
        r_min = float(valid_right.min()) if not valid_right.empty else 10.0

    l_rom = max(0.0, l_max - l_min)
    r_rom = max(0.0, r_max - r_min)

    # Compute parameter-based ROM Symmetry Index (Section 6 & 8)
    rom_denom = 0.5 * (abs(l_rom) + abs(r_rom))
    if rom_denom > 1e-6:
        mean_si = float((abs(l_rom - r_rom) / rom_denom) * 100.0)
    else:
        mean_si = 0.0

    if not valid_si.empty and len(valid_si) > 5:
        peak_si = float(np.percentile(valid_si, 95))
    else:
        peak_si = float(np.nanmax(valid_si)) if not valid_si.empty else 0.0

    # Calculate Confidence Score (0-100%)
    total_frames = len(df_pose) if not df_pose.empty else 1
    valid_frames_count = len(valid_left) if not valid_left.empty else total_frames
    valid_frame_ratio = (valid_frames_count / total_frames) if total_frames > 0 else 1.0

    vis_cols = [c for c in df_pose.columns if c.endswith("_visibility")]
    if vis_cols:
        mean_vis_val = float(df_pose[vis_cols].mean().mean(skipna=True))
        if np.isnan(mean_vis_val) or mean_vis_val <= 0.0:
            mean_vis_val = 0.90
    else:
        mean_vis_val = 0.90

    confidence_score = round(min(100.0, max(0.0, (valid_frame_ratio * 50.0 + mean_vis_val * 50.0))), 1)

    gait_symmetry = max(0.0, round(100.0 - mean_si, 1))
    peak_knee_flexion = round(min(l_max, r_max), 1)

    time_series = [
        {
            "frame": int(idx),
            "leftKnee": round(float(row["left_knee_angle"]), 1),
            "rightKnee": round(float(row["right_knee_angle"]), 1),
            "symmetryIndex": round(float(si), 1)
        }
        for idx, (row, si) in enumerate(zip(angles_df.to_dict(orient="records"), si_series.values))
    ]

    # Save annotated video if output_webm_path provided
    target_video_path = output_webm_path or f"temp_annotated_{video_hash[:8]}.webm"
    if not os.path.isabs(target_video_path):
        target_video_path = os.path.abspath(target_video_path)

    if not os.path.exists(target_video_path) and rgb_frames:
        try:
            writer = imageio.get_writer(
                target_video_path,
                fps=fps,
                codec="libvpx-vp9" if target_video_path.endswith(".webm") else "libx264",
                quality=7 if target_video_path.endswith(".webm") else None,
                pixelformat="yuv420p" if not target_video_path.endswith(".webm") else None,
                macro_block_size=None
            )
            for rgb_frame in rgb_frames:
                writer.append_data(rgb_frame)
            writer.close()
        except Exception as e:
            print(f"Warning writing annotated video: {e}")

    result_dict = {
        "video_hash": video_hash,
        "df_pose": df_pose,
        "angles_df": angles_df,
        "si_series": si_series,
        "risk_result": risk_result,
        "time_series": time_series,
        "annotated_video_path": target_video_path,
        "metrics": {
            "left_knee_angle": round(l_max, 1),
            "right_knee_angle": round(r_max, 1),
            "left_knee_rom": round(l_rom, 1),
            "right_knee_rom": round(r_rom, 1),
            "gait_symmetry": gait_symmetry,
            "mean_asymmetry": round(mean_si, 1),
            "peak_asymmetry": round(peak_si, 1),
            "rom_difference": round(abs(l_rom - r_rom), 1),
            "peak_knee_flexion": peak_knee_flexion,
            "confidence_score": confidence_score,
            "analysis_confidence": "HIGH" if confidence_score >= 75.0 else ("MEDIUM" if confidence_score >= 50.0 else "LOW"),
        },
        "angles_summary": {
            "left_knee_max": round(l_max, 1),
            "left_knee_min": round(l_min, 1),
            "right_knee_max": round(r_max, 1),
            "right_knee_min": round(r_min, 1)
        }
    }

    SINGLE_PASS_CACHE[video_hash] = result_dict
    return result_dict


def extract_pose_data(
    video_path: str,
    static_image_mode: bool = False,
    model_complexity: int = 1,
    smooth_landmarks: bool = True,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
    use_world_landmarks: bool = False
) -> pd.DataFrame:
    """Extracts 3D pose landmarks via process_video_single_pass for max efficiency."""
    res = process_video_single_pass(video_path)
    return res["df_pose"]


def generate_annotated_video(input_path: str, output_path: str) -> str:
    """Generates annotated video via process_video_single_pass for max efficiency."""
    res = process_video_single_pass(input_path, output_path)
    return res.get("annotated_video_path") or os.path.abspath(output_path)


def stream_annotated_frames(input_path: str, output_webm_path: str):
    """Generates annotated WebM video via process_video_single_pass for max efficiency."""
    res = process_video_single_pass(input_path, output_webm_path)
    cap = cv2.VideoCapture(res.get("annotated_video_path") or input_path)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        yield cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    cap.release()


if __name__ == "__main__":
    import sys
    print("cv_engine.py loaded successfully.")
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
        print(f"Processing {video_file}...")
        try:
            res = process_video_single_pass(video_file, "annotated_test.webm")
            print(f"Single pass analysis complete for: {video_file}")
            print(f"Metrics: {res['metrics']}")
        except Exception as e:
            print(f"Error processing video: {e}")
