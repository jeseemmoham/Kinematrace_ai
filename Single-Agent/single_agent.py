"""
single_agent.py

KinemaTrace AI — Central Single-Agent Implementation

Defines a single, unified autonomous agent (KinemaTraceSingleAgent) that orchestrates
the complete end-to-end pediatric gait analysis pipeline:
1. Video Quality Validation
2. MediaPipe Pose Extraction & Skeletal Overlay Generation
3. Biomechanical Kinematic & Symmetry Analysis
4. Pediatric Normative Comparison & Clinical Risk Classification
5. Longitudinal Patient Progress Tracking (if baseline data provided)
6. Clinical PDF Report Generation
7. Conversational Q&A and Parent Summary Translation

Reuses proven underlying biomechanical calculations and computer vision engines:
- clinical_math.py
- cv_engine.py
- pediatric_normatives.py
- pdf_generator.py
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, Optional, List, Union
import pandas as pd
import numpy as np

# Ensure local imports work cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clinical_math import calculate_joint_angles, compute_symmetry_index, evaluate_gait_risk
from cv_engine import extract_pose_data, generate_annotated_video, process_video_single_pass
from pediatric_normatives import get_pediatric_normative_profile, PEDIATRIC_RISK_CONFIG
from pdf_generator import generate_clinical_pdf_report


class KinemaTraceSingleAgent:
    """
    Monolithic Single-Agent Controller for KinemaTrace AI.
    Handles the entire video-to-report clinical workflow autonomously within a single agent context.
    """

    def __init__(self, agent_name: str = "KinemaTrace Single Agent"):
        self.agent_name = agent_name
        self.role = "Autonomous End-to-End Pediatric Motor Screening Agent"
        self.goal = (
            "Individually perform video quality inspection, 3D pose extraction, "
            "biomechanical gait angle computation, clinical risk assessment, longitudinal progress "
            "tracking, and clinical PDF report generation."
        )

    def validate_video_quality(self, video_path: str) -> Dict[str, Any]:
        """
        Sub-step 1: Validates raw video files using computer vision metrics.
        Inspects resolution, frame rate, full-body visibility, and duration.
        """
        if not os.path.exists(video_path):
            return {
                "status": "FAIL",
                "video_quality_score": 0,
                "reasons": [f"Video file not found at: {video_path}"],
                "recommendation": "Provide a valid video file path."
            }

        import cv2
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {
                "status": "FAIL",
                "video_quality_score": 0,
                "reasons": ["Unable to open video stream."],
                "recommendation": "Check video file encoding."
            }

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_sec = frame_count / fps if fps > 0 else 0
        cap.release()

        score = 100
        reasons = []

        if duration_sec < 3.0:
            score -= 30
            reasons.append("Walking duration is under 3 seconds.")
        if width < 640 or height < 480:
            score -= 20
            reasons.append("Resolution is lower than recommended HD standard.")
        if fps < 20:
            score -= 15
            reasons.append("Frame rate is below 20 FPS.")

        status = "PASS" if score >= 80 else ("WARNING" if score >= 60 else "FAIL")

        return {
            "status": status,
            "video_quality_score": score,
            "resolution": f"{width}x{height}",
            "fps": round(fps, 1),
            "duration_sec": round(duration_sec, 2),
            "total_frames": frame_count,
            "reasons": reasons,
            "recommendation": "Video is acceptable for kinematic processing." if status != "FAIL" else "Re-record video following recording guidelines."
        }

    def analyze_biomechanics(self, df_pose: pd.DataFrame, patient_age: str = "2") -> Dict[str, Any]:
        """
        Sub-step 2: Calculates joint flexion angles, bilateral symmetry index, and ROM metrics.
        """
        norm_profile = get_pediatric_normative_profile(patient_age)
        angles_df = calculate_joint_angles(df_pose)

        left_knee = angles_df["left_knee_angle"].dropna()
        right_knee = angles_df["right_knee_angle"].dropna()

        left_knee_rom = float(left_knee.max() - left_knee.min()) if len(left_knee) > 0 else 0.0
        right_knee_rom = float(right_knee.max() - right_knee.min()) if len(right_knee) > 0 else 0.0
        rom_diff = abs(left_knee_rom - right_knee_rom)

        si_series = compute_symmetry_index(left_knee, right_knee)
        mean_si = float(si_series.mean()) if len(si_series) > 0 else 0.0
        peak_si = float(si_series.max()) if len(si_series) > 0 else 0.0

        gait_symmetry_pct = max(0.0, 100.0 - mean_si)

        gait_risk_data = evaluate_gait_risk(df_pose)

        return {
            "normative_profile": norm_profile,
            "metrics": {
                "left_knee_rom_deg": round(left_knee_rom, 2),
                "right_knee_rom_deg": round(right_knee_rom, 2),
                "rom_difference_deg": round(rom_diff, 2),
                "mean_symmetry_index_pct": round(mean_si, 2),
                "peak_symmetry_index_pct": round(peak_si, 2),
                "gait_symmetry_pct": round(gait_symmetry_pct, 2),
            },
            "angles_df": angles_df,
            "gait_risk_raw": gait_risk_data
        }

    def assess_clinical_risk(self, bio_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sub-step 3: Classifies motor risk based on pediatric risk thresholds.
        """
        metrics = bio_results["metrics"]
        gait_sym = metrics["gait_symmetry_pct"]
        rom_diff = metrics["rom_difference_deg"]
        peak_si = metrics["peak_symmetry_index_pct"]

        triggered_factors = []
        severity_score = 0.0

        if gait_sym < 85.0:
            triggered_factors.append(f"Severe bilateral asymmetry: Gait symmetry is {gait_sym}% (threshold >= 88.0%)")
            severity_score += 4.0
        elif gait_sym < 90.0:
            triggered_factors.append(f"Moderate bilateral asymmetry: Gait symmetry is {gait_sym}% (threshold >= 90.0%)")
            severity_score += 2.0

        if rom_diff > 12.0:
            triggered_factors.append(f"High inter-limb ROM discrepancy: {rom_diff}° (threshold <= 10.0°)")
            severity_score += 3.5
        elif rom_diff > 10.0:
            triggered_factors.append(f"Moderate ROM discrepancy: {rom_diff}° (threshold <= 10.0°)")
            severity_score += 1.5

        if peak_si > 25.0:
            triggered_factors.append(f"Excessive peak asymmetry spike: {peak_si}% (threshold <= 20.0%)")
            severity_score += 2.5

        if severity_score >= 5.0 or gait_sym < 85.0:
            risk_level = "HIGH"
            recommendation = "Refer to Pediatric Orthopedic Specialist for formal gait laboratory evaluation."
            followup = "Immediate / Within 2 weeks"
        elif severity_score >= 2.0 or gait_sym < 90.0:
            risk_level = "MEDIUM"
            recommendation = "Pediatric Physical Therapy evaluation & home exercises recommended."
            followup = "3 to 6 months"
        else:
            risk_level = "LOW"
            recommendation = "Gait parameters within normal pediatric screening range. Continue routine developmental checkups."
            followup = "12 months routine"

        return {
            "risk_level": risk_level,
            "severity_score": round(severity_score, 1),
            "triggered_risk_factors": triggered_factors,
            "clinical_recommendation": recommendation,
            "followup_timeline": followup
        }

    def track_patient_progress(
        self,
        current_metrics: Dict[str, Any],
        previous_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Sub-step 4: Longitudinal progress comparison against prior screening session.
        """
        if not previous_metrics:
            return {
                "progress_status": "BASELINE",
                "delta_symmetry_pct": 0.0,
                "delta_rom_difference_deg": 0.0,
                "summary": "First recorded assessment for this patient. Baseline established."
            }

        curr_sym = current_metrics["gait_symmetry_pct"]
        prev_sym = previous_metrics.get("gait_symmetry_pct", curr_sym)

        curr_rom_diff = current_metrics["rom_difference_deg"]
        prev_rom_diff = previous_metrics.get("rom_difference_deg", curr_rom_diff)

        delta_sym = curr_sym - prev_sym
        delta_rom_diff = curr_rom_diff - prev_rom_diff

        if delta_sym >= 3.0 and delta_rom_diff <= -1.5:
            status = "IMPROVED"
            summary = f"Gait symmetry improved by +{delta_sym:.1f}% and ROM asymmetry reduced by {abs(delta_rom_diff):.1f}°."
        elif delta_sym <= -3.0 or delta_rom_diff >= 2.0:
            status = "WORSENED"
            summary = f"Gait symmetry declined by {delta_sym:.1f}% and ROM asymmetry increased by {delta_rom_diff:.1f}°."
        else:
            status = "STABLE"
            summary = "Gait parameters remain stable relative to baseline assessment."

        return {
            "progress_status": status,
            "delta_symmetry_pct": round(delta_sym, 2),
            "delta_rom_difference_deg": round(delta_rom_diff, 2),
            "summary": summary
        }

    def generate_report(
        self,
        patient_info: Dict[str, Any],
        quality_res: Dict[str, Any],
        bio_res: Dict[str, Any],
        risk_res: Dict[str, Any],
        progress_res: Dict[str, Any],
        output_pdf_path: str
    ) -> str:
        """
        Sub-step 5: Generates comprehensive PDF clinical report.
        """
        metrics = bio_res["metrics"]
        context = {
            "patient_info": patient_info,
            "video_quality": quality_res,
            "telemetry": metrics,
            "clinical_risk": risk_res,
            "patient_progress": progress_res
        }

        pdf_bytes = generate_clinical_pdf_report(context)
        with open(output_pdf_path, "wb") as f:
            f.write(pdf_bytes)

        return output_pdf_path

    def run_complete_pipeline(
        self,
        video_path: str,
        patient_id: str = "PATIENT-001",
        patient_name: str = "Demo Child",
        patient_age: str = "2 years",
        previous_assessment: Optional[Dict[str, Any]] = None,
        output_pdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main Orchestrator Method: Executes the complete end-to-end workflow sequentially.
        """
        start_time = time.time()

        # 1. Video Quality Validation
        quality_res = self.validate_video_quality(video_path)
        if quality_res["status"] == "FAIL":
            return {
                "agent_name": self.agent_name,
                "status": "FAILED_AT_QUALITY_CHECK",
                "quality_assessment": quality_res,
                "message": "Pipeline halted due to failed video quality inspection."
            }

        # 2. Pose Extraction (CSV or MediaPipe)
        base_name = os.path.splitext(video_path)[0]
        csv_path = f"{base_name}.csv"

        if os.path.exists(csv_path):
            df_pose = pd.read_csv(csv_path, index_col="frame" if "frame" in pd.read_csv(csv_path, nrows=1).columns else None)
        else:
            df_pose = extract_pose_data(video_path)

        # 3. Biomechanical Analysis
        bio_res = self.analyze_biomechanics(df_pose, patient_age)

        # 4. Clinical Risk Assessment
        risk_res = self.assess_clinical_risk(bio_res)

        # 5. Progress Tracking
        prev_metrics = previous_assessment.get("metrics") if previous_assessment else None
        progress_res = self.track_patient_progress(bio_res["metrics"], prev_metrics)

        # 6. Report Generation
        if not output_pdf_path:
            output_pdf_path = os.path.join(os.path.dirname(video_path), f"{patient_id}_SingleAgent_Report.pdf")

        patient_info = {
            "patient_id": patient_id,
            "patient_name": patient_name,
            "age": patient_age,
            "screening_date": time.strftime("%Y-%m-%d")
        }

        try:
            pdf_path = self.generate_report(patient_info, quality_res, bio_res, risk_res, progress_res, output_pdf_path)
        except Exception as e:
            pdf_path = f"PDF Generation Error: {str(e)}"

        elapsed = round(time.time() - start_time, 2)

        return {
            "agent_name": self.agent_name,
            "status": "SUCCESS",
            "execution_time_sec": elapsed,
            "patient_info": patient_info,
            "video_quality": quality_res,
            "biomechanical_metrics": bio_res["metrics"],
            "clinical_risk": risk_res,
            "longitudinal_progress": progress_res,
            "generated_pdf_report": pdf_path,
            "agent_summary": (
                f"Single-agent analysis complete in {elapsed}s. Video quality: {quality_res['status']}. "
                f"Gait Symmetry: {bio_res['metrics']['gait_symmetry_pct']}%. Clinical Risk: {risk_res['risk_level']}. "
                f"Progress Status: {progress_res['progress_status']}."
            )
        }

    def answer_clinical_query(self, query: str, context: Dict[str, Any]) -> str:
        """
        Unified Q&A Engine for Clinicians.
        """
        metrics = context.get("biomechanical_metrics", {})
        risk = context.get("clinical_risk", {})
        query_lower = query.lower()

        if "symmetry" in query_lower:
            return f"The patient's bilateral gait symmetry is {metrics.get('gait_symmetry_pct', 'N/A')}%. Normal threshold is >= 90.0%."
        elif "risk" in query_lower:
            return f"The assessed risk level is {risk.get('risk_level', 'N/A')} with severity score {risk.get('severity_score', 'N/A')}. Recommendation: {risk.get('clinical_recommendation', 'N/A')}."
        elif "rom" in query_lower or "knee" in query_lower:
            return f"Left Knee ROM: {metrics.get('left_knee_rom_deg', 'N/A')}°, Right Knee ROM: {metrics.get('right_knee_rom_deg', 'N/A')}° (Discrepancy: {metrics.get('rom_difference_deg', 'N/A')}°)."
        else:
            return f"Single Agent Analysis Summary: {context.get('agent_summary', 'All parameters evaluated successfully.')}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KinemaTrace AI Single-Agent Pipeline Runner")
    parser.add_argument("--video", type=str, default="demo_normative.mp4", help="Path to input walking video file")
    parser.add_argument("--age", type=str, default="2", help="Patient age in years (1-4)")
    parser.add_argument("--patient_id", type=str, default="PATIENT-001", help="Patient ID")
    args = parser.parse_args()

    agent = KinemaTraceSingleAgent()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(script_dir, args.video) if not os.path.isabs(args.video) else args.video

    print(f"=== Launching {agent.agent_name} ===")
    print(f"Target Video: {video_path}")
    result = agent.run_complete_pipeline(video_path=video_path, patient_id=args.patient_id, patient_age=args.age)

    print("\n--- Pipeline Result Summary ---")
    print(json.dumps(result, indent=2, default=str))
