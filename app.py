"""
app.py

KinemaTrace AI: Pediatric Markerless Motor Screening Dashboard
Streamlit application integrating OpenCV, MediaPipe BlazePose, and clinical kinematic analytics.
Outputs H.264 yuv420p HTML5 web-compatible video overlay player.
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from cv_engine import extract_pose_data, generate_annotated_video, stream_annotated_frames
from clinical_math import calculate_joint_angles, compute_symmetry_index, evaluate_gait_risk

# --- 1. Page Configuration & Custom Dark Medical Theme ---
st.set_page_config(
    page_title="KinemaTrace AI: Pediatric Markerless Motor Screening",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark medical aesthetic
st.markdown("""
    <style>
    /* Global dark theme colors */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Card containers */
    .medical-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }

    /* Metric card styles */
    .status-card-red {
        background: linear-gradient(135deg, rgba(255, 51, 68, 0.15) 0%, rgba(220, 20, 60, 0.05) 100%);
        border: 2px solid #ff3344;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 0 20px rgba(255, 51, 68, 0.25);
    }

    .status-card-green {
        background: linear-gradient(135deg, rgba(0, 230, 118, 0.15) 0%, rgba(0, 200, 83, 0.05) 100%);
        border: 2px solid #00e676;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 0 20px rgba(0, 230, 118, 0.25);
    }

    .status-title {
        font-size: 1.1rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .status-value {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .status-value-red {
        color: #ff4d4d;
    }

    .status-value-green {
        color: #00e676;
    }

    .status-score {
        font-size: 1.2rem;
        color: #8b949e;
    }

    /* Disclaimer banner */
    .disclaimer-box {
        background-color: #21262d;
        border-left: 5px solid #d29922;
        padding: 14px 20px;
        border-radius: 6px;
        margin-top: 30px;
        font-size: 0.95rem;
        color: #e6edf3;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. Sidebar: Patient Case Selection & Upload ---
st.sidebar.image("https://img.icons8.com/color/96/medical-heart.png", width=64)
st.sidebar.title("Patient Case Selection")

case_option = st.sidebar.radio(
    "Select Demonstration Case:",
    options=[
        "Patient Case 1: Normative Gait (Low Risk)",
        "Patient Case 2: Asymmetrical Limp (High Risk)",
        "Custom Upload (.mp4)"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("Clinical Parameters")
st.sidebar.markdown("""
- **Joint Target**: Bilateral Knee Flexion
- **Tracking Engine**: MediaPipe BlazePose 3D
- **Symmetry Threshold**: 15.0%
- **Sampling Rate**: 30 FPS
""")

st.sidebar.markdown("---")
st.sidebar.caption("KinemaTrace AI v1.0 • Pediatric Motor Screening")


# --- 3. Main Dashboard Header ---
st.title("🩺 KinemaTrace AI: Pediatric Markerless Motor Screening")
st.markdown("Automated 3D kinematic pose extraction, joint angle estimation, and bilateral gait asymmetry evaluation.")

st.markdown("---")


# --- 4. Load or Extract Gait Data & Video Path ---
raw_video_path = None
annotated_video_path = None
webm_video_path = None
df_pose = None

if case_option == "Patient Case 1: Normative Gait (Low Risk)":
    raw_video_path = "demo_normative.mp4"
    annotated_video_path = "demo_normative_annotated.mp4"
    webm_video_path = "demo_normative_annotated.webm"
    csv_path = "demo_normative.csv"
    patient_info = {"id": "PED-2026-001", "age": "7 y/o", "case": "Normative Control"}
    if os.path.exists(csv_path):
        df_pose = pd.read_csv(csv_path, index_col="frame")

elif case_option == "Patient Case 2: Asymmetrical Limp (High Risk)":
    raw_video_path = "demo_asymmetric.mp4"
    annotated_video_path = "demo_asymmetric_annotated.mp4"
    webm_video_path = "demo_asymmetric_annotated.webm"
    csv_path = "demo_asymmetric.csv"
    patient_info = {"id": "PED-2026-002", "age": "6 y/o", "case": "Post-Injury Asymmetric Gait"}
    if os.path.exists(csv_path):
        df_pose = pd.read_csv(csv_path, index_col="frame")

else:
    patient_info = {"id": "PED-CUSTOM", "age": "N/A", "case": "User Uploaded Video"}
    uploaded_file = st.sidebar.file_uploader("Upload custom video file (.mp4)", type=["mp4"])
    if uploaded_file is not None:
        raw_video_path = "temp_uploaded.mp4"
        annotated_video_path = "temp_uploaded_annotated.mp4"
        webm_video_path = "temp_uploaded_annotated.webm"
        with open(raw_video_path, "wb") as f:
            f.write(uploaded_file.read())
        if os.path.exists(webm_video_path):
            os.remove(webm_video_path)
        with st.spinner("Processing video frame-by-frame with MediaPipe BlazePose..."):
            try:
                df_pose = extract_pose_data(raw_video_path)
                st.sidebar.success("Pose extraction completed successfully!")
            except Exception as e:
                st.sidebar.error(f"Error processing video: {e}")


# Generate clinical pose overlay video if not present (MP4 for legacy, WebM for browser)
if raw_video_path and os.path.exists(raw_video_path):
    if not annotated_video_path or not os.path.exists(annotated_video_path):
        with st.spinner("Rendering clinical pose overlay..."):
            annotated_video_path = generate_annotated_video(
                raw_video_path,
                annotated_video_path or "temp_annotated.mp4"
            )


# Process pose data with cv_engine if CSV not cached
if raw_video_path and os.path.exists(raw_video_path) and df_pose is None:
    with st.spinner("Extracting 3D pose landmarks from video..."):
        try:
            df_pose = extract_pose_data(raw_video_path)
        except Exception as e:
            st.error(f"Failed to process video: {e}")


# --- 5. Main Layout Grid (2 Columns) ---
col_left, col_right = st.columns([5, 6], gap="large")

# --- LEFT COLUMN: Live Frame Stream + Final WebM Video Player ---
with col_left:
    st.subheader("📹 Live Motion Capture & Clinical Skeleton Tracking")

    live_stream = st.empty()
    video_container = st.empty()

    if raw_video_path and os.path.exists(raw_video_path):
        # Stream frames live if WebM not already cached
        if not webm_video_path or not os.path.exists(webm_video_path):
            with st.spinner("Rendering clinical pose overlay (live streaming)..."):
                frame_count = 0
                for live_frame in stream_annotated_frames(
                    raw_video_path,
                    webm_video_path or "temp_annotated.webm"
                ):
                    # Show every 3rd frame to keep the UI responsive
                    if frame_count % 3 == 0:
                        live_stream.image(
                            live_frame,
                            channels="RGB",
                            caption="⚡ Live Clinical Tracking — Rendering skeleton overlay...",
                            use_container_width=True
                        )
                    frame_count += 1
            live_stream.empty()  # Clear live feed once done

        # Display final replayable WebM vid
        if webm_video_path and os.path.exists(webm_video_path):
            video_container.empty()
            with open(webm_video_path, "rb") as f:
              video_bytes = f.read()
              video_container.video(video_bytes, format="video/webm", autoplay=True, loop=True)
              st.caption(f"📍 Patient ID: **{patient_info['id']}** | Age: **{patient_info['age']}** | Clinical Note: **{patient_info['case']}**")

        else:
            video_container.warning("Video processing in progress. Please wait.")
    else:
        video_container.warning("Please upload an MP4 video or select a demonstration case from the sidebar.")

    # Show raw joint coordinates toggle
    with st.expander("🔍 View Raw 3D Joint Coordinates Table"):
        if df_pose is not None:
            st.dataframe(df_pose.head(10), use_container_width=True)
        else:
            st.info("No pose data loaded.")



# --- RIGHT COLUMN: Clinical Metric Card & Interactive Line Chart ---
with col_right:
    st.subheader("📊 Kinematic Gait & Asymmetry Analysis")

    if df_pose is not None and not df_pose.empty:
        # Calculate joint angles & gait risk
        angles_df = calculate_joint_angles(df_pose)
        risk_result = evaluate_gait_risk(df_pose)
        si_series = compute_symmetry_index(angles_df["left_knee_angle"], angles_df["right_knee_angle"])

        # Display Large Clinical Status Metric Card
        status = risk_result["status"]
        score = risk_result["risk_score"]
        color = risk_result["color"]

        card_class = "status-card-red" if color == "red" else "status-card-green"
        text_class = "status-value-red" if color == "red" else "status-value-green"
        badge_icon = "⚠️" if color == "red" else "✅"

        st.markdown(f"""
            <div class="{card_class}">
                <div class="status-title" style="color: {'#ff8888' if color == 'red' else '#88ffbb'};">Clinical Screening Result</div>
                <div class="status-value {text_class}">{badge_icon} {status}</div>
                <div class="status-score">Mean Symmetry Index: <strong>{score:.1f}%</strong> (Normative Threshold: ≤ 15.0%)</div>
            </div>
        """, unsafe_allow_html=True)

        # Plotly Interactive Line Chart: Left Knee Angle vs Right Knee Angle
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=angles_df.index,
            y=angles_df["left_knee_angle"],
            mode="lines",
            name="Left Knee Angle (°)",
            line=dict(color="#00e5ff", width=3),
            hovertemplate="Frame %{x}: Left Knee %{y:.1f}°"
        ))

        fig.add_trace(go.Scatter(
            x=angles_df.index,
            y=angles_df["right_knee_angle"],
            mode="lines",
            name="Right Knee Angle (°)",
            line=dict(color="#ff4081", width=3, dash="solid" if color == "green" else "dot"),
            hovertemplate="Frame %{x}: Right Knee %{y:.1f}°"
        ))

        fig.update_layout(
            title=dict(
                text="Bilateral Knee Flexion Angles Over Time",
                font=dict(size=16, color="#e6edf3")
            ),
            xaxis=dict(
                title="Frame Number (#)",
                gridcolor="#21262d",
                zerolinecolor="#30363d",
                showgrid=True
            ),
            yaxis=dict(
                title="Interior Angle (Degrees °)",
                gridcolor="#21262d",
                zerolinecolor="#30363d",
                showgrid=True,
                range=[60, 190]
            ),
            paper_bgcolor="#161b22",
            plot_bgcolor="#0d1117",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="#c9d1d9")
            ),
            margin=dict(l=40, r=40, t=60, b=40),
            height=340
        )

        st.plotly_chart(fig, use_container_width=True)

        # Additional Kinematic Summary Statistics
        st.markdown("##### 📈 Kinematic Summary Metrics")
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("Left Knee ROM", f"{angles_df['left_knee_angle'].max() - angles_df['left_knee_angle'].min():.1f}°")
        stat_col2.metric("Right Knee ROM", f"{angles_df['right_knee_angle'].max() - angles_df['right_knee_angle'].min():.1f}°")
        stat_col3.metric("Peak Symmetry Index", f"{si_series.max():.1f}%")

    else:
        st.info("Awaiting video processing and pose calculation...")


# --- 6. Prominent Medical Disclaimer Banner ---
st.markdown("---")
st.markdown("""
    <div class="disclaimer-box">
        <strong>⚠️ CAUTION:</strong> For Investigational Pediatric Screening Only. Not a definitive clinical diagnosis.
        All algorithmic outputs must be reviewed by a licensed pediatric clinician or physical therapist before clinical action.
    </div>
""", unsafe_allow_html=True)
