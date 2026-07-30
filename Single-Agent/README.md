# KinemaTrace AI — Single-Agent Architecture

## Overview

**KinemaTrace AI (Single-Agent Implementation)** is a streamlined, monolithic autonomous pediatric gait analysis system. Unlike the Multi-Agent architecture where tasks are distributed across specialized agent services communicating via REST APIs, the Single-Agent architecture uses one unified controller—`KinemaTraceSingleAgent` (`single_agent.py`)—that orchestrates the entire video-to-report clinical workflow sequentially within a single agent context.

---

## Single-Agent Architecture & Workflow

```
                                 ┌───────────────────────────┐
                                 │   Video Upload (User)     │
                                 └─────────────┬─────────────┘
                                               │
                                               ▼
                                 ┌───────────────────────────┐
                                 │ KinemaTrace Single Agent  │
                                 │     (single_agent.py)     │
                                 └─────────────┬─────────────┘
                                               │
               ┌───────────────────────────────┼───────────────────────────────┐
               │                               │                               │
               ▼                               ▼                               ▼
  ┌──────────────────────────┐   ┌──────────────────────────┐   ┌──────────────────────────┐
  │  1. Video Quality Check  │   │  2. Pose & Biomechanics  │   │   3. Pediatric Risk      │
  │   (Resolution, FPS,      │   │  (3D Landmarks, Knee/Hip │   │   (Normative Lookup,     │
  │    Visibility Gate)      │   │   ROM, Symmetry Index)   │   │    Severity Score)       │
  └──────────────────────────┘   └──────────────────────────┘   └──────────────────────────┘
               │                               │                               │
               └───────────────────────────────┼───────────────────────────────┘
                                               │
               ┌───────────────────────────────┴───────────────────────────────┐
               │                                                               │
               ▼                                                               ▼
  ┌──────────────────────────┐                                   ┌──────────────────────────┐
  │  4. Progress Comparison  │                                   │ 5. Clinical PDF Report & │
  │   (Baseline vs Current,  │                                   │  Conversational Guidance │
  │    Status Shift)         │                                   │ (pdf_generator.py, Q&A)  │
  └──────────────────────────┘                                   └──────────────────────────┘
```

---

## How the Single Agent Performs All Tasks

The central `KinemaTraceSingleAgent` class encapsulates all necessary clinical screening steps:

1. **Video Quality Validation**: Evaluates smartphone video properties (resolution, FPS, walking duration, full-body pose visibility rate) before initiating kinematic analysis.
2. **Pose Extraction & Biomechanical Calculations**: Reuses `cv_engine.py` for MediaPipe pose extraction and `clinical_math.py` to calculate frame-by-frame joint angles and bilateral Symmetry Index (SI).
3. **Pediatric Normative Lookup & Risk Assessment**: Compares computed knee ROM and symmetry metrics against age-stratified reference thresholds from `pediatric_normatives.py` to calculate clinical severity scores and risk levels (`LOW`, `MEDIUM`, `HIGH`).
4. **Longitudinal Progress Tracking**: Compares current metrics with historical baseline sessions to compute delta symmetry and status (`IMPROVED`, `STABLE`, `WORSENED`).
5. **Clinical PDF Report Generation**: Reuses `pdf_generator.py` to automatically compile patient metadata, kinematic tables, triggered risk factors, and agent notes into a downloadable report.
6. **Conversational Assistance**: Provides direct natural language Q&A for clinician inquiries regarding patient results and progress.

---

## Shared Mathematical & Computer Vision Foundation

To maintain complete scientific and mathematical parity between Single-Agent and Multi-Agent implementations, the Single-Agent reuses the exact same underlying modules:

- **`clinical_math.py`**: Interior joint vector angles $\theta = \arccos\left(\frac{\vec{v}_1 \cdot \vec{v}_2}{\|\vec{v}_1\| \|\vec{v}_2\|}\right) \times \frac{180}{\pi}$ and Symmetry Index (SI) calculations.
- **`cv_engine.py`**: MediaPipe BlazePose 3D landmark extraction and skeletal overlay rendering.
- **`pediatric_normatives.py`**: Age-stratified reference ranges for toddlers aged 1–4 years.
- **`pdf_generator.py`**: Professional ReportLab PDF document compilation.

---

## Tech Stack

- **Core Language**: Python 3.10+
- **Computer Vision & Kinematics**: MediaPipe, OpenCV, NumPy, Pandas
- **Interactive Dashboard**: Streamlit, Plotly
- **PDF Generation**: ReportLab
- **Automated Testing**: pytest

---

## Installation & Running Instructions

### 1. Run via Streamlit Dashboard

```bash
# Navigate to Single-Agent directory
cd Single-Agent

# Install dependencies
pip install -r requirements.txt

# Run Streamlit dashboard
streamlit run app.py
```

### 2. Run via Command Line Interface (CLI)

```bash
# Execute single agent directly on a video file
python single_agent.py --video demo_normative.mp4 --age 2 --patient_id PATIENT-101
```

### 3. Run Automated Verification Test Suite

```bash
# Run pytest verification suite
python test_single_agent.py
```
