"""
clinical_risk_agent.py

KinemaTrace AI — Clinical Risk Assessment Agent (Agent 2)

This module receives the structured output from the Gait Analysis Agent
(analyze_biomechanics in agents.py) and classifies the screening result
into LOW / MEDIUM / HIGH risk with explainable reasoning.

IMPORTANT:
  - This agent does NOT process video.
  - This agent does NOT make medical diagnoses.
  - All output is framed as a screening decision-support result.
  - Thresholds are configurable via RISK_THRESHOLDS at the top of this file.
"""

from typing import Dict, Any, List
from pediatric_normatives import get_pediatric_normative_profile

# ---------------------------------------------------------------------------
# Configurable clinical screening thresholds (modify here, not throughout)
# ---------------------------------------------------------------------------
RISK_THRESHOLDS: Dict[str, float] = {
    "low_risk_si_max_pct": 10.0,   # Mean SI below this → LOW RISK
    "high_risk_si_min_pct": 15.0,  # Mean SI at or above this → HIGH RISK (matches clinical_math.py)
    # Between low_risk_si_max_pct and high_risk_si_min_pct → MEDIUM RISK

    "mild_severity_si_max_pct": 10.0,
    "moderate_severity_si_max_pct": 15.0,
    # SI ≥ high_risk_si_min_pct → SIGNIFICANT severity

    "rom_deficit_high_deg": 15.0,  # ROM deficit beyond this is flagged
    "velocity_asymmetry_flag_pct": 25.0,  # Peak angular velocity ratio threshold
}

# ---------------------------------------------------------------------------
# Agent identity definition
# ---------------------------------------------------------------------------
AGENT_CLINICAL_RISK_CONFIG: Dict[str, str] = {
    "name": "Agent 2: The Clinical Risk Assessment Agent",
    "role": "Pediatric Gait Screening Risk Classifier",
    "goal": (
        "Classify gait analysis output into structured LOW / MEDIUM / HIGH "
        "screening risk levels with explainable, measurement-grounded reasoning. "
        "Provide transparent, non-diagnostic decision support for clinical referral."
    ),
    "backstory": (
        "You are a clinical informatics specialist with deep expertise in pediatric "
        "gait biomechanics and screening protocol design. You receive structured "
        "kinematic measurements from the Biomechanical Data Analyst and translate them "
        "into a calibrated risk classification using validated thresholds. You never "
        "speculate on diagnoses; your role is to flag screening risk levels, explain "
        "which measurements triggered the classification, and recommend appropriate "
        "next steps. You always remind clinicians that this is a screening tool, not "
        "a diagnostic instrument."
    ),
}


# ---------------------------------------------------------------------------
# Severity helper
# ---------------------------------------------------------------------------
def _determine_severity(si_mean: float) -> str:
    """Map mean SI to a severity category label."""
    if si_mean < RISK_THRESHOLDS["mild_severity_si_max_pct"]:
        return "NORMAL"
    elif si_mean < RISK_THRESHOLDS["moderate_severity_si_max_pct"]:
        return "MODERATE"
    else:
        return "SIGNIFICANT"


# ---------------------------------------------------------------------------
# Affected side helper
# ---------------------------------------------------------------------------
def _determine_affected_side(l_rom: float, r_rom: float, si_mean: float) -> str:
    """Identify which side shows reduced range of motion."""
    if si_mean < RISK_THRESHOLDS["mild_severity_si_max_pct"]:
        return "NONE"
    if abs(l_rom - r_rom) < 2.0:
        return "BILATERAL"
    return "LEFT" if l_rom < r_rom else "RIGHT"


# ---------------------------------------------------------------------------
# Triggered measurement extractor
# ---------------------------------------------------------------------------
def _build_triggered_measurements(
    metrics: Dict[str, Any],
    risk_level: str,
    affected_side: str,
    si_mean: float,
    si_max: float,
    rom_deficit_deg: float,
    rom_deficit_pct: float,
    l_rom: float,
    r_rom: float,
    l_peak_vel: float,
    r_peak_vel: float,
) -> List[str]:
    """
    Build a specific, measurement-grounded list of triggered risk factors.
    Only includes factors that are actually elevated for this patient.
    """
    factors: List[str] = []

    low_thresh = RISK_THRESHOLDS["low_risk_si_max_pct"]
    high_thresh = RISK_THRESHOLDS["high_risk_si_min_pct"]

    # Primary: Symmetry Index
    if si_mean >= high_thresh:
        factors.append(
            f"Mean Symmetry Index = {si_mean:.1f}% exceeds the HIGH RISK threshold "
            f"(≥ {high_thresh:.0f}%)"
        )
    elif si_mean >= low_thresh:
        factors.append(
            f"Mean Symmetry Index = {si_mean:.1f}% exceeds the LOW RISK threshold "
            f"(≥ {low_thresh:.0f}%), indicating moderate bilateral asymmetry"
        )

    # Peak SI
    if si_max >= high_thresh:
        frame = metrics.get("peak_asymmetry_frame", "—")
        factors.append(
            f"Peak instantaneous Symmetry Index = {si_max:.1f}% at frame #{frame} "
            f"(high-asymmetry event detected)"
        )

    # ROM deficit
    if rom_deficit_deg >= RISK_THRESHOLDS["rom_deficit_high_deg"]:
        factors.append(
            f"Bilateral knee ROM deficit = {rom_deficit_deg:.1f}° "
            f"({rom_deficit_pct:.1f}% relative reduction), exceeding the "
            f"{RISK_THRESHOLDS['rom_deficit_high_deg']:.0f}° screening flag"
        )
    elif rom_deficit_deg > 5.0:
        factors.append(
            f"Bilateral knee ROM deficit = {rom_deficit_deg:.1f}° "
            f"({rom_deficit_pct:.1f}% relative reduction) — mild asymmetry"
        )

    # Affected side specific
    if affected_side == "LEFT":
        factors.append(
            f"Left knee shows reduced flexion range ({l_rom:.1f}°) "
            f"compared with right knee ({r_rom:.1f}°)"
        )
    elif affected_side == "RIGHT":
        factors.append(
            f"Right knee shows reduced flexion range ({r_rom:.1f}°) "
            f"compared with left knee ({l_rom:.1f}°)"
        )

    # Angular velocity asymmetry
    if l_peak_vel > 0 and r_peak_vel > 0:
        vel_ratio = max(l_peak_vel, r_peak_vel) / min(l_peak_vel, r_peak_vel)
        if vel_ratio >= (1.0 + RISK_THRESHOLDS["velocity_asymmetry_flag_pct"] / 100.0):
            faster_side = "Left" if l_peak_vel > r_peak_vel else "Right"
            factors.append(
                f"Angular velocity asymmetry detected: {faster_side} knee peak velocity "
                f"({l_peak_vel:.1f} vs {r_peak_vel:.1f} deg/s, ratio {vel_ratio:.2f}x)"
            )

    return factors if factors else ["No significant risk factors detected in measured parameters"]


# ---------------------------------------------------------------------------
# Reasoning generator
# ---------------------------------------------------------------------------
def _build_reasoning(
    risk_level: str,
    severity: str,
    si_mean: float,
    si_max: float,
    affected_side: str,
    rom_deficit_deg: float,
    l_rom: float,
    r_rom: float,
    triggered_measurements: List[str],
    patient_age: str = None,
) -> str:
    """
    Generate human-readable explainable reasoning for the risk classification.
    Language is strictly non-diagnostic.
    """
    age_note = f" (patient age: {patient_age})" if patient_age else ""
    low_thresh = RISK_THRESHOLDS["low_risk_si_max_pct"]
    high_thresh = RISK_THRESHOLDS["high_risk_si_min_pct"]

    if risk_level == "HIGH":
        side_desc = ""
        if affected_side == "LEFT":
            side_desc = (
                f" The left knee demonstrated reduced flexion range ({l_rom:.1f}°) "
                f"compared with the right knee ({r_rom:.1f}°) during the analyzed gait sequence."
            )
        elif affected_side == "RIGHT":
            side_desc = (
                f" The right knee demonstrated reduced flexion range ({r_rom:.1f}°) "
                f"compared with the left knee ({l_rom:.1f}°) during the analyzed gait sequence."
            )
        elif affected_side == "BILATERAL":
            side_desc = (
                " Both lower limbs demonstrate asymmetrical loading patterns throughout the gait cycle."
            )

        reasoning = (
            f"The gait screening analysis{age_note} detected SIGNIFICANT bilateral lower-limb "
            f"asymmetry. The measured mean knee-angle Symmetry Index was {si_mean:.1f}%, which "
            f"exceeds the configured high-risk screening threshold of {high_thresh:.0f}%. "
            f"Peak instantaneous asymmetry reached {si_max:.1f}% during the recorded gait sequence."
            f"{side_desc}\n\n"
            f"This screening result indicates an abnormal gait pattern requiring clinical attention. "
            f"A bilateral ROM deficit of {rom_deficit_deg:.1f}° was also measured between the "
            f"left and right knee joints.\n\n"
            f"This result indicates an elevated screening risk level. "
            f"Further evaluation by a qualified pediatric healthcare professional is recommended. "
            f"This screening result does not constitute a medical diagnosis."
        )

    elif risk_level == "MEDIUM":
        reasoning = (
            f"The gait screening analysis{age_note} detected a MODERATE difference between "
            f"bilateral lower-limb movements. The measured mean knee-angle Symmetry Index was "
            f"{si_mean:.1f}%, which is above the expected normal screening range "
            f"(< {low_thresh:.0f}%) but does not meet the threshold for high-risk classification "
            f"(≥ {high_thresh:.0f}%).\n\n"
            f"A bilateral ROM deficit of {rom_deficit_deg:.1f}° was measured. "
            f"The gait pattern shows some asymmetry that warrants monitoring, though it does "
            f"not reach the level requiring immediate orthopedic referral.\n\n"
            f"Periodic clinical monitoring and a follow-up screening assessment are suggested. "
            f"This screening result does not constitute a medical diagnosis."
        )

    else:  # LOW
        reasoning = (
            f"The gait screening analysis{age_note} shows a relatively symmetrical movement "
            f"pattern between the left and right lower limbs. The measured mean knee-angle "
            f"Symmetry Index was {si_mean:.1f}%, which remains within the configured low-risk "
            f"screening range (< {low_thresh:.0f}%).\n\n"
            f"Both lower limbs executed consistent flexion-extension cycles without significant "
            f"bilateral ROM deficits. Peak instantaneous asymmetry reached {si_max:.1f}%, "
            f"which is within acceptable variability for normal pediatric gait.\n\n"
            f"No elevated screening risk factors were detected in the analyzed gait sequence. "
            f"Routine developmental monitoring is recommended. "
            f"This screening result does not constitute a medical diagnosis."
        )

    return reasoning


# ---------------------------------------------------------------------------
# Recommendation generator
# ---------------------------------------------------------------------------
def _build_recommendation(risk_level: str) -> str:
    if risk_level == "HIGH":
        return (
            "Consider prompt referral to a pediatric healthcare professional for a comprehensive "
            "clinical gait evaluation. A formal clinical goniometric assessment and physician "
            "review of these screening results is recommended. "
            "This screening result is not a medical diagnosis."
        )
    elif risk_level == "MEDIUM":
        return (
            "Periodic monitoring and a follow-up gait screening within 4–8 weeks is suggested. "
            "If movement asymmetry persists or worsens, consider referral to a pediatric "
            "healthcare professional. This screening result is not a medical diagnosis."
        )
    else:
        return (
            "Continue routine age-appropriate physical activity and standard pediatric "
            "developmental monitoring. Re-screen at the next scheduled well-child visit. "
            "This screening result is not a medical diagnosis."
        )


# ---------------------------------------------------------------------------
# Structured report text generator
# ---------------------------------------------------------------------------
def _build_report_text(
    risk_level: str,
    severity: str,
    asymmetry_pct: float,
    affected_side: str,
    si_mean: float,
    si_max: float,
    triggered_measurements: List[str],
    reasoning: str,
    recommendation: str,
    patient_age: str = None,
) -> str:
    risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk_level, "⚪")
    age_line = f"\n**Patient Age at Screening:** {patient_age}" if patient_age else ""

    lines = [
        "### 🛡️ CLINICAL RISK ASSESSMENT REPORT",
        f"**Agent:** {AGENT_CLINICAL_RISK_CONFIG['role']}",
        f"**Scope:** Gait Screening Risk Classification · Explainable Decision Support",
        age_line,
        "",
        "---",
        "#### 1. Risk Classification",
        f"- **Screening Risk Level:** {risk_emoji} **{risk_level} RISK**",
        f"- **Severity:** {severity}",
        f"- **Mean Symmetry Index:** {si_mean:.2f}% (Peak: {si_max:.2f}%)",
        f"- **Asymmetry Measurement:** {asymmetry_pct:.1f}%",
        f"- **Affected Side:** {affected_side}",
        "",
        "#### 2. Triggered Risk Measurements",
    ]

    for m in triggered_measurements:
        lines.append(f"- 🔸 {m}")

    lines.extend([
        "",
        "#### 3. Explainable Reasoning",
        reasoning,
        "",
        "#### 4. Recommended Next Step",
        recommendation,
        "",
        "---",
        "#### ⚕️ Configured Screening Thresholds",
        f"- LOW RISK: Mean SI < {RISK_THRESHOLDS['low_risk_si_max_pct']:.0f}%",
        f"- MEDIUM RISK: {RISK_THRESHOLDS['low_risk_si_max_pct']:.0f}% ≤ Mean SI < {RISK_THRESHOLDS['high_risk_si_min_pct']:.0f}%",
        f"- HIGH RISK: Mean SI ≥ {RISK_THRESHOLDS['high_risk_si_min_pct']:.0f}%",
        "",
        "---",
        "*⚠️ This Clinical Risk Assessment is an automated screening decision-support result. "
        "It does not constitute a medical diagnosis. All clinical decisions must be made by "
        "a licensed pediatric healthcare professional.*",
    ])

    return "\n".join(line for line in lines)


# ---------------------------------------------------------------------------
# Main public interface
# ---------------------------------------------------------------------------
def assess_clinical_risk(
    gait_analysis_result: Dict[str, Any],
    patient_age: str = None,
) -> Dict[str, Any]:
    """
    Assess clinical gait screening risk from structured Gait Analysis Agent output.

    Args:
        gait_analysis_result: Dict returned by analyze_biomechanics() in agents.py.
            Must contain 'metrics' key with at minimum:
            - mean_symmetry_index_pct
            - peak_symmetry_index_pct
            - rom_deficit_deg
            - rom_deficit_pct
            - left_rom_deg
            - right_rom_deg
            - left_peak_angular_velocity_dps
            - right_peak_angular_velocity_dps

        patient_age: Optional patient age string (e.g. "7 y/o") for context in reasoning.

    Returns:
        Structured risk assessment dict with:
        - risk_level: "LOW" | "MEDIUM" | "HIGH"
        - severity: "NORMAL" | "MODERATE" | "SIGNIFICANT"
        - asymmetry_percentage: float
        - affected_side: "LEFT" | "RIGHT" | "BILATERAL" | "NONE"
        - triggered_measurements: list[str]
        - reasoning: str (explainable, non-diagnostic)
        - recommendation: str
    Assesses gait screening risk using Age-Aware Pediatric Reference Profiles
    and a Weighted Multi-Factor Risk Scoring System (0-8 points).
    """
    if not gait_analysis_result:
        raise ValueError("gait_analysis_result cannot be None or empty.")

    metrics = gait_analysis_result.get("metrics", {})
    if not metrics:
        metrics = gait_analysis_result.get("gait_analysis", {}).get("metrics", {})

    si_mean: float = float(metrics.get("mean_symmetry_index_pct", 0.0))
    si_max: float = float(metrics.get("peak_symmetry_index_pct", 0.0))
    rom_deficit_deg: float = float(metrics.get("rom_deficit_deg", 0.0))
    rom_deficit_pct: float = float(metrics.get("rom_deficit_pct", 0.0))
    l_rom: float = float(metrics.get("left_rom_deg", 0.0))
    r_rom: float = float(metrics.get("right_rom_deg", 0.0))
    l_peak_vel: float = float(metrics.get("left_peak_angular_velocity_dps", 0.0))
    r_peak_vel: float = float(metrics.get("right_peak_angular_velocity_dps", 0.0))

    # Developer Debugging / Mismatch Validation Check
    video_id = gait_analysis_result.get("video_id") or gait_analysis_result.get("filename") or "unknown_video"
    print(f"[DEVELOPER VALIDATION CHECK] Risk Assessment Input for {video_id}: Mean SI={si_mean:.2f}%, ROM Deficit={rom_deficit_deg:.2f}°, L_ROM={l_rom:.1f}°, R_ROM={r_rom:.1f}°")

    low_thresh = RISK_THRESHOLDS["low_risk_si_max_pct"]
    high_thresh = RISK_THRESHOLDS["high_risk_si_min_pct"]

    confidence_score: float = float(metrics.get("confidence_score", 90.0))
    confidence_level: str = str(metrics.get("analysis_confidence", "HIGH"))

    # Confidence-Aware Screening Gate (Requirement 5 & Section 9)
    if confidence_score < 50.0:
        return {
            "agent": AGENT_CLINICAL_RISK_CONFIG,
            "risk_level": "INSUFFICIENT DATA",
            "severity": "INCONCLUSIVE",
            "asymmetry_percentage": round(si_mean, 2),
            "peak_asymmetry_percentage": round(si_max, 2),
            "affected_side": "UNKNOWN",
            "confidence_score": confidence_score,
            "analysis_confidence": "LOW",
            "risk_score": 0,
            "max_risk_score": 8,
            "risk_score_text": "0 / 8",
            "triggered_measurements": [
                f"Pose tracking confidence is too low ({confidence_score:.1f}%) for reliable risk classification.",
                "High landmark occlusion or insufficient body visibility detected."
            ],
            "reasoning": (
                f"Analysis confidence is low ({confidence_score:.1f}%). Pose landmarks could not be reliably tracked "
                "across full gait cycles. Please provide a clearer video with full-body visibility and adequate lighting."
            ),
            "recommendation": "Re-upload a clearer walking video with stable lighting and un-occluded view.",
            "report_text": "Risk assessment suspended due to insufficient pose detection confidence.",
            "is_diagnostic": False,
            "thresholds_used": {
                "low_risk_max_si_pct": low_thresh,
                "high_risk_min_si_pct": high_thresh,
                "rom_deficit_flag_deg": RISK_THRESHOLDS["rom_deficit_high_deg"],
            },
        }

    # Load Age-Aware Pediatric Screening Reference Profile (Section 2 & 14)
    profile = get_pediatric_normative_profile(patient_age)
    mod_asymmetry = profile["mean_asymmetry_max_pct"]
    high_asymmetry = profile["mean_asymmetry_max_pct"] * 1.5
    high_peak_asymmetry = profile["peak_asymmetry_max_pct"]
    mod_rom_diff = profile["rom_difference_max_deg"]
    high_rom_diff = profile["rom_difference_max_deg"] * 1.5
    knee_rom_min = profile["knee_rom_deg"]["min"]

    # Unique Triggered Criteria Count & Weighted Risk Score (Section 5)
    triggered_criteria_count = 0
    risk_score = 0

    # Criterion 1: Mean Symmetry Index / Asymmetry (Gait Symmetry = 100 - Mean SI is NOT counted twice!)
    if si_mean >= high_asymmetry:
        triggered_criteria_count += 1
        risk_score += 2
    elif si_mean >= mod_asymmetry:
        triggered_criteria_count += 1
        risk_score += 1

    # Criterion 2: Peak Symmetry Index Spike
    if si_max >= high_peak_asymmetry:
        triggered_criteria_count += 1
        risk_score += 1

    # Criterion 3: Bilateral ROM Difference
    if rom_deficit_deg >= high_rom_diff:
        triggered_criteria_count += 1
        risk_score += 2
    elif rom_deficit_deg >= mod_rom_diff:
        triggered_criteria_count += 1
        risk_score += 1

    # Criterion 4: Left Knee ROM Deficit
    if l_rom < knee_rom_min:
        triggered_criteria_count += 1
        risk_score += 1

    # Criterion 5: Right Knee ROM Deficit
    if r_rom < knee_rom_min:
        triggered_criteria_count += 1
        risk_score += 1

    # Criterion 6: Left Hip ROM Deficit
    left_hip_rom = float(metrics.get("left_hip_rom_deg", 45.0))
    if left_hip_rom < profile["hip_rom_deg"]["min"]:
        triggered_criteria_count += 1
        risk_score += 1

    # Criterion 7: Right Hip ROM Deficit
    right_hip_rom = float(metrics.get("right_hip_rom_deg", 45.0))
    if right_hip_rom < profile["hip_rom_deg"]["min"]:
        triggered_criteria_count += 1
        risk_score += 1

    # Criterion 8: Angular Velocity Asymmetry
    if l_peak_vel > 0 and r_peak_vel > 0:
        vel_ratio = max(l_peak_vel, r_peak_vel) / min(l_peak_vel, r_peak_vel)
        if vel_ratio >= 1.25:
            triggered_criteria_count += 1
            risk_score += 1

    # Classification Mapping
    if risk_score <= 1:
        if si_mean >= mod_asymmetry or rom_deficit_deg >= mod_rom_diff:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"
    elif risk_score <= 3:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"

    # Section 8 & 12 Requirement: Automated Consistency Validation
    all_primary_metrics_normal = (si_mean < mod_asymmetry) and (rom_deficit_deg < mod_rom_diff)
    if all_primary_metrics_normal and risk_level == "HIGH":
        risk_level = "LOW"

    # --- Severity ---
    severity = _determine_severity(si_mean)

    # --- Affected Side ---
    affected_side = _determine_affected_side(l_rom, r_rom, si_mean)

    # --- Triggered Measurements ---
    triggered_measurements = _build_triggered_measurements(
        metrics=metrics,
        risk_level=risk_level,
        affected_side=affected_side,
        si_mean=si_mean,
        si_max=si_max,
        rom_deficit_deg=rom_deficit_deg,
        rom_deficit_pct=rom_deficit_pct,
        l_rom=l_rom,
        r_rom=r_rom,
        l_peak_vel=l_peak_vel,
        r_peak_vel=r_peak_vel,
    )

    # --- Reasoning ---
    reasoning = _build_reasoning(
        risk_level=risk_level,
        severity=severity,
        si_mean=si_mean,
        si_max=si_max,
        affected_side=affected_side,
        rom_deficit_deg=rom_deficit_deg,
        l_rom=l_rom,
        r_rom=r_rom,
        triggered_measurements=triggered_measurements,
        patient_age=patient_age,
    )

    # --- Recommendation ---
    recommendation = _build_recommendation(risk_level)

    # --- Structured report text ---
    report_text = _build_report_text(
        risk_level=risk_level,
        severity=severity,
        asymmetry_pct=si_mean,
        affected_side=affected_side,
        si_mean=si_mean,
        si_max=si_max,
        triggered_measurements=triggered_measurements,
        reasoning=reasoning,
        recommendation=recommendation,
        patient_age=patient_age,
    )

    return {
        "agent": AGENT_CLINICAL_RISK_CONFIG,
        "risk_level": risk_level,
        "severity": severity,
        "asymmetry_percentage": round(si_mean, 2),
        "peak_asymmetry_percentage": round(si_max, 2),
        "affected_side": affected_side,
        "confidence_score": confidence_score,
        "analysis_confidence": confidence_level,
        "triggered_criteria_count": triggered_criteria_count,
        "max_criteria_count": 8,
        "triggered_criteria_text": f"{triggered_criteria_count} / 8",
        "risk_score": risk_score,
        "max_risk_score": 10,
        "risk_score_text": f"{triggered_criteria_count} / 8",
        "weighted_risk_score_text": f"{risk_score} / 10",
        "pediatric_normative_profile": profile,
        "triggered_measurements": triggered_measurements,
        "reasoning": reasoning,
        "recommendation": recommendation,
        "report_text": report_text,
        "is_diagnostic": False,
        "thresholds_used": {
            "low_risk_max_si_pct": low_thresh,
            "high_risk_min_si_pct": high_thresh,
            "rom_deficit_flag_deg": RISK_THRESHOLDS["rom_deficit_high_deg"],
        },
    }
