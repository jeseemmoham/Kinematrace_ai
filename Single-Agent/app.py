"""
app.py (Single-Agent)

KinemaTrace AI: Single-Agent Pediatric Markerless Gait Screening Dashboard
Streamlit interface for the unified autonomous KinemaTrace single agent.
"""

import os
import sys
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from single_agent import KinemaTraceSingleAgent

st.set_page_config(
    page_title="KinemaTrace AI — Single-Agent Motor Screening",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🩺 KinemaTrace AI — Single-Agent Architecture")
st.caption("Pediatric Markerless Gait Screening powered by a single autonomous agent orchestrating the complete workflow.")

st.sidebar.header("Agent Configuration")
agent = KinemaTraceSingleAgent()

st.sidebar.markdown(f"**Agent Name:** {agent.agent_name}")
st.sidebar.markdown(f"**Role:** {agent.role}")
st.sidebar.info(agent.goal)

st.sidebar.header("Patient & Video Input")
patient_id = st.sidebar.text_input("Patient ID", value="PATIENT-101")
patient_name = st.sidebar.text_input("Patient Name", value="Alex Smith")
patient_age = st.sidebar.selectbox("Age Group", ["1-2 years", "2-3 years", "3-4 years"], index=1)

demo_choice = st.sidebar.selectbox("Select Demo Video", ["demo_normative.mp4", "demo_asymmetric.mp4"])
custom_upload = st.sidebar.file_uploader("Or Upload Custom Video (MP4/WebM)", type=["mp4", "webm", "mov"])

script_dir = os.path.dirname(os.path.abspath(__file__))
if custom_upload is not None:
    video_path = os.path.join(script_dir, f"temp_{custom_upload.name}")
    with open(video_path, "wb") as f:
        f.write(custom_upload.getbuffer())
else:
    video_path = os.path.join(script_dir, demo_choice)

if st.sidebar.button("Run Single-Agent Screening", type="primary"):
    with st.spinner("Single Agent executing complete pipeline (Validation -> Pose -> Biomechanics -> Risk -> PDF)..."):
        result = agent.run_complete_pipeline(
            video_path=video_path,
            patient_id=patient_id,
            patient_name=patient_name,
            patient_age=patient_age
        )

    if result["status"] == "SUCCESS":
        st.success(f"✅ {result['agent_summary']}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Video Quality", result["video_quality"]["status"], f"Score: {result['video_quality']['video_quality_score']}/100")
        col2.metric("Gait Symmetry", f"{result['biomechanical_metrics']['gait_symmetry_pct']}%", "Normal >= 90%")
        col3.metric("Clinical Risk Level", result["clinical_risk"]["risk_level"], f"Severity: {result['clinical_risk']['severity_score']}")
        col4.metric("Progress Status", result["longitudinal_progress"]["progress_status"])

        st.subheader("Biomechanical Knee Flexion Metrics")
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Left Knee ROM", f"{result['biomechanical_metrics']['left_knee_rom_deg']}°")
        m_col2.metric("Right Knee ROM", f"{result['biomechanical_metrics']['right_knee_rom_deg']}°")
        m_col3.metric("ROM Discrepancy", f"{result['biomechanical_metrics']['rom_difference_deg']}°")

        st.subheader("Clinical Recommendation & Guidance")
        st.info(f"**Recommendation:** {result['clinical_risk']['clinical_recommendation']}\n\n**Follow-up Timeline:** {result['clinical_risk']['followup_timeline']}")

        if result['clinical_risk']['triggered_risk_factors']:
            st.warning("**Triggered Risk Factors:**\n" + "\n".join([f"- {factor}" for factor in result['clinical_risk']['triggered_risk_factors']]))

        if os.path.exists(result["generated_pdf_report"]):
            with open(result["generated_pdf_report"], "rb") as pdf_file:
                st.download_button(
                    label="📄 Download Clinical PDF Report",
                    data=pdf_file,
                    file_name=os.path.basename(result["generated_pdf_report"]),
                    mime="application/pdf"
                )
    else:
        st.error(f"Pipeline Failed: {result.get('message', 'Unknown error')}")
else:
    st.info("Click 'Run Single-Agent Screening' in the sidebar to start the analysis.")
