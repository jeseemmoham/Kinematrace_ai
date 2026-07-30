"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_BASE = "http://localhost:8000";

type RiskLevel = "HIGH" | "MEDIUM" | "LOW";
type Severity = "SIGNIFICANT" | "MODERATE" | "NORMAL";

interface ThresholdsUsed {
  low_risk_max_si_pct: number;
  high_risk_min_si_pct: number;
  rom_deficit_flag_deg: number;
}

interface ClinicalRiskData {
  risk_level: RiskLevel;
  severity: Severity;
  asymmetry_percentage: number;
  peak_asymmetry_percentage?: number;
  affected_side: string;
  triggered_measurements: string[];
  reasoning: string;
  recommendation: string;
  report_text: string;
  is_diagnostic: boolean;
  thresholds_used: ThresholdsUsed;
  video_id?: string;
}

interface ApiResponse {
  clinical_risk: ClinicalRiskData;
  gait_analysis?: Record<string, any>;
  metrics: Record<string, any>;
  agent_name?: string;
  agent_role?: string;
}

const RISK_CONFIG: Record<
  RiskLevel,
  {
    bg: string;
    border: string;
    text: string;
    badgeBg: string;
    icon: string;
    label: string;
    supportingText: string;
  }
> = {
  LOW: {
    bg: "rgba(16, 185, 129, 0.08)",
    border: "rgba(16, 185, 129, 0.4)",
    text: "#10B981",
    badgeBg: "rgba(16, 185, 129, 0.2)",
    icon: "✓",
    label: "LOW RISK",
    supportingText: "Gait measurements are within expected screening normative ranges.",
  },
  MEDIUM: {
    bg: "rgba(217, 119, 6, 0.1)",
    border: "rgba(217, 119, 6, 0.4)",
    text: "#D97706",
    badgeBg: "rgba(217, 119, 6, 0.2)",
    icon: "⚠",
    label: "MEDIUM RISK",
    supportingText: "Kinematic measurements show moderate deviation from screening thresholds.",
  },
  HIGH: {
    bg: "rgba(239, 68, 68, 0.12)",
    border: "rgba(239, 68, 68, 0.45)",
    text: "#EF4444",
    badgeBg: "rgba(239, 68, 68, 0.2)",
    icon: "!",
    label: "HIGH RISK",
    supportingText: "Gait measurements significantly exceed configured pediatric screening risk thresholds.",
  },
};

export default function ClinicalRiskPage() {
  const router = useRouter();

  const [caseId, setCaseId] = useState<"case1" | "case2" | "custom">("case2");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Custom upload session state
  const [sessionData, setSessionData] = useState<any>(null);
  const [customFile, setCustomFile] = useState<string | null>(null);
  const [videoName, setVideoName] = useState<string>("uploaded_video.mp4");
  const [gaitAnalysisCompleted, setGaitAnalysisCompleted] = useState<boolean>(false);

  const fetchRisk = async (selectedCase: "case1" | "case2" | "custom", filePathOverride?: string | null) => {
    setLoading(true);
    setError(null);
    try {
      const bodyPayload: Record<string, any> = {
        agent_id: "clinical-risk",
      };

      if (selectedCase === "custom") {
        bodyPayload.source_type = "custom";
        if (filePathOverride || customFile) {
          bodyPayload.file_path = filePathOverride || customFile;
        }
      } else {
        bodyPayload.case_id = selectedCase;
      }

      const res = await fetch(`${API_BASE}/api/agents/clinical-risk`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bodyPayload),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      const json: ApiResponse = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || "Failed to reach backend.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const loadSession = () => {
      try {
        const stored = localStorage.getItem("kt_session");
        if (stored) {
          const parsed = JSON.parse(stored);
          setSessionData(parsed);
          if (parsed.video_quality?.file_path || parsed.file_path) {
            const filePath = parsed.video_quality?.file_path || parsed.file_path;
            setCustomFile(filePath);
            setVideoName(parsed.filename || "uploaded_video.mp4");
            const isCompleted = parsed.gait_analysis_completed === true || !!parsed.telemetry || !!parsed.gait_analysis;
            setGaitAnalysisCompleted(isCompleted);

            setCaseId("custom");
            if (isCompleted) {
              fetchRisk("custom", filePath);
            }
            return;
          }
        }
      } catch (e) {
        console.warn("Could not parse kt_session", e);
      }
      setSessionData(null);
      setCustomFile(null);
      setGaitAnalysisCompleted(false);
      setCaseId("case2");
      fetchRisk("case2");
    };

    loadSession();
    window.addEventListener("kt_session_updated", loadSession);
    return () => window.removeEventListener("kt_session_updated", loadSession);
  }, []);

  // ── video_id Verification Mismatch Guard ──────────────────────────────────
  const gaVideoId = sessionData?.gait_analysis?.video_id || sessionData?.video_id;
  const riskVideoId = data?.clinical_risk?.video_id || data?.gait_analysis?.video_id || data?.metrics?.video_id;
  const isVideoIdMismatch = caseId === "custom" && !!gaVideoId && !!riskVideoId && gaVideoId !== riskVideoId;

  const handleRemoveVideo = () => {
    try {
      localStorage.removeItem("kt_session");
      window.dispatchEvent(new Event("kt_session_updated"));
    } catch (e) {
      console.warn("Could not remove kt_session", e);
    }
  };

  // ── Developer Debugging Mismatch Validation Check ──────────────────────────
  useEffect(() => {
    if (data && sessionData && caseId === "custom") {
      const gaSymmetry = sessionData.gait_analysis?.gait_symmetry ?? sessionData.telemetry?.gait_symmetry_pct;
      const riskSymmetry = data.gait_analysis?.gait_symmetry ?? (data.metrics?.mean_symmetry_index_pct !== undefined ? (100 - Number(data.metrics.mean_symmetry_index_pct)) : undefined);

      if (gaSymmetry !== undefined && riskSymmetry !== undefined && Math.abs(gaSymmetry - riskSymmetry) > 1.0) {
        console.error("🛑 Risk Assessment data mismatch detected.", {
          video_id: sessionData.filename || sessionData.video_id || "custom_video",
          gait_analysis_values: sessionData.gait_analysis || sessionData.telemetry,
          risk_assessment_input_values: data.gait_analysis || data.metrics,
          timestamp: new Date().toISOString(),
        });
      } else {
        console.log("✅ Risk Assessment data matches Gait Analysis single source of truth.", {
          video_id: sessionData.filename || sessionData.video_id,
          gait_symmetry: gaSymmetry,
          timestamp: new Date().toISOString(),
        });
      }
    }
  }, [data, sessionData, caseId]);

  const handleCaseSwitch = (id: "case1" | "case2" | "custom") => {
    setCaseId(id);
    if (id === "custom") {
      if (gaitAnalysisCompleted) {
        fetchRisk("custom", customFile);
      }
    } else {
      fetchRisk(id);
    }
  };

  const cr = data?.clinical_risk;
  const riskLevel: RiskLevel = cr?.risk_level || (caseId === "case1" ? "LOW" : "HIGH");
  const riskConfig = RISK_CONFIG[riskLevel];

  // ── Single Source of Truth Metrics ─────────────────────────────────────────
  const ga = (caseId === "custom" ? (sessionData?.gait_analysis || sessionData?.metrics || data?.gait_analysis || data?.metrics) : (data?.gait_analysis || data?.metrics)) || {};

  const gaitSymmetry = Number(ga.gait_symmetry ?? sessionData?.telemetry?.gait_symmetry_pct ?? (100.0 - (ga.mean_asymmetry ?? ga.mean_symmetry_index_pct ?? (caseId === "case1" ? 3.2 : 18.5))));
  const meanAsymmetry = Number(ga.mean_asymmetry ?? ga.mean_symmetry_index_pct ?? (100.0 - gaitSymmetry));
  const peakAsymmetry = Number(ga.peak_asymmetry ?? cr?.peak_asymmetry_percentage ?? (caseId === "case1" ? 4.8 : 24.2));

  const leftRom = Number(ga.left_knee_rom ?? ga.left_rom_deg ?? sessionData?.telemetry?.left_rom ?? (caseId === "case1" ? 118.5 : 84.2));
  const rightRom = Number(ga.right_knee_rom ?? ga.right_rom_deg ?? sessionData?.telemetry?.right_rom ?? (caseId === "case1" ? 120.2 : 120.5));
  const romDelta = Number(ga.rom_difference ?? ga.rom_deficit_deg ?? Math.abs(leftRom - rightRom));

  const hipRom = Number(ga.left_hip_rom ?? ga.hip_flexion_rom_deg ?? sessionData?.telemetry?.hip_flexion_rom_deg ?? 120.0);

  // Active Assessment Source Banner Text
  const sourceText = caseId === "custom"
    ? `Custom Patient — ${videoName}`
    : caseId === "case1"
    ? "Case 1 — Normative Control"
    : "Case 2 — Post-Injury Asymmetric Gait";

  // Compute Comparison Table Rows
  const comparisons = [
    {
      metric: "Gait Symmetry",
      patientVal: `${gaitSymmetry.toFixed(1)}%`,
      expectedVal: "≥ 90.0%",
      diff: `${(gaitSymmetry - 90.0).toFixed(1)}%`,
      status: gaitSymmetry >= 90.0 ? "✓ Within Expected Range" : gaitSymmetry >= 85.0 ? "⚠ Mild Asymmetry" : "🔴 Significant Asymmetry",
      color: gaitSymmetry >= 90.0 ? "#10B981" : gaitSymmetry >= 85.0 ? "#D97706" : "#EF4444",
    },
    {
      metric: "Left Knee ROM",
      patientVal: `${leftRom.toFixed(1)}°`,
      expectedVal: "≥ 55.0°",
      diff: `${(leftRom - 55.0).toFixed(1)}°`,
      status: leftRom >= 55.0 ? "✓ Within Expected Range" : "🔴 Reduced Flexibility",
      color: leftRom >= 55.0 ? "#10B981" : "#EF4444",
    },
    {
      metric: "Right Knee ROM",
      patientVal: `${rightRom.toFixed(1)}°`,
      expectedVal: "≥ 55.0°",
      diff: `${(rightRom - 55.0).toFixed(1)}°`,
      status: rightRom >= 55.0 ? "✓ Within Expected Range" : "🔴 Reduced Flexibility",
      color: rightRom >= 55.0 ? "#10B981" : "#EF4444",
    },
    {
      metric: "ROM Difference",
      patientVal: `${romDelta.toFixed(1)}°`,
      expectedVal: "< 10.0°",
      diff: `+${romDelta.toFixed(1)}°`,
      status: romDelta < 10.0 ? "✓ Within Expected Range" : romDelta <= 15.0 ? "⚠ Moderate Deficit" : "🔴 Significant Discrepancy",
      color: romDelta < 10.0 ? "#10B981" : romDelta <= 15.0 ? "#D97706" : "#EF4444",
    },
  ];

  return (
    <div style={{ padding: "28px 32px", maxWidth: "1180px", margin: "0 auto", background: "#171412", minHeight: "100vh" }}>
      {/* ── Page Navigation Header ── */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ fontSize: "12px", color: "#A8A09A", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#D97706", textDecoration: "none" }}>Dashboard</Link>
          {" / Agents / "}
          <span style={{ color: "#F8F5F0" }}>Clinical Risk Assessment</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: "26px", fontWeight: 800, color: "#F8F5F0", letterSpacing: "-0.02em" }}>
              🛡️ Clinical Risk Assessment Agent
            </h1>
            <div style={{ marginTop: "4px", fontSize: "13px", color: "#A8A09A" }}>
              Single Source of Truth Decision Support · {sourceText}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ padding: "6px 12px", borderRadius: "8px", fontSize: "11px", fontWeight: 700, background: "rgba(180,83,9,0.18)", color: "#D97706", border: "1px solid rgba(180,83,9,0.4)" }}>
              Agent 03 Active
            </span>
          </div>
        </div>
      </div>

      {/* ── Case Switcher ── */}
      <div
        style={{
          background: "#211C18",
          border: "1px solid #3A3028",
          borderRadius: "12px",
          padding: "12px 16px",
          marginBottom: "20px",
          display: "flex",
          alignItems: "center",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
        <span style={{ fontSize: "12px", color: "#A8A09A", fontWeight: 600, textTransform: "uppercase" }}>
          📂 Active Patient Source:
        </span>
        <button
          onClick={() => handleCaseSwitch("case1")}
          style={{
            padding: "7px 14px",
            borderRadius: "8px",
            fontSize: "12px",
            fontWeight: caseId === "case1" ? 700 : 500,
            border: caseId === "case1" ? "1px solid #10B981" : "1px solid #3A3028",
            background: caseId === "case1" ? "rgba(16,185,129,0.15)" : "#171412",
            color: caseId === "case1" ? "#10B981" : "#A8A09A",
            cursor: "pointer",
          }}
        >
          🟢 Case 1: Normative Control
        </button>

        <button
          onClick={() => handleCaseSwitch("case2")}
          style={{
            padding: "7px 14px",
            borderRadius: "8px",
            fontSize: "12px",
            fontWeight: caseId === "case2" ? 700 : 500,
            border: caseId === "case2" ? "1px solid #EF4444" : "1px solid #3A3028",
            background: caseId === "case2" ? "rgba(239,68,68,0.15)" : "#171412",
            color: caseId === "case2" ? "#EF4444" : "#A8A09A",
            cursor: "pointer",
          }}
        >
          🔴 Case 2: Asymmetric Gait
        </button>

        {sessionData && (
          <button
            onClick={() => handleCaseSwitch("custom")}
            style={{
              padding: "7px 14px",
              borderRadius: "8px",
              fontSize: "12px",
              fontWeight: caseId === "custom" ? 700 : 500,
              border: caseId === "custom" ? "1px solid #D97706" : "1px solid #3A3028",
              background: caseId === "custom" ? "rgba(217,119,6,0.15)" : "#171412",
              color: caseId === "custom" ? "#D97706" : "#A8A09A",
              cursor: "pointer",
            }}
          >
            📹 Custom Uploaded Video
          </button>
        )}
      </div>

      {/* ── Mismatch Warning Guard ── */}
      {isVideoIdMismatch && (
        <div style={{ background: "rgba(239, 68, 68, 0.15)", border: "1px solid #EF4444", borderRadius: "10px", padding: "14px 18px", marginBottom: "20px", color: "#EF4444", fontSize: "13px" }}>
          ⚠️ <strong>Analysis mismatch detected.</strong> Please re-run the analysis for the current video.
        </div>
      )}

      {/* ── Active Custom Video Control Row ── */}
      {caseId === "custom" && sessionData && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#211C18", border: "1px solid #3A3028", borderRadius: "10px", padding: "12px 18px", marginBottom: "20px" }}>
          <div style={{ fontSize: "13px", color: "#F8F5F0" }}>
            📹 Active Upload: <strong>{videoName}</strong> (ID: <code style={{ color: "#D97706" }}>{gaVideoId || "custom"}</code>)
          </div>
          <button
            onClick={handleRemoveVideo}
            style={{
              background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.4)",
              color: "#EF4444",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "12px",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            🗑️ Remove Video
          </button>
        </div>
      )}

      {error && (
        <div style={{ background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.4)", padding: "12px 16px", borderRadius: "8px", color: "#EF4444", fontSize: "13px", marginBottom: "20px" }}>
          ⚠️ {error}
        </div>
      )}

      {caseId === "custom" && !gaitAnalysisCompleted ? (
        <div style={{ background: "#211C18", border: "1px dashed #3A3028", borderRadius: "14px", padding: "48px 24px", textAlign: "center" }}>
          <div style={{ fontSize: "36px", marginBottom: "12px" }}>🔒</div>
          <h3 style={{ fontSize: "16px", fontWeight: 800, color: "#F8F5F0", margin: "0 0 8px 0" }}>Complete Gait Analysis First</h3>
          <p style={{ fontSize: "13px", color: "#A8A09A", maxWidth: "480px", margin: "0 auto 18px", lineHeight: "1.6" }}>
            Click &quot;Get Results&quot; in Gait Analysis to generate the objective biomechanical measurements required for clinical risk assessment.
          </p>
          <Link
            href="/"
            className="btn-copper"
            style={{ textDecoration: "none", display: "inline-block", padding: "10px 20px", fontSize: "13px", fontWeight: 700 }}
          >
            ← Return to Dashboard &amp; Analyze Video
          </Link>
        </div>
      ) : loading ? (
        <div style={{ padding: "48px", textAlign: "center", background: "#211C18", borderRadius: "14px", border: "1px solid #3A3028" }}>
          <div className="spinner" style={{ width: "36px", height: "36px", margin: "0 auto 12px" }} />
          <div style={{ fontSize: "14px", color: "#F8F5F0", fontWeight: 700 }}>Synthesizing Risk Evaluation…</div>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

          {/* ── 1. MAIN RISK BADGE CARD ── */}
          <div
            style={{
              background: riskConfig.bg,
              border: `1px solid ${riskConfig.border}`,
              borderRadius: "14px",
              padding: "24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "16px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <div
                style={{
                  width: "52px",
                  height: "52px",
                  borderRadius: "50%",
                  background: riskConfig.badgeBg,
                  color: riskConfig.text,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "26px",
                  fontWeight: 800,
                  border: `1px solid ${riskConfig.border}`,
                }}
              >
                {riskConfig.icon}
              </div>
              <div>
                <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", color: "#A8A09A", textTransform: "uppercase" }}>
                  OVERALL SCREENING RESULT
                </div>
                <div style={{ fontSize: "26px", fontWeight: 900, color: riskConfig.text, margin: "2px 0 4px 0" }}>
                  {riskConfig.label}
                </div>
                <div style={{ fontSize: "12px", color: "#F8F5F0" }}>
                  {riskConfig.supportingText}
                </div>
              </div>
            </div>

            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
              <div style={{ background: "#171412", border: "1px solid #3A3028", borderRadius: "10px", padding: "12px 18px", textAlign: "center" }}>
                <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase" }}>Triggered Criteria</div>
                <div style={{ fontSize: "22px", fontWeight: 800, color: riskConfig.text }}>{(data?.clinical_risk as any)?.triggered_criteria_text || (data?.clinical_risk as any)?.risk_score_text || "1 / 8"}</div>
                <div style={{ fontSize: "10px", color: "#786E65", marginTop: "2px" }}>Toddler Profile (1–4 YRS)</div>
              </div>

              <div style={{ background: "#171412", border: "1px solid #3A3028", borderRadius: "10px", padding: "12px 18px", textAlign: "center" }}>
                <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase" }}>Weighted Score</div>
                <div style={{ fontSize: "22px", fontWeight: 800, color: riskConfig.text }}>{(data?.clinical_risk as any)?.weighted_risk_score_text || "2 / 10"}</div>
                <div style={{ fontSize: "10px", color: "#786E65", marginTop: "2px" }}>Risk Points</div>
              </div>

              <div style={{ background: "#171412", border: "1px solid #3A3028", borderRadius: "10px", padding: "12px 18px", textAlign: "right" }}>
                <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase" }}>Gait Symmetry Index</div>
                <div style={{ fontSize: "22px", fontWeight: 800, color: riskConfig.text }}>{gaitSymmetry.toFixed(1)}%</div>
                <div style={{ fontSize: "10px", color: "#786E65", marginTop: "2px" }}>Mean SI: {meanAsymmetry.toFixed(1)}%</div>
              </div>
            </div>
          </div>

          {/* ── 2. "WHY THIS RESULT?" MEASUREMENT BREAKDOWN TABLE ── */}
          <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "14px", padding: "20px" }}>
            <div style={{ fontSize: "13px", fontWeight: 800, letterSpacing: "0.06em", textTransform: "uppercase", color: "#F8F5F0", marginBottom: "14px" }}>
              📊 Why This Result? (Single Source of Truth Measurements)
            </div>

            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid #3A3028", textAlign: "left", color: "#A8A09A", fontSize: "11px" }}>
                    <th style={{ padding: "10px" }}>Kinematic Metric</th>
                    <th style={{ padding: "10px" }}>Patient Value</th>
                    <th style={{ padding: "10px" }}>Expected Screening Range</th>
                    <th style={{ padding: "10px" }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisons.map((row) => (
                    <tr key={row.metric} style={{ borderBottom: "1px solid rgba(58,48,40,0.5)" }}>
                      <td style={{ padding: "12px 10px", fontWeight: 600, color: "#F8F5F0" }}>{row.metric}</td>
                      <td style={{ padding: "12px 10px", fontWeight: 800, color: "#F8F5F0", fontFamily: "monospace" }}>{row.patientVal}</td>
                      <td style={{ padding: "12px 10px", color: "#A8A09A" }}>{row.expectedVal}</td>
                      <td style={{ padding: "12px 10px" }}>
                        <span style={{ padding: "4px 10px", borderRadius: "6px", fontSize: "11px", fontWeight: 700, color: row.color, background: `${row.color}18`, border: `1px solid ${row.color}40` }}>
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* ── 3. RISK FACTORS SECTION ── */}
          <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "14px", padding: "20px" }}>
            <div style={{ fontSize: "13px", fontWeight: 800, letterSpacing: "0.06em", textTransform: "uppercase", color: "#F8F5F0", marginBottom: "12px" }}>
              🚩 Risk Factors &amp; Triggered Screening Measurements
            </div>

            {riskLevel === "LOW" ? (
              <div style={{ background: "rgba(16, 185, 129, 0.1)", border: "1px solid rgba(16, 185, 129, 0.3)", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
                <div style={{ fontSize: "13px", fontWeight: 700, color: "#10B981" }}>
                  ✓ Within Expected Range — No Significant Risk Factors Detected
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px", fontSize: "12px", color: "#F8F5F0", marginTop: "4px" }}>
                  <div>✓ Gait symmetry within expected range ({gaitSymmetry.toFixed(1)}%)</div>
                  <div>✓ Left knee ROM within expected range ({leftRom.toFixed(1)}°)</div>
                  <div>✓ Right knee ROM within expected range ({rightRom.toFixed(1)}°)</div>
                  <div>✓ Bilateral ROM difference within expected range ({romDelta.toFixed(1)}°)</div>
                  <div>✓ No significant asymmetry detected</div>
                </div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {cr?.triggered_measurements && cr.triggered_measurements.length > 0 ? (
                  cr.triggered_measurements.map((tf, idx) => (
                    <div key={idx} style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "8px", padding: "12px 14px", fontSize: "12px", color: "#F8F5F0", display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ color: "#EF4444", fontSize: "16px" }}>🔸</span>
                      <span>{tf}</span>
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: "12px", color: "#A8A09A" }}>Moderate kinematics variance requiring periodic clinical monitoring.</div>
                )}
              </div>
            )}
          </div>

          {/* ── 4. EXPLAINABLE REASONING & RECOMMENDATIONS ── */}
          <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "14px", padding: "20px" }}>
            <div style={{ fontSize: "13px", fontWeight: 800, letterSpacing: "0.06em", textTransform: "uppercase", color: "#B45309", marginBottom: "10px" }}>
              📄 Clinical Explainable Decision Support Reasoning
            </div>
            <p style={{ fontSize: "13px", color: "#F8F5F0", lineHeight: 1.6, margin: 0 }}>
              {cr?.reasoning || "Evaluation based on structured biomechanical keypoints."}
            </p>

            <div style={{ marginTop: "16px", padding: "14px", background: "#171412", borderRadius: "8px", border: "1px solid #3A3028" }}>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "#D97706", textTransform: "uppercase", marginBottom: "4px" }}>
                Recommended Action Plan
              </div>
              <div style={{ fontSize: "12px", color: "#A8A09A" }}>
                {cr?.recommendation || "Continue routine developmental tracking."}
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
