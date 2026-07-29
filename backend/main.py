"""
backend/main.py

FastAPI Web Server for KinemaTrace AI Electronic Health Record (EHR) Platform.
Serves decoupled API endpoints for 3D pose extraction, kinematic calculation, and multi-agent clinical decision support.
"""

import os
import glob
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel
import pandas as pd
import numpy as np

from cv_engine import extract_pose_data, generate_annotated_video, stream_annotated_frames, process_video_single_pass
from clinical_math import calculate_joint_angles, compute_symmetry_index, evaluate_gait_risk
from agents import (
    AGENT_1_CONFIG,
    AGENT_2_CONFIG,
    AGENT_CLINICAL_RISK_CONFIG,
    AGENT_PROGRESS_CONFIG,
    AGENT_VIDEO_QUALITY_CONFIG,
    AGENT_COMPARISON_CONFIG,
    AGENT_5_CONFIG,
    AGENT_6_CONFIG,
    analyze_biomechanics,
    analyze_physical_therapy,
    assess_clinical_risk,
    assess_progress,
    get_patient_assessments,
    save_patient_assessment,
    validate_video_quality,
    compare_gait_progress,
    process_clinical_assistant_query,
    process_empathetic_translator,
)
from pdf_generator import generate_clinical_pdf_report

app = FastAPI(
    title="KinemaTrace AI EHR Backend API",
    version="1.0.0",
    description="Pediatric Markerless Motor Screening & Multi-Agent Analytics API"
)

# Enable CORS for Next.js frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Workspace Root & Asset Directory
WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Mount static file directories
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


class AgentReportRequest(BaseModel):
    agent_id: Optional[str] = "analyst"
    case_id: Optional[str] = None
    user_instruction: Optional[str] = None
    patient_info: Optional[Dict[str, str]] = None
    angles_data: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    source_type: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None



class PDFReportRequest(BaseModel):
    patient_id: Optional[str] = None
    case_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@app.post("/api/agents/chat")
@app.post("/api/agents/clinical-assistant")
async def chat_with_clinical_assistant(req: ChatRequest):
    return process_clinical_assistant_query(req.message, req.context)


@app.post("/api/generate-pdf")
@app.post("/api/reports/pdf")
async def generate_pdf_endpoint(req: PDFReportRequest):
    ctx = req.context or {}
    if req.patient_id and not ctx.get("patient_info"):
        ctx["patient_info"] = {"id": req.patient_id, "age": "7 y/o", "case": "Pediatric Gait Screening"}
    if req.case_id:
        ctx["case_id"] = req.case_id

    pdf_bytes = generate_clinical_pdf_report(ctx)
    patient_id = req.patient_id or ctx.get("patient_info", {}).get("id") or "KT-2026-P902"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="KinemaTrace_Report_{patient_id}.pdf"'
        }
    )


@app.get("/api/generate-pdf")
@app.get("/api/reports/pdf")
def get_pdf_endpoint(patient_id: Optional[str] = "KT-2026-P902", case_id: Optional[str] = None):
    ctx = {"case_id": case_id, "patient_info": {"id": patient_id, "age": "7 y/o", "case": "Pediatric Gait Screening"}}
    pdf_bytes = generate_clinical_pdf_report(ctx)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="KinemaTrace_Report_{patient_id}.pdf"'
        }
    )



@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "KinemaTrace AI Backend", "version": "1.0.0"}


@app.get("/api/cases")
def get_demo_cases():
    return [
        {
            "id": "case1",
            "name": "Patient Case 1: Normative Gait (Low Risk)",
            "patient_info": {"id": "PED-2026-001", "age": "7 y/o", "case": "Normative Control"},
            "telemetry_default": {"symmetry_index": 98.2, "peak_knee_flexion": 110.0, "hip_flexion_rom": 125.1}
        },
        {
            "id": "case2",
            "name": "Patient Case 2: Asymmetrical Limp (High Risk)",
            "patient_info": {"id": "KT-2026-P902", "age": "7 y/o", "case": "Post-Injury Asymmetric Gait"},
            "telemetry_default": {"symmetry_index": 87.5, "peak_knee_flexion": 89.1, "hip_flexion_rom": 125.1}
        }
    ]


@app.get("/api/quality/{case_id}")
def get_demo_quality(case_id: str):
    """
    Returns the video quality validation report for a preset demo case.
    case_id: 'case1' | 'case2'
    Returns the same structured quality report as the upload endpoint.
    """
    if case_id == "case1":
        video_path = os.path.join(WORKSPACE_DIR, "demo_normative.mp4")
    elif case_id == "case2":
        video_path = os.path.join(WORKSPACE_DIR, "demo_asymmetric.mp4")
    else:
        raise HTTPException(status_code=404, detail=f"Unknown case_id: {case_id}")

    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Demo video not found: {video_path}")

    result = validate_video_quality(video_path)
    return result


@app.get("/api/video/{filename}")
def serve_video(filename: str):
    # Check uploads dir first
    upload_file = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(upload_file):
        ext = os.path.splitext(filename)[1].lower()
        media_type = "video/webm" if ext == ".webm" else "video/mp4"
        return FileResponse(upload_file, media_type=media_type)

    # Check static dir
    static_file = os.path.join(STATIC_DIR, filename)
    if os.path.exists(static_file):
        ext = os.path.splitext(filename)[1].lower()
        media_type = "video/webm" if ext == ".webm" else "video/mp4"
        return FileResponse(static_file, media_type=media_type)

    # Check workspace root
    root_file = os.path.join(WORKSPACE_DIR, filename)
    if os.path.exists(root_file):
        ext = os.path.splitext(filename)[1].lower()
        media_type = "video/webm" if ext == ".webm" else "video/mp4"
        return FileResponse(root_file, media_type=media_type)

    raise HTTPException(status_code=404, detail=f"Video file not found: {filename}")


@app.post("/api/upload")
@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """
    Dedicated video upload endpoint. Accepts .mp4, .avi, .mov, .webm video files.
    Saves file to /backend/uploads/, runs MediaPipe pose landmark extraction & clinical math,
    and returns full video details and extracted telemetry metrics.
    """
    import time
    allowed_exts = [".mp4", ".avi", ".mov", ".webm", ".mkv"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {allowed_exts}"
        )

    # Save uploaded file temporarily to /backend/uploads/
    timestamp_str = str(int(time.time()))
    safe_filename = f"upload_{timestamp_str}_{file.filename.replace(' ', '_')}"
    upload_file_path = os.path.join(UPLOADS_DIR, safe_filename)

    with open(upload_file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # --- AGENT 1: VIDEO QUALITY VALIDATION GATE ---
    # Run computer vision quality checks (duration, resolution, fps, brightness, blur, stability, landmarks)
    video_quality = validate_video_quality(upload_file_path)

    # If quality status is FAIL, stop processing and ask user to re-record
    if video_quality.get("status") == "FAIL":
        return {
            "status": "FAIL",
            "message": "Video quality validation failed. Gait analysis was stopped.",
            "filename": file.filename,
            "file_path": f"/uploads/{safe_filename}",
            "video_quality": video_quality,
        }

    # Extract 3D pose landmarks using MediaPipe (Agent 2 - Gait Analysis)
    df_pose = extract_pose_data(upload_file_path)

    # Render WebM annotated skeleton overlay video for browser HTML5 video playback
    target_webm_name = f"annotated_upload_{timestamp_str}.webm"
    target_webm_path = os.path.join(STATIC_DIR, target_webm_name)
    video_url = f"/uploads/{safe_filename}"
    try:
        for _ in stream_annotated_frames(upload_file_path, target_webm_path):
            pass
        if os.path.exists(target_webm_path):
            video_url = f"/api/video/{target_webm_name}"
    except Exception as e:
        print(f"Warning generating WebM overlay for uploaded video: {e}")

    # Compute clinical joint angles & symmetry index
    angles_df = calculate_joint_angles(df_pose)
    si_series = compute_symmetry_index(angles_df["left_knee_angle"], angles_df["right_knee_angle"])
    risk_result = evaluate_gait_risk(df_pose)
    fps_val = float(video_quality.get("metrics", {}).get("fps", 30.0))
    bio_result = analyze_biomechanics(angles_df, risk_result, fps=fps_val)
    clinical_risk_eval = assess_clinical_risk(bio_result)

    l_max = float(angles_df["left_knee_angle"].max()) if not angles_df.empty else 110.0
    r_max = float(angles_df["right_knee_angle"].max()) if not angles_df.empty else 110.0
    l_min = float(angles_df["left_knee_angle"].min()) if not angles_df.empty else 10.0
    r_min = float(angles_df["right_knee_angle"].min()) if not angles_df.empty else 10.0
    mean_si = float(np.nanmean(si_series)) if not si_series.empty else 5.0
    peak_si = float(np.nanmax(si_series)) if not si_series.empty else 5.0

    gait_symmetry = max(0.0, round(100.0 - mean_si, 1))
    peak_knee_flexion = round(min(l_max, r_max), 1)
    hip_flexion_rom = bio_result["metrics"].get("hip_flexion_rom_deg", 120.0)

    time_series = [
        {
            "frame": int(idx),
            "leftKnee": round(float(row["left_knee_angle"]), 1),
            "rightKnee": round(float(row["right_knee_angle"]), 1),
            "symmetryIndex": round(float(si), 1)
        }
        for idx, (row, si) in enumerate(zip(angles_df.to_dict(orient="records"), si_series.values))
    ]

    return {
        "status": "success",
        "video_id": safe_filename,
        "gait_analysis_completed": True,
        "filename": file.filename,
        "file_path": upload_file_path,
        "relative_file_path": f"/uploads/{safe_filename}",
        "video_url": video_url,
        "video_quality": video_quality,
        "patient_info": {
            "id": f"KT-CUSTOM-{timestamp_str[-4:]}",
            "age": "Pediatric",
            "case": f"Uploaded Gait Scan ({file.filename})"
        },
        "metrics": {
            "left_knee_angle": round(l_max, 1),
            "right_knee_angle": round(r_max, 1),
            "left_knee_rom": round(l_max - l_min, 1),
            "right_knee_rom": round(r_max - r_min, 1),
            "left_hip_rom": bio_result["metrics"].get("left_hip_rom_deg", 48.5),
            "right_hip_rom": bio_result["metrics"].get("right_hip_rom_deg", 52.1),
            "gait_symmetry": gait_symmetry,
            "mean_asymmetry": round(mean_si, 1),
            "peak_asymmetry": round(peak_si, 1),
            "rom_difference": round(abs((l_max - l_min) - (r_max - r_min)), 1),
            "left_angular_velocity": bio_result["metrics"].get("left_peak_angular_velocity_dps", 0.0),
            "right_angular_velocity": bio_result["metrics"].get("right_peak_angular_velocity_dps", 0.0),
            "pose_confidence": round(float(video_quality.get("metrics", {}).get("landmark_detection_rate", 0.95)) * 100, 1),
            "tracking_quality": video_quality.get("checks", {}).get("pose_detection", "Good"),
            "symmetry_index": round(mean_si, 1),
            "peak_knee_flexion": peak_knee_flexion,
            "hip_flexion_rom": hip_flexion_rom,
        },
        "telemetry": {
            "gait_symmetry_pct": gait_symmetry,
            "peak_knee_flexion_deg": peak_knee_flexion,
            "hip_flexion_rom_deg": hip_flexion_rom,
            "mean_si_pct": round(mean_si, 1),
            "left_rom": round(l_max - l_min, 1),
            "right_rom": round(r_max - r_min, 1),
            "risk_status": clinical_risk_eval["risk_level"] + " RISK",
            "risk_color": "red" if clinical_risk_eval["risk_level"] == "HIGH" else ("yellow" if clinical_risk_eval["risk_level"] == "MEDIUM" else "green")
        },
        "clinical_risk": clinical_risk_eval,
        "time_series": time_series[:150],
        "angles_summary": {
            "left_knee_max": round(l_max, 1),
            "left_knee_min": round(l_min, 1),
            "right_knee_max": round(r_max, 1),
            "right_knee_min": round(r_min, 1)
        }
    }


@app.post("/api/validate-quality")
async def validate_quality_endpoint(file: UploadFile = File(...)):
    """
    Step 1 of Custom Video Workflow:
    Accepts video file, saves to /uploads/, runs Agent 1 (validate_video_quality),
    and returns quality score, status (PASS / WARNING / FAIL), checks, metrics,
    issues, recommendations, file_path, and metadata.
    """
    import time
    allowed_exts = [".mp4", ".avi", ".mov", ".webm", ".mkv"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {allowed_exts}"
        )

    timestamp_str = str(int(time.time()))
    safe_filename = f"upload_{timestamp_str}_{file.filename.replace(' ', '_')}"
    upload_file_path = os.path.join(UPLOADS_DIR, safe_filename)

    with open(upload_file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    video_quality = validate_video_quality(upload_file_path)

    metrics = video_quality.get("metrics", {})
    return {
        "status": video_quality.get("status", "PASS"),
        "video_quality_score": video_quality.get("video_quality_score", 0),
        "filename": file.filename,
        "file_path": upload_file_path,
        "relative_file_path": f"/uploads/{safe_filename}",
        "metadata": {
            "resolution": metrics.get("resolution_str", f"{metrics.get('width', 0)} × {metrics.get('height', 0)}"),
            "fps": round(float(metrics.get("fps", 30.0)), 1),
            "duration": round(float(metrics.get("duration_sec", 0.0)), 1),
            "orientation": metrics.get("orientation", "Landscape"),
            "full_body_visible": video_quality.get("checks", {}).get("full_body_visible", "N/A"),
            "lighting": video_quality.get("checks", {}).get("lighting", "N/A"),
            "camera_stability": video_quality.get("checks", {}).get("camera_stability", "N/A"),
            "camera_angle": video_quality.get("checks", {}).get("camera_angle", "N/A"),
            "pose_detection": video_quality.get("checks", {}).get("pose_detection", "N/A"),
            "walking_duration": video_quality.get("checks", {}).get("walking_duration", "N/A"),
        },
        "video_quality": video_quality,
        "patient_info": {
            "id": f"KT-CUSTOM-{timestamp_str[-4:]}",
            "age": "Pediatric",
            "case": f"Uploaded Gait Scan ({file.filename})"
        }
    }


class CustomAnalyzeRequest(BaseModel):
    file_path: str
    patient_info: Optional[Dict[str, str]] = None


def sanitize_json_floats(obj: Any) -> Any:
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return float(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_json_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json_floats(v) for v in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        val = obj.item()
        return sanitize_json_floats(val)
    return obj


VIDEO_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}


def get_video_sha256_id(file_path: str) -> str:
    """Generates deterministic video ID using SHA-256 hash."""
    if not os.path.exists(file_path):
        return f"vid_unknown_{os.path.basename(file_path)}"
    import hashlib
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return f"vid_sha256_{hasher.hexdigest()[:16]}"


@app.post("/api/upload")
@app.post("/api/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """
    Dedicated video upload endpoint. Accepts .mp4, .avi, .mov, .webm video files.
    Saves file to /backend/uploads/, runs Agent 1 fast video quality validation (< 1s),
    and executes Agent 2 single-pass pose extraction.
    """
    import time
    allowed_exts = [".mp4", ".avi", ".mov", ".webm", ".mkv"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {allowed_exts}"
        )

    timestamp_str = str(int(time.time()))
    safe_filename = f"upload_{timestamp_str}_{file.filename.replace(' ', '_')}"
    upload_file_path = os.path.join(UPLOADS_DIR, safe_filename)

    with open(upload_file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    video_id = get_video_sha256_id(upload_file_path)

    # Agent 1: Video Quality Validation Gate (Fast 5 key frame check, < 1s)
    video_quality = validate_video_quality(upload_file_path)
    video_quality["video_id"] = video_id

    if video_quality.get("status") == "FAIL":
        return {
            "status": "FAIL",
            "video_id": video_id,
            "message": "Video quality validation failed. Gait analysis was stopped.",
            "filename": file.filename,
            "file_path": f"/uploads/{safe_filename}",
            "video_quality": video_quality,
        }

    # Agent 2: Single-pass gait analysis execution
    target_webm_name = f"annotated_{video_id}.webm"
    target_webm_path = os.path.join(STATIC_DIR, target_webm_name)
    pass_res = process_video_single_pass(upload_file_path, target_webm_path)

    video_url = f"/api/video/{target_webm_name}" if os.path.exists(target_webm_path) else f"/uploads/{safe_filename}"
    angles_df = pass_res["angles_df"]
    df_pose = pass_res["df_pose"]
    risk_result = pass_res["risk_result"]
    fps_val = float(video_quality.get("metrics", {}).get("fps", 30.0))

    bio_result = analyze_biomechanics(angles_df, risk_result, fps=fps_val)
    bio_result["video_id"] = video_id
    clinical_risk_eval = assess_clinical_risk(bio_result)
    clinical_risk_eval["video_id"] = video_id

    metrics = pass_res["metrics"]
    patient_info = {
        "id": f"KT-CUSTOM-{timestamp_str[-4:]}",
        "age": "Pediatric",
        "case": f"Uploaded Gait Scan ({file.filename})"
    }

    payload = {
        "status": "success",
        "video_id": video_id,
        "gait_analysis_completed": True,
        "filename": file.filename,
        "file_path": upload_file_path,
        "relative_file_path": f"/uploads/{safe_filename}",
        "video_url": video_url,
        "video_quality": video_quality,
        "patient_info": patient_info,
        "metrics": metrics,
        "telemetry": {
            "gait_symmetry_pct": metrics["gait_symmetry"],
            "peak_knee_flexion_deg": metrics["peak_knee_flexion"],
            "hip_flexion_rom_deg": bio_result["metrics"].get("hip_flexion_rom_deg", 120.0),
            "mean_si_pct": metrics["mean_asymmetry"],
            "left_rom": metrics["left_knee_rom"],
            "right_rom": metrics["right_knee_rom"],
            "risk_status": clinical_risk_eval["risk_level"] + " RISK",
            "risk_color": "red" if clinical_risk_eval["risk_level"] == "HIGH" else ("yellow" if clinical_risk_eval["risk_level"] == "MEDIUM" else "green")
        },
        "clinical_risk": clinical_risk_eval,
        "risk_assessment": clinical_risk_eval,
        "time_series": pass_res["time_series"][:150],
        "angles_summary": pass_res["angles_summary"]
    }

    VIDEO_ANALYSIS_CACHE[video_id] = payload
    VIDEO_ANALYSIS_CACHE[upload_file_path] = payload
    return payload


@app.post("/api/validate-quality")
async def validate_quality_endpoint(file: UploadFile = File(...)):
    """
    Step 1 of Custom Video Workflow:
    Accepts video file, saves to /uploads/, runs Agent 1 (validate_video_quality < 1s),
    and returns quality score, status (PASS / WARNING / FAIL), checks, metrics,
    issues, recommendations, file_path, and metadata WITHOUT running pose extraction or WebM conversion.
    """
    import time
    allowed_exts = [".mp4", ".avi", ".mov", ".webm", ".mkv"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {allowed_exts}"
        )

    timestamp_str = str(int(time.time()))
    safe_filename = f"upload_{timestamp_str}_{file.filename.replace(' ', '_')}"
    upload_file_path = os.path.join(UPLOADS_DIR, safe_filename)

    with open(upload_file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    video_id = get_video_sha256_id(upload_file_path)
    video_quality = validate_video_quality(upload_file_path)
    video_quality["video_id"] = video_id

    metrics = video_quality.get("metrics", {})
    return {
        "status": video_quality.get("status", "PASS"),
        "video_id": video_id,
        "gait_analysis_completed": False,
        "video_quality_score": video_quality.get("video_quality_score", 0),
        "filename": file.filename,
        "file_path": upload_file_path,
        "relative_file_path": f"/uploads/{safe_filename}",
        "metadata": {
            "resolution": metrics.get("resolution_str", f"{metrics.get('width', 0)} × {metrics.get('height', 0)}"),
            "fps": round(float(metrics.get("fps", 30.0)), 1),
            "duration": round(float(metrics.get("duration_sec", 0.0)), 1),
            "orientation": metrics.get("orientation", "Landscape"),
            "full_body_visible": video_quality.get("checks", {}).get("full_body_visible", "N/A"),
            "lighting": video_quality.get("checks", {}).get("lighting", "N/A"),
            "camera_stability": video_quality.get("checks", {}).get("camera_stability", "N/A"),
            "camera_angle": video_quality.get("checks", {}).get("camera_angle", "N/A"),
            "pose_detection": video_quality.get("checks", {}).get("pose_detection", "N/A"),
            "walking_duration": video_quality.get("checks", {}).get("walking_duration", "N/A"),
        },
        "video_quality": video_quality,
        "patient_info": {
            "id": f"KT-CUSTOM-{timestamp_str[-4:]}",
            "age": "Pediatric",
            "case": f"Uploaded Gait Scan ({file.filename})"
        }
    }


class CustomAnalyzeRequest(BaseModel):
    file_path: str
    patient_info: Optional[Dict[str, str]] = None


def sanitize_json_floats(obj: Any) -> Any:
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return float(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_json_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json_floats(v) for v in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        val = obj.item()
        return sanitize_json_floats(val)
    return obj


@app.post("/api/analyze-custom-video")
async def analyze_custom_video_endpoint(req: CustomAnalyzeRequest):
    """
    Executes Agent 2 (MediaPipe Pose & Joint Angle Math via SINGLE PASS) -> WebM Overlay Video -> Agent 3 (Clinical Risk).
    Uses in-memory VIDEO_ANALYSIS_CACHE and SHA-256 video hash to prevent re-processing identical video files (< 10ms lookup).
    """
    import time
    file_path = req.file_path
    if not file_path or not os.path.exists(file_path):
        if file_path and file_path.startswith("/uploads/"):
            file_path = os.path.join(UPLOADS_DIR, os.path.basename(file_path))
        else:
            raise HTTPException(status_code=404, detail=f"Custom video file not found: {file_path}")

    filename = os.path.basename(file_path)
    video_id = get_video_sha256_id(file_path)

    cache_keys = [
        f"{file_path}_{os.path.getmtime(file_path)}",
        file_path,
        video_id
    ]

    for ck in cache_keys:
        if ck in VIDEO_ANALYSIS_CACHE:
            print(f"[PERFORMANCE CACHE HIT] Returning pre-calculated gait analysis for: {filename}")
            return VIDEO_ANALYSIS_CACHE[ck]

    timestamp_str = str(int(time.time()))

    video_quality = validate_video_quality(file_path)
    video_quality["video_id"] = video_id
    if video_quality.get("status") == "FAIL":
        return JSONResponse(
            status_code=400,
            content={
                "status": "FAIL",
                "video_id": video_id,
                "message": "Video quality validation failed. Gait analysis was stopped.",
                "video_quality": video_quality
            }
        )

    target_webm_name = f"annotated_custom_{video_id}.webm"
    target_webm_path = os.path.join(STATIC_DIR, target_webm_name)
    pass_res = process_video_single_pass(file_path, target_webm_path)

    video_url = f"/api/video/{target_webm_name}" if os.path.exists(target_webm_path) else f"/uploads/{filename}"
    angles_df = pass_res["angles_df"]
    risk_result = pass_res["risk_result"]
    fps_val = float(video_quality.get("metrics", {}).get("fps", 30.0))

    bio_result = analyze_biomechanics(angles_df, risk_result, fps=fps_val)
    bio_result["video_id"] = video_id
    clinical_risk_eval = assess_clinical_risk(bio_result)
    clinical_risk_eval["video_id"] = video_id

    metrics = pass_res["metrics"]
    patient_info = req.patient_info or {
        "id": f"KT-CUSTOM-{timestamp_str[-4:]}",
        "age": "Pediatric",
        "case": f"Uploaded Gait Scan ({filename})"
    }

    gait_analysis_data = {
        "video_id": video_id,
        "left_knee_angle": metrics["left_knee_angle"],
        "right_knee_angle": metrics["right_knee_angle"],
        "left_knee_rom": metrics["left_knee_rom"],
        "right_knee_rom": metrics["right_knee_rom"],
        "left_hip_rom": bio_result["metrics"].get("left_hip_rom_deg", 48.5),
        "right_hip_rom": bio_result["metrics"].get("right_hip_rom_deg", 52.1),
        "gait_symmetry": metrics["gait_symmetry"],
        "mean_asymmetry": metrics["mean_asymmetry"],
        "peak_asymmetry": metrics["peak_asymmetry"],
        "rom_difference": metrics["rom_difference"],
        "left_angular_velocity": bio_result["metrics"].get("left_peak_angular_velocity_dps", 0.0),
        "right_angular_velocity": bio_result["metrics"].get("right_peak_angular_velocity_dps", 0.0),
        "pose_confidence": round(float(video_quality.get("metrics", {}).get("landmark_detection_rate", 0.95)) * 100, 1),
        "tracking_quality": video_quality.get("checks", {}).get("pose_detection", "Good"),
    }

    result_payload = {
        "status": "success",
        "video_id": video_id,
        "source": "custom_upload",
        "gait_analysis_completed": True,
        "filename": filename,
        "file_path": file_path,
        "video_url": video_url,
        "video_quality": video_quality,
        "patient_info": patient_info,
        "gait_analysis": gait_analysis_data,
        "metrics": {
            **gait_analysis_data,
            "symmetry_index": metrics["mean_asymmetry"],
            "peak_knee_flexion": metrics["peak_knee_flexion"],
            "hip_flexion_rom": bio_result["metrics"].get("hip_flexion_rom_deg", 120.0),
        },
        "telemetry": {
            "gait_symmetry_pct": metrics["gait_symmetry"],
            "peak_knee_flexion_deg": metrics["peak_knee_flexion"],
            "hip_flexion_rom_deg": bio_result["metrics"].get("hip_flexion_rom_deg", 120.0),
            "mean_si_pct": metrics["mean_asymmetry"],
            "left_rom": metrics["left_knee_rom"],
            "right_rom": metrics["right_knee_rom"],
            "risk_status": clinical_risk_eval["risk_level"] + " RISK",
            "risk_color": "red" if clinical_risk_eval["risk_level"] == "HIGH" else ("yellow" if clinical_risk_eval["risk_level"] == "MEDIUM" else "green")
        },
        "clinical_risk": clinical_risk_eval,
        "risk_assessment": clinical_risk_eval,
        "time_series": pass_res["time_series"][:150],
        "angles_summary": pass_res["angles_summary"]
    }

    result_payload = sanitize_json_floats(result_payload)

    for ck in cache_keys:
        VIDEO_ANALYSIS_CACHE[ck] = result_payload

    return result_payload


@app.post("/api/analyze-video")
async def analyze_video(
    case_id: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    video_path = None
    patient_info = {"id": "KT-2026-P902", "age": "7 y/o", "case": "Outpatient Gait Screening"}
    webm_name = "demo_asymmetric_annotated.webm"

    if case_id == "case1":
        csv_path = os.path.join(WORKSPACE_DIR, "demo_normative.csv")
        raw_video = os.path.join(WORKSPACE_DIR, "demo_normative.mp4")
        patient_info = {"id": "PED-2026-001", "age": "7 y/o", "case": "Normative Control"}
        webm_name = "demo_normative_annotated.webm"
    elif case_id == "case2":
        csv_path = os.path.join(WORKSPACE_DIR, "demo_asymmetric.csv")
        raw_video = os.path.join(WORKSPACE_DIR, "demo_asymmetric.mp4")
        patient_info = {"id": "KT-2026-P902", "age": "7 y/o", "case": "Post-Injury Asymmetric Gait"}
        webm_name = "demo_asymmetric_annotated.webm"
    elif file is not None:
        raw_video = os.path.join(STATIC_DIR, "uploaded_temp.mp4")
        with open(raw_video, "wb") as f:
            f.write(await file.read())
        csv_path = None
        patient_info = {"id": "KT-CUSTOM-P99", "age": "Pediatric", "case": "User Uploaded Gait Scan"}
        webm_name = "uploaded_annotated.webm"
    else:
        # Default to Case 2 (Asymmetric)
        csv_path = os.path.join(WORKSPACE_DIR, "demo_asymmetric.csv")
        raw_video = os.path.join(WORKSPACE_DIR, "demo_asymmetric.mp4")
        patient_info = {"id": "KT-2026-P902", "age": "7 y/o", "case": "Post-Injury Asymmetric Gait"}
        webm_name = "demo_asymmetric_annotated.webm"

    # Read CSV cache or extract pose data
    if csv_path and os.path.exists(csv_path):
        df_pose = pd.read_csv(csv_path, index_col="frame")
    else:
        df_pose = extract_pose_data(raw_video)

    # Render webm annotated video if missing in static
    target_webm = os.path.join(STATIC_DIR, webm_name)
    if not os.path.exists(target_webm):
        workspace_webm = os.path.join(WORKSPACE_DIR, webm_name)
        if os.path.exists(workspace_webm):
            target_webm = workspace_webm
        else:
            for _ in stream_annotated_frames(raw_video, target_webm):
                pass

    # Compute clinical joint angles & symmetry index
    angles_df = calculate_joint_angles(df_pose)
    si_series = compute_symmetry_index(angles_df["left_knee_angle"], angles_df["right_knee_angle"])
    risk_result = evaluate_gait_risk(df_pose)

    l_max = float(angles_df["left_knee_angle"].max())
    r_max = float(angles_df["right_knee_angle"].max())
    l_min = float(angles_df["left_knee_angle"].min())
    r_min = float(angles_df["right_knee_angle"].min())
    mean_si = float(np.nanmean(si_series))

    # Real-time telemetry badges matching EHR specifications
    gait_symmetry = max(0.0, round(100.0 - mean_si, 1))
    peak_knee_flexion = round(min(l_max, r_max), 1)
    hip_flexion_rom = 125.1

    time_series = [
        {
            "frame": int(idx),
            "leftKnee": round(float(row["left_knee_angle"]), 1),
            "rightKnee": round(float(row["right_knee_angle"]), 1),
            "symmetryIndex": round(float(si), 1)
        }
        for idx, (row, si) in enumerate(zip(angles_df.to_dict(orient="records"), si_series.values))
    ]

    return {
        "status": "success",
        "patient_info": patient_info,
        "video_url": f"/api/video/{os.path.basename(target_webm)}",
        "telemetry": {
            "gait_symmetry_pct": gait_symmetry,
            "peak_knee_flexion_deg": peak_knee_flexion,
            "hip_flexion_rom_deg": hip_flexion_rom,
            "mean_si_pct": round(mean_si, 1),
            "left_rom": round(l_max - l_min, 1),
            "right_rom": round(r_max - r_min, 1),
            "risk_status": risk_result["status"],
            "risk_color": risk_result["color"]
        },
        "time_series": time_series[:150],
        "angles_summary": {
            "left_knee_max": round(l_max, 1),
            "left_knee_min": round(l_min, 1),
            "right_knee_max": round(r_max, 1),
            "right_knee_min": round(r_min, 1)
        }
    }


def _process_agent_request(target_agent: str, req: AgentReportRequest):
    case_id = req.case_id
    user_instruction = req.user_instruction
    source_type = req.source_type
    custom_path = req.file_path

    # Determine video source: custom upload vs preset case
    is_custom = (
        source_type == "custom"
        or case_id == "custom"
        or bool(custom_path)
    )

    if is_custom:
        raw_video_file = None
        if custom_path:
            # Handle relative URL paths (/uploads/... or /static/...) or absolute paths
            if custom_path.startswith("/uploads/"):
                raw_video_file = os.path.join(UPLOADS_DIR, os.path.basename(custom_path))
            elif custom_path.startswith("/static/"):
                raw_video_file = os.path.join(STATIC_DIR, os.path.basename(custom_path))
            elif custom_path.startswith("/api/video/"):
                raw_video_file = os.path.join(STATIC_DIR, os.path.basename(custom_path))
            elif os.path.exists(custom_path):
                raw_video_file = custom_path

        if not raw_video_file or not os.path.exists(raw_video_file):
            # Fallback: check UPLOADS_DIR for the latest upload
            uploads = sorted(glob.glob(os.path.join(UPLOADS_DIR, "upload_*")), key=os.path.getmtime, reverse=True)
            if uploads:
                raw_video_file = uploads[0]
            else:
                raw_video_file = os.path.join(STATIC_DIR, "uploaded_temp.mp4")

        patient_info = req.patient_info or {
            "id": f"KT-CUSTOM-{os.path.basename(raw_video_file)[:12]}",
            "age": "Pediatric",
            "case": f"Custom Video Analysis ({os.path.basename(raw_video_file)})"
        }
        df_pose = extract_pose_data(raw_video_file)
        vq_result = validate_video_quality(raw_video_file)
    elif case_id == "case1":
        patient_info = req.patient_info or {"id": "PED-2026-001", "age": "7 y/o", "case": "Normative Control"}
        csv_path = os.path.join(WORKSPACE_DIR, "demo_normative.csv")
        raw_video_file = os.path.join(WORKSPACE_DIR, "demo_normative.mp4")
        if os.path.exists(csv_path):
            df_pose = pd.read_csv(csv_path, index_col="frame")
        else:
            df_pose = extract_pose_data(raw_video_file)
        vq_result = validate_video_quality(raw_video_file)
    else:  # Default Case 2
        patient_info = req.patient_info or {"id": "KT-2026-P902", "age": "7 y/o", "case": "Post-Injury Asymmetric Gait"}
        csv_path = os.path.join(WORKSPACE_DIR, "demo_asymmetric.csv")
        raw_video_file = os.path.join(WORKSPACE_DIR, "demo_asymmetric.mp4")
        if os.path.exists(csv_path):
            df_pose = pd.read_csv(csv_path, index_col="frame")
        else:
            df_pose = extract_pose_data(raw_video_file)
        vq_result = validate_video_quality(raw_video_file)

    angles_df = calculate_joint_angles(df_pose)
    risk_result = evaluate_gait_risk(df_pose)

    # Compute all agent outputs with user_instruction
    bio_result = analyze_biomechanics(angles_df, risk_result, user_instruction=user_instruction)

    # --- Clinical Risk Assessment Agent ---
    clinical_risk_result = assess_clinical_risk(
        gait_analysis_result=bio_result,
        patient_age=patient_info.get("age"),
    )

    # --- Patient Progress Monitoring Agent ---
    patient_id = patient_info.get("id", "KT-2026-P902")
    progress_result = assess_progress(
        patient_id=patient_id,
        gait_analysis_result=bio_result,
        clinical_risk_result=clinical_risk_result,
        patient_age=patient_info.get("age"),
        save=False,
    )

    # --- Pediatric Physical Therapist Agent ---
    pt_result = analyze_physical_therapy(bio_result, user_instruction=user_instruction)

    # Format video quality markdown report text
    vq_checks = vq_result.get("checks", {})
    vq_metrics_data = vq_result.get("metrics", {})
    vq_issues = vq_result.get("issues", [])
    vq_status = vq_result.get("status", "PASS")
    vq_score = vq_result.get("video_quality_score", 100)
    vq_emoji = "✅" if vq_status == "PASS" else ("⚠️" if vq_status == "WARNING" else "❌")

    vq_lines = [
        "### 🎥 VIDEO QUALITY VALIDATION REPORT",
        "**Agent:** Agent 1: The Video Quality Validation Agent",
        "**Scope:** Pre-Processing Video Quality Gate · Technical Suitability Evaluation",
        "",
        "---",
        "#### 1. Video Quality Status",
        f"- **Quality Score:** **{vq_score} / 100**",
        f"- **Validation Status:** {vq_emoji} **{vq_status}**",
        f"- **Recommendation:** {vq_result.get('recommendation', '')}",
        "",
        "#### 2. Technical Quality Checks",
        f"- **Full Body Visibility:** {vq_checks.get('full_body_visible', 'N/A')}",
        f"- **Lighting Quality:** {vq_checks.get('lighting', 'N/A')} (Brightness: {vq_metrics_data.get('brightness_score', '—')})",
        f"- **Camera Stability:** {vq_checks.get('camera_stability', 'N/A')} (Shake: {vq_metrics_data.get('camera_shake_score', '—')})",
        f"- **Walking Duration:** {vq_checks.get('walking_duration', 'N/A')}",
        f"- **Camera Angle:** {vq_checks.get('camera_angle', 'N/A')}",
        f"- **Pose Detection:** {vq_checks.get('pose_detection', 'N/A')} ({vq_metrics_data.get('landmark_detection_rate', 0)*100:.1f}% rate)",
        f"- **Resolution:** {vq_checks.get('resolution', 'N/A')}",
        f"- **Frame Rate:** {vq_checks.get('frame_rate', 'N/A')}",
    ]
    if vq_issues:
        vq_lines.extend(["", "#### 3. Quality Issues & Recording Recommendations"])
        for issue in vq_issues:
            vq_lines.append(f"- ⚠️ **{issue['criterion']}**: {issue['reason']}")
            vq_lines.append(f"  - *Impact*: {issue['impact']}")
            vq_lines.append(f"  - *Recommendation*: {issue['recommendation']}")

    vq_lines.extend([
        "",
        "---",
        "*Note: This Video Quality Validation Agent acts as a pre-processing quality gate only. "
        "It does not perform gait analysis, risk classification, or medical diagnosis.*"
    ])
    vq_report_text = "\n".join(vq_lines)

    agent_key = target_agent.lower()

    if agent_key in ["video-quality", "quality", "quality-validation", "0", "1-quality", "agent1"]:
        report_text = vq_report_text
        agent_info = AGENT_VIDEO_QUALITY_CONFIG
        metrics = bio_result["metrics"]
    elif agent_key in ["analyst", "1", "biomechanical", "gait"]:
        report_text = bio_result["report_text"]
        agent_info = AGENT_1_CONFIG
        metrics = bio_result["metrics"]
    elif agent_key in ["clinical-risk", "2", "risk-assessment"]:
        report_text = clinical_risk_result["report_text"]
        agent_info = AGENT_CLINICAL_RISK_CONFIG
        metrics = bio_result["metrics"]
    elif agent_key in ["progress", "3", "patient-progress", "progress-monitoring", "therapist", "physical-therapy"]:
        report_text = progress_result["report_text"]
        agent_info = AGENT_PROGRESS_CONFIG
        metrics = bio_result["metrics"]
    else:
        # Default: biomechanical report
        report_text = bio_result["report_text"]
        agent_info = AGENT_1_CONFIG
        metrics = bio_result["metrics"]

    # Recharts comparison data (Patient vs Normative Pediatric Baseline)
    l_max_val = bio_result["metrics"]["left_max_flexion_deg"]
    r_max_val = bio_result["metrics"]["right_max_flexion_deg"]
    knee_flex_val = min(l_max_val, r_max_val)
    gait_sym_val = round(100.0 - bio_result["metrics"]["mean_symmetry_index_pct"], 1)
    hip_flex_val = bio_result["metrics"].get("hip_flexion_rom_deg", 120.0)

    recharts_data = [
        {"metric": "Knee Flexion (°)", "Patient": knee_flex_val, "Normative": 110.0},
        {"metric": "Hip Flexion (°)", "Patient": hip_flex_val, "Normative": 120.0},
        {"metric": "Gait Symmetry (%)", "Patient": max(0.0, gait_sym_val), "Normative": 96.0},
    ]

    return {
        "agent_id": agent_key,
        "agent_name": agent_info["name"],
        "agent_role": agent_info["role"],
        "user_instruction": user_instruction,
        "report_text": report_text,
        "metrics": metrics,
        "recharts_data": recharts_data,
        "gait_pattern": pt_result["gait_pattern"],
        # Agent 1: Video Quality Agent payload
        "video_quality": vq_result,
        # Clinical Risk Assessment Agent payload
        "clinical_risk": {
            "risk_level": clinical_risk_result["risk_level"],
            "severity": clinical_risk_result["severity"],
            "asymmetry_percentage": clinical_risk_result["asymmetry_percentage"],
            "peak_asymmetry_percentage": clinical_risk_result["peak_asymmetry_percentage"],
            "affected_side": clinical_risk_result["affected_side"],
            "triggered_measurements": clinical_risk_result["triggered_measurements"],
            "reasoning": clinical_risk_result["reasoning"],
            "recommendation": clinical_risk_result["recommendation"],
            "report_text": clinical_risk_result["report_text"],
            "is_diagnostic": False,
            "thresholds_used": clinical_risk_result["thresholds_used"],
        },
        # Patient Progress Monitoring Agent payload
        "patient_progress": progress_result,
    }


@app.post("/api/agent-report")
async def generate_agent_report(req: AgentReportRequest):
    target = req.agent_id or "analyst"
    return _process_agent_request(target, req)


@app.post("/api/agents/{agent_type}")
async def generate_agent_by_type(agent_type: str, req: Dict[str, Any]):
    if agent_type in ["empathetic-translator", "translator", "family-guide", "6"]:
        kinematic_data = req.get("kinematic_data") or req.get("gait_analysis") or req.get("metrics")
        file_path = req.get("file_path")
        case_id = req.get("case_id")
        user_instruction = req.get("user_instruction") or req.get("message")

        if not kinematic_data and (file_path or case_id):
            try:
                agent_req = AgentReportRequest(
                    agent_id="biomechanical",
                    file_path=file_path,
                    case_id=case_id,
                    source_type="custom" if file_path else "preset"
                )
                processed = _process_agent_request("biomechanical", agent_req)
                kinematic_data = processed
            except Exception:
                pass

        if not kinematic_data or not isinstance(kinematic_data, dict) or not (
            kinematic_data.get("metrics") or kinematic_data.get("telemetry") or kinematic_data.get("gait_analysis")
        ):
            raise HTTPException(
                status_code=400,
                detail="No kinematic telemetry provided. Please complete a video scan first."
            )

        return process_empathetic_translator(kinematic_data, user_instruction=user_instruction)

    if agent_type in ["chat", "clinical-assistant", "assistant"]:
        msg = req.get("message") or req.get("user_instruction") or "Give me a summary"
        ctx = req.get("context") or req
        return process_clinical_assistant_query(msg, ctx)
    try:
        req_obj = AgentReportRequest(**req)
    except Exception:
        req_obj = AgentReportRequest(agent_id=agent_type)
    return _process_agent_request(agent_type, req_obj)


class EmpatheticTranslatorRequest(BaseModel):
    kinematic_data: Optional[Dict[str, Any]] = None
    user_instruction: Optional[str] = None
    file_path: Optional[str] = None
    case_id: Optional[str] = None


@app.post("/api/agents/empathetic-translator")
async def empathetic_translator_endpoint(req: EmpatheticTranslatorRequest):
    kinematic_data = req.kinematic_data
    file_path = req.file_path
    case_id = req.case_id

    if not kinematic_data and (file_path or case_id):
        try:
            agent_req = AgentReportRequest(
                agent_id="biomechanical",
                file_path=file_path,
                case_id=case_id,
                source_type="custom" if file_path else "preset"
            )
            processed = _process_agent_request("biomechanical", agent_req)
            kinematic_data = processed
        except Exception as e:
            print(f"Warning deriving kinematic data for empathetic translator: {e}")

    if not kinematic_data or not isinstance(kinematic_data, dict) or not (
        kinematic_data.get("metrics") or kinematic_data.get("telemetry") or kinematic_data.get("gait_analysis")
    ):
        raise HTTPException(
            status_code=400,
            detail="No kinematic telemetry provided. Please complete a video scan first."
        )

    return process_empathetic_translator(kinematic_data, user_instruction=req.user_instruction)


@app.get("/api/patient-history/{patient_id}")
def get_history(patient_id: str):
    assessments = get_patient_assessments(patient_id)
    return {"patient_id": patient_id, "count": len(assessments), "assessments": assessments}


class SaveAssessmentRequest(BaseModel):
    patient_id: str
    assessment: Dict[str, Any]


@app.post("/api/save-assessment")
def save_assessment_endpoint(req: SaveAssessmentRequest):
    saved, msg = save_patient_assessment(req.patient_id, req.assessment)
    return {"saved": saved, "message": msg, "patient_id": req.patient_id}


@app.get("/api/generate-pdf")
@app.post("/api/generate-pdf")
async def generate_pdf_endpoint(context: Optional[Dict[str, Any]] = None):
    """
    Generates and downloads a binary PDF report for the current patient session context.
    """
    ctx = context or {}
    pdf_bytes = generate_clinical_pdf_report(ctx)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=kinematrace_clinical_report.pdf",
            "Access-Control-Allow-Origin": "*"
        }
    )


@app.post("/api/compare-progress")
async def compare_progress_endpoint(
    old_video: Optional[UploadFile] = File(None),
    new_video: Optional[UploadFile] = File(None),
    old_case_id: Optional[str] = Form(None),
    new_case_id: Optional[str] = Form(None)
):
    """
    Agent 4: Patient Gait Progress Comparison Agent endpoint.
    Accepts two actual walking videos (old_video and new_video) or preset case IDs (old_case_id, new_case_id).
    Runs Agent 1 (Video Quality) -> Agent 2 (Gait Analysis) -> Clinical Risk for both videos,
    and returns Agent 4 comparison analysis (IMPROVED / STABLE / WORSENED).
    """
    import time

    def _process_video_source(
        file_obj: Optional[UploadFile],
        case_id: Optional[str],
        label: str
    ) -> Dict[str, Any]:
        if file_obj is not None:
            timestamp_str = str(int(time.time() * 1000))
            safe_name = f"{label}_{timestamp_str}_{file_obj.filename.replace(' ', '_')}"
            file_path = os.path.join(UPLOADS_DIR, safe_name)
            # Read bytes
            with open(file_path, "wb") as f:
                f.write(file_obj.file.read())
            display_name = file_obj.filename
            
            # Agent 1 Quality
            quality = validate_video_quality(file_path)
            if quality.get("status") == "FAIL":
                return {"status": "FAIL", "label": label, "quality": quality, "display_name": display_name}
            
            # Agent 2 Pose & Angles
            df_pose = extract_pose_data(file_path)
            angles_df = calculate_joint_angles(df_pose)
            risk_res = evaluate_gait_risk(df_pose)
            bio_res = analyze_biomechanics(angles_df, risk_res)

            # WebM render for UI video player
            webm_name = f"annotated_{label}_{timestamp_str}.webm"
            webm_path = os.path.join(STATIC_DIR, webm_name)
            video_url = f"/uploads/{safe_name}"
            try:
                for _ in stream_annotated_frames(file_path, webm_path):
                    pass
                if os.path.exists(webm_path):
                    video_url = f"/api/video/{webm_name}"
            except Exception as e:
                print(f"Warning generating WebM for {label}: {e}")

            risk_eval = assess_clinical_risk(bio_res)
            return {
                "status": "PASS",
                "file_path": file_path,
                "display_name": display_name,
                "video_url": video_url,
                "quality": quality,
                "bio_result": bio_res,
                "risk_result": risk_eval,
                "angles_df": angles_df
            }
        
        elif case_id:
            if case_id == "case1":
                csv_path = os.path.join(WORKSPACE_DIR, "demo_normative.csv")
                raw_video = os.path.join(WORKSPACE_DIR, "demo_normative.mp4")
                display_name = "demo_normative.mp4 (Normative Control)"
                webm_name = "demo_normative_annotated.webm"
            else:
                csv_path = os.path.join(WORKSPACE_DIR, "demo_asymmetric.csv")
                raw_video = os.path.join(WORKSPACE_DIR, "demo_asymmetric.mp4")
                display_name = "demo_asymmetric.mp4 (Asymmetric Gait)"
                webm_name = "demo_asymmetric_annotated.webm"

            quality = validate_video_quality(raw_video)
            if quality.get("status") == "FAIL":
                return {"status": "FAIL", "label": label, "quality": quality, "display_name": display_name}

            if os.path.exists(csv_path):
                df_pose = pd.read_csv(csv_path, index_col="frame")
            else:
                df_pose = extract_pose_data(raw_video)

            angles_df = calculate_joint_angles(df_pose)
            risk_res = evaluate_gait_risk(df_pose)
            bio_res = analyze_biomechanics(angles_df, risk_res)
            risk_eval = assess_clinical_risk(bio_res)

            video_url = f"/api/video/{webm_name}"
            return {
                "status": "PASS",
                "file_path": raw_video,
                "display_name": display_name,
                "video_url": video_url,
                "quality": quality,
                "bio_result": bio_res,
                "risk_result": risk_eval,
                "angles_df": angles_df
            }
        else:
            raise HTTPException(status_code=400, detail=f"No video file or case_id provided for {label}")

    # Process OLD video
    old_res = _process_video_source(old_video, old_case_id or ("case2" if not old_video else None), "old")
    if old_res["status"] == "FAIL":
        return JSONResponse(
            status_code=400,
            content={
                "comparison_status": "FAILED",
                "failed_video": "OLD",
                "message": f"❌ Old video ({old_res['display_name']}) is not suitable for gait comparison.\n\nPlease upload a better-quality previous assessment video.",
                "quality": old_res["quality"]
            }
        )

    # Process NEW video
    new_res = _process_video_source(new_video, new_case_id or ("case1" if not new_video else None), "new")
    if new_res["status"] == "FAIL":
        return JSONResponse(
            status_code=400,
            content={
                "comparison_status": "FAILED",
                "failed_video": "NEW",
                "message": f"❌ New video ({new_res['display_name']}) is not suitable for gait comparison.\n\nPlease upload a better-quality current assessment video.",
                "quality": new_res["quality"]
            }
        )

    # Run Agent 4 Gait Progress Comparison
    comp_result = compare_gait_progress(
        old_gait_result=old_res["bio_result"],
        new_gait_result=new_res["bio_result"],
        old_risk_result=old_res["risk_result"],
        new_risk_result=new_res["risk_result"],
        old_quality_result=old_res["quality"],
        new_quality_result=new_res["quality"],
        old_file_name=old_res["display_name"],
        new_file_name=new_res["display_name"],
        old_video_url=old_res["video_url"],
        new_video_url=new_res["video_url"]
    )

    return comp_result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

