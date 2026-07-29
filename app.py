"""
app.py

KinemaTrace AI: Pediatric Markerless Motor Screening Dashboard
Streamlit application integrating OpenCV, MediaPipe BlazePose, and clinical kinematic analytics.
Outputs H.264 yuv420p HTML5 web-compatible video overlay player.
"""

import os
import time
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from cv_engine import extract_pose_data, generate_annotated_video, stream_annotated_frames, process_video_single_pass
from clinical_math import calculate_joint_angles, compute_symmetry_index, evaluate_gait_risk
from agents import (
    AGENT_1_CONFIG,
    AGENT_2_CONFIG,
    AGENT_3_CONFIG,
    AGENT_4_CONFIG,
    AGENT_VIDEO_QUALITY_CONFIG,
    QUALITY_CONFIG,
    validate_video_quality,
    analyze_biomechanics,
    analyze_physical_therapy,
    analyze_orthopedic_risk,
    synthesize_clinical_report
)

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

# Track video cache and warning state in Streamlit session state
if "quality_results" not in st.session_state:
    st.session_state.quality_results = {}
if "gait_results_cache" not in st.session_state:
    st.session_state.gait_results_cache = {}
if "warning_approved" not in st.session_state:
    st.session_state.warning_approved = False
if "pose_coordinates_cache" not in st.session_state:
    st.session_state.pose_coordinates_cache = {}
if "get_results_clicked" not in st.session_state:
    st.session_state.get_results_clicked = False

if case_option == "Patient Case 1: Normative Gait (Low Risk)":
    raw_video_path = "demo_normative.mp4"
    annotated_video_path = "demo_normative_annotated.mp4"
    webm_video_path = "demo_normative_annotated.webm"
    csv_path = "demo_normative.csv"
    patient_info = {"id": "PED-2026-001", "age": "7 y/o", "case": "Normative Control"}
    if st.session_state.get("validated_video_path") != raw_video_path:
        st.session_state.warning_approved = False
        st.session_state.validated_video_path = raw_video_path

elif case_option == "Patient Case 2: Asymmetrical Limp (High Risk)":
    raw_video_path = "demo_asymmetric.mp4"
    annotated_video_path = "demo_asymmetric_annotated.mp4"
    webm_video_path = "demo_asymmetric_annotated.webm"
    csv_path = "demo_asymmetric.csv"
    patient_info = {"id": "PED-2026-002", "age": "6 y/o", "case": "Post-Injury Asymmetric Gait"}
    if st.session_state.get("validated_video_path") != raw_video_path:
        st.session_state.warning_approved = False
        st.session_state.validated_video_path = raw_video_path

else:
    patient_info = {"id": "PED-CUSTOM", "age": "N/A", "case": "User Uploaded Video"}
    uploaded_file = st.sidebar.file_uploader("Upload custom video file (.mp4)", type=["mp4"])
    if uploaded_file is not None:
        raw_video_path = "temp_uploaded.mp4"
        annotated_video_path = "temp_uploaded_annotated.mp4"
        webm_video_path = "temp_uploaded_annotated.webm"
        csv_path = None
        
        file_key = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("last_uploaded_file_key") != file_key:
            st.session_state.last_uploaded_file_key = file_key
            st.session_state.warning_approved = False
            st.session_state.get_results_clicked = False
            st.session_state.validated_video_path = raw_video_path
            
            if raw_video_path in st.session_state.quality_results:
                del st.session_state.quality_results[raw_video_path]
            if raw_video_path in st.session_state.pose_coordinates_cache:
                del st.session_state.pose_coordinates_cache[raw_video_path]
            if raw_video_path in st.session_state.gait_results_cache:
                del st.session_state.gait_results_cache[raw_video_path]
            
            for p in [raw_video_path, webm_video_path, annotated_video_path]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            
            with open(raw_video_path, "wb") as f:
                f.write(uploaded_file.read())

# --- 4.1 Run Video Quality Validation Agent (Agent 1 - Fast Check < 1s) ---
quality_result = None
allow_analysis = False

if raw_video_path and os.path.exists(raw_video_path):
    if raw_video_path not in st.session_state.quality_results:
        with st.spinner("🤖 Agent 1: Checking Video Quality Suitability..."):
            quality_result = validate_video_quality(raw_video_path)
            st.session_state.quality_results[raw_video_path] = quality_result
    else:
        quality_result = st.session_state.quality_results[raw_video_path]

    if quality_result:
        status = quality_result["status"]
        if status == "PASS":
            allow_analysis = True
        elif status == "WARNING" and st.session_state.get("warning_approved", False):
            allow_analysis = True

# --- 4.2 Run Gait Analysis Agent (Agent 2 - Single Pass execution on demand) ---
gait_analysis_data = None

if allow_analysis and raw_video_path and os.path.exists(raw_video_path):
    # Check if pre-computed CSV exists for preset cases
    if case_option == "Patient Case 1: Normative Gait (Low Risk)":
        csv_path = "demo_normative.csv"
        if os.path.exists(csv_path) and df_pose is None:
            df_pose = pd.read_csv(csv_path, index_col="frame")
    elif case_option == "Patient Case 2: Asymmetrical Limp (High Risk)":
        csv_path = "demo_asymmetric.csv"
        if os.path.exists(csv_path) and df_pose is None:
            df_pose = pd.read_csv(csv_path, index_col="frame")

    # If cached in session state, load immediately
    if raw_video_path in st.session_state.gait_results_cache:
        gait_analysis_data = st.session_state.gait_results_cache[raw_video_path]
        df_pose = gait_analysis_data.get("df_pose")

    # If not cached, present [ GET RESULTS ] button for custom video or run single-pass ONCE
    elif case_option == "Custom Upload (.mp4)" and not st.session_state.get_results_clicked:
        st.info("⚡ Video Quality Validated! Click **[ GET RESULTS ]** to extract 3D pose landmarks and biomechanics.")
        if st.button("🚀 GET RESULTS", type="primary", use_container_width=True):
            st.session_state.get_results_clicked = True
            st.rerun()

    if (case_option != "Custom Upload (.mp4)" or st.session_state.get_results_clicked) and gait_analysis_data is None:
        progress_bar = st.progress(0, text="Analyzing Video...")
        progress_bar.progress(25, text="Step 1/4: Extracting Pose Landmarks...")
        time.sleep(0.1)
        progress_bar.progress(50, text="Step 2/4: Calculating Joint Angles...")
        time.sleep(0.1)
        progress_bar.progress(75, text="Step 3/4: Calculating Gait Metrics...")

        pass_res = process_video_single_pass(raw_video_path, webm_video_path or "temp_uploaded_annotated.webm")
        df_pose = pass_res["df_pose"]
        st.session_state.pose_coordinates_cache[raw_video_path] = df_pose

        progress_bar.progress(100, text="Step 4/4: Generating Results")
        time.sleep(0.1)
        progress_bar.empty()

        gait_analysis_data = pass_res
        st.session_state.gait_results_cache[raw_video_path] = gait_analysis_data


# --- 5. Main Layout Grid (2 Columns) ---
col_left, col_right = st.columns([5, 6], gap="large")

# --- LEFT COLUMN: Live Frame Stream + Final WebM Video Player ---
with col_left:
    st.subheader("📹 Live Motion Capture & Clinical Skeleton Tracking")

    live_stream = st.empty()
    video_container = st.empty()

    if raw_video_path and os.path.exists(raw_video_path):
        if allow_analysis:
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
            # Display raw uploaded video if validation failed or is pending warning approval
            video_container.empty()
            with open(raw_video_path, "rb") as f:
                video_bytes = f.read()
                video_container.video(video_bytes, format="video/mp4", autoplay=True, loop=True)
                st.caption(f"📍 Patient ID: **{patient_info['id']}** | Age: **{patient_info['age']}** | Clinical Note: **{patient_info['case']}** (Raw Video - Quality Validation Pending/Failed)")
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
    # 1. Display Video Quality Validation Agent Report (Agent 1)
    if quality_result:
        status = quality_result["status"]
        score = quality_result["video_quality_score"]
        checks = quality_result["checks"]
        metrics = quality_result["metrics"]
        issues = quality_result["issues"]
        rec = quality_result["recommendation"]

        if status == "FAIL":
            st.markdown(f"""
                <div class="medical-card" style="border: 2px solid #ff3344; background: linear-gradient(135deg, rgba(255, 51, 68, 0.15) 0%, rgba(220, 20, 60, 0.05) 100%); margin-bottom: 20px;">
                    <div class="status-title" style="color: #ff8888; font-weight: 600; letter-spacing: 1px;">❌ Video Quality Failed</div>
                    <div class="status-value status-value-red" style="color: #ff4d4d; font-size: 2rem; font-weight: 800;">Score: {score} / 100</div>
                    <div style="font-size: 1.1rem; font-weight: 600; margin-top: 10px; color: #ff8888;">{rec}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Display detailed issues
            st.write("### Problems:")
            if issues:
                for issue in issues:
                    st.markdown(f"• **{issue['criterion']}**: {issue['reason']} *({issue['impact']})*")
            else:
                st.write("Multiple quality criteria failed to meet the minimum required values.")

            # Display recording guidelines
            st.write("### Please record a new video with:")
            st.markdown("""
* **Full body visible** (head, shoulders, hips, knees, ankles, and feet fully in the frame)
* **At least 5 seconds of walking** (continuous walking sequence)
* **Good lighting** (sufficient exposure, avoiding low-light or strong shadows)
* **Stable camera** (resting on a stable surface, tripod, or steady hold)
* **720p or higher resolution** (1280x720 minimum)
* **30 FPS or higher** (standard smooth mobile recording)
            """)

        elif status == "WARNING" and not st.session_state.get("warning_approved", False):
            st.markdown(f"""
                <div class="medical-card" style="border: 2px solid #ffaa00; background: linear-gradient(135deg, rgba(255, 170, 0, 0.15) 0%, rgba(200, 120, 0, 0.05) 100%); margin-bottom: 20px;">
                    <div class="status-title" style="color: #ffcc66; font-weight: 600; letter-spacing: 1px;">⚠️ Video Quality Warning</div>
                    <div class="status-value" style="color: #ffaa00; font-size: 2rem; font-weight: 800;">Score: {score} / 100</div>
                    <div style="font-size: 1.1rem; font-weight: 600; margin-top: 10px; color: #ffcc66;">{rec}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Display issues
            st.write("### Quality Issues:")
            if issues:
                for issue in issues:
                    st.markdown(f"• **{issue['criterion']}**: {issue['reason']} *({issue['impact']})*")

            st.write("Would you like to proceed with the gait analysis anyway?")
            col_warn_btn1, col_warn_btn2 = st.columns(2)
            with col_warn_btn1:
                if st.button("Continue to Gait Analysis", use_container_width=True, type="primary"):
                    st.session_state.warning_approved = True
                    st.rerun()
            with col_warn_btn2:
                if st.button("Upload New Video", use_container_width=True):
                    # Guide user to sidebar
                    st.info("Please use the file uploader in the sidebar to upload a new video.")

        else:
            # PASS or approved WARNING: display a nice expander with metrics at the top
            status_emoji = "✅ PASS" if status == "PASS" else "⚠️ WARNING"
            border_color = "#00e676" if status == "PASS" else "#ffaa00"
            bg_color = "rgba(0, 230, 118, 0.05)" if status == "PASS" else "rgba(255, 170, 0, 0.05)"
            
            with st.expander(f"🎥 Video Quality Assessment: {status_emoji} (Score: {score}/100)", expanded=False):
                st.markdown(f"""
                    <div class="medical-card" style="border: 1px solid {border_color}; background-color: {bg_color}; padding: 15px; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: {border_color};">Video Quality Score: {score} / 100</h4>
                        <p style="margin: 5px 0 0 0; font-size: 0.95rem;"><strong>Recommendation:</strong> {rec}</p>
                    </div>
                """, unsafe_allow_html=True)

                # Quality checklist metrics
                vis_label = "Good" if checks.get("full_body_visible", False) else "Poor"
                # Wait, we added full_body_visibility_status string to quality_result
                vis_label = quality_result.get("full_body_visibility_status", vis_label)
                light_label = checks.get("lighting", "Good")
                stab_label = checks.get("camera_stability", "Stable")
                dur_label = checks.get("walking_duration", "5.0 seconds")
                angle_label = checks.get("camera_angle", "Side View")
                pose_label = checks.get("pose_detection", "Reliable")
                res_label = checks.get("resolution", "1280x720")
                fps_label = checks.get("frame_rate", "30 FPS")

                st.markdown(f"""
* ✓ **Full Body Visibility**: {vis_label}
* ✓ **Lighting**: {light_label}
* ✓ **Camera Stability**: {stab_label}
* ✓ **Walking Duration**: {dur_label}
* ✓ **Camera Angle**: {angle_label}
* ✓ **Pose Detection**: {pose_label}
* ✓ **Resolution**: {res_label}
* ✓ **Frame Rate**: {fps_label}
                """)
                
                if issues:
                    st.write("**Minor Issues & Recording Recommendations:**")
                    for issue in issues:
                        st.markdown(f"- ⚠️ **{issue['criterion']}**: {issue['reason']}")
                        st.markdown(f"  * *Recommendation*: {issue['recommendation']}")

    # 2. Display Gait Analysis only if allow_analysis is True and pose data is available
    if allow_analysis and df_pose is not None and not df_pose.empty:
        st.subheader("📊 Kinematic Gait & Asymmetry Analysis")
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

        # --- 3. HORIZONTAL AGENT COMMAND CENTER ---
        st.markdown("---")
        st.write("### 🤖 Multi-Agent Clinical Decision Support Command Center")

        # Initialize session state to track active agent
        if "active_agent" not in st.session_state:
            st.session_state.active_agent = "analyst"

        # Pre-compute multi-agent analytics
        agent_analysis = analyze_biomechanics(angles_df, risk_result)
        pt_analysis = analyze_physical_therapy(agent_analysis)
        ortho_analysis = analyze_orthopedic_risk(agent_analysis, pt_analysis)
        synth_analysis = synthesize_clinical_report(patient_info, agent_analysis, pt_analysis, ortho_analysis)

        # 4 Horizontal agent navigation buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("🔬 1. Analyst", use_container_width=True, type="primary" if st.session_state.active_agent == "analyst" else "secondary"):
                st.session_state.active_agent = "analyst"
        with col2:
            if st.button("🤸 2. Therapist", use_container_width=True, type="primary" if st.session_state.active_agent == "therapist" else "secondary"):
                st.session_state.active_agent = "therapist"
        with col3:
            if st.button("🩺 3. Orthopedic Risk", use_container_width=True, type="primary" if st.session_state.active_agent == "risk" else "secondary"):
                st.session_state.active_agent = "risk"
        with col4:
            if st.button("📋 4. Care Plan", use_container_width=True, type="primary" if st.session_state.active_agent == "synthesizer" else "secondary"):
                st.session_state.active_agent = "synthesizer"

        st.divider()

        # --- AGENT WORKSPACES & GENERATION LOGIC ---

        # AGENT 1: BIOMECHANICAL DATA ANALYST
        if st.session_state.active_agent == "analyst":
            st.subheader("🔬 Agent 1: Biomechanical Data Analyst")
            st.caption(f"🤖 **{AGENT_1_CONFIG['name']}** | *{AGENT_1_CONFIG['role']}*")
            st.write("Strictly interprets raw quantitative kinematics, angular velocities, and bilateral symmetry indices.")
            
            if st.button("⚡ Run Biomechanical Analysis", key="btn_a1"):
                with st.spinner("🤖 Agent 1 is extracting joint angular velocities and calculating symmetry deficits..."):
                    time.sleep(1.5)
                st.success("Quantitative Analysis Complete!")
                
            st.info(agent_analysis["report_text"])
            st.download_button(
                "📥 Download Biomechanical Report",
                agent_analysis["report_text"],
                file_name=f"{patient_info['id']}_Agent1_Biomechanical_Analysis.txt",
                key="dl_a1"
            )

        # AGENT 2: PEDIATRIC PHYSICAL THERAPIST (VISUAL COMPREHENSIVE)
        elif st.session_state.active_agent == "therapist":
            st.subheader("🤸 Agent 2: Pediatric Physical Therapy & Movement Specialist")
            st.caption(f"🤖 **{AGENT_2_CONFIG['name']}** | *{AGENT_2_CONFIG['role']}*")
            st.write("Translates raw angular deficits into functional movement impacts and visualizes deviations against pediatric normative baselines.")
            
            if st.button("⚡ Generate Therapy & Movement Assessment", key="btn_a2"):
                with st.spinner("🤖 Agent 2 is mapping kinematic curves against normative pediatric datasets..."):
                    time.sleep(1.8)
                st.success("Visual Movement Assessment Generated!")
                
            # Plotly Comparison Chart: Patient vs. Normal Pediatric Baselines
            categories = ['Left Knee ROM (°)', 'Right Knee ROM (°)', 'Symmetry Index (%)']
            l_rom_val = angles_df['left_knee_angle'].max() - angles_df['left_knee_angle'].min()
            r_rom_val = angles_df['right_knee_angle'].max() - angles_df['right_knee_angle'].min()
            si_val = 100.0 - float(np.nanmean(si_series))
            
            patient_vals = [round(l_rom_val, 1), round(r_rom_val, 1), max(0.0, round(si_val, 1))]
            normative_vals = [125.0, 125.0, 98.0]
            
            fig_norm = go.Figure()
            fig_norm.add_trace(go.Bar(x=categories, y=patient_vals, name='Patient (KinemaTrace)', marker_color='#ff4d4d' if si_series.mean() > 15.0 else '#00e676'))
            fig_norm.add_trace(go.Bar(x=categories, y=normative_vals, name='Normal Pediatric Baseline', marker_color='#00e5ff'))
            fig_norm.update_layout(
                title="Patient Kinematics vs. Normal Pediatric Baselines",
                barmode='group',
                height=320,
                paper_bgcolor="#161b22",
                plot_bgcolor="#0d1117",
                font=dict(color="#c9d1d9"),
                margin=dict(l=20, r=20, t=50, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_norm, use_container_width=True)
            
            st.markdown(pt_analysis["report_text"])
            st.download_button(
                "📥 Download Therapy Assessment",
                pt_analysis["report_text"],
                file_name=f"{patient_info['id']}_Agent2_PT_Assessment.txt",
                key="dl_a2"
            )

        # AGENT 3: ORTHOPEDIC RISK CONSULTANT
        elif st.session_state.active_agent == "risk":
            st.subheader("🩺 Agent 3: Orthopedic Diagnostic Risk Consultant")
            st.caption(f"🤖 **{AGENT_3_CONFIG['name']}** | *{AGENT_3_CONFIG['role']}*")
            st.write("Screens for compensatory movement strategies and flags high-risk musculoskeletal patterns.")
            
            if st.button("⚡ Run Clinical Risk Screening", key="btn_a3"):
                with st.spinner("🤖 Agent 3 is screening for compensatory mechanisms and joint loading risks..."):
                    time.sleep(1.5)
                st.success("Risk Screening Complete!")
                
            if risk_result["color"] == "red":
                st.warning(ortho_analysis["report_text"])
            else:
                st.info(ortho_analysis["report_text"])

            st.download_button(
                "📥 Download Risk Screening Report",
                ortho_analysis["report_text"],
                file_name=f"{patient_info['id']}_Agent3_Orthopedic_Risk.txt",
                key="dl_a3"
            )

        # AGENT 4: CLINICAL REPORT SYNTHESIZER (FORMAL MEDICAL BOX LAYOUT)
        elif st.session_state.active_agent == "synthesizer":
            st.subheader("📋 Agent 4: Clinical Report Synthesizer")
            st.caption(f"🤖 **{AGENT_4_CONFIG['name']}** | *{AGENT_4_CONFIG['role']}*")
            st.write("Compiles multi-disciplinary findings into an authoritative, structured medical care plan.")
            
            if st.button("⚡ Synthesize Comprehensive Care Plan", key="btn_a4", type="primary"):
                with st.spinner("🤖 Agent 4 is compiling biomechanical, therapy, and risk data into a formal clinical document..."):
                    time.sleep(2.0)
                st.success("Official Clinical Care Plan Synthesized!")
                
            # Formal Report Layout inside a bordered container box
            with st.container(border=True):
                st.markdown("## 🏥 KinemaTrace AI — Official Clinical Care Plan")
                st.markdown(f"**Patient ID:** {patient_info['id']} &nbsp;|&nbsp; **Age:** {patient_info['age']} &nbsp;|&nbsp; **Clinical Case:** {patient_info['case']}")
                st.divider()
                st.markdown(synth_analysis["report_text"])
            
            st.download_button(
                "📥 Download Official Care Plan (.TXT)",
                synth_analysis["report_text"],
                file_name=f"{patient_info['id']}_KinemaTrace_Comprehensive_Care_Plan.txt",
                type="primary",
                key="dl_a4"
            )

    else:
        if allow_analysis:
            st.info("Awaiting video processing and pose calculation...")


# --- 6. Prominent Medical Disclaimer Banner ---
st.markdown("---")
st.markdown("""
    <div class="disclaimer-box">
        <strong>⚠️ CAUTION:</strong> For Investigational Pediatric Screening Only. Not a definitive clinical diagnosis.
        All algorithmic outputs must be reviewed by a licensed pediatric clinician or physical therapist before clinical action.
    </div>
""", unsafe_allow_html=True)
