"""
patient_progress_agent.py

KinemaTrace AI — Patient Progress Monitoring Agent (Agent 3)

Receives structured output from:
  - Gait Analysis Agent      (Agent 1)  →  analyze_biomechanics()
  - Clinical Risk Assessment Agent (Agent 2)  →  assess_clinical_risk()

Tracks gait history per patient and classifies longitudinal trend as:
  IMPROVING | STABLE | WORSENING | INSUFFICIENT_DATA | FLUCTUATING

Architecture:
  Agent 1 (Gait Analysis)
      │ structured kinematic metrics
      ▼
  Agent 2 (Clinical Risk)
      │ risk_level + severity + asymmetry
      ▼
  Agent 3 (Progress Monitoring)  ← THIS MODULE
      │ trend + history + chart data
      ▼
  Dashboard

IMPORTANT:
  - Does NOT process video.
  - Does NOT make medical diagnoses.
  - All conclusions are based solely on measured kinematic screening data.
"""

import os
import json
import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple

# ── Storage Configuration ─────────────────────────────────────────────────────
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
_HISTORY_FILE = os.path.join(_DATA_DIR, "patient_history.json")

# ── Configurable Progress Thresholds ─────────────────────────────────────────
PROGRESS_THRESHOLDS: Dict[str, float] = {
    "significant_change_pct": 3.0,        # min asymmetry Δ to be "significant"
    "long_term_overall_pct": 5.0,         # min first→last Δ for overall trend
    "consistent_direction_ratio": 0.60,   # fraction of steps in same direction = "consistent"
}

# ── Ordinal Mappings ──────────────────────────────────────────────────────────
RISK_ORDER: Dict[str, int] = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
SEVERITY_ORDER: Dict[str, int] = {"NORMAL": 0, "MILD": 1, "MODERATE": 2, "SIGNIFICANT": 3}

# ── Agent Identity ────────────────────────────────────────────────────────────
AGENT_PROGRESS_CONFIG: Dict[str, str] = {
    "name": "Agent 3: The Patient Progress Monitoring Agent",
    "role": "Pediatric Gait Progress Tracker & Longitudinal Analysis Specialist",
    "goal": (
        "Track a child's gait screening assessments across multiple sessions "
        "to determine whether the measured gait pattern is improving, stable, or worsening. "
        "Present longitudinal progress in a transparent, clinician-ready, non-diagnostic format."
    ),
    "backstory": (
        "You are a clinical outcomes researcher specialising in pediatric gait rehabilitation. "
        "You receive structured kinematic and risk data from multiple assessment sessions and compare "
        "them chronologically to identify meaningful trends. You never make diagnoses — instead you "
        "describe observed measurement changes precisely and consistently, supporting evidence-based "
        "clinical decision-making through objective longitudinal screening data."
    ),
}

# ── Demo Seed Data ────────────────────────────────────────────────────────────
_DEMO_SEED: Dict[str, List[Dict[str, Any]]] = {
    "KT-2026-P902": [
        {
            "assessment_date": "2026-05-10",
            "asymmetry_percentage": 28.5, "peak_asymmetry_percentage": 41.2,
            "risk_level": "HIGH", "severity": "SIGNIFICANT", "affected_side": "RIGHT",
            "left_rom_deg": 45.0, "right_rom_deg": 33.0, "rom_deficit_deg": 12.0,
            "mean_si_pct": 28.5, "peak_si_pct": 41.2, "age": "7 y/o",
        },
        {
            "assessment_date": "2026-06-05",
            "asymmetry_percentage": 23.8, "peak_asymmetry_percentage": 37.4,
            "risk_level": "HIGH", "severity": "SIGNIFICANT", "affected_side": "RIGHT",
            "left_rom_deg": 46.0, "right_rom_deg": 36.0, "rom_deficit_deg": 10.0,
            "mean_si_pct": 23.8, "peak_si_pct": 37.4, "age": "7 y/o",
        },
        {
            "assessment_date": "2026-07-01",
            "asymmetry_percentage": 19.2, "peak_asymmetry_percentage": 32.6,
            "risk_level": "HIGH", "severity": "SIGNIFICANT", "affected_side": "RIGHT",
            "left_rom_deg": 47.0, "right_rom_deg": 38.5, "rom_deficit_deg": 8.5,
            "mean_si_pct": 19.2, "peak_si_pct": 32.6, "age": "7 y/o",
        },
    ],
    "PED-2026-001": [
        {
            "assessment_date": "2026-05-15",
            "asymmetry_percentage": 27.0, "peak_asymmetry_percentage": 40.0,
            "risk_level": "HIGH", "severity": "SIGNIFICANT", "affected_side": "BILATERAL",
            "left_rom_deg": 50.0, "right_rom_deg": 50.0, "rom_deficit_deg": 0.0,
            "mean_si_pct": 27.0, "peak_si_pct": 40.0, "age": "7 y/o",
        },
        {
            "assessment_date": "2026-06-12",
            "asymmetry_percentage": 26.3, "peak_asymmetry_percentage": 39.5,
            "risk_level": "HIGH", "severity": "SIGNIFICANT", "affected_side": "BILATERAL",
            "left_rom_deg": 50.5, "right_rom_deg": 50.5, "rom_deficit_deg": 0.0,
            "mean_si_pct": 26.3, "peak_si_pct": 39.5, "age": "7 y/o",
        },
        {
            "assessment_date": "2026-07-05",
            "asymmetry_percentage": 25.8, "peak_asymmetry_percentage": 38.9,
            "risk_level": "HIGH", "severity": "SIGNIFICANT", "affected_side": "BILATERAL",
            "left_rom_deg": 51.0, "right_rom_deg": 51.0, "rom_deficit_deg": 0.0,
            "mean_si_pct": 25.8, "peak_si_pct": 38.9, "age": "7 y/o",
        },
    ],
}


# ── JSON Storage Layer ────────────────────────────────────────────────────────

def _load_history() -> Dict[str, Any]:
    if not os.path.exists(_HISTORY_FILE):
        return {"patients": {}}
    try:
        with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"patients": {}}


def _write_history(data: Dict[str, Any]) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _ensure_demo_seed() -> None:
    """Populate demo patient history on first run if empty."""
    history = _load_history()
    changed = False
    for patient_id, sessions in _DEMO_SEED.items():
        if patient_id not in history["patients"]:
            history["patients"][patient_id] = {"assessments": []}
            for s in sessions:
                record = {
                    "assessment_id": str(uuid.uuid4()),
                    "saved_at": datetime.now().isoformat(),
                    "patient_id": patient_id,
                    **s,
                }
                history["patients"][patient_id]["assessments"].append(record)
            changed = True
    if changed:
        _write_history(history)


def get_patient_assessments(patient_id: str) -> List[Dict[str, Any]]:
    """Return all saved assessments for a patient, sorted by date ascending."""
    history = _load_history()
    records = history.get("patients", {}).get(patient_id, {}).get("assessments", [])
    return sorted(records, key=lambda a: a.get("assessment_date", ""))


def save_patient_assessment(
    patient_id: str,
    assessment: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Persist an assessment to JSON store with dedup guard.

    Returns:
        (True, assessment_id)  if saved
        (False, reason)        if duplicate or error
    """
    history = _load_history()
    history.setdefault("patients", {}).setdefault(patient_id, {"assessments": []})

    existing: List[Dict] = history["patients"][patient_id]["assessments"]

    # Dedup: same date + asymmetry rounded to 1 dp
    a_date = assessment.get("assessment_date", "")
    asym_r = round(float(assessment.get("asymmetry_percentage", 0.0)), 1)
    for a in existing:
        if (
            a.get("assessment_date", "") == a_date
            and round(float(a.get("asymmetry_percentage", 0.0)), 1) == asym_r
        ):
            return False, "Duplicate: same date and asymmetry value already recorded."

    aid = str(uuid.uuid4())
    record = {
        "assessment_id": aid,
        "saved_at": datetime.now().isoformat(),
        "patient_id": patient_id,
        **assessment,
    }
    existing.append(record)
    existing.sort(key=lambda x: x.get("assessment_date", ""))
    history["patients"][patient_id]["assessments"] = existing
    _write_history(history)
    return True, aid


def delete_patient_history(patient_id: str) -> bool:
    """Clear all history for a patient (admin/demo reset use only)."""
    history = _load_history()
    if patient_id in history.get("patients", {}):
        del history["patients"][patient_id]
        _write_history(history)
        return True
    return False


# ── Trend Logic ───────────────────────────────────────────────────────────────

def _risk_score(level: str) -> int:
    return RISK_ORDER.get(str(level).upper(), 1)


def _sev_score(sev: str) -> int:
    return SEVERITY_ORDER.get(str(sev).upper(), 0)


def _compare_two(
    prev: Dict[str, Any],
    curr: Dict[str, Any],
) -> Tuple[str, List[str], str]:
    """
    Determine trend + key changes + explanation between two assessments.
    Returns: (trend_label, key_changes, explanation)
    """
    threshold = PROGRESS_THRESHOLDS["significant_change_pct"]

    prev_asym = float(prev.get("asymmetry_percentage", 0.0))
    curr_asym = float(curr.get("asymmetry_percentage", 0.0))
    asym_delta = curr_asym - prev_asym  # negative = improved

    prev_risk = str(prev.get("risk_level", "HIGH"))
    curr_risk = str(curr.get("risk_level", "HIGH"))
    risk_delta = _risk_score(curr_risk) - _risk_score(prev_risk)

    prev_sev = str(prev.get("severity", "SIGNIFICANT"))
    curr_sev = str(curr.get("severity", "SIGNIFICANT"))
    sev_delta = _sev_score(curr_sev) - _sev_score(prev_sev)

    key_changes: List[str] = []

    if abs(asym_delta) >= threshold:
        direction = "decreased" if asym_delta < 0 else "increased"
        key_changes.append(
            f"Gait asymmetry {direction} by {abs(asym_delta):.1f} percentage points "
            f"({prev_asym:.1f}% → {curr_asym:.1f}%)"
        )
    if risk_delta < 0:
        key_changes.append(f"Screening risk level improved: {prev_risk} → {curr_risk}")
    elif risk_delta > 0:
        key_changes.append(f"Screening risk level increased: {prev_risk} → {curr_risk}")
    if sev_delta < 0:
        key_changes.append(f"Asymmetry severity improved: {prev_sev} → {curr_sev}")
    elif sev_delta > 0:
        key_changes.append(f"Asymmetry severity increased: {prev_sev} → {curr_sev}")

    # ── Trend classification ──────────────────────────────────────────────
    if asym_delta <= -threshold:
        trend = "IMPROVING"
    elif asym_delta >= threshold:
        trend = "WORSENING"
    elif risk_delta < 0:
        trend = "IMPROVING"
    elif risk_delta > 0:
        trend = "WORSENING"
    else:
        trend = "STABLE"

    if not key_changes:
        key_changes.append(
            f"Gait asymmetry remained relatively unchanged "
            f"({prev_asym:.1f}% → {curr_asym:.1f}%); screening risk level unchanged ({curr_risk})."
        )

    # ── Explanation text ──────────────────────────────────────────────────
    prev_date = prev.get("assessment_date", "previous session")
    curr_date = curr.get("assessment_date", "current session")

    if trend == "IMPROVING":
        explanation = (
            f"The latest screening assessment ({curr_date}) shows a positive change compared with "
            f"the previous assessment ({prev_date}). The measured gait asymmetry changed from "
            f"{prev_asym:.1f}% to {curr_asym:.1f}% (Δ {asym_delta:+.1f} percentage points)."
        )
        if risk_delta < 0:
            explanation += f" The screening risk level also improved from {prev_risk} to {curr_risk}."
        explanation += (
            " This observation reflects an improving gait screening trend based on available "
            "kinematic data. This is a screening observation only and does not constitute a "
            "medical assessment or clinical discharge."
        )
    elif trend == "WORSENING":
        explanation = (
            f"The latest screening assessment ({curr_date}) shows a negative change compared with "
            f"the previous assessment ({prev_date}). The measured gait asymmetry changed from "
            f"{prev_asym:.1f}% to {curr_asym:.1f}% (Δ {asym_delta:+.1f} percentage points)."
        )
        if risk_delta > 0:
            explanation += f" The screening risk level also increased from {prev_risk} to {curr_risk}."
        explanation += (
            " A qualified pediatric healthcare professional should review these findings. "
            "This is a screening observation only and does not constitute a medical assessment."
        )
    else:  # STABLE
        explanation = (
            f"The patient's measured gait asymmetry and screening risk level remain relatively "
            f"consistent between the previous assessment ({prev_date}: {prev_asym:.1f}%, {prev_risk}) "
            f"and the current assessment ({curr_date}: {curr_asym:.1f}%, {curr_risk}). "
            f"No significant directional change was detected in the available kinematic metrics."
        )

    return trend, key_changes, explanation


def _long_term_analysis(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyse trend across 3+ chronological assessment sessions."""
    threshold = PROGRESS_THRESHOLDS["significant_change_pct"]
    ratio = PROGRESS_THRESHOLDS["consistent_direction_ratio"]
    overall_t = PROGRESS_THRESHOLDS["long_term_overall_pct"]

    asym_vals = [float(a.get("asymmetry_percentage", 0.0)) for a in sessions]
    first_asym, last_asym = asym_vals[0], asym_vals[-1]
    overall_delta = last_asym - first_asym

    first_risk = sessions[0].get("risk_level", "HIGH")
    last_risk = sessions[-1].get("risk_level", "HIGH")

    deltas = [asym_vals[i + 1] - asym_vals[i] for i in range(len(asym_vals) - 1)]
    n = len(deltas)
    imp = sum(1 for d in deltas if d <= -threshold)
    wor = sum(1 for d in deltas if d >= threshold)

    if overall_delta <= -overall_t:
        lt = "CONSISTENTLY_IMPROVING" if (imp / n) >= ratio else "FLUCTUATING_BUT_IMPROVING"
    elif overall_delta >= overall_t:
        lt = "CONSISTENTLY_WORSENING" if (wor / n) >= ratio else "FLUCTUATING_BUT_WORSENING"
    elif imp == 0 and wor == 0:
        lt = "STABLE"
    else:
        lt = "FLUCTUATING"

    lt_labels = {
        "CONSISTENTLY_IMPROVING": "Consistently improving across all recorded sessions.",
        "FLUCTUATING_BUT_IMPROVING": "Fluctuating between sessions, but with an overall improving trend.",
        "CONSISTENTLY_WORSENING": "Consistently worsening across all recorded sessions.",
        "FLUCTUATING_BUT_WORSENING": "Fluctuating between sessions, but with an overall worsening trend.",
        "STABLE": "Stable across all recorded sessions — no significant directional change.",
        "FLUCTUATING": "Fluctuating across sessions with no clear directional trend.",
    }

    chart_data = [
        {
            "session": i + 1,
            "date": a.get("assessment_date", ""),
            "asymmetry_pct": round(float(a.get("asymmetry_percentage", 0.0)), 2),
            "risk_score": _risk_score(a.get("risk_level", "HIGH")),
            "risk_level": a.get("risk_level", "—"),
        }
        for i, a in enumerate(sessions)
    ]

    return {
        "long_term_trend": lt,
        "long_term_summary": lt_labels.get(lt, ""),
        "total_sessions": len(sessions),
        "first_asymmetry": round(first_asym, 2),
        "latest_asymmetry": round(last_asym, 2),
        "overall_asymmetry_change": round(overall_delta, 2),
        "first_risk_level": first_risk,
        "latest_risk_level": last_risk,
        "improving_sessions": imp,
        "worsening_sessions": wor,
        "stable_sessions": n - imp - wor,
        "chart_data": chart_data,
    }


# ── Report Text Builder ───────────────────────────────────────────────────────

def _build_report_text(
    patient_id: str,
    trend: str,
    current: Dict[str, Any],
    previous: Optional[Dict[str, Any]],
    key_changes: List[str],
    explanation: str,
    recommendation: str,
    lt: Optional[Dict[str, Any]],
    patient_age: str = None,
) -> str:
    emoji = {"IMPROVING": "🟢", "STABLE": "🔵", "WORSENING": "🔴",
             "INSUFFICIENT_DATA": "⚪", "FLUCTUATING": "🟡"}.get(trend, "⚪")
    age_note = f" · Age: {patient_age}" if patient_age else ""
    lines = [
        "### 📊 PATIENT PROGRESS MONITORING REPORT",
        f"**Agent:** {AGENT_PROGRESS_CONFIG['role']}",
        f"**Patient ID:** {patient_id}{age_note}",
        f"**Current Assessment Date:** {current.get('assessment_date', '—')}",
        "",
        "---",
        "#### 1. Progress Trend",
        f"- **Overall Trend:** {emoji} **{trend}**",
    ]
    if previous:
        pa = float(previous.get("asymmetry_percentage", 0.0))
        ca = float(current.get("asymmetry_percentage", 0.0))
        lines += [
            f"- **Previous:** {previous.get('assessment_date', '—')} | "
            f"Asymmetry: {pa:.1f}% | Risk: {previous.get('risk_level', '—')}",
            f"- **Current:** {current.get('assessment_date', '—')} | "
            f"Asymmetry: {ca:.1f}% | Risk: {current.get('risk_level', '—')}",
            f"- **Asymmetry Change:** {ca - pa:+.1f} percentage points",
        ]
    lines += ["", "#### 2. Key Observed Changes"]
    for c in key_changes:
        lines.append(f"- 🔸 {c}")
    lines += ["", "#### 3. Progress Explanation", explanation]
    if lt and lt.get("total_sessions", 0) >= 3:
        lines += [
            "", "#### 4. Long-Term Trend Analysis",
            f"- **Sessions Analysed:** {lt['total_sessions']}",
            f"- **Long-Term Pattern:** {lt['long_term_trend']}",
            f"- **Initial Asymmetry:** {lt['first_asymmetry']:.1f}%  →  "
            f"**Latest:** {lt['latest_asymmetry']:.1f}%  "
            f"(Overall: {lt['overall_asymmetry_change']:+.1f} pp)",
            f"- **Summary:** {lt['long_term_summary']}",
        ]
    lines += [
        "", "#### 5. Recommended Next Step", recommendation, "",
        "---",
        "*⚠️ This Progress Monitoring Report is generated by an automated screening system. "
        "Changes in asymmetry and risk level are measured observations from kinematic screening data only. "
        "This report does not constitute a medical diagnosis or treatment recommendation. "
        "All findings must be reviewed by a licensed pediatric healthcare professional.*",
    ]
    return "\n".join(lines)


# ── Recommendation Builder ────────────────────────────────────────────────────

def _build_recommendation(trend: str, current_risk: str) -> str:
    disc = " This screening result does not constitute a medical diagnosis."
    if trend == "IMPROVING":
        return (
            f"The observed improving trend is encouraging. Continue monitoring the patient's "
            f"gait pattern at regular screening intervals. Clinical follow-up is still recommended "
            f"if the current risk level ({current_risk}) is HIGH or MEDIUM." + disc
        )
    elif trend == "WORSENING":
        return (
            f"The observed worsening trend warrants clinical attention. Consider scheduling "
            f"a prompt review with a qualified pediatric healthcare professional. The current "
            f"screening risk level is {current_risk}." + disc
        )
    elif trend == "STABLE":
        return (
            f"The patient's gait pattern has remained stable between sessions. Continue routine "
            f"monitoring at the recommended screening interval. Current risk level: {current_risk}." + disc
        )
    elif trend in ("FLUCTUATING", "FLUCTUATING_BUT_IMPROVING", "FLUCTUATING_BUT_WORSENING"):
        return (
            f"Variable screening results across sessions. Consistent follow-up monitoring is "
            f"recommended to identify a clearer trend. Current risk level: {current_risk}." + disc
        )
    else:
        return (
            "Additional assessment sessions are required to determine a meaningful gait progress trend. "
            "Schedule regular follow-up screenings to build a longitudinal dataset for this patient." + disc
        )


# ── Main Public Interface ─────────────────────────────────────────────────────

def assess_progress(
    patient_id: str,
    gait_analysis_result: Dict[str, Any],
    clinical_risk_result: Dict[str, Any],
    patient_age: str = None,
    assessment_date: str = None,
    save: bool = False,
) -> Dict[str, Any]:
    """
    Assess patient gait progress across multiple screening sessions.

    Args:
        patient_id:             Unique patient identifier string.
        gait_analysis_result:   Dict from analyze_biomechanics() — must include 'metrics'.
        clinical_risk_result:   Dict from assess_clinical_risk() — must include risk_level etc.
        patient_age:            Optional age string (e.g. "7 y/o").
        assessment_date:        ISO date string YYYY-MM-DD (defaults to today).
        save:                   If True, persist current assessment to history.

    Returns:
        Structured progress result dict.
    """
    if assessment_date is None:
        assessment_date = date.today().isoformat()

    metrics: Dict[str, Any] = gait_analysis_result.get("metrics", {})
    cr = clinical_risk_result

    current_record: Dict[str, Any] = {
        "patient_id": patient_id,
        "assessment_date": assessment_date,
        "age": patient_age or "—",
        "asymmetry_percentage": round(float(cr.get("asymmetry_percentage", 0.0)), 2),
        "peak_asymmetry_percentage": round(float(cr.get("peak_asymmetry_percentage", 0.0)), 2),
        "risk_level": cr.get("risk_level", "HIGH"),
        "severity": cr.get("severity", "SIGNIFICANT"),
        "affected_side": cr.get("affected_side", "—"),
        "left_rom_deg": round(float(metrics.get("left_rom_deg", 0.0)), 2),
        "right_rom_deg": round(float(metrics.get("right_rom_deg", 0.0)), 2),
        "rom_deficit_deg": round(float(metrics.get("rom_deficit_deg", 0.0)), 2),
        "mean_si_pct": round(float(metrics.get("mean_symmetry_index_pct", 0.0)), 2),
        "peak_si_pct": round(float(metrics.get("peak_symmetry_index_pct", 0.0)), 2),
    }

    # Optionally save
    saved = False
    save_message = ""
    if save:
        saved, save_message = save_patient_assessment(patient_id, current_record)

    # Load history after potential save
    all_stored = get_patient_assessments(patient_id)

    def _is_current(a: Dict) -> bool:
        return (
            a.get("assessment_date", "") == assessment_date
            and round(float(a.get("asymmetry_percentage", 0.0)), 1)
            == round(current_record["asymmetry_percentage"], 1)
        )

    past = [a for a in all_stored if not _is_current(a)]

    # ── INSUFFICIENT DATA ──────────────────────────────────────────────────
    if not past:
        rec = _build_recommendation("INSUFFICIENT_DATA", current_record["risk_level"])
        explanation = (
            "This is the first recorded screening assessment for this patient. "
            "At least one previous session is required to determine a meaningful gait progress trend. "
            "Please complete additional screening sessions to enable longitudinal comparison."
        )
        report_text = _build_report_text(
            patient_id, "INSUFFICIENT_DATA", current_record,
            None, [], explanation, rec, None, patient_age,
        )
        return {
            "agent": AGENT_PROGRESS_CONFIG,
            "patient_id": patient_id,
            "trend": "INSUFFICIENT_DATA",
            "data_available": False,
            "total_history_sessions": len(all_stored),
            "current_assessment": current_record,
            "previous_assessment": None,
            "key_changes": [],
            "explanation": explanation,
            "recommendation": rec,
            "long_term_analysis": None,
            "chart_data": [
                {
                    "session": 1,
                    "date": assessment_date,
                    "asymmetry_pct": current_record["asymmetry_percentage"],
                    "risk_score": _risk_score(current_record["risk_level"]),
                    "risk_level": current_record["risk_level"],
                }
            ],
            "report_text": report_text,
            "saved": saved,
            "save_message": save_message,
            "is_diagnostic": False,
        }

    # ── COMPARE with most recent past session ──────────────────────────────
    previous_record = past[-1]
    trend, key_changes, explanation = _compare_two(previous_record, current_record)

    # ── Long-term analysis (3+ sessions including current) ─────────────────
    all_for_chart = past + [current_record]
    lt = _long_term_analysis(all_for_chart) if len(all_for_chart) >= 3 else None

    # Build chart data (past sessions + current, whether saved or not)
    chart_data = [
        {
            "session": i + 1,
            "date": a.get("assessment_date", ""),
            "asymmetry_pct": round(float(a.get("asymmetry_percentage", 0.0)), 2),
            "risk_score": _risk_score(a.get("risk_level", "HIGH")),
            "risk_level": a.get("risk_level", "—"),
            "is_current": _is_current(a),
        }
        for i, a in enumerate(all_for_chart)
    ]
    if not any(d.get("is_current") for d in chart_data):
        chart_data.append({
            "session": len(chart_data) + 1,
            "date": assessment_date,
            "asymmetry_pct": current_record["asymmetry_percentage"],
            "risk_score": _risk_score(current_record["risk_level"]),
            "risk_level": current_record["risk_level"],
            "is_current": True,
        })

    rec = _build_recommendation(trend, current_record["risk_level"])
    report_text = _build_report_text(
        patient_id, trend, current_record, previous_record,
        key_changes, explanation, rec, lt, patient_age,
    )

    asym_change = round(
        current_record["asymmetry_percentage"]
        - float(previous_record.get("asymmetry_percentage", 0.0)), 2
    )
    rd = _risk_score(current_record["risk_level"]) - _risk_score(previous_record.get("risk_level", "HIGH"))
    sd = _sev_score(current_record["severity"]) - _sev_score(previous_record.get("severity", "SIGNIFICANT"))

    return {
        "agent": AGENT_PROGRESS_CONFIG,
        "patient_id": patient_id,
        "trend": trend,
        "data_available": True,
        "total_history_sessions": len(all_stored) + (0 if saved else 1),

        # Current
        "current_assessment": current_record,
        "current_assessment_date": current_record["assessment_date"],
        "current_asymmetry": current_record["asymmetry_percentage"],
        "current_risk_level": current_record["risk_level"],
        "current_severity": current_record["severity"],

        # Previous
        "previous_assessment": previous_record,
        "previous_assessment_date": previous_record.get("assessment_date", "—"),
        "previous_asymmetry": round(float(previous_record.get("asymmetry_percentage", 0.0)), 2),
        "previous_risk_level": previous_record.get("risk_level", "—"),
        "previous_severity": previous_record.get("severity", "—"),

        # Delta
        "asymmetry_change": asym_change,
        "risk_change": "IMPROVED" if rd < 0 else ("WORSENED" if rd > 0 else "UNCHANGED"),
        "severity_change": "IMPROVED" if sd < 0 else ("WORSENED" if sd > 0 else "UNCHANGED"),

        # Narrative
        "key_changes": key_changes,
        "explanation": explanation,
        "recommendation": rec,

        # Long-term
        "long_term_analysis": lt,

        # Chart
        "chart_data": chart_data,

        # Report
        "report_text": report_text,
        "saved": saved,
        "save_message": save_message,
        "is_diagnostic": False,
    }


# ── Auto-seed demo data on module import ──────────────────────────────────────
_ensure_demo_seed()
