"""
cv_engine.py

Modular Python script for extracting 3D human pose landmarks from video files
and generating professional YOLOv8-Pose style clinical skeleton overlays using OpenCV and MediaPipe.
Uses imageio libx264 with yuv420p pixel format for 100% HTML5 browser video compatibility.
"""

import os
from typing import Optional, List, Dict, Tuple
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import imageio


JOINTS_OF_INTEREST = {
    "left_hip": mp.solutions.pose.PoseLandmark.LEFT_HIP,
    "right_hip": mp.solutions.pose.PoseLandmark.RIGHT_HIP,
    "left_knee": mp.solutions.pose.PoseLandmark.LEFT_KNEE,
    "right_knee": mp.solutions.pose.PoseLandmark.RIGHT_KNEE,
    "left_ankle": mp.solutions.pose.PoseLandmark.LEFT_ANKLE,
    "right_ankle": mp.solutions.pose.PoseLandmark.RIGHT_ANKLE,
}


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


def extract_pose_data(
    video_path: str,
    static_image_mode: bool = False,
    model_complexity: int = 1,
    smooth_landmarks: bool = True,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5,
    use_world_landmarks: bool = False
) -> pd.DataFrame:
    """
    Extracts 3D pose landmarks (hips, knees, ankles) from a video file frame by frame.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found at path: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video file: {video_path}")

    columns = ["frame"]
    for joint_name in JOINTS_OF_INTEREST.keys():
        columns.extend([
            f"{joint_name}_x",
            f"{joint_name}_y",
            f"{joint_name}_z",
            f"{joint_name}_visibility"
        ])

    rows: List[Dict[str, float]] = []
    frame_idx = 0

    mp_pose = mp.solutions.pose

    with mp_pose.Pose(
        static_image_mode=static_image_mode,
        model_complexity=model_complexity,
        smooth_landmarks=smooth_landmarks,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    ) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            frame_data: Dict[str, float] = {"frame": frame_idx}

            landmarks = None
            if results:
                if use_world_landmarks and results.pose_world_landmarks:
                    landmarks = results.pose_world_landmarks.landmark
                elif results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark

            if landmarks is not None:
                for joint_name, landmark_enum in JOINTS_OF_INTEREST.items():
                    idx = landmark_enum.value
                    lm = landmarks[idx]
                    frame_data[f"{joint_name}_x"] = lm.x
                    frame_data[f"{joint_name}_y"] = lm.y
                    frame_data[f"{joint_name}_z"] = lm.z
                    frame_data[f"{joint_name}_visibility"] = getattr(lm, "visibility", np.nan)
            else:
                for joint_name in JOINTS_OF_INTEREST.keys():
                    frame_data[f"{joint_name}_x"] = np.nan
                    frame_data[f"{joint_name}_y"] = np.nan
                    frame_data[f"{joint_name}_z"] = np.nan
                    frame_data[f"{joint_name}_visibility"] = np.nan

            rows.append(frame_data)
            frame_idx += 1

    cap.release()

    df = pd.DataFrame(rows, columns=columns)
    if not df.empty:
        df.set_index("frame", inplace=True)

    return df


def generate_annotated_video(input_path: str, output_path: str) -> str:
    """
    Reads a video frame-by-frame, extracts pose landmarks, draws a YOLOv8-Pose style
    clinical skeleton overlay, bounding box, label, and gait asymmetry highlights,
    and encodes the output using imageio libx264 with yuv420p pixel format for HTML5 browser compatibility.

    Args:
        input_path (str): Path to input MP4 video file.
        output_path (str): Path where annotated MP4 video will be written.

    Returns:
        str: Absolute path to written output video file.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open input video: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    rgb_frames: List[np.ndarray] = []

    mp_pose = mp.solutions.pose

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if results and results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # 1. Compute frame-level knee angles & asymmetry index
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

                # 2. Compute Bounding Box around patient
                valid_coords = [(int(lm.x * width), int(lm.y * height)) for lm in landmarks if getattr(lm, 'visibility', 1.0) > 0.3]
                if valid_coords:
                    xs = [c[0] for c in valid_coords]
                    ys = [c[1] for c in valid_coords]
                    x_min = max(0, min(xs) - 25)
                    y_min = max(0, min(ys) - 35)
                    x_max = min(width, max(xs) + 25)
                    y_max = min(height, max(ys) + 25)

                    bbox_color = (50, 50, 255) if is_asymmetric_frame else (0, 230, 118)

                    # Draw Bounding Box
                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), bbox_color, 2, cv2.LINE_AA)

                    # Draw Header Label Box
                    status_lbl = "HIGH ASYMMETRY" if is_asymmetric_frame else "NORMATIVE"
                    header_text = f"Patient Tracked | MediaPipe 3D [{status_lbl}]"
                    (tw, th), _ = cv2.getTextSize(header_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)

                    label_y1 = max(0, y_min - 24)
                    label_y2 = y_min
                    cv2.rectangle(frame, (x_min, label_y1), (x_min + tw + 16, label_y2), bbox_color, -1)
                    cv2.putText(frame, header_text, (x_min + 8, label_y2 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

                # 3. Draw Skeleton Connections with custom colors
                def lm_pt(lm_enum):
                    lm = landmarks[lm_enum.value]
                    return (int(lm.x * width), int(lm.y * height))

                left_leg_color = (50, 50, 255) if is_asymmetric_frame else (255, 220, 0)
                right_leg_color = (50, 50, 255) if is_asymmetric_frame else (50, 100, 255)
                torso_color = (0, 230, 118)

                # Draw Left Leg Lines
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_HIP), lm_pt(mp_pose.PoseLandmark.LEFT_KNEE), left_leg_color, 4, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_KNEE), lm_pt(mp_pose.PoseLandmark.LEFT_ANKLE), left_leg_color, 4, cv2.LINE_AA)

                # Draw Right Leg Lines
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.RIGHT_HIP), lm_pt(mp_pose.PoseLandmark.RIGHT_KNEE), right_leg_color, 4, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.RIGHT_KNEE), lm_pt(mp_pose.PoseLandmark.RIGHT_ANKLE), right_leg_color, 4, cv2.LINE_AA)

                # Draw Torso Connections
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_SHOULDER), lm_pt(mp_pose.PoseLandmark.RIGHT_SHOULDER), torso_color, 3, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_SHOULDER), lm_pt(mp_pose.PoseLandmark.LEFT_HIP), torso_color, 3, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.RIGHT_SHOULDER), lm_pt(mp_pose.PoseLandmark.RIGHT_HIP), torso_color, 3, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_HIP), lm_pt(mp_pose.PoseLandmark.RIGHT_HIP), torso_color, 3, cv2.LINE_AA)

                # 4. Draw Joint Dots
                keypoints_to_draw = [
                    mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.RIGHT_HIP,
                    mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.RIGHT_KNEE,
                    mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.RIGHT_ANKLE,
                    mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER,
                ]

                for kp in keypoints_to_draw:
                    pt = lm_pt(kp)
                    cv2.circle(frame, pt, 7, (255, 255, 0), -1, cv2.LINE_AA)
                    cv2.circle(frame, pt, 3, (255, 255, 255), -1, cv2.LINE_AA)

                # 5. Draw Live Clinical HUD Panel
                hud_x = width - 260
                hud_y = 20
                cv2.rectangle(frame, (hud_x, hud_y), (width - 15, hud_y + 85), (20, 24, 33), -1)
                cv2.rectangle(frame, (hud_x, hud_y), (width - 15, hud_y + 85), (60, 70, 90), 1)

                cv2.putText(frame, "LIVE CLINICAL METRICS", (hud_x + 10, hud_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 118), 1, cv2.LINE_AA)
                cv2.putText(frame, f"L Knee: {angle_l:.1f}deg", (hud_x + 10, hud_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 220, 0), 1, cv2.LINE_AA)
                cv2.putText(frame, f"R Knee: {angle_r:.1f}deg", (hud_x + 10, hud_y + 58), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (50, 100, 255), 1, cv2.LINE_AA)

                si_color = (50, 50, 255) if is_asymmetric_frame else (0, 230, 118)
                cv2.putText(frame, f"SI: {si_frame:.1f}%", (hud_x + 10, hud_y + 76), cv2.FONT_HERSHEY_SIMPLEX, 0.42, si_color, 1, cv2.LINE_AA)

            # Convert BGR frame to RGB for imageio writer
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frames.append(frame_rgb)

    cap.release()

    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass

    # Save to H.264 web-compatible MP4 file using imageio libx264 with pixelformat yuv420p
    writer = imageio.get_writer(
        output_path,
        fps=fps,
        codec="libx264",
        pixelformat="yuv420p",
        macro_block_size=None
    )
    for rgb_frame in rgb_frames:
        writer.append_data(rgb_frame)
    writer.close()

    return os.path.abspath(output_path)


def stream_annotated_frames(input_path: str, output_webm_path: str):
    """
    Generator that yields annotated RGB frames live (for Streamlit real-time preview)
    and saves a final VP9 WebM video file for guaranteed browser playback.

    Yields:
        np.ndarray: Annotated RGB frame (H, W, 3) for each video frame.

    After iteration is complete, the WebM file at output_webm_path is fully written and closed.

    Args:
        input_path (str): Path to input video file.
        output_webm_path (str): Path for output WebM file (VP9 codec).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input video not found: {input_path}")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open input video: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 640
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 480
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    if os.path.exists(output_webm_path):
        try:
            os.remove(output_webm_path)
        except Exception:
            pass

    writer = imageio.get_writer(
        output_webm_path,
        fps=fps,
        codec="libvpx-vp9",
        quality=7
    )

    mp_pose = mp.solutions.pose

    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    ) as pose:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            if results and results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

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
                is_asymmetric_frame = si_frame > 15.0

                valid_coords = [(int(lm.x * width), int(lm.y * height)) for lm in landmarks if getattr(lm, 'visibility', 1.0) > 0.3]
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

                def lm_pt(lm_enum):
                    lm = landmarks[lm_enum.value]
                    return (int(lm.x * width), int(lm.y * height))

                left_leg_color = (50, 50, 255) if is_asymmetric_frame else (255, 220, 0)
                right_leg_color = (50, 50, 255) if is_asymmetric_frame else (50, 100, 255)
                torso_color = (0, 230, 118)

                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_HIP), lm_pt(mp_pose.PoseLandmark.LEFT_KNEE), left_leg_color, 4, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_KNEE), lm_pt(mp_pose.PoseLandmark.LEFT_ANKLE), left_leg_color, 4, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.RIGHT_HIP), lm_pt(mp_pose.PoseLandmark.RIGHT_KNEE), right_leg_color, 4, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.RIGHT_KNEE), lm_pt(mp_pose.PoseLandmark.RIGHT_ANKLE), right_leg_color, 4, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_SHOULDER), lm_pt(mp_pose.PoseLandmark.RIGHT_SHOULDER), torso_color, 3, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_SHOULDER), lm_pt(mp_pose.PoseLandmark.LEFT_HIP), torso_color, 3, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.RIGHT_SHOULDER), lm_pt(mp_pose.PoseLandmark.RIGHT_HIP), torso_color, 3, cv2.LINE_AA)
                cv2.line(frame, lm_pt(mp_pose.PoseLandmark.LEFT_HIP), lm_pt(mp_pose.PoseLandmark.RIGHT_HIP), torso_color, 3, cv2.LINE_AA)

                for kp in [mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.RIGHT_HIP,
                           mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.RIGHT_KNEE,
                           mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.RIGHT_ANKLE,
                           mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER]:
                    pt = lm_pt(kp)
                    cv2.circle(frame, pt, 7, (255, 255, 0), -1, cv2.LINE_AA)
                    cv2.circle(frame, pt, 3, (255, 255, 255), -1, cv2.LINE_AA)

                hud_x, hud_y = width - 260, 20
                cv2.rectangle(frame, (hud_x, hud_y), (width - 15, hud_y + 85), (20, 24, 33), -1)
                cv2.rectangle(frame, (hud_x, hud_y), (width - 15, hud_y + 85), (60, 70, 90), 1)
                cv2.putText(frame, "LIVE CLINICAL METRICS", (hud_x + 10, hud_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 118), 1, cv2.LINE_AA)
                cv2.putText(frame, f"L Knee: {angle_l:.1f}deg", (hud_x + 10, hud_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 220, 0), 1, cv2.LINE_AA)
                cv2.putText(frame, f"R Knee: {angle_r:.1f}deg", (hud_x + 10, hud_y + 58), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (50, 100, 255), 1, cv2.LINE_AA)
                si_color = (50, 50, 255) if is_asymmetric_frame else (0, 230, 118)
                cv2.putText(frame, f"SI: {si_frame:.1f}%", (hud_x + 10, hud_y + 76), cv2.FONT_HERSHEY_SIMPLEX, 0.42, si_color, 1, cv2.LINE_AA)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            writer.append_data(frame_rgb)
            yield frame_rgb

    cap.release()
    writer.close()


if __name__ == "__main__":
    import sys
    print("cv_engine.py loaded successfully.")
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
        print(f"Processing {video_file}...")
        try:
            out_v = generate_annotated_video(video_file, "annotated_test.mp4")
            print(f"Annotated video (MP4) generated at: {out_v}")
            # Also test WebM generator
            webm_path = "annotated_test.webm"
            for _ in stream_annotated_frames(video_file, webm_path):
                pass
            print(f"Annotated video (WebM) generated at: {webm_path}")
        except Exception as e:
            print(f"Error processing video: {e}")

