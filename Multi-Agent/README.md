# KinemaTrace AI — Multi-Agent Architecture

## Overview

**KinemaTrace AI (Multi-Agent Implementation)** is a pediatric markerless gait screening and motor analysis platform powered by a collaborative mesh of specialized AI agents. Designed for pediatricians, physical therapists, and pediatric orthopedic specialists, the system converts raw smartphone walking videos into objective kinematic measurements, risk assessments, longitudinal progress comparisons, and clinical reports.

---

## Specialized Agent Roster & Responsibilities

The Multi-Agent architecture delegates specific clinical, analytical, and technical responsibilities across specialized agents:

```
                          ┌───────────────────────────┐
                          │   Video Upload (User)     │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │  Agent 1: Video Quality   │
                          │     Validation Agent      │
                          └─────────────┬─────────────┘
                                        │ PASS / WARNING
                                        ▼
                          ┌───────────────────────────┐
                          │  Agent 2: Biomechanical   │
                          │   Data & PT Analyst       │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │  Agent 3: Clinical Risk   │
                          │    Assessment Agent       │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │  Agent 4: Gait Progress   │
                          │    Comparison Agent       │
                          └─────────────┬─────────────┘
                                        │
                      ┌─────────────────┴─────────────────┐
                      ▼                                   ▼
          ┌───────────────────────┐           ┌───────────────────────┐
          │  Agent 5: Clinical    │           │  Agent 6: Empathetic  │
          │   Assistant Chatbot   │           │   Parent Translator   │
          └───────────┬───────────┘           └───────────┬───────────┘
                      │                                   │
                      └─────────────────┬─────────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │   Clinical PDF Report &   │
                          │    EHR Visual Dashboard   │
                          └───────────────────────────┘
```

### 1. Agent 1: Video Quality Validation Agent (`video_quality_agent.py`)
- **Role**: Lead Computer Vision & Quality Inspector
- **Goal**: Evaluate uploaded walking videos against strict technical quality standards prior to kinematic processing.
- **Metrics Calculated**:
  - Full-body pose visibility rate (minimum 70% threshold)
  - Video resolution ($\ge 1280 \times 720$) & Frame Rate ($\ge 30 \text{ FPS}$)
  - Lighting quality & pixel contrast distribution
  - Camera stability & unwanted motion jitter
  - Subject walking duration ($\ge 5 \text{ seconds}$)
- **Output Gate**: Produces a `PASS`, `WARNING`, or `FAIL` status with an overall quality score (0–100). If `FAIL`, downstream analysis is halted to protect diagnostic accuracy.

### 2. Agent 2: Biomechanical Data Analyst & Physical Therapist (`agents.py`)
- **Role**: Orthopedic Biomechanist & Pediatric Physical Therapist
- **Goal**: Extract 3D skeletal landmarks (MediaPipe BlazePose), calculate frame-by-frame joint flexion angles (Knee/Hip), and compute bilateral Symmetry Index (SI).
- **Calculations**:
  - Interior joint angle $\theta = \arccos\left(\frac{\vec{v}_1 \cdot \vec{v}_2}{\|\vec{v}_1\| \|\vec{v}_2\|}\right) \times \frac{180}{\pi}$
  - Bilateral Symmetry Index: $\text{SI} = 100 \times \frac{|\text{Left} - \text{Right}|}{0.5 \times (|\text{Left}| + |\text{Right}|)}$
  - Gait Symmetry Percentage: $\text{Gait Symmetry \%} = \max(0, 100 - \text{SI})$
- **Responsibility**: Identifies functional movement limitations, range of motion (ROM) deficits, and gait cycle asymmetries against age-stratified pediatric normatives.

### 3. Agent 3: Clinical Risk Assessment Agent (`clinical_risk_agent.py`)
- **Role**: Orthopedic Risk Consultant
- **Goal**: Synthesize biomechanical metrics into a standardized pediatric motor risk level (`LOW`, `MEDIUM`, `HIGH`).
- **Logic**:
  - Evaluates triggered clinical risk factors (e.g., knee ROM difference $> 12^\circ$, symmetry $< 88\%$, peak asymmetry $> 25\%$).
  - Computes weighted severity scores and suggests follow-up timelines (Routine, 3–6 months, Immediate Specialist Referral).

### 4. Agent 4: Gait Progress Comparison Agent (`gait_progress_comparison_agent.py` & `patient_progress_agent.py`)
- **Role**: Longitudinal Progress Specialist
- **Goal**: Conduct side-by-side comparative analysis of historical baseline sessions vs. follow-up assessments.
- **Classification**: Classifies patient trajectory as `IMPROVED`, `STABLE`, or `WORSENED` based on delta changes in ROM, symmetry index, and risk tier shifts.

### 5. Agent 5 & 6: Clinical Assistant Chatbot & Empathetic Translator (`backend/main.py`)
- **Role**: Conversational EHR Assistant & Communication Specialist
- **Goal**: Answer natural language inquiries from clinicians regarding patient progress, and translate complex clinical findings into accessible, comforting explanations for parents and caregivers.

---

## Agent Communication & Workflow

1. **Structured Payload Exchange**: Agents pass strongly typed JSON data schemas containing metric vectors, quality scores, risk matrices, and historical session logs.
2. **Sequential Decision Gate**: If Agent 1 fails the video quality check, execution halts gracefully with clear re-recording recommendations.
3. **Multi-Agent API Service**: FastAPI endpoints orchestrate execution across agent modules and return unified JSON responses to the Next.js frontend or Streamlit dashboard.

---

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic, OpenCV, MediaPipe, NumPy, Pandas, ReportLab
- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS, Lucide Icons, Recharts
- **Dashboard**: Streamlit, Plotly Express
- **Video Processing**: imageio libx264/yuv420p for HTML5 web compatibility

---

## Installation & Running Instructions

### Prerequisites
- Python 3.10 or higher
- Node.js 18+ and npm (for Next.js frontend)

### 1. Run via Streamlit Dashboard

```bash
# Navigate to Multi-Agent directory
cd Multi-Agent

# Install Python dependencies
pip install -r requirements.txt

# Launch Streamlit app
streamlit run app.py
```

### 2. Run via Decoupled FastAPI + Next.js EHR Platform

```bash
# Terminal 1: Launch FastAPI Backend Server
cd Multi-Agent/backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Launch Next.js Frontend App
cd Multi-Agent/frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your web browser.

---

## Automated Test Suite

To run the complete 8-scenario integration test suite for the Multi-Agent system:

```bash
cd Multi-Agent
python -m pytest test_master_multiagent_workflow.py -v
```
