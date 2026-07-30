"""
gait_progress_comparison_agent.py

KinemaTrace AI — Agent 4: Patient Gait Progress Comparison Agent

Compares two independent gait analysis results (from Agent 2/Biomechanical Analyst)
and two optional clinical risk assessments (from Clinical Risk Agent) to determine
whether a child's gait has IMPROVED, remained STABLE, or WORSENED over time.

Architecture:
  Old Video → Agent 1 (Quality) → Agent 2 (Gait) → Clinical Risk ──┐
  New Video → Agent 1 (Quality) → Agent 2 (Gait) → Clinical Risk ──┤
                                                                      ▼
                                                          Agent 4 (Comparison)
                                                                      │
                                                      IMPROVED | STABLE | WORSENED

IMPORTANT:
  - Does NOT process video.
  - Does NOT make medical diagnoses.
  - All conclusions are based solely on measured kinematic differences
    between the two independently analyzed gait assessments.
"""

from typing import Dict, Any, Optional, List

# ---------------------------------------------------------------------------
# Configurable threshold (percentage points of SI change to be considered
# meaningful; changes within ±STABILITY_THRESHOLD are classified as STABLE)
# ---------------------------------------------------------------------------
STABILITY_THRESHOLD: float = 5.0  # percentage points of asymmetry SI change

# ---------------------------------------------------------------------------
# Agent identity
# ---------------------------------------------------------------------------
AGENT_COMPARISON_CONFIG: Dict[str, str] = {
    "name": "Agent 4: The Patient Gait Progress Comparison Agent",
    "role": "Pediatric Gait Progress Comparison Specialist",
    "goal": (
        "Compare gait measurements from two separate walking videos of the same child "
        "to objectively determine whether measured gait parameters have improved, "
        "remained stable, or worsened since the previous assessment."
    ),
    "backstory": (
        "You are a clinical gait analysis specialist focused on longitudinal pediatric assessment. "
        "You receive structured kinematic and risk data from two independent gait analysis sessions "
        "and compare them objectively to identify meaningful changes. You never speculate on diagnoses "
        "— your role is to clearly describe what the measurements show and classify the overall "
        "directional change in gait symmetry and joint mobility parameters."
    ),
}

# Ordinal risk levels for change classification
_RISK_ORDER: Dict[str, int] = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _classify_risk_change(old_risk: str, new_risk: str) -> str:
    """Return a human-readable risk transition string."""
    old_v = _RISK_ORDER.get(old_risk.upper(), 1)
    new_v = _RISK_ORDER.get(new_risk.upper(), 1)
    if new_v < old_v:
        return f"{old_risk}_TO_{new_risk}_IMPROVED"
    elif new_v > old_v:
        return f"{old_risk}_TO_{new_risk}_WORSENED"
    else:
        return f"{old_risk}_TO_{new_risk}_STABLE"


def _build_comparability_warning(
    old_quality: Dict[str, Any],
    new_quality: Dict[str, Any],
) -> Optional[str]:
    """
    Detect recording-condition differences that may reduce direct comparability.
    Returns a warning string if any differences are found, otherwise None.
    """
    warnings: List[str] = []

    old_metrics = old_quality.get("metrics", {})
    new_metrics = new_quality.get("metrics", {})

    # Camera angle difference
    old_angle = old_metrics.get("camera_angle_detected", "UNKNOWN")
    new_angle = new_metrics.get("camera_angle_detected", "UNKNOWN")
    if (
        old_angle and new_angle
        and old_angle != "UNKNOWN"
        and new_angle != "UNKNOWN"
        and old_angle != new_angle
    ):
        warnings.append(
            f"The previous video was recorded from a {old_angle} view while the current video "
            f"was recorded from a {new_angle} view. Direct measurement comparison may be less reliable. "
            f"For more reliable progress tracking, record both assessments using a similar camera angle."
        )

    # Pose detection rate difference
    old_detect = old_metrics.get("landmark_detection_rate", 1.0) or 1.0
    new_detect = new_metrics.get("landmark_detection_rate", 1.0) or 1.0
    if abs(old_detect - new_detect) > 0.20:
        warnings.append(
            f"Pose detection rates differ significantly between videos "
            f"(previous: {old_detect * 100:.0f}%, current: {new_detect * 100:.0f}%). "
            f"Measurements from the video with lower detection confidence may be less accurate."
        )

    # Quality status warning
    old_status = old_quality.get("status", "PASS")
    new_status = new_quality.get("status", "PASS")
    if old_status == "WARNING" or new_status == "WARNING":
        warnings.append(
            "One or both videos received a WARNING quality status. "
            "Comparison results may be less reliable than assessments from PASS-quality videos."
        )

    return " ".join(warnings) if warnings else None


# ---------------------------------------------------------------------------
# Core comparison function
# ---------------------------------------------------------------------------

def compare_gait_progress(
    old_gait_result: Dict[str, Any],
    new_gait_result: Dict[str, Any],
    old_risk_result: Optional[Dict[str, Any]] = None,
    new_risk_result: Optional[Dict[str, Any]] = None,
    old_quality_result: Optional[Dict[str, Any]] = None,
    new_quality_result: Optional[Dict[str, Any]] = None,
    old_file_name: str = "old_video",
    new_file_name: str = "new_video",
    old_video_url: str = "",
    new_video_url: str = "",
) -> Dict[str, Any]:
    """
    Compare two independently analyzed gait results and produce a structured
    progress report.

    Parameters
    ----------
    old_gait_result  : dict — output of analyze_biomechanics() for the old/previous video
    new_gait_result  : dict — output of analyze_biomechanics() for the new/current video
    old_risk_result  : dict — optional output of assess_clinical_risk() for old video
    new_risk_result  : dict — optional output of assess_clinical_risk() for new video
    old_quality_result : dict — optional output of validate_video_quality() for old video
    new_quality_result : dict — optional output of validate_video_quality() for new video
    old_file_name    : str  — display name for the previous video
    new_file_name    : str  — display name for the current video
    old_video_url    : str  — URL path for serving the previous annotated video
    new_video_url    : str  — URL path for serving the current annotated video

    Returns
    -------
    dict — structured comparison result (see docstring for schema)
    """
    old_m = old_gait_result["metrics"]
    new_m = new_gait_result["metrics"]

    # ── Primary metrics ──────────────────────────────────────────────────────
    old_asymmetry = old_m["mean_symmetry_index_pct"]
    new_asymmetry = new_m["mean_symmetry_index_pct"]
    asymmetry_change = round(new_asymmetry - old_asymmetry, 2)

    old_l_max = old_m["left_max_flexion_deg"]
    new_l_max = new_m["left_max_flexion_deg"]
    old_r_max = old_m["right_max_flexion_deg"]
    new_r_max = new_m["right_max_flexion_deg"]

    old_l_rom = old_m["left_rom_deg"]
    new_l_rom = new_m["left_rom_deg"]
    old_r_rom = old_m["right_rom_deg"]
    new_r_rom = new_m["right_rom_deg"]

    old_rom_deficit = old_m["rom_deficit_deg"]
    new_rom_deficit = new_m["rom_deficit_deg"]
    rom_deficit_change = round(new_rom_deficit - old_rom_deficit, 2)

    # ── Risk levels ──────────────────────────────────────────────────────────
    old_risk = old_risk_result.get("risk_level", "UNKNOWN") if old_risk_result else "UNKNOWN"
    new_risk = new_risk_result.get("risk_level", "UNKNOWN") if new_risk_result else "UNKNOWN"
    risk_change = (
        _classify_risk_change(old_risk, new_risk)
        if (old_risk != "UNKNOWN" and new_risk != "UNKNOWN")
        else None
    )

    # ── Overall progress classification ─────────────────────────────────────
    # Multi-metric weighted scoring: each metric votes toward IMPROVED (+) or WORSENED (-)
    score = 0

    # Asymmetry: lower SI = more symmetrical = better (weight ×2 as primary metric)
    if asymmetry_change <= -STABILITY_THRESHOLD:
        score += 2
    elif asymmetry_change >= STABILITY_THRESHOLD:
        score -= 2

    # ROM deficit: lower deficit = more bilateral symmetry = better
    if rom_deficit_change <= -2.0:
        score += 1
    elif rom_deficit_change >= 2.0:
        score -= 1

    # Risk classification change
    if risk_change and "IMPROVED" in risk_change:
        score += 1
    elif risk_change and "WORSENED" in risk_change:
        score -= 1

    if score >= 1:
        overall_progress = "IMPROVED"
    elif score <= -1:
        overall_progress = "WORSENED"
    else:
        overall_progress = "STABLE"

    # ── Key findings ─────────────────────────────────────────────────────────
    key_findings: List[str] = []

    # Asymmetry finding (always included)
    if abs(asymmetry_change) >= STABILITY_THRESHOLD:
        direction = "decreased" if asymmetry_change < 0 else "increased"
        key_findings.append(
            f"Measured gait asymmetry (symmetry index) {direction} by "
            f"{abs(asymmetry_change):.1f} percentage points "
            f"(previous: {old_asymmetry:.1f}%, current: {new_asymmetry:.1f}%)."
        )
    else:
        key_findings.append(
            f"Gait asymmetry remained approximately stable "
            f"(previous: {old_asymmetry:.1f}%, current: {new_asymmetry:.1f}%, "
            f"change: {asymmetry_change:+.1f} percentage points)."
        )

    # Left knee angle finding
    l_angle_change = round(new_l_max - old_l_max, 1)
    if abs(l_angle_change) >= 3.0:
        key_findings.append(
            f"Left knee peak flexion angle "
            f"{'increased' if l_angle_change > 0 else 'decreased'} "
            f"by {abs(l_angle_change):.1f}° "
            f"({old_l_max:.1f}° → {new_l_max:.1f}°)."
        )

    # Right knee angle finding
    r_angle_change = round(new_r_max - old_r_max, 1)
    if abs(r_angle_change) >= 3.0:
        key_findings.append(
            f"Right knee peak flexion angle "
            f"{'increased' if r_angle_change > 0 else 'decreased'} "
            f"by {abs(r_angle_change):.1f}° "
            f"({old_r_max:.1f}° → {new_r_max:.1f}°)."
        )

    # ROM deficit finding
    if abs(rom_deficit_change) >= 2.0:
        direction = "decreased" if rom_deficit_change < 0 else "increased"
        key_findings.append(
            f"Bilateral ROM deficit {direction} by {abs(rom_deficit_change):.1f}° "
            f"({old_rom_deficit:.1f}° → {new_rom_deficit:.1f}°)."
        )

    # Risk change finding
    if risk_change:
        key_findings.append(
            f"Screening risk classification changed from {old_risk} to {new_risk}."
        )

    # ── Summary and recommendation ────────────────────────────────────────────
    if overall_progress == "IMPROVED":
        summary = (
            f"The latest gait assessment shows an overall improvement in measured gait parameters "
            f"compared with the previous assessment. "
        )
        if asymmetry_change <= -STABILITY_THRESHOLD:
            summary += (
                f"Measured gait asymmetry decreased by {abs(asymmetry_change):.1f} percentage points, "
                f"indicating more symmetrical bilateral limb movement."
            )
        recommendation = (
            "Continue the current intervention programme and schedule a follow-up assessment to "
            "monitor sustained progress. Discuss these findings with the treating clinician."
        )
    elif overall_progress == "WORSENED":
        summary = (
            f"The latest gait assessment shows that measured gait parameters have worsened "
            f"compared with the previous assessment. "
        )
        if asymmetry_change >= STABILITY_THRESHOLD:
            summary += (
                f"Measured gait asymmetry increased by {abs(asymmetry_change):.1f} percentage points, "
                f"indicating reduced bilateral limb symmetry."
            )
        recommendation = (
            "The measured gait parameters have worsened since the previous assessment. "
            "Consider prompt clinical review and re-evaluation of the current care plan "
            "with the treating clinician."
        )
    else:
        summary = (
            "No significant change was detected between the two gait assessments. "
            f"Measured parameters remained within {STABILITY_THRESHOLD:.0f} percentage points "
            "of the previous assessment values."
        )
        recommendation = (
            "Continue monitoring with scheduled follow-up assessments. "
            "Discuss findings with the treating clinician."
        )

    # ── Comparability warning ─────────────────────────────────────────────────
    comparability_warning: Optional[str] = None
    if old_quality_result and new_quality_result:
        comparability_warning = _build_comparability_warning(old_quality_result, new_quality_result)

    # ── Assemble structured result ────────────────────────────────────────────
    return {
        "comparison_status": "COMPLETED",
        "overall_progress": overall_progress,
        "score": score,
        "agent": AGENT_COMPARISON_CONFIG,
        "old_video": {
            "file_name": old_file_name,
            "video_url": old_video_url,
            "gait_asymmetry": round(old_asymmetry, 2),
            "left_knee_max_flexion": round(old_l_max, 1),
            "right_knee_max_flexion": round(old_r_max, 1),
            "left_rom": round(old_l_rom, 1),
            "right_rom": round(old_r_rom, 1),
            "rom_deficit_deg": round(old_rom_deficit, 1),
            "risk_level": old_risk,
            "quality_status": (
                old_quality_result.get("status", "UNKNOWN") if old_quality_result else "UNKNOWN"
            ),
            "quality_score": (
                old_quality_result.get("video_quality_score", 0) if old_quality_result else 0
            ),
        },
        "new_video": {
            "file_name": new_file_name,
            "video_url": new_video_url,
            "gait_asymmetry": round(new_asymmetry, 2),
            "left_knee_max_flexion": round(new_l_max, 1),
            "right_knee_max_flexion": round(new_r_max, 1),
            "left_rom": round(new_l_rom, 1),
            "right_rom": round(new_r_rom, 1),
            "rom_deficit_deg": round(new_rom_deficit, 1),
            "risk_level": new_risk,
            "quality_status": (
                new_quality_result.get("status", "UNKNOWN") if new_quality_result else "UNKNOWN"
            ),
            "quality_score": (
                new_quality_result.get("video_quality_score", 0) if new_quality_result else 0
            ),
        },
        "comparison": {
            "asymmetry_change": asymmetry_change,
            "left_knee_max_flexion_change": round(new_l_max - old_l_max, 1),
            "right_knee_max_flexion_change": round(new_r_max - old_r_max, 1),
            "left_rom_change": round(new_l_rom - old_l_rom, 1),
            "right_rom_change": round(new_r_rom - old_r_rom, 1),
            "rom_deficit_change": rom_deficit_change,
            "risk_change": risk_change,
        },
        "key_findings": key_findings,
        "summary": summary,
        "recommendation": recommendation,
        "comparability_warning": comparability_warning,
        "stability_threshold_used": STABILITY_THRESHOLD,
    }
