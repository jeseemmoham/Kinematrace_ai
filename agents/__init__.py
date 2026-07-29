"""
agents.py

KinemaTrace AI Agent Definitions and Clinical Analytics Module.
Defines:
- Agent 1: The Biomechanical Data Analyst
- Agent 2: The Pediatric Physical Therapist
- Agent 3: The Orthopedic Risk Consultant
- Agent 4: The Clinical Report Synthesizer
"""

from typing import Dict, Any, Union
import pandas as pd
import numpy as np
from clinical_math import compute_symmetry_index

# Import the new Video Quality Validation Agent components
from .video_quality_agent import (
    AGENT_VIDEO_QUALITY_CONFIG,
    QUALITY_CONFIG,
    validate_video_quality,
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
    "knee_extension_target_deg": 175.0,  # ~170 - 180 degrees full extension in stance
    "knee_flexion_peak_deg": 140.0,      # Full active ROM flexion peak
    "gait_swing_flexion_deg": 65.0,      # Typical peak flexion during gait swing phase
    "symmetry_index_max_pct": 15.0       # Clinical normative threshold
}


def analyze_biomechanics(
    angles_df: pd.DataFrame,
    risk_result: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Performs strictly quantitative biomechanical kinematic analysis on joint angle time-series
    conforming strictly to Agent 1's role and backstory.

    Args:
        angles_df (pd.DataFrame): DataFrame with 'left_knee_angle' and 'right_knee_angle'.
        risk_result (dict, optional): Result dictionary from evaluate_gait_risk.

    Returns:
        dict: Containing 'metrics', 'normative_comparisons', and 'report_text'.
    """
    left_angles = angles_df["left_knee_angle"].dropna()
    right_angles = angles_df["right_knee_angle"].dropna()

    # Peak metrics
    l_min, l_max = float(left_angles.min()), float(left_angles.max())
    r_min, r_max = float(right_angles.min()), float(right_angles.max())

    l_rom = l_max - l_min
    r_rom = r_max - r_min

    # Absolute ROM difference & percentage deficit
    rom_diff_deg = abs(l_rom - r_rom)
    max_rom = max(l_rom, r_rom)
    rom_deficit_pct = (rom_diff_deg / max_rom * 100.0) if max_rom > 0 else 0.0

    # Symmetry Index calculations
    si_series = compute_symmetry_index(left_angles, right_angles)
    si_mean = float(np.nanmean(si_series))
    si_max = float(np.nanmax(si_series))
    si_min = float(np.nanmin(si_series))

    # Angular Velocity estimation (degrees/sec assuming 30 FPS)
    l_vel = np.gradient(left_angles.values) * 30.0
    r_vel = np.gradient(right_angles.values) * 30.0
    l_peak_vel = float(np.max(np.abs(l_vel)))
    r_peak_vel = float(np.max(np.abs(r_vel)))

    # Frame of maximum asymmetry
    peak_si_frame = int(si_series.idxmax()) if not si_series.empty else 0

    metrics = {
        "left_min_extension_deg": round(l_min, 2),
        "left_max_flexion_deg": round(l_max, 2),
        "left_rom_deg": round(l_rom, 2),
        "right_min_extension_deg": round(r_min, 2),
        "right_max_flexion_deg": round(r_max, 2),
        "right_rom_deg": round(r_rom, 2),
        "rom_deficit_deg": round(rom_diff_deg, 2),
        "rom_deficit_pct": round(rom_deficit_pct, 2),
        "mean_symmetry_index_pct": round(si_mean, 2),
        "peak_symmetry_index_pct": round(si_max, 2),
        "min_symmetry_index_pct": round(si_min, 2),
        "peak_asymmetry_frame": peak_si_frame,
        "left_peak_angular_velocity_dps": round(l_peak_vel, 2),
        "right_peak_angular_velocity_dps": round(r_peak_vel, 2),
    }

    # Evaluate against Pediatric Normative Thresholds
    si_exceeded = si_mean > PEDIATRIC_NORMATIVES["symmetry_index_max_pct"]
    l_ext_deficit = max(0.0, PEDIATRIC_NORMATIVES["knee_extension_target_deg"] - l_max)
    r_ext_deficit = max(0.0, PEDIATRIC_NORMATIVES["knee_extension_target_deg"] - r_max)

    normative_comparisons = {
        "normative_si_threshold": PEDIATRIC_NORMATIVES["symmetry_index_max_pct"],
        "si_status": "ELEVATED_ASYMMETRY" if si_exceeded else "NORMATIVE_RANGE",
        "left_extension_deficit_deg": round(l_ext_deficit, 2),
        "right_extension_deficit_deg": round(r_ext_deficit, 2),
    }

    # Construct Quantitative Analysis Report Text
    report_lines = [
        "### 🔬 BIOMECHANICAL KINEMATIC ANALYSIS REPORT",
        f"**Analyst:** {AGENT_1_CONFIG['role']}",
        f"**Scope:** Strictly Quantitative Motion Metrics & Pediatric Normative Comparison",
        "",
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
    ]

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
        "report_text": report_text
    }


def analyze_physical_therapy(biomechanical_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs functional movement and pediatric physical therapy analysis based on Agent 1's
    quantitative biomechanical findings, conforming strictly to Agent 2's role and backstory.

    Args:
        biomechanical_analysis (dict): The output dictionary from analyze_biomechanics().

    Returns:
        dict: Functional gait pattern, energy expenditure, stability assessment, and report text.
    """
    metrics = biomechanical_analysis["metrics"]
    si_mean = metrics["mean_symmetry_index_pct"]
    l_rom = metrics["left_rom_deg"]
    r_rom = metrics["right_rom_deg"]

    # Identify Functional Gait Pattern
    if si_mean > 15.0:
        if l_rom < r_rom:
            restricted_side = "Left"
            unaffected_side = "Right"
        else:
            restricted_side = "Right"
            unaffected_side = "Left"

        gait_pattern = f"Asymmetric Stiff-Knee Gait Pattern with {restricted_side} Limb ROM Reduction"
        fatigability_impact = "Elevated metabolic cost due to compensatory muscle activation and limb vaulting"
        balance_risk = "Moderate-to-High balance perturbation during single-leg stance phase on restricted side"
        developmental_impact = "Risk of asymmetrical muscle development, joint stiffness, and reduced endurance during play activities"
    else:
        gait_pattern = "Symmetrical Pediatric Gait Pattern with Normative Swing & Stance Kinematics"
        fatigability_impact = "Normative energy expenditure with efficient kinetic transfer across gait cycles"
        balance_risk = "Low balance perturbation; normative dynamic stance stability"
        developmental_impact = "Age-appropriate motor milestone execution and full functional mobility"

    # Construct Agent 2 Clinical Report
    report_lines = [
        "### 🏃 PEDIATRIC PHYSICAL THERAPY & FUNCTIONAL MOVEMENT REPORT",
        f"**Specialist:** {AGENT_2_CONFIG['role']}",
        f"**Scope:** Translation of Biomechanical Metrics into Functional Mobility & Gait Impact",
        "",
        "#### 1. Functional Gait Pattern Visual Interpretation",
        f"- **Primary Visual Pattern**: **{gait_pattern}**",
        f"- **Kinematic Translation**: Mean SI of {si_mean:.1f}% indicates {'notable physical asymmetry during gait transition' if si_mean > 15.0 else 'fluid bilateral stride symmetry'}.",
    ]

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
        "report_text": report_text
    }


def analyze_orthopedic_risk(
    biomechanical_analysis: Dict[str, Any],
    physical_therapy_analysis: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Performs pediatric orthopedic risk screening and compensatory strategy analysis based on
    findings from Agent 1 and Agent 2, conforming strictly to Agent 3's role and backstory.

    Args:
        biomechanical_analysis (dict): The output from analyze_biomechanics().
        physical_therapy_analysis (dict, optional): The output from analyze_physical_therapy().

    Returns:
        dict: Risk triage level, compensatory strategies, clinical red flags, and report text.
    """
    metrics = biomechanical_analysis["metrics"]
    si_mean = metrics["mean_symmetry_index_pct"]
    si_max = metrics["peak_symmetry_index_pct"]
    rom_deficit_deg = metrics["rom_deficit_deg"]

    # Evaluate Compensatory Mechanisms & Triage Level
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

    # Construct Agent 3 Diagnostic Screening Report
    report_lines = [
        "### 🏥 PEDIATRIC ORTHOPEDIC DIAGNOSTIC SCREENING REPORT",
        f"**Consultant:** {AGENT_3_CONFIG['role']}",
        f"**Scope:** Compensatory Mechanism Identification & Orthopedic Physician Referral Guidance",
        "",
        "#### 1. Screening Referral Triage Level",
        f"- **Referral Status**: **{'⚠️ ' + triage_level if si_mean > 15.0 else '✅ ' + triage_level}**",
        f"- **Asymmetry Baseline**: Mean SI = **{si_mean:.1f}%** | Peak Instantaneous SI = **{si_max:.1f}%**",
        "",
        "#### 2. Identified Compensatory Movement Strategies",
    ]

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
        "report_text": report_text
    }


def synthesize_clinical_report(
    patient_info: Dict[str, str],
    bio_result: Dict[str, Any],
    pt_result: Dict[str, Any],
    ortho_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Synthesizes complex multi-agent biomechanical, functional, and risk findings into an
    authoritative, structured clinical report with progressive, evidence-based physical therapy
    recommendations, conforming strictly to Agent 4's role and backstory.

    Args:
        patient_info (dict): Patient metadata (ID, Age, Case Note).
        bio_result (dict): Agent 1 quantitative output.
        pt_result (dict): Agent 2 functional movement output.
        ortho_result (dict): Agent 3 orthopedic risk output.

    Returns:
        dict: Complete synthesized care plan and markdown report text.
    """
    metrics = bio_result["metrics"]
    si_mean = metrics["mean_symmetry_index_pct"]
    si_max = metrics["peak_symmetry_index_pct"]
    l_rom = metrics["left_rom_deg"]
    r_rom = metrics["right_rom_deg"]
    rom_deficit_deg = metrics["rom_deficit_deg"]

    triage_level = ortho_result["triage_level"]

    # Executive Summary Generation
    if si_mean > 15.0:
        exec_summary = (
            f"Patient **{patient_info.get('id', 'PED-UNKNOWN')}** ({patient_info.get('age', 'N/A')}) presented for 3D markerless motion capture. "
            f"Multi-agent kinematic analysis identified significant bilateral gait asymmetry (Mean SI: **{si_mean:.1f}%**, Peak SI: **{si_max:.1f}%**). "
            f"Functional evaluation reveals an asymmetric stiff-knee gait pattern with a bilateral knee ROM deficit of **{rom_deficit_deg:.1f}°**. "
            f"Triage status is categorized as **{triage_level}** due to observed compensatory vaulting strategies and risk of asymmetrical joint loading."
        )
    else:
        exec_summary = (
            f"Patient **{patient_info.get('id', 'PED-UNKNOWN')}** ({patient_info.get('age', 'N/A')}) presented for 3D markerless motion capture. "
            f"Multi-agent kinematic screening demonstrates fluid bilateral knee flexion/extension symmetry (Mean SI: **{si_mean:.1f}%**). "
            f"Both limbs operate within pediatric normative range of motion thresholds. Triage status is categorized as **{triage_level}**."
        )

    # Progressive 3-Phase Rehabilitation Plan
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

    # Synthesize Master Clinical Report Text
    report_lines = [
        "# 📄 COMPREHENSIVE PEDIATRIC KINETIC & MOTOR SCREENING CARE PLAN",
        f"**Lead Synthesizer:** {AGENT_4_CONFIG['role']}",
        f"**Patient ID:** {patient_info.get('id', 'N/A')} | **Age:** {patient_info.get('age', 'N/A')} | **Case:** {patient_info.get('case', 'N/A')}",
        "",
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
    ]

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
        "report_text": report_text
    }


if __name__ == "__main__":
    print("agents package loaded successfully.")
    print("Agent 1 Loaded:", AGENT_1_CONFIG["name"])
    print("Agent 2 Loaded:", AGENT_2_CONFIG["name"])
    print("Agent 3 Loaded:", AGENT_3_CONFIG["name"])
    print("Agent 4 Loaded:", AGENT_4_CONFIG["name"])
