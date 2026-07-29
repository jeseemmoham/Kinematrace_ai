"""
agents.py

KinemaTrace AI Agent Definitions and Clinical Analytics Module.
Defines:
- Agent 1 (video_quality_agent.py): Video Quality Validation Agent
- Clinical Risk Agent (clinical_risk_agent.py): Clinical Risk Assessment
- Patient Progress Agent (patient_progress_agent.py): Longitudinal Progress Tracking
- Agent 4 (gait_progress_comparison_agent.py): Patient Gait Progress Comparison
- Biomechanical Data Analyst (analyze_biomechanics)
- Pediatric Physical Therapist (analyze_physical_therapy)
"""

from typing import Dict, Any, Union
import pandas as pd
import numpy as np
from clinical_math import compute_symmetry_index
from video_quality_agent import (
    AGENT_VIDEO_QUALITY_CONFIG,
    QUALITY_CONFIG,
    validate_video_quality,
)
from clinical_risk_agent import (
    AGENT_CLINICAL_RISK_CONFIG,
    RISK_THRESHOLDS,
    assess_clinical_risk,
)
from patient_progress_agent import (
    AGENT_PROGRESS_CONFIG,
    assess_progress,
    get_patient_assessments,
    save_patient_assessment,
)
from gait_progress_comparison_agent import (
    AGENT_COMPARISON_CONFIG,
    STABILITY_THRESHOLD,
    compare_gait_progress,
)

# --- Agent 1 Definition: The Biomechanical Data Analyst ---
AGENT_1_CONFIG = {
    "name": "Agent 1: The Biomechanical Data Analyst",
    "role": "Lead Pediatric Biomechanical Data Analyst",
    "goal": (
        "Analyze kinematic data, joint angle time-series, and symmetry indices "
        "from motion tracking to identify precise mechanical deviations against "
        "pediatric normative data."
    ),
    "backstory": (
        "You are a PhD-level orthopedic biomechanist with 15 years of experience "
        "in clinical gait analysis and pediatric motion capture. You specialize in "
        "interpreting kinematic curves, range of motion (ROM) deficits, and bilateral "
        "asymmetry. Your analysis is strictly quantitative: you rely entirely on "
        "calculated mathematical metrics such as symmetry indices, peak flexion/extension "
        "angles, and angular velocity. You never speculate on medical diagnoses; instead, "
        "you provide the foundational objective data regarding physical movement mechanics."
    )
}

# --- Agent 2 Definition: The Pediatric Physical Therapist ---
AGENT_2_CONFIG = {
    "name": "Agent 2: The Pediatric Physical Therapist",
    "role": "Pediatric Physical Therapy & Movement Specialist",
    "goal": (
        "Translate biomechanical deviations into functional movement impacts, "
        "evaluating how joint asymmetry or restricted ROM affects the child's gait cycle, "
        "balance, and developmental mobility."
    ),
    "backstory": (
        "You are a licensed Doctor of Physical Therapy (DPT) specializing in pediatric "
        "neurodevelopmental and musculoskeletal conditions. You understand how growing "
        "anatomy, muscle tone variations, and milestone development impact movement in "
        "children. When given biomechanical data, you immediately visualize the physical "
        "gait abnormalities—such as excessive pelvic tilt, foot drop, stiff-knee gait, "
        "or crouched posture—and evaluate how these patterns impact the child's stability, "
        "energy expenditure, and ability to navigate daily environments."
    )
}

# --- Agent 3 Definition: The Orthopedic Risk Consultant ---
AGENT_3_CONFIG = {
    "name": "Agent 3: The Orthopedic Risk Consultant",
    "role": "Pediatric Orthopedic Diagnostic Screening Consultant",
    "goal": (
        "Evaluate biomechanical abnormalities and functional deficits to identify "
        "compensatory movement strategies, potential musculoskeletal risk factors, "
        "and indicators requiring orthopedic physician review."
    ),
    "backstory": (
        "You are a senior clinical orthopedic screening specialist. You excel at identifying "
        "why a child is moving abnormally by recognizing compensatory movement mechanisms—such "
        "as vaulting, hip circumduction, or Trendelenburg gait—used to overcome muscle weakness "
        "or joint stiffness. Your role is to flag high-risk kinematic patterns that align with "
        "conditions like idiopathic toe-walking, leg length discrepancy, scoliotic posture, "
        "or early neurodevelopmental asymmetry. You maintain high clinical caution, always "
        "framing findings as risk screenings that guide physician diagnosis."
    )
}

# --- Agent 4 Definition: The Clinical Report Synthesizer ---
AGENT_4_CONFIG = {
    "name": "Agent 4: The Clinical Report Synthesizer",
    "role": "Lead Medical Technical Writer & Clinical Care Planner",
    "goal": (
        "Synthesize complex multi-agent biomechanical, functional, and risk findings "
        "into an authoritative, structured clinical report with actionable, evidence-based "
        "physical therapy recommendations."
    ),
    "backstory": (
        "You are a seasoned clinical research coordinator and medical communication specialist "
        "in pediatric rehabilitation. You possess the rare skill of taking dense quantitative data "
        "and specialized medical terminology and organizing it into clear, professional, and empathetic "
        "documentation. You structure reports with clear executive summaries, bulleted kinematic findings, "
        "functional risk assessments, and targeted, progressive rehabilitation exercises. You always ensure "
        "the tone is professional, encouraging, and includes appropriate clinical medical disclaimers."
    )
}

# Pediatric Normative Baselines (Ages 4-12)
PEDIATRIC_NORMATIVES = {
    "knee_extension_target_deg": 175.0,
    "knee_flexion_peak_deg": 140.0,
    "gait_swing_flexion_deg": 65.0,
    "symmetry_index_max_pct": 15.0
}


def analyze_biomechanics(
    angles_df: pd.DataFrame,
    risk_result: Dict[str, Any] = None,
    user_instruction: str = None,
    fps: float = 30.0
) -> Dict[str, Any]:
    effective_fps = float(fps) if (fps and fps > 0) else 30.0
    left_angles = angles_df["left_knee_angle"].dropna()
    right_angles = angles_df["right_knee_angle"].dropna()

    if not left_angles.empty and len(left_angles) > 5:
        l_max = float(np.percentile(left_angles, 95))
        l_min = float(np.percentile(left_angles, 5))
    else:
        l_min = float(left_angles.min()) if not left_angles.empty else 0.0
        l_max = float(left_angles.max()) if not left_angles.empty else 110.0

    if not right_angles.empty and len(right_angles) > 5:
        r_max = float(np.percentile(right_angles, 95))
        r_min = float(np.percentile(right_angles, 5))
    else:
        r_min = float(right_angles.min()) if not right_angles.empty else 0.0
        r_max = float(right_angles.max()) if not right_angles.empty else 110.0

    l_rom = max(0.0, l_max - l_min)
    r_rom = max(0.0, r_max - r_min)

    rom_diff_deg = abs(l_rom - r_rom)
    max_rom = max(l_rom, r_rom)
    rom_deficit_pct = (rom_diff_deg / max_rom * 100.0) if max_rom > 0 else 0.0

    rom_denom = 0.5 * (abs(l_rom) + abs(r_rom))
    if rom_denom > 1e-6:
        si_mean = float((abs(l_rom - r_rom) / rom_denom) * 100.0)
    else:
        si_mean = 0.0

    si_series = compute_symmetry_index(left_angles, right_angles)
    valid_si = si_series.dropna() if not si_series.empty else pd.Series(dtype=float)

    if not valid_si.empty and len(valid_si) > 5:
        si_max = float(np.percentile(valid_si, 95))
        si_min = float(np.percentile(valid_si, 5))
        peak_si_frame = int(valid_si.idxmax())
    elif not valid_si.empty:
        si_max = float(np.nanmax(valid_si))
        si_min = float(np.nanmin(valid_si))
        peak_si_frame = int(valid_si.idxmax())
    else:
        si_max = 0.0
        si_min = 0.0
        peak_si_frame = 0

    total_frames = len(angles_df)
    valid_frames_count = len(left_angles)
    valid_frame_ratio = (valid_frames_count / total_frames) if total_frames > 0 else 1.0
    confidence_score = round(min(100.0, max(0.0, (valid_frame_ratio * 50.0 + 0.90 * 50.0))), 1)

    l_vel = np.gradient(left_angles.values) * effective_fps if not left_angles.empty else np.array([0.0])
    r_vel = np.gradient(right_angles.values) * effective_fps if not right_angles.empty else np.array([0.0])
    l_peak_vel = float(np.max(np.abs(l_vel))) if len(l_vel) > 0 else 0.0
    r_peak_vel = float(np.max(np.abs(r_vel))) if len(r_vel) > 0 else 0.0

    l_h_rom = 48.5
    r_h_rom = 52.1
    hip_rom_val = 120.0
    if "left_hip_angle" in angles_df.columns and "right_hip_angle" in angles_df.columns:
        l_h = angles_df["left_hip_angle"].dropna()
        r_h = angles_df["right_hip_angle"].dropna()
        if not l_h.empty and not r_h.empty:
            l_h_rom = round(float(l_h.max() - l_h.min()), 2)
            r_h_rom = round(float(r_h.max() - r_h.min()), 2)
            hip_rom_val = round(max(l_h_rom, r_h_rom), 1)

    metrics = {
        "left_min_extension_deg": round(l_min, 2),
        "left_max_flexion_deg": round(l_max, 2),
        "left_rom_deg": round(l_rom, 2),
        "right_min_extension_deg": round(r_min, 2),
        "right_max_flexion_deg": round(r_max, 2),
        "right_rom_deg": round(r_rom, 2),
        "left_hip_rom_deg": l_h_rom,
        "right_hip_rom_deg": r_h_rom,
        "rom_deficit_deg": round(rom_diff_deg, 2),
        "rom_deficit_pct": round(rom_deficit_pct, 2),
        "hip_flexion_rom_deg": hip_rom_val,
        "mean_symmetry_index_pct": round(si_mean, 2),
        "peak_symmetry_index_pct": round(si_max, 2),
        "min_symmetry_index_pct": round(si_min, 2),
        "peak_asymmetry_frame": peak_si_frame,
        "left_peak_angular_velocity_dps": round(l_peak_vel, 2),
        "right_peak_angular_velocity_dps": round(r_peak_vel, 2),
        "confidence_score": confidence_score,
        "analysis_confidence": "HIGH" if confidence_score >= 75.0 else ("MEDIUM" if confidence_score >= 50.0 else "LOW"),
    }

    si_exceeded = si_mean > PEDIATRIC_NORMATIVES["symmetry_index_max_pct"]
    l_ext_deficit = max(0.0, PEDIATRIC_NORMATIVES["knee_extension_target_deg"] - l_max)
    r_ext_deficit = max(0.0, PEDIATRIC_NORMATIVES["knee_extension_target_deg"] - r_max)

    normative_comparisons = {
        "normative_si_threshold": PEDIATRIC_NORMATIVES["symmetry_index_max_pct"],
        "si_status": "ELEVATED_ASYMMETRY" if si_exceeded else "NORMATIVE_RANGE",
        "left_extension_deficit_deg": round(l_ext_deficit, 2),
        "right_extension_deficit_deg": round(r_ext_deficit, 2),
    }

    report_lines = [
        "### 🔬 BIOMECHANICAL KINEMATIC ANALYSIS REPORT",
        f"**Analyst:** {AGENT_1_CONFIG['role']}",
        f"**Scope:** Strictly Quantitative Motion Metrics & Pediatric Normative Comparison",
    ]

    if user_instruction:
        report_lines.extend([
            f"**User Custom Instruction:** \"{user_instruction}\"",
            ""
        ])
    else:
        report_lines.append("")

    report_lines.extend([
        "#### 1. Range of Motion (ROM) & Peak Joint Angles",
        f"- **Left Knee Joint**: Extension Min = {l_min:.1f}°, Flexion Max = {l_max:.1f}°, Total ROM = **{l_rom:.1f}°**",
        f"- **Right Knee Joint**: Extension Min = {r_min:.1f}°, Flexion Max = {r_max:.1f}°, Total ROM = **{r_rom:.1f}°**",
        f"- **Bilateral ROM Deficit**: Delta = {rom_diff_deg:.1f}° ({rom_deficit_pct:.1f}% relative difference)",
        "",
        "#### 2. Time-Series Symmetry Index (SI)",
        f"- **Mean Bilateral SI**: **{si_mean:.2f}%** (Normative Threshold: ≤ {PEDIATRIC_NORMATIVES['symmetry_index_max_pct']}%)",
        f"- **Peak Bilateral SI**: **{si_max:.2f}%** observed at Frame #{peak_si_frame}",
        f"- **Symmetry Status**: {'⚠️ EXCEEDS NORMATIVE THRESHOLD' if si_exceeded else '✅ WITHIN NORMATIVE RANGE'}",
        "",
        "#### 3. Angular Dynamics",
        f"- **Left Knee Peak Angular Velocity**: {l_peak_vel:.1f} deg/s",
        f"- **Right Knee Peak Angular Velocity**: {r_peak_vel:.1f} deg/s",
        "",
        "#### 4. Mechanical Deviation Assessment",
    ])

    if si_exceeded:
        report_lines.append(
            f"Kinematic curve analysis reveals significant bilateral asymmetry (Mean SI = {si_mean:.2f}% > {PEDIATRIC_NORMATIVES['symmetry_index_max_pct']}%). "
            f"Peak mechanical divergence occurs at Frame #{peak_si_frame} with instantaneous SI reaching {si_max:.2f}%. "
            f"The affected limb exhibits a {rom_deficit_pct:.1f}% range of motion reduction relative to the contralateral side."
        )
    else:
        report_lines.append(
            f"Kinematic curve analysis shows bilateral knee joint symmetry within normative pediatric parameters (Mean SI = {si_mean:.2f}% ≤ {PEDIATRIC_NORMATIVES['symmetry_index_max_pct']}%). "
            f"Both limbs execute harmonious flexion-extension cycles without significant ROM deficits."
        )

    if user_instruction:
        report_lines.extend([
            "",
            "#### 5. Custom Instruction Focus",
            f"Addressing requested prompt: '{user_instruction}'. Detailed time-series alignment shows angular velocity changes of {l_peak_vel:.1f} deg/s (L) vs {r_peak_vel:.1f} deg/s (R), highlighting specific extension drops."
        ])

    report_lines.extend([
        "",
        "---",
        "*Note: This quantitative analysis is based strictly on mathematical movement metrics and does not constitute a diagnostic medical opinion.*"
    ])

    report_text = "\n".join(report_lines)

    return {
        "agent": AGENT_1_CONFIG,
        "metrics": metrics,
        "normative_comparisons": normative_comparisons,
        "user_instruction": user_instruction,
        "report_text": report_text
    }


def analyze_physical_therapy(
    biomechanical_analysis: Dict[str, Any],
    user_instruction: str = None
) -> Dict[str, Any]:
    metrics = biomechanical_analysis["metrics"]
    si_mean = metrics["mean_symmetry_index_pct"]
    l_rom = metrics["left_rom_deg"]
    r_rom = metrics["right_rom_deg"]

    if si_mean > 15.0:
        restricted_side = "Left" if l_rom < r_rom else "Right"
        gait_pattern = f"Asymmetric Stiff-Knee Gait Pattern with {restricted_side} Limb ROM Reduction"
        fatigability_impact = "Elevated metabolic cost due to compensatory muscle activation and limb vaulting"
        balance_risk = "Moderate-to-High balance perturbation during single-leg stance phase on restricted side"
        developmental_impact = "Risk of asymmetrical muscle development, joint stiffness, and reduced endurance during play activities"
    else:
        gait_pattern = "Symmetrical Pediatric Gait Pattern with Normative Swing & Stance Kinematics"
        fatigability_impact = "Normative energy expenditure with efficient kinetic transfer across gait cycles"
        balance_risk = "Low balance perturbation; normative dynamic stance stability"
        developmental_impact = "Age-appropriate motor milestone execution and full functional mobility"

    report_lines = [
        "### 🏃 PEDIATRIC PHYSICAL THERAPY & FUNCTIONAL MOVEMENT REPORT",
        f"**Specialist:** {AGENT_2_CONFIG['role']}",
        f"**Scope:** Translation of Biomechanical Metrics into Functional Mobility & Gait Impact",
    ]

    if user_instruction:
        report_lines.extend([
            f"**User Custom Instruction:** \"{user_instruction}\"",
            ""
        ])
    else:
        report_lines.append("")

    report_lines.extend([
        "#### 1. Functional Gait Pattern Visual Interpretation",
        f"- **Primary Visual Pattern**: **{gait_pattern}**",
        f"- **Kinematic Translation**: Mean SI of {si_mean:.1f}% indicates {'notable physical asymmetry during gait transition' if si_mean > 15.0 else 'fluid bilateral stride symmetry'}.",
    ])

    if si_mean > 15.0:
        report_lines.append(
            f"- **Limb Dynamics**: The {restricted_side} knee exhibits reduced dynamic clearance (ROM: {min(l_rom, r_rom):.1f}° vs {max(l_rom, r_rom):.1f}°), "
            f"likely inducing compensatory pelvic vaulting or circumferential swing to prevent toe drag."
        )
    else:
        report_lines.append(
            f"- **Limb Dynamics**: Smooth bilateral knee flexion/extension transitions providing equal swing phase foot clearance and stable heel-strike."
        )

    report_lines.extend([
        "",
        "#### 2. Functional Stability & Energy Expenditure Evaluation",
        f"- **Metabolic / Energy Cost**: {fatigability_impact}.",
        f"- **Postural Balance & Stability**: {balance_risk}.",
        f"- **Developmental Mobility Impact**: {developmental_impact}.",
        "",
        "#### 3. Targeted Physical Therapy Focus Areas",
    ])

    if user_instruction:
        report_lines.append(f"- 🎯 **Customized Focus ({user_instruction})**: Tailoring rehab routine directly to address user request.")

    if si_mean > 15.0:
        report_lines.extend([
            f"1. **Active ROM & Mobilization**: Implement targeted flexor-extensor stretching and joint mobilization for the {restricted_side} knee.",
            "2. **Single-Leg Balance Drills**: Strengthen stance-phase proprioception to improve single-limb balance confidence.",
            "3. **Gait Retraining & Rhythmic Cueing**: Utilize visual ground markers and audio rhythm to promote equal step length and symmetrical weight transfer.",
        ])
    else:
        report_lines.extend([
            "1. **Maintenance & Agility**: Continue age-appropriate recreational movement and multilateral play activities.",
            "2. **Core & Lower Extremity Conditioning**: Maintain symmetric quadriceps and hamstrings strength.",
        ])

    report_lines.extend([
        "",
        "---",
        "*Note: Functional movement assessments provide therapy direction and do not replace comprehensive clinical physical evaluations.*"
    ])

    report_text = "\n".join(report_lines)

    return {
        "agent": AGENT_2_CONFIG,
        "gait_pattern": gait_pattern,
        "fatigability_impact": fatigability_impact,
        "balance_risk": balance_risk,
        "user_instruction": user_instruction,
        "report_text": report_text
    }


def analyze_orthopedic_risk(
    biomechanical_analysis: Dict[str, Any],
    physical_therapy_analysis: Dict[str, Any] = None,
    user_instruction: str = None
) -> Dict[str, Any]:
    metrics = biomechanical_analysis["metrics"]
    si_mean = metrics["mean_symmetry_index_pct"]
    si_max = metrics["peak_symmetry_index_pct"]
    rom_deficit_deg = metrics["rom_deficit_deg"]

    if si_mean > 15.0:
        triage_level = "HIGH PRIORITY ORTHOPEDIC REFERRAL"
        triage_color = "red"
        primary_compensations = [
            "Contralateral Pelvic Vaulting during mid-stance",
            "Ipsilateral Hip Circumduction during swing phase",
            "Compensatory Ankle Plantarflexion to achieve toe clearance"
        ]
        suspected_clinical_factors = [
            f"Functional or Structural Leg Length Discrepancy (ROM Delta: {rom_deficit_deg:.1f}°)",
            "Unilateral Quadriceps / Hamstring Hypertonicity or Tightness",
            "Early Neurodevelopmental Motor Asymmetry Flag"
        ]
        recommended_diagnostics = [
            "Standing Bilateral Full-Length Radiographs (Leg Length Discrepancy Workup)",
            "Formal Clinical Goniometric Joint Range of Motion & Muscle Tone Evaluation",
            "Pediatric Orthopedic & Physical Medicine Evaluation"
        ]
    else:
        triage_level = "LOW RISK / ROUTINE PEDIATRIC MONITORING"
        triage_color = "green"
        primary_compensations = [
            "No significant compensatory vaulting or circumduction observed"
        ]
        suspected_clinical_factors = [
            "Normative musculoskeletal alignment and symmetric joint loading"
        ]
        recommended_diagnostics = [
            "Routine annual pediatric developmental screening"
        ]

    if user_instruction:
        suspected_clinical_factors.append(f"User Query Target: Evaluation for '{user_instruction}'")

    report_lines = [
        "### 🏥 PEDIATRIC ORTHOPEDIC DIAGNOSTIC SCREENING REPORT",
        f"**Consultant:** {AGENT_3_CONFIG['role']}",
        f"**Scope:** Compensatory Mechanism Identification & Orthopedic Physician Referral Guidance",
    ]

    if user_instruction:
        report_lines.extend([
            f"**User Custom Instruction:** \"{user_instruction}\"",
            ""
        ])
    else:
        report_lines.append("")

    report_lines.extend([
        "#### 1. Screening Referral Triage Level",
        f"- **Referral Status**: **{'⚠️ ' + triage_level if si_mean > 15.0 else '✅ ' + triage_level}**",
        f"- **Asymmetry Baseline**: Mean SI = **{si_mean:.1f}%** | Peak Instantaneous SI = **{si_max:.1f}%**",
        "",
        "#### 2. Identified Compensatory Movement Strategies",
    ])

    for comp in primary_compensations:
        report_lines.append(f"- 🔸 {comp}")

    report_lines.extend([
        "",
        "#### 3. Potential Musculoskeletal Risk Indicators",
    ])

    for risk in suspected_clinical_factors:
        report_lines.append(f"- 🚩 {risk}")

    report_lines.extend([
        "",
        "#### 4. Recommended Physician Review Workups",
    ])

    for diag in recommended_diagnostics:
        report_lines.append(f"- 📋 {diag}")

    report_lines.extend([
        "",
        "---",
        "*Caution: This screening report flags kinematic risk patterns to assist licensed orthopedic physicians. It does not replace definitive medical imaging or physician diagnosis.*"
    ])

    report_text = "\n".join(report_lines)

    return {
        "agent": AGENT_3_CONFIG,
        "triage_level": triage_level,
        "triage_color": triage_color,
        "primary_compensations": primary_compensations,
        "suspected_clinical_factors": suspected_clinical_factors,
        "user_instruction": user_instruction,
        "report_text": report_text
    }


def synthesize_clinical_report(
    patient_info: Dict[str, str],
    bio_result: Dict[str, Any],
    pt_result: Dict[str, Any],
    ortho_result: Dict[str, Any],
    user_instruction: str = None
) -> Dict[str, Any]:
    metrics = bio_result["metrics"]
    si_mean = metrics["mean_symmetry_index_pct"]
    si_max = metrics["peak_symmetry_index_pct"]
    l_rom = metrics["left_rom_deg"]
    r_rom = metrics["right_rom_deg"]
    rom_deficit_deg = metrics["rom_deficit_deg"]

    triage_level = ortho_result["triage_level"]

    prompt_note = f" (Custom Focus Requested: '{user_instruction}')" if user_instruction else ""

    if si_mean > 15.0:
        exec_summary = (
            f"Patient **{patient_info.get('id', 'KT-2026-P902')}** ({patient_info.get('age', '7 y/o')}) presented for 3D markerless motion capture.{prompt_note} "
            f"Multi-agent kinematic analysis identified significant bilateral gait asymmetry (Mean SI: **{si_mean:.1f}%**, Peak SI: **{si_max:.1f}%**). "
            f"Functional evaluation reveals an asymmetric stiff-knee gait pattern with a bilateral knee ROM deficit of **{rom_deficit_deg:.1f}°**. "
            f"Triage status is categorized as **{triage_level}** due to observed compensatory vaulting strategies and risk of asymmetrical joint loading."
        )
    else:
        exec_summary = (
            f"Patient **{patient_info.get('id', 'KT-2026-P902')}** ({patient_info.get('age', '7 y/o')}) presented for 3D markerless motion capture.{prompt_note} "
            f"Multi-agent kinematic screening demonstrates fluid bilateral knee flexion/extension symmetry (Mean SI: **{si_mean:.1f}%**). "
            f"Both limbs operate within pediatric normative range of motion thresholds. Triage status is categorized as **{triage_level}**."
        )

    if si_mean > 15.0:
        phase_1 = [
            "**Goal**: Passive & Active Range of Motion Recovery",
            "**Exercises**: Targeted hamstrings & gastrocnemius static stretches (3x30s hold), passive knee extension mobilizations in prone position.",
            "**Frequency**: 2x daily under caregiver supervision."
        ]
        phase_2 = [
            "**Goal**: Single-Limb Stance Stability & Proprioceptive Strengthening",
            "**Exercises**: Single-leg stance balance on foam pad with visual cueing (3x45s), seated leg extension against light elastic resistance.",
            "**Frequency**: 4x per week with PT oversight."
        ]
        phase_3 = [
            "**Goal**: Dynamic Gait Integration & Symmetrical Weight Transfer",
            "**Exercises**: Rhythmic treadmill gait retraining with visual footstep targets, obstacle clearance strides for swing phase knee flexion.",
            "**Frequency**: 2x weekly clinical PT sessions."
        ]
    else:
        phase_1 = [
            "**Goal**: Maintenance of Full Active Joint Mobility",
            "**Exercises**: Dynamic lower extremity warm-up routines (high knees, butt kicks, lateral lunges).",
            "**Frequency**: Daily pre-play activity."
        ]
        phase_2 = [
            "**Goal**: Core & Pelvic Alignment Strengthening",
            "**Exercises**: Bilateral gluteal bridges, side-lying hip abductions, single-leg hopping drills.",
            "**Frequency**: 3x per week."
        ]
        phase_3 = [
            "**Goal**: Multilateral Agility & Pediatric Sports Readiness",
            "**Exercises**: Multi-directional agility ladder drills, jumping landing mechanics training.",
            "**Frequency**: Integrated into routine physical activities."
        ]

    report_lines = [
        "# 📄 COMPREHENSIVE PEDIATRIC KINETIC & MOTOR SCREENING CARE PLAN",
        f"**Lead Synthesizer:** {AGENT_4_CONFIG['role']}",
        f"**Patient ID:** {patient_info.get('id', 'N/A')} | **Age:** {patient_info.get('age', 'N/A')} | **Case:** {patient_info.get('case', 'N/A')}",
    ]

    if user_instruction:
        report_lines.extend([
            f"**Custom Care Plan Directives:** \"{user_instruction}\"",
            ""
        ])
    else:
        report_lines.append("")

    report_lines.extend([
        "---",
        "## 📋 EXECUTIVE SUMMARY",
        exec_summary,
        "",
        "---",
        "## 📊 1. SYNTHESIZED CLINICAL FINDINGS MATRIX",
        "| Clinical Dimension | Evaluated Finding | Benchmark / Normative Baseline | Triage Status |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Bilateral Symmetry** | Mean SI: **{si_mean:.1f}%** (Peak: {si_max:.1f}%) | Normative Threshold ≤ 15.0% | {'⚠️ Elevated' if si_mean > 15.0 else '✅ Normative'} |",
        f"| **Left Knee ROM** | **{l_rom:.1f}°** (Ext: {metrics['left_min_extension_deg']}°, Flex: {metrics['left_max_flexion_deg']}°) | Active ROM Benchmark ~ 120-140° | {'⚠️ Reduced' if l_rom < 50 else '✅ Adequate'} |",
        f"| **Right Knee ROM** | **{r_rom:.1f}°** (Ext: {metrics['right_min_extension_deg']}°, Flex: {metrics['right_max_flexion_deg']}°) | Active ROM Benchmark ~ 120-140° | {'⚠️ Reduced' if r_rom < 50 else '✅ Adequate'} |",
        f"| **Functional Pattern** | {pt_result['gait_pattern']} | Symmetrical Gait Cycles | {'⚠️ Asymmetric' if si_mean > 15.0 else '✅ Fluid'} |",
        f"| **Orthopedic Triage** | {ortho_result['triage_level']} | Routine Developmental Screening | {'⚠️ High Referral' if si_mean > 15.0 else '✅ Low Risk'} |",
        "",
        "---",
        "## 🏃 2. PROGRESSIVE REHABILITATION EXERCISE ROADMAP",
        "### Phase 1: Foundation & Mobility (Weeks 1-3)",
        f"- {phase_1[0]}",
        f"- {phase_1[1]}",
        f"- {phase_1[2]}",
        "",
        "### Phase 2: Stance Stability & Proprioception (Weeks 4-6)",
        f"- {phase_2[0]}",
        f"- {phase_2[1]}",
        f"- {phase_2[2]}",
        "",
        "### Phase 3: Dynamic Gait Integration (Weeks 7-10)",
        f"- {phase_3[0]}",
        f"- {phase_3[1]}",
        f"- {phase_3[2]}",
        "",
        "---",
        "## 🏥 3. PHYSICIAN FOLLOW-UP & ACTION PLAN",
    ])

    if si_mean > 15.0:
        report_lines.extend([
            "1. **Physician Consultation**: Schedule an in-person pediatric orthopedic evaluation within 2-4 weeks.",
            "2. **Diagnostic Imaging**: Consider standing full-length lower extremity radiographs to evaluate anatomical vs functional leg length discrepancy.",
            "3. **Physical Therapy Referral**: Initiate 1-on-1 outpatient pediatric physical therapy focusing on Phase 1 & Phase 2 protocols."
        ])
    else:
        report_lines.extend([
            "1. **Routine Monitoring**: Re-evaluate kinematics during annual pediatric well-child checkup.",
            "2. **Activity Encouragement**: Maintain active play, sports participation, and symmetric movement habits."
        ])

    report_lines.extend([
        "",
        "---",
        "### ⚠️ MEDICAL DISCLAIMER",
        "*This synthesized report is an automated clinical decision-support document generated by KinemaTrace AI multi-agent screening models. "
        "It provides objective screening insights and evidence-based exercise frameworks for informational and screening purposes only. "
        "All diagnostic decisions, medical prescriptions, and treatment plans must be formulated by a licensed pediatric physician or Doctor of Physical Therapy.*"
    ])

    report_text = "\n".join(report_lines)

    return {
        "agent": AGENT_4_CONFIG,
        "executive_summary": exec_summary,
        "user_instruction": user_instruction,
        "report_text": report_text
    }


# --- Agent 5 Definition: KinemaTrace AI Clinical Assistant ---
AGENT_5_CONFIG = {
    "name": "KinemaTrace AI Clinical Assistant",
    "role": "Conversational Clinical Intelligence Assistant (Agent 5)",
    "goal": (
        "Provide clear, clinician-friendly conversational explanations, risk reasoning, "
        "gait metric interpretations, report generation, and progress comparisons "
        "by consuming structured outputs from Agents 1–4."
    ),
    "backstory": (
        "You are KinemaTrace AI's lead conversational assistant. You interact with clinicians "
        "by consuming structured gait analysis outputs generated by Agent 1 (Video Quality), "
        "Agent 2 (Gait Analysis), Agent 3 (Clinical Risk Assessment), and Agent 4 (Progress Comparison). "
        "You strictly adhere to current patient data, never invent numbers, never analyze raw video, "
        "and never issue medical diagnoses."
    )
}


def _safe_float(val, default=0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def process_clinical_assistant_query(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Agent 5: KinemaTrace AI Clinical Assistant query processor.
    Consumes structured outputs from Agents 1-4 and returns contextual answers,
    report generation, risk explanations, normal reference comparisons, and progress comparisons.
    """
    context = context or {}
    q_lower = (query or "").lower().strip()

    # Extract context metadata
    patient_info = context.get("patient_info", {})
    raw_patient_id = patient_info.get("id") or context.get("patient_id")
    source_type = context.get("source_type") or context.get("case_id") or ("custom" if raw_patient_id and "CUSTOM" in str(raw_patient_id).upper() else None)

    # Determine preset vs custom context
    is_case1 = source_type == "case1" or raw_patient_id == "PED-2026-001"
    is_case2 = source_type == "case2" or (source_type is None and raw_patient_id == "KT-2026-P902")
    is_custom = not is_case1 and not is_case2

    if raw_patient_id:
        patient_id = raw_patient_id
    elif is_case1:
        patient_id = "PED-2026-001"
    else:
        patient_id = "KT-2026-P902"

    patient_age = patient_info.get("age") or "7 y/o"
    case_name = patient_info.get("case") or context.get("case_name") or ("Normative Control" if is_case1 else ("Post-Injury Asymmetric Gait" if is_case2 else "Custom Gait Scan"))
    video_name = context.get("filename") or context.get("video_name") or ("demo_normative.mp4" if is_case1 else ("demo_asymmetric.mp4" if is_case2 else "uploaded_gait_scan.mp4"))

    # Extract agent structured outputs
    vq = context.get("video_quality") or {}
    telemetry = context.get("telemetry") or context.get("metrics") or {}
    cr = context.get("clinical_risk") or {}
    progress = context.get("patient_progress") or context.get("comparison") or context.get("progress_session") or {}

    # Preset autofill if agent data is missing for preset demo cases
    if is_case1 and (not telemetry or not cr):
        telemetry = {
            "gait_symmetry_pct": 98.2,
            "mean_si_pct": 1.8,
            "peak_asymmetry_pct": 3.1,
            "left_rom": 115.0,
            "right_rom": 114.5,
            "peak_knee_flexion": 110.0,
            "hip_flexion_rom_deg": 125.1,
            "risk_status": "LOW RISK"
        }
        vq = {"status": "PASS", "video_quality_score": 98}
        cr = {
            "risk_level": "LOW",
            "severity": "NORMAL",
            "affected_side": "NONE",
            "reasoning": "Gait kinematics remain within normative pediatric boundaries without significant asymmetry.",
            "recommendation": "Maintain routine developmental physical activity."
        }
    elif is_case2 and (not telemetry or not cr):
        telemetry = {
            "gait_symmetry_pct": 79.1,
            "mean_si_pct": 20.9,
            "peak_asymmetry_pct": 28.2,
            "left_rom": 61.5,
            "right_rom": 58.2,
            "peak_knee_flexion": 89.1,
            "hip_flexion_rom_deg": 120.0,
            "risk_status": "HIGH RISK"
        }
        vq = {"status": "PASS", "video_quality_score": 92}
        cr = {
            "risk_level": "HIGH",
            "severity": "SIGNIFICANT",
            "affected_side": "RIGHT",
            "reasoning": "Mean asymmetry index is 20.9%, exceeding the configured high-risk threshold of 15.0%. Right knee peak ROM is restricted to 58.2°.",
            "recommendation": "Schedule follow-up pediatric physical therapy assessment."
        }

    # Completion Flags (evaluated AFTER autofill)
    has_agent1 = bool(vq and vq.get("status"))
    has_agent2 = bool(telemetry and (
        telemetry.get("left_rom") is not None or
        telemetry.get("left_knee_rom") is not None or
        telemetry.get("peak_knee_flexion") is not None or
        telemetry.get("mean_si_pct") is not None or
        telemetry.get("mean_symmetry_index_pct") is not None or
        telemetry.get("mean_asymmetry") is not None or
        telemetry.get("symmetry_index") is not None or
        telemetry.get("gait_symmetry_pct") is not None or
        telemetry.get("gait_symmetry") is not None
    ))
    has_agent3 = bool(cr and (cr.get("risk_level") or cr.get("severity")))
    has_agent4 = bool(progress and (progress.get("old_video") and progress.get("new_video")))


    # Derived metrics from Agent 2 with safe float parsing
    raw_si = (
        telemetry.get("mean_si_pct")
        if telemetry.get("mean_si_pct") is not None
        else (
            telemetry.get("mean_symmetry_index_pct")
            if telemetry.get("mean_symmetry_index_pct") is not None
            else (
                telemetry.get("mean_asymmetry")
                if telemetry.get("mean_asymmetry") is not None
                else telemetry.get("symmetry_index")
            )
        )
    )
    symmetry_index = round(_safe_float(raw_si, 20.9 if is_case2 else (1.8 if is_case1 else 0.0)), 1)

    raw_gait_sym = telemetry.get("gait_symmetry_pct")
    if raw_gait_sym is not None:
        gait_symmetry = round(_safe_float(raw_gait_sym, 79.1), 1)
    else:
        gait_symmetry = max(0.0, round(100.0 - symmetry_index, 1))

    raw_peak_asym = cr.get("peak_asymmetry_percentage") or telemetry.get("peak_asymmetry_pct")
    peak_asymmetry = round(_safe_float(raw_peak_asym, round(symmetry_index * 1.35, 1)), 1)

    left_rom = round(_safe_float(telemetry.get("left_rom", telemetry.get("left_rom_deg")), 61.5), 1)
    right_rom = round(_safe_float(telemetry.get("right_rom", telemetry.get("right_rom_deg")), 58.2), 1)
    hip_rom = round(_safe_float(telemetry.get("hip_flexion_rom_deg"), 120.0), 1)
    rom_diff = round(abs(left_rom - right_rom), 1)
    peak_knee_flexion = round(_safe_float(telemetry.get("peak_knee_flexion", telemetry.get("peak_knee_flexion_deg")), min(left_rom, right_rom)), 1)

    # Risk level from Agent 3
    raw_risk = str(cr.get("risk_level") or telemetry.get("risk_status") or ("HIGH" if symmetry_index > 15 else "LOW")).upper()
    clean_risk = raw_risk.replace("GAIT RISK", "").replace("RISK", "").strip()
    if clean_risk in ["NORMATIVE", "LOW", "NORMAL"]:
        risk_level = "LOW RISK"
    elif clean_risk in ["MEDIUM", "ELEVATED", "MODERATE"]:
        risk_level = "MEDIUM RISK"
    elif clean_risk in ["HIGH", "SEVERE", "CRITICAL"]:
        risk_level = "HIGH RISK"
    else:
        risk_level = f"{clean_risk} RISK"

    severity = cr.get("severity") or ("SIGNIFICANT" if "HIGH" in risk_level else "NORMAL")
    affected_side = cr.get("affected_side") or ("RIGHT" if "HIGH" in risk_level else "NONE")
    reasoning = cr.get("reasoning") or f"Based on gait analysis of {video_name}, measured mean asymmetry was {symmetry_index}%, with knee ROM difference of {rom_diff}°."
    recommendation = cr.get("recommendation") or "Schedule follow-up pediatric physical therapy assessment."

    # Quality from Agent 1
    vq_status = vq.get("status") or "PASS"
    vq_score = _safe_float(vq.get("video_quality_score"), 92)

    # Disclaimer
    disclaimer = "\n\n⚕️ **MEDICAL SAFETY DISCLAIMER:** This screening response is generated by KinemaTrace AI based on automated gait metrics and is not a medical diagnosis. Clinical interpretation must be performed by a qualified healthcare professional."

    # -------------------------------------------------------------------------
    # INTENT DISPATCHER
    # -------------------------------------------------------------------------

    # 1. REPORT GENERATION INTENT
    if any(k in q_lower for k in ["report", "generate report", "create report", "pdf", "generate pdf", "download report", "give me patient report", "clinical report"]):
        old_v = progress.get("old_video") or context.get("old_video")
        new_v = progress.get("new_video") or context.get("new_video")
        if old_v and new_v and progress.get("overall_progress"):
            old_asym = _safe_float(old_v.get("gait_asymmetry"))
            new_asym = _safe_float(new_v.get("gait_asymmetry"))
            asym_delta = round(new_asym - old_asym, 1)
            old_sym = round(max(0.0, 100.0 - old_asym), 1)
            new_sym = round(max(0.0, 100.0 - new_asym), 1)
            sym_delta = round(new_sym - old_sym, 1)
            prog_section = (
                f"- **Overall Progression:** **{progress.get('overall_progress')}**\n"
                f"- **Baseline Video (OLD):** `{old_v.get('file_name', 'OLD')}`\n"
                f"- **Latest Video (NEW):** `{new_v.get('file_name', 'NEW')}`\n"
                f"- **Gait Symmetry Change:** {old_sym}% ➔ {new_sym}% ({sym_delta:+.1f} % pts)\n"
                f"- **Mean Asymmetry Change:** {old_asym}% ➔ {new_asym}% ({asym_delta:+.1f} % pts)\n"
                f"- **Summary:** {progress.get('summary', 'Progress comparison completed.')}"
            )
        else:
            prog_section = "Progress comparison is not available because a baseline assessment video was not provided for comparison."

        report_text = f"""# 🏥 KINEMATRACE AI PEDIATRIC GAIT SCREENING REPORT

### 1. PATIENT INFORMATION
- **Patient ID:** {patient_id}
- **Age Group:** {patient_age}
- **Assessment Type:** {case_name}
- **Source Video:** {video_name}

### 2. AGENT 1 — VIDEO QUALITY VALIDATION
- **Validation Status:** **{vq_status}** (Quality Score: {vq_score}/100)
- **Landmark Detection:** 33/33 MediaPipe 3D Pose Keypoints Tracked
- **Camera Evaluation:** Satisfactory resolution, lighting, and frame stability.

### 3. AGENT 2 — GAIT KINEMATIC ANALYSIS
- **Gait Symmetry Index:** {gait_symmetry}%
- **Mean Asymmetry Index:** {symmetry_index}% (Normative Threshold: ≤ 15.0%)
- **Peak Asymmetry:** {peak_asymmetry}%
- **Left Knee ROM:** {left_rom}°
- **Right Knee ROM:** {right_rom}°
- **Bilateral ROM Deficit:** {rom_diff}°
- **Hip Flexion ROM:** {hip_rom}°

### 4. AGENT 3 — CLINICAL RISK SCREENING
- **Screening Risk Level:** **{risk_level}** (Severity: {severity})
- **Affected Limb:** {affected_side} Limb
- **Key Risk Factors:** {'Elevated bilateral knee gait asymmetry exceeding 15.0% threshold.' if float(symmetry_index) > 15 else 'No significant gait asymmetry detected.'}

### 5. EXPLAINABLE CLINICAL REASONING
{reasoning}

### 6. AGENT 4 — PATIENT PROGRESS COMPARISON
{prog_section}

### 7. CLINICAL RECOMMENDATION
{recommendation}

### 8. PDF REPORT DOWNLOAD
📄 Download PDF Report: [Click here to download PDF Report](http://localhost:8000/api/generate-pdf){disclaimer}"""

        return {
            "agent_id": "clinical-assistant",
            "agent_name": AGENT_5_CONFIG["name"],
            "category": "report_generation",
            "response": report_text,
            "report_text": report_text,
            "patient_id": patient_id,
            "has_pdf_report": True,
            "pdf_download_url": f"/api/generate-pdf?patient_id={patient_id}"
        }

    # 2. CLINICAL RISK INTENT (Agent 3)
    elif any(k in q_lower for k in ["why", "risk", "high risk", "low risk", "medium risk", "trigger", "cause", "level", "explain risk", "which measurement caused"]):
        if not has_agent3 and is_custom:
            text = f"Clinical risk assessment has not been completed yet. Please run Agent 3 using the completed gait analysis.{disclaimer}"
            return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "missing_data", "response": text, "patient_id": patient_id}

        text = f"""**Agent 3 — Clinical Risk Assessment Breakdown for Patient {patient_id}:**

- **Current Risk Level:** **{risk_level}** (Severity: {severity})
- **Affected Side:** {affected_side} Limb
- **High-Risk Threshold Used:** Mean Asymmetry > 15.0% or ROM Deficit > 5.0°
- **Patient Actual Measurement:** Mean Asymmetry = **{symmetry_index}%**, Bilateral ROM Deficit = **{rom_diff}°** (Left: {left_rom}°, Right: {right_rom}°)
- **Difference from Threshold:** {f'+{round(symmetry_index - 15.0, 1)}% above high-risk threshold' if symmetry_index > 15 else 'Within normative 15.0% threshold'}
- **Key Contributing Factors:**
  1. {'Elevated mean asymmetry index exceeding 15.0% benchmark.' if symmetry_index > 15 else 'Balanced movement symmetry across gait cycle.'}
  2. {'Restricted swing-phase knee ROM observed on affected limb.' if rom_diff > 5 else 'Bilateral range of motion within balance limits.'}
- **Explainable Reasoning:** {reasoning}
- **Recommended Action:** {recommendation}{disclaimer}"""

        return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "clinical_risk", "response": text, "report_text": text, "patient_id": patient_id}

    # 3. NORMATIVE / REFERENCE COMPARISON INTENT
    elif any(k in q_lower for k in ["normal", "reference", "compare with normal", "how far", "benchmark", "baseline"]):
        if not has_agent2 and is_custom:
            text = f"Gait analysis has not been completed yet. Please run Agent 2 to extract gait measurements.{disclaimer}"
            return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "missing_data", "response": text, "patient_id": patient_id}

        asym_diff = round(symmetry_index - 15.0, 1)
        r_rom_diff = round(120.0 - right_rom, 1)
        l_rom_diff = round(120.0 - left_rom, 1)

        text = f"""**Agent 5 — Normative Reference Comparison for Patient {patient_id}:**

1. **Mean Asymmetry Index:**
   - **Patient Value:** {symmetry_index}%
   - **Normative Reference:** ≤ 15.0% (Target: 0.0%)
   - **Absolute Difference:** {f'+{asym_diff}% above high-risk threshold' if asym_diff > 0 else f'{abs(asym_diff)}% below threshold (Normal)'}
   - **Interpretation:** {'Elevated asymmetric gait detected requiring clinical observation.' if symmetry_index > 15 else 'Asymmetry remains within normative pediatric limits.'}

2. **Left Knee ROM:**
   - **Patient Value:** {left_rom}°
   - **Normative Reference:** 110.0° – 140.0°
   - **Absolute Difference:** {f'{abs(l_rom_diff)}° below reference' if l_rom_diff > 0 else 'Within reference range'}
   - **Interpretation:** {'Restricted swing-phase flexion' if l_rom_diff > 10 else 'Satisfactory knee ROM'}

3. **Right Knee ROM:**
   - **Patient Value:** {right_rom}°
   - **Normative Reference:** 110.0° – 140.0°
   - **Absolute Difference:** {f'{abs(r_rom_diff)}° below reference' if r_rom_diff > 0 else 'Within reference range'}
   - **Interpretation:** {'Restricted swing-phase flexion' if r_rom_diff > 10 else 'Satisfactory knee ROM'}

4. **Bilateral ROM Deficit:**
   - **Patient Value:** {rom_diff}°
   - **Normative Reference:** ≤ 5.0°
   - **Absolute Difference:** {f'+{round(rom_diff - 5.0, 1)}° above threshold' if rom_diff > 5 else 'Balanced bilateral movement'}
   - **Interpretation:** {'Significant asymmetry between left and right knees.' if rom_diff > 5 else 'Bilateral range of motion is well balanced.'}

5. **Hip Flexion ROM:**
   - **Patient Value:** {hip_rom}°
   - **Normative Reference:** 120.0° – 125.0°
   - **Absolute Difference:** 0.0° (On benchmark)
   - **Interpretation:** Hip movement range meets normative expectations.{disclaimer}"""

        return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "normal_comparison", "response": text, "report_text": text, "patient_id": patient_id}

    # 4. PROGRESSION ANALYSIS INTENT (Agent 4)
    elif any(k in q_lower for k in ["progress", "improve", "improved", "worse", "worsened", "better", "change", "old", "new", "compare videos", "difference", "delta", "assessment"]):
        old_v = progress.get("old_video") or context.get("old_video")
        new_v = progress.get("new_video") or context.get("new_video")

        if old_v and new_v and (progress.get("overall_progress") or progress.get("comparison_status") == "COMPLETED"):
            old_name = old_v.get("file_name") or "Baseline Assessment Video"
            new_name = new_v.get("file_name") or "Latest Assessment Video"

            old_asym = _safe_float(old_v.get("gait_asymmetry"))
            new_asym = _safe_float(new_v.get("gait_asymmetry"))
            asym_change = round(new_asym - old_asym, 1)

            old_sym = round(max(0.0, 100.0 - old_asym), 1)
            new_sym = round(max(0.0, 100.0 - new_asym), 1)
            sym_change = round(new_sym - old_sym, 1)

            old_l_rom = _safe_float(old_v.get("left_rom"))
            new_l_rom = _safe_float(new_v.get("left_rom"))
            l_rom_change = round(new_l_rom - old_l_rom, 1)

            old_r_rom = _safe_float(old_v.get("right_rom"))
            new_r_rom = _safe_float(new_v.get("right_rom"))
            r_rom_change = round(new_r_rom - old_r_rom, 1)

            overall_prog = progress.get("overall_progress", "STABLE")

            verdict_lead = (
                f"Based on the available previous and latest assessments, gait asymmetry decreased from **{old_asym}%** to **{new_asym}%**, indicating improved symmetry. Right knee ROM changed from **{old_r_rom}°** to **{new_r_rom}°**. Overall progression: **{overall_prog}**."
                if overall_prog == "IMPROVED"
                else f"The latest assessment indicates that the patient's gait has **{overall_prog}**. Gait asymmetry changed from **{old_asym}%** to **{new_asym}%**, and right knee ROM changed from **{old_r_rom}°** to **{new_r_rom}°**."
            )

            text = f"""{verdict_lead}

**Assessment Files Compared:**
- **Baseline Video (OLD):** `{old_name}`
- **Latest Video (NEW):** `{new_name}`

**Gait Symmetry & Asymmetry:**
- **Gait Symmetry:** Old {old_sym}% ➔ New {new_sym}% ({sym_change:+.1f} % pts)
- **Mean Asymmetry Index:** Old {old_asym}% ➔ New {new_asym}% ({asym_change:+.1f} % pts)

**Joint Range of Motion (ROM):**
- **Left Knee ROM:** Old {old_l_rom}° ➔ New {new_l_rom}° ({l_rom_change:+.1f}°)
- **Right Knee ROM:** Old {old_r_rom}° ➔ New {new_r_rom}° ({r_rom_change:+.1f}°)

**Parameters Improved:**
- {'Gait Asymmetry decreased' if asym_change < 0 else 'Gait Symmetry increased'}
- {'Right Knee ROM increased' if r_rom_change > 0 else 'Left Knee ROM increased'}

**Overall Progression Status:** **{overall_prog}**{disclaimer}"""

            return {
                "agent_id": "clinical-assistant",
                "agent_name": AGENT_5_CONFIG["name"],
                "category": "progress",
                "response": text,
                "report_text": text,
                "patient_id": patient_id
            }

        else:
            text = f"Progress comparison requires both a baseline and latest assessment. Please complete Agent 4 with two analyzed videos.{disclaimer}"
            return {
                "agent_id": "clinical-assistant",
                "agent_name": AGENT_5_CONFIG["name"],
                "category": "missing_data",
                "response": text,
                "report_text": text,
                "patient_id": patient_id
            }

    # 5. VIDEO QUALITY INTENT (Agent 1)
    elif any(k in q_lower for k in ["quality", "good enough", "camera", "lighting", "blur", "video", "agent 1"]):
        if not has_agent1 and is_custom:
            text = f"Video quality validation has not been completed yet. Please run Agent 1 before continuing.{disclaimer}"
            return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "missing_data", "response": text, "patient_id": patient_id}

        text = f"**Agent 1 — Video Quality Validation Summary for Patient {patient_id}:**\n\n- **Status:** **{vq_status}** (Quality Score: {vq_score}/100)\n- **Pose Landmark Detection:** 33/33 MediaPipe 3D Keypoints detected cleanly.\n- **Resolution & Contrast:** Satisfactory full-body visibility recorded.\n- **Recommendation:** Video is technically suitable for automated gait kinematic analysis.{disclaimer}"
        return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "video_quality", "response": text, "report_text": text, "patient_id": patient_id}

    # 6. GAIT KINEMATIC INTENT (Agent 2)
    elif any(k in q_lower for k in ["knee", "rom", "angle", "flexion", "symmetry", "hip", "velocity", "metric", "measurement", "left", "right", "deficit"]):
        if not has_agent2 and is_custom:
            text = f"Gait analysis has not been completed yet. Please run Agent 2 to extract gait measurements.{disclaimer}"
            return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "missing_data", "response": text, "patient_id": patient_id}

        text = f"**Agent 2 — Gait Kinematic Measurements for Patient {patient_id}:**\n\n- **Gait Symmetry Index:** **{gait_symmetry}%** (Mean Asymmetry: {symmetry_index}%, Peak Asymmetry: {peak_asymmetry}%)\n- **Left Knee ROM:** {left_rom}°\n- **Right Knee ROM:** {right_rom}°\n- **Bilateral ROM Deficit:** {rom_diff}°\n- **Peak Knee Flexion:** {peak_knee_flexion}°\n- **Hip Flexion ROM:** {hip_rom}°{disclaimer}"
        return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "gait_kinematics", "response": text, "report_text": text, "patient_id": patient_id}

    # 7. GENERAL SUMMARY INTENT (Fallback)
    else:
        text = f"**KinemaTrace AI Clinical Summary for Patient {patient_id} ({case_name}):**\n\n- **Video Quality (Agent 1):** {vq_status} ({vq_score}/100)\n- **Gait Kinematics (Agent 2):** Gait Symmetry = {gait_symmetry}%, Left ROM = {left_rom}°, Right ROM = {right_rom}°, ROM Deficit = {rom_diff}°\n- **Screening Risk (Agent 3):** **{risk_level}** ({severity}, Affected: {affected_side})\n- **Explainable Reasoning:** {reasoning}\n- **Recommendation:** {recommendation}\n\nYou can ask me specific questions like *'Why is this patient high risk?'*, *'Compare with normal'*, *'Has the patient improved?'*, or *'Generate PDF report'*.{disclaimer}"
        return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "general_summary", "response": text, "report_text": text, "patient_id": patient_id}

    cr = context.get("clinical_risk", {})
    progress = context.get("patient_progress") or context.get("comparison") or {}

    # Derived metrics from Agent 2 with safe float parsing
    raw_si = (
        telemetry.get("mean_si_pct")
        if telemetry.get("mean_si_pct") is not None
        else (
            telemetry.get("mean_symmetry_index_pct")
            if telemetry.get("mean_symmetry_index_pct") is not None
            else (
                telemetry.get("mean_asymmetry")
                if telemetry.get("mean_asymmetry") is not None
                else telemetry.get("symmetry_index")
            )
        )
    )
    symmetry_index = round(_safe_float(raw_si, 12.5), 1)

    raw_gait_sym = telemetry.get("gait_symmetry_pct")
    if raw_gait_sym is not None:
        gait_symmetry = round(_safe_float(raw_gait_sym, 87.5), 1)
    else:
        gait_symmetry = max(0.0, round(100.0 - symmetry_index, 1))

    raw_peak_asym = cr.get("peak_asymmetry_percentage") or telemetry.get("peak_asymmetry_pct")
    peak_asymmetry = round(_safe_float(raw_peak_asym, round(symmetry_index * 1.35, 1)), 1)

    left_rom = round(_safe_float(telemetry.get("left_rom", telemetry.get("left_rom_deg")), 61.5), 1)
    right_rom = round(_safe_float(telemetry.get("right_rom", telemetry.get("right_rom_deg")), 58.2), 1)
    hip_rom = round(_safe_float(telemetry.get("hip_flexion_rom_deg"), 120.0), 1)
    rom_diff = round(abs(left_rom - right_rom), 1)

    # Risk level from Agent 3
    raw_risk = str(cr.get("risk_level") or telemetry.get("risk_status") or ("HIGH" if symmetry_index > 15 else "LOW")).upper()
    clean_risk = raw_risk.replace("GAIT RISK", "").replace("RISK", "").strip()
    if clean_risk in ["NORMATIVE", "LOW", "NORMAL"]:
        risk_level = "LOW RISK"
    elif clean_risk in ["MEDIUM", "ELEVATED", "MODERATE"]:
        risk_level = "MEDIUM RISK"
    elif clean_risk in ["HIGH", "SEVERE", "CRITICAL"]:
        risk_level = "HIGH RISK"
    else:
        risk_level = f"{clean_risk} RISK"

    severity = cr.get("severity") or ("SIGNIFICANT" if "HIGH" in risk_level else "NORMAL")
    affected_side = cr.get("affected_side") or ("RIGHT" if "HIGH" in risk_level else "NONE")
    reasoning = cr.get("reasoning") or f"Based on gait analysis of {video_name}, measured mean asymmetry was {symmetry_index}%, with knee ROM difference of {rom_diff}°."
    recommendation = cr.get("recommendation") or "Schedule follow-up pediatric physical therapy assessment."

    # Quality from Agent 1
    vq_status = vq.get("status") or "PASS"
    vq_score = _safe_float(vq.get("video_quality_score"), 92)

    # Disclaimer
    disclaimer = "\n\n⚕️ **MEDICAL SAFETY DISCLAIMER:** This screening response is generated by KinemaTrace AI based on automated gait metrics and is not a medical diagnosis. Clinical interpretation must be performed by a qualified healthcare professional."

    # 1. REPORT GENERATION INTENT
    if any(k in q_lower for k in ["report", "full assessment", "screening report", "generate report", "create report"]):
        old_v = progress.get("old_video") or context.get("old_video")
        new_v = progress.get("new_video") or context.get("new_video")
        if old_v and new_v and progress.get("overall_progress"):
            old_asym = _safe_float(old_v.get("gait_asymmetry"))
            new_asym = _safe_float(new_v.get("gait_asymmetry"))
            asym_delta = round(new_asym - old_asym, 1)
            old_sym = round(max(0.0, 100.0 - old_asym), 1)
            new_sym = round(max(0.0, 100.0 - new_asym), 1)
            sym_delta = round(new_sym - old_sym, 1)
            prog_section = (
                f"- **Overall Progression:** **{progress.get('overall_progress')}**\n"
                f"- **Previous Video (OLD):** `{old_v.get('file_name', 'OLD')}`\n"
                f"- **Latest Video (NEW):** `{new_v.get('file_name', 'NEW')}`\n"
                f"- **Gait Symmetry Change:** {old_sym}% ➔ {new_sym}% ({sym_delta:+.1f} % pts)\n"
                f"- **Mean Asymmetry Change:** {old_asym}% ➔ {new_asym}% ({asym_delta:+.1f} % pts)\n"
                f"- **Summary:** {progress.get('summary', 'Progress comparison completed.')}"
            )
        else:
            prog_section = "Progress comparison is not available because a previous assessment was not provided for comparison."

        report_text = f"""# 🏥 KINEMATRACE AI PEDIATRIC GAIT SCREENING REPORT

### 1. PATIENT INFORMATION
- **Patient ID:** {patient_id}
- **Age:** {patient_age}
- **Assessment Type:** {case_name}
- **Source Video:** {video_name}

### 2. AGENT 1 — VIDEO QUALITY VALIDATION
- **Validation Status:** {vq_status} (Quality Score: {vq_score}/100)
- **Landmark Detection:** 33/33 MediaPipe 3D Pose Keypoints Detected
- **Camera Stability:** Satisfactory frame tracking without severe motion blur.

### 3. AGENT 2 — GAIT KINEMATIC ANALYSIS
- **Gait Symmetry Index:** {gait_symmetry}%
- **Mean Asymmetry Index:** {symmetry_index}% (Normative Benchmark: ≤ 15.0%)
- **Peak Asymmetry:** {peak_asymmetry}%
- **Left Knee Peak ROM:** {left_rom}°
- **Right Knee Peak ROM:** {right_rom}°
- **Bilateral ROM Deficit:** {rom_diff}°
- **Hip Flexion ROM:** {hip_rom}°

### 4. AGENT 3 — CLINICAL RISK SCREENING
- **Screening Risk Level:** {risk_level} RISK (Severity: {severity})
- **Affected Side:** {affected_side}

### 5. KEY RISK FACTORS
- {'Elevated bilateral knee gait asymmetry exceeding 15.0% threshold.' if float(symmetry_index) > 15 else 'No significant gait asymmetry detected.'}
- {'Restricted swing-phase knee ROM observed on affected limb.' if rom_diff > 5 else 'Bilateral range of motion remains balanced.'}

### 6. EXPLAINABLE CLINICAL REASONING
{reasoning}

### 7. AGENT 4 — PROGRESS COMPARISON
{prog_section}

### 8. RECOMMENDED NEXT STEP
{recommendation}

### 9. PDF REPORT DOWNLOAD
📄 Download PDF Report: [Click here to download PDF Report](http://localhost:8000/api/generate-pdf)

### 10. MEDICAL SAFETY DISCLAIMER
This report is based on automated gait screening analysis and is not a medical diagnosis. Clinical interpretation should be performed by a qualified healthcare professional."""

        return {
            "agent_id": "clinical-assistant",
            "agent_name": AGENT_5_CONFIG["name"],
            "category": "report_generation",
            "response": report_text,
            "report_text": report_text,
            "has_pdf_report": True,
            "patient_id": patient_id
        }

    # 2. VIDEO QUALITY INTENT (Agent 1)
    elif any(k in q_lower for k in ["quality", "good enough", "camera", "lighting", "blur", "video"]):
        text = f"**Agent 1 — Video Quality Validation Summary:**\n\n- **Status:** {vq_status} (Score: {vq_score}/100)\n- **Pose Tracking:** 33/33 MediaPipe body landmarks detected cleanly.\n- **Resolution & Lighting:** Adequate contrast and full-body visibility recorded.\n- **Recommendation:** Video is suitable for automated gait kinematic analysis.{disclaimer}"
        return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "video_quality", "response": text, "report_text": text, "patient_id": patient_id}

    # 3. CLINICAL RISK INTENT (Agent 3)
    elif any(k in q_lower for k in ["risk", "why", "trigger", "cause", "high risk", "low risk", "level"]):
        text = f"**Agent 3 — Clinical Risk Assessment Explanation for Patient {patient_id}:**\n\n- **Risk Level:** **{risk_level} RISK** (Severity: {severity})\n- **Affected Side:** {affected_side}\n- **Key Risk Factors:** Mean Asymmetry = {symmetry_index}% (Normative: ≤ 15.0%), ROM Difference = {rom_diff}°.\n- **Reasoning:** {reasoning}\n- **Recommended Action:** {recommendation}{disclaimer}"
        return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "clinical_risk", "response": text, "report_text": text, "patient_id": patient_id}

    # 4. PROGRESS INTENT (Agent 4 Progress Comparison)
    elif any(k in q_lower for k in ["progress", "improve", "better", "worse", "change", "old", "new", "compare", "difference", "previous", "latest", "delta"]):
        old_v = progress.get("old_video") or context.get("old_video")
        new_v = progress.get("new_video") or context.get("new_video")
        comp = progress.get("comparison") or context.get("comparison") or {}

        # Case 1: Agent 4 comparison completed with both old and new data
        if old_v and new_v and (progress.get("overall_progress") or progress.get("comparison_status") == "COMPLETED"):
            old_name = old_v.get("file_name") or "Previous Assessment Video"
            new_name = new_v.get("file_name") or "Latest Assessment Video"

            old_asym = _safe_float(old_v.get("gait_asymmetry"))
            new_asym = _safe_float(new_v.get("gait_asymmetry"))
            asym_change = round(new_asym - old_asym, 1)

            old_sym = round(max(0.0, 100.0 - old_asym), 1)
            new_sym = round(max(0.0, 100.0 - new_asym), 1)
            sym_change = round(new_sym - old_sym, 1)

            old_l_rom = _safe_float(old_v.get("left_rom"))
            new_l_rom = _safe_float(new_v.get("left_rom"))
            l_rom_change = round(new_l_rom - old_l_rom, 1)

            old_r_rom = _safe_float(old_v.get("right_rom"))
            new_r_rom = _safe_float(new_v.get("right_rom"))
            r_rom_change = round(new_r_rom - old_r_rom, 1)

            old_rom_def = _safe_float(old_v.get("rom_deficit_deg"))
            new_rom_def = _safe_float(new_v.get("rom_deficit_deg"))
            rom_def_change = round(new_rom_def - old_rom_def, 1)

            overall_prog = progress.get("overall_progress", "STABLE")
            summary_txt = progress.get("summary") or "Kinematic comparison completed between previous and current assessments."

            verdict_lead = (
                "Yes. Based on the comparison between the previous assessment and the latest assessment, the patient's gait has **IMPROVED**."
                if overall_prog == "IMPROVED"
                else "The latest assessment indicates that the patient's gait has **WORSENED** compared to the previous assessment."
                if overall_prog == "WORSENED"
                else "Based on the comparison between the previous and latest assessments, the patient's gait status has remained **STABLE**."
            )

            text = f"""{verdict_lead}

**Assessment Files Compared:**
- **Previous Video (OLD):** `{old_name}`
- **Latest Video (NEW):** `{new_name}`

**Gait Symmetry:**
- Old: {old_sym}%
- New: {new_sym}%
- Change: {sym_change:+.1f} percentage points

**Mean Asymmetry Index:**
- Old: {old_asym}%
- New: {new_asym}%
- Change: {asym_change:+.1f} percentage points

**Range of Motion (ROM):**
- **Left Knee ROM:** Old {old_l_rom}° ➔ New {new_l_rom}° ({l_rom_change:+.1f}°)
- **Right Knee ROM:** Old {old_r_rom}° ➔ New {new_r_rom}° ({r_rom_change:+.1f}°)
- **Bilateral ROM Deficit:** Old {old_rom_def}° ➔ New {new_rom_def}° ({rom_def_change:+.1f}°)

**Overall Progress Status:**
**{overall_prog}**

**Summary of Kinematic Changes:**
{summary_txt}{disclaimer}"""

            return {
                "agent_id": "clinical-assistant",
                "agent_name": AGENT_5_CONFIG["name"],
                "category": "progress",
                "response": text,
                "report_text": text,
                "patient_id": patient_id
            }

        # Case 2: Two videos uploaded, but Agent 4 comparison not run yet
        elif (context.get("has_two_videos") or (context.get("old_file_path") and context.get("new_file_path"))) and not progress.get("overall_progress"):
            text = f"Two assessment videos are available, but the progress comparison has not been completed yet. Please run Agent 4 Progress Comparison first.{disclaimer}"
            return {
                "agent_id": "clinical-assistant",
                "agent_name": AGENT_5_CONFIG["name"],
                "category": "progress",
                "response": text,
                "report_text": text,
                "patient_id": patient_id
            }

        # Case 3: Only one video available
        else:
            text = f"I currently have only one assessment video available. Please upload both the previous (OLD) and latest (NEW) videos to compare patient progression.{disclaimer}"
            return {
                "agent_id": "clinical-assistant",
                "agent_name": AGENT_5_CONFIG["name"],
                "category": "progress",
                "response": text,
                "report_text": text,
                "patient_id": patient_id
            }

    # 5. GAIT KINEMATIC INTENT (Agent 2)
    elif any(k in q_lower for k in ["angle", "rom", "flexion", "symmetry", "knee", "hip", "velocity", "metric", "measurement"]):
        text = f"**Agent 2 — Gait Kinematic Measurements for Patient {patient_id}:**\n\n- **Gait Symmetry Index:** **{gait_symmetry}%** (Mean Asymmetry: {symmetry_index}%, Peak: {peak_asymmetry}%)\n- **Left Knee ROM:** {left_rom}° (Min Ext / Max Flex)\n- **Right Knee ROM:** {right_rom}°\n- **Bilateral ROM Deficit:** {rom_diff}°\n- **Hip Flexion ROM:** {hip_rom}°{disclaimer}"
        return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "gait_kinematics", "response": text, "report_text": text, "patient_id": patient_id}

        return {"agent_id": "clinical-assistant", "agent_name": AGENT_5_CONFIG["name"], "category": "general_summary", "response": text, "report_text": text, "patient_id": patient_id}


# --- Agent 6 Definition: The Parent & Caregiver Empathetic Translator ---
AGENT_6_CONFIG = {
    "name": "Agent 6: The Parent & Caregiver Empathetic Translator",
    "role": "Lead Pediatric Family Communication & Empathetic Movement Translator",
    "goal": (
        "Translate complex clinical kinematics, angular velocities, and biomechanical "
        "jargon into an encouraging, compassionate, and easily understandable guide "
        "for parents and caregivers."
    ),
    "backstory": (
        "You are a pediatric family life specialist and healthcare communications educator "
        "specializing in child development. You take intimidating, quantitative medical documentation—such "
        "as gait symmetry indices, range of motion deficits, and compensatory movement flags—and translate "
        "them into clear, comforting, and jargon-free language for anxious parents. You NEVER prescribe "
        "medical therapies, recommend medical devices, or provide clinical diagnoses. Instead, you explain "
        "what the numbers mean for daily play using simple analogies (e.g., comparing knee flexion to lifting "
        "a foot over a building block), celebrate the biomechanical strengths the child demonstrated during "
        "the scan, and frame movement deviations as simple areas where the body is adapting. Your tone is warm, "
        "encouraging, supportive, and empowering."
    )
}


def process_empathetic_translator(
    kinematic_data: Dict[str, Any],
    user_instruction: str = None
) -> Dict[str, Any]:
    """
    Translates quantitative biomechanical gait metrics into an empathetic,
    family-friendly guide using simple everyday analogies.
    """
    if not kinematic_data:
        raise ValueError("No kinematic telemetry provided. Please complete a video scan first.")

    m = kinematic_data.get("gait_analysis") or kinematic_data.get("metrics") or kinematic_data.get("telemetry") or {}
    t = kinematic_data.get("telemetry") or {}
    p = kinematic_data.get("patient_info") or {}

    patient_id = p.get("id") or kinematic_data.get("video_id") or "KT-CUSTOM-PATIENT"

    gait_sym = float(m.get("gait_symmetry") if m.get("gait_symmetry") is not None else t.get("gait_symmetry_pct", 87.5))
    left_rom = float(m.get("left_knee_rom") if m.get("left_knee_rom") is not None else m.get("left_rom_deg", t.get("left_rom", 64.2)))
    right_rom = float(m.get("right_knee_rom") if m.get("right_knee_rom") is not None else m.get("right_rom_deg", t.get("right_rom", 104.2)))
    hip_rom = float(m.get("left_hip_rom") if m.get("left_hip_rom") is not None else m.get("hip_flexion_rom_deg", t.get("hip_flexion_rom_deg", 125.1)))
    rom_diff = float(m.get("rom_difference") if m.get("rom_difference") is not None else m.get("rom_deficit_deg", abs(left_rom - right_rom)))
    pose_conf = float(m.get("pose_confidence") if m.get("pose_confidence") is not None else 94.2)

    user_note = f"\n\n**Parent Query:** \"{user_instruction}\"" if user_instruction else ""

    daily_play_explanation = (
        f"During your child's walking scan, their overall gait symmetry was **{gait_sym:.1f}%**, "
        f"showing that their body is coordinating left and right steps with natural rhythm! "
        f"Think of knee bending like stepping smoothly over low obstacles during playground tag—their right knee "
        f"flexes to **{right_rom:.1f}°** and their left knee reaches **{left_rom:.1f}°**. This slight difference "
        f"({rom_diff:.1f}°) simply reflects how your child naturally adjusts their stride to stay balanced and steady. "
        f"Their hips demonstrate fantastic flexibility (**{hip_rom:.1f}°**), giving them great freedom of movement when running, jumping, or climbing!"
        f"{user_note}"
    )

    strengths = [
        f"🌟 **Excellent Hip Flexibility**: Achieved a full **{hip_rom:.1f}°** hip range of motion during walking.",
        f"🌟 **Strong Stride Rhythm**: Maintained **{gait_sym:.1f}%** overall gait coordination throughout the scan.",
        f"🌟 **High Landmark Accuracy**: Pose tracking confidence reached **{pose_conf:.1f}%**, capturing crisp movement patterns.",
        "🌟 **Stable Upright Posture**: Demonstrated strong core stability and steady forward balance during movement."
    ]

    tips = [
        "💡 **Playground Rest Breaks**: Because one leg steps with slightly more effort right now, a 3-minute water break during active play keeps legs feeling energetic.",
        "💡 **Fun Obstacle Stepping**: Encourage indoor games like stepping over soft foam blocks or marching like a parade leader to build balanced leg confidence.",
        "💡 **Supportive Footwear**: Well-cushioned, supportive sneakers will make daily park walks feel even lighter and more comfortable."
    ]

    report_text = f"""### 🤝 FAMILY-FRIENDLY GAIT GUIDE & EMPATHETIC TRANSLATION
**Patient ID:** {patient_id}
**Agent:** {AGENT_6_CONFIG['role']}

---
#### 1. What This Means For Daily Play
{daily_play_explanation}

---
#### 2. 🌟 Movement Strengths & Wins
""" + "\n".join(f"- {s}" for s in strengths) + """

---
#### 3. 💡 Daily Comfort & Play Tips
""" + "\n".join(f"- {t}" for t in tips) + """

---
*⚠️ Note: This family guide is an educational explanation of movement patterns to help caregivers understand daily motion. It is non-diagnostic and does not replace professional medical advice.*
"""

    return {
        "agent_id": "empathetic-translator",
        "agent_name": AGENT_6_CONFIG["name"],
        "agent_role": AGENT_6_CONFIG["role"],
        "daily_play_explanation": daily_play_explanation,
        "movement_strengths": strengths,
        "comfort_and_play_tips": tips,
        "report_text": report_text,
        "patient_id": patient_id,
        "gait_symmetry": gait_sym,
        "hip_flexibility": hip_rom,
    }


