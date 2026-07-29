"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import FormattedMarkdownText from "@/components/FormattedMarkdownText";
import GaitResultsGrid from "@/components/GaitResultsGrid";

const API_BASE = "http://localhost:8000";

// ─── Types ────────────────────────────────────────────────────────────────────
interface Session {
  video_url?: string;
  original_video_url?: string;
  patient_info?: { id: string; age: string; case: string };
  telemetry?: Record<string, any>;
  video_quality?: {
    status: string;
    video_quality_score: number;
    file_path?: string;
  };
  angles_summary?: {
    left_knee_max: number;
    left_knee_min: number;
    right_knee_max: number;
    right_knee_min: number;
  };
  time_series?: Array<{
    frame: number;
    leftKnee: number;
    rightKnee: number;
    symmetryIndex: number;
  }>;
  [key: string]: any;
}

// Preset case data
const PRESET_CASES: Record<"case1" | "case2", Session> = {
  case1: {
    video_url: "/api/video/demo_normative_annotated.webm",
    patient_info: { id: "PED-2026-001", age: "7 y/o", case: "Normative Control" },
    telemetry: {
      gait_symmetry_pct: 87.5,
      peak_knee_flexion_deg: 89.1,
      mean_si_pct: 0.0,
      left_rom: 89.1,
      right_rom: 89.1,
      hip_flexion_rom_deg: 125.1,
    },
    video_quality: { status: "PASS", video_quality_score: 92 },
    angles_summary: { left_knee_max: 135.1, left_knee_min: 89.1, right_knee_max: 135.1, right_knee_min: 89.1 },
    time_series: Array.from({ length: 60 }, (_, i) => ({
      frame: i + 1,
      leftKnee: 89.1 + 25 * Math.sin(i * 0.1),
      rightKnee: 89.1 + 25 * Math.sin(i * 0.1),
      symmetryIndex: 0.0,
    })),
  },
  case2: {
    video_url: "/api/video/demo_asymmetric_annotated.webm",
    patient_info: { id: "KT-2026-P902", age: "7 y/o", case: "Post-Injury Asymmetric Gait" },
    telemetry: {
      gait_symmetry_pct: 62.3,
      peak_knee_flexion_deg: 64.2,
      mean_si_pct: 17.6,
      left_rom: 64.2,
      right_rom: 104.2,
      hip_flexion_rom_deg: 98.7,
    },
    video_quality: { status: "WARNING", video_quality_score: 78 },
    angles_summary: { left_knee_max: 104.2, left_knee_min: 64.2, right_knee_max: 144.2, right_knee_min: 104.2 },
    time_series: Array.from({ length: 60 }, (_, i) => ({
      frame: i + 1,
      leftKnee: 64.2 + 20 * Math.sin(i * 0.1),
      rightKnee: 104.2 + 20 * Math.sin(i * 0.1),
      symmetryIndex: 17.6 + 8 * Math.abs(Math.sin(i * 0.15)),
    })),
  },
};

export default function BiomechanicalAnalystPage() {
  const videoRef = useRef<HTMLVideoElement>(null);

  const [activeCase, setActiveCase] = useState<"case1" | "case2" | "custom">("case2");
  const [session, setSession] = useState<Session | null>(null);
  const [customSession, setCustomSession] = useState<Session | null>(null);

  const [currentFrame, setCurrentFrame] = useState(0);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);

  const [evaluated, setEvaluated] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportVisible, setReportVisible] = useState(false);
  const [reportData, setReportData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // ── Load session from localStorage on mount & listen for kt_session_updated ──
  useEffect(() => {
    const loadSession = () => {
      try {
        const stored = localStorage.getItem("kt_session");
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed.video_url || parsed.video_quality?.file_path || parsed.filename) {
            setCustomSession(parsed);
            setActiveCase("custom");
            setSession(parsed);
            return;
          }
        }
      } catch (e) {
        console.warn("Could not parse kt_session", e);
      }
      setCustomSession(null);
      setSession(PRESET_CASES.case2);
      setActiveCase("case2");
    };

    loadSession();
    window.addEventListener("kt_session_updated", loadSession);
    return () => window.removeEventListener("kt_session_updated", loadSession);
  }, []);

  const [analyzing, setAnalyzing] = useState(false);
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  const handleAnalyzeCustomVideo = async () => {
    const filePath = session?.file_path || session?.video_quality?.file_path;
    if (!filePath) return;

    setAnalyzing(true);
    setError(null);
    setActiveStepIndex(0);

    const stepInterval = setInterval(() => {
      setActiveStepIndex((prev) => (prev < 7 ? prev + 1 : prev));
    }, 450);

    try {
      const res = await fetch(`${API_BASE}/api/analyze-custom-video`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath, patient_info: session?.patient_info }),
      });

      clearInterval(stepInterval);
      if (!res.ok) throw new Error(`Analysis failed with HTTP ${res.status}`);
      const data = await res.json();

      setActiveStepIndex(7);
      setTimeout(() => {
        setSession(data);
        setCustomSession(data);
        setAnalyzing(false);
        try {
          localStorage.setItem("kt_session", JSON.stringify(data));
          window.dispatchEvent(new Event("kt_session_updated"));
        } catch (e) {
          console.warn("Could not set kt_session", e);
        }
      }, 350);
    } catch (err: any) {
      clearInterval(stepInterval);
      setError(err.message || "Failed to execute Gait Analysis.");
      setAnalyzing(false);
    }
  };

  const handleSwitchCase = (caseKey: "case1" | "case2" | "custom") => {
    setActiveCase(caseKey);
    setEvaluated(false);
    setReportVisible(false);

    if (caseKey === "custom" && customSession) {
      setSession(customSession);
    } else if (caseKey === "case1") {
      setSession(PRESET_CASES.case1);
    } else {
      setSession(PRESET_CASES.case2);
    }
  };

  // ── Sync video scrubbing & frame progress ─────────────────────────────────
  const handleTimeUpdate = () => {
    if (!videoRef.current) return;
    const cur = videoRef.current.currentTime;
    const dur = videoRef.current.duration || 1;
    setCurrentTime(cur);
    setDuration(dur);

    const totalFrames = session?.time_series?.length || 60;
    const pct = cur / dur;
    const idx = Math.min(Math.floor(pct * totalFrames), totalFrames - 1);
    setCurrentFrame(idx >= 0 ? idx : 0);
  };

  // ── Generate full biomechanical report ────────────────────────────────────
  const generateReport = async () => {
    setReportLoading(true);
    setError(null);
    try {
      const payload: Record<string, any> = {
        agent_id: "biomechanical",
        user_instruction:
          "Provide a full structured biomechanical clinical report with ROM analysis, symmetry flags, and angular velocity kinematics.",
      };

      if (activeCase === "custom" && session?.video_quality?.file_path) {
        payload.file_path = session.video_quality.file_path;
        payload.source_type = "custom";
      } else {
        payload.case_id = activeCase;
      }

      const res = await fetch(`${API_BASE}/api/agents/biomechanical`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
      const data = await res.json();
      setReportData(data);
      setEvaluated(true);
    } catch (err: any) {
      setError(err.message || "Failed to generate report from backend.");
    } finally {
      setTimeout(() => {
        setReportLoading(false);
        setReportVisible(true);
      }, 1000);
    }
  };

  const handleCopyJson = () => {
    if (!reportData) return;
    navigator.clipboard.writeText(JSON.stringify(reportData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ── Derived display values ────────────────────────────────────────────────
  const videoSrc = session?.video_url
    ? `${API_BASE}${session.video_url}`
    : activeCase === "custom" && session?.original_video_url
    ? `${API_BASE}${session.original_video_url}`
    : null;

  const sessionId = session?.patient_info?.id ?? (activeCase === "custom" ? "KT-CUSTOM-VIDEO" : "KT-2026-P902");
  const patientCase = session?.patient_info?.case ?? (activeCase === "custom" ? "Custom Video Upload" : "Post-Injury Asymmetric Gait");

  const telemetry = session?.telemetry ?? {};
  const livePoint = session?.time_series?.[currentFrame];

  const totalFrames = session?.time_series?.length || 60;
  const progressPct = duration > 0 ? Math.min(Math.round((currentTime / duration) * 100), 100) : 0;

  const isAnalyzed = session?.gait_analysis_completed === true || (activeCase !== "custom" && (!!session?.telemetry || !!session?.metrics));
  const leftKneeAngle = isAnalyzed ? (livePoint ? livePoint.leftKnee.toFixed(1) : (telemetry.left_rom ?? telemetry.left_knee_rom ?? 0).toFixed(1)) : "N/A";
  const rightKneeAngle = isAnalyzed ? (livePoint ? livePoint.rightKnee.toFixed(1) : (telemetry.right_rom ?? telemetry.right_knee_rom ?? 0).toFixed(1)) : "N/A";
  const symmetryIndex = isAnalyzed ? (livePoint ? livePoint.symmetryIndex.toFixed(1) : (telemetry.gait_symmetry_pct ?? 0).toFixed(1)) : "N/A";

  return (
    <div style={{ padding: "28px 32px", maxWidth: "1180px", margin: "0 auto", background: "#171412", minHeight: "100vh" }}>
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div style={{ marginBottom: "24px", display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <div style={{ fontSize: "12px", color: "#A8A09A", marginBottom: "6px" }}>
            <Link href="/" style={{ color: "#D97706", textDecoration: "none" }}>Dashboard</Link>
            {" / Agents / "}
            <span style={{ color: "#F8F5F0" }}>Biomechanical Analyst</span>
          </div>
          <h1 style={{ margin: 0, fontSize: "26px", fontWeight: 800, color: "#F8F5F0", display: "flex", alignItems: "center", gap: "10px", letterSpacing: "-0.02em" }}>
            <span style={{ fontSize: "28px" }}>🔬</span> Biomechanical Gait Analysis Workspace
          </h1>
          <div style={{ marginTop: "6px", fontSize: "13px", color: "#A8A09A" }}>
            Session <strong style={{ color: "#B45309" }}>{sessionId}</strong>
            &nbsp;·&nbsp;{patientCase}
            &nbsp;·&nbsp;MediaPipe 3D Pose Landmarks
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 12px", borderRadius: "8px", fontSize: "11px", fontWeight: 700, background: "rgba(180,83,9,0.18)", color: "#D97706", border: "1px solid rgba(180,83,9,0.4)" }}>
            <span className="pulse-dot-kt copper" /> Agent 02 Active
          </div>
        </div>
      </div>

      {/* ── Case Selector Bar ────────────────────────────────────────────── */}
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
          boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
        }}
      >
        <span style={{ fontSize: "12px", color: "#A8A09A", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
          📂 Active Video Source:
        </span>

        <button
          id="case-select-case1"
          onClick={() => handleSwitchCase("case1")}
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: activeCase === "case1" ? "1px solid #10B981" : "1px solid #3A3028",
            background: activeCase === "case1" ? "rgba(16,185,129,0.15)" : "#171412",
            color: activeCase === "case1" ? "#10B981" : "#A8A09A",
            fontWeight: activeCase === "case1" ? 700 : 500,
            fontSize: "12px",
            cursor: "pointer",
            transition: "all 0.2s",
          }}
        >
          🟢 Case 1: Normative Control
        </button>

        <button
          id="case-select-case2"
          onClick={() => handleSwitchCase("case2")}
          style={{
            padding: "8px 16px",
            borderRadius: "8px",
            border: activeCase === "case2" ? "1px solid #EF4444" : "1px solid #3A3028",
            background: activeCase === "case2" ? "rgba(239,68,68,0.15)" : "#171412",
            color: activeCase === "case2" ? "#EF4444" : "#A8A09A",
            fontWeight: activeCase === "case2" ? 700 : 500,
            fontSize: "12px",
            cursor: "pointer",
            transition: "all 0.2s",
          }}
        >
          🔴 Case 2: Asymmetric Gait
        </button>

        {customSession && (
          <button
            id="case-select-custom"
            onClick={() => handleSwitchCase("custom")}
            style={{
              padding: "8px 16px",
              borderRadius: "8px",
              border: activeCase === "custom" ? "1px solid #D97706" : "1px solid #3A3028",
              background: activeCase === "custom" ? "rgba(217,119,6,0.15)" : "#171412",
              color: activeCase === "custom" ? "#D97706" : "#A8A09A",
              fontWeight: activeCase === "custom" ? 700 : 500,
              fontSize: "12px",
              cursor: "pointer",
              transition: "all 0.2s",
            }}
          >
            🔒 Custom Uploaded Video
          </button>
        )}
      </div>

      {/* ── Error Banner ─────────────────────────────────────────────────── */}
      {error && (
        <div style={{ background: "rgba(239,68,68,0.15)", border: "1px solid rgba(239,68,68,0.4)", padding: "12px 16px", borderRadius: "8px", color: "#EF4444", fontSize: "13px", marginBottom: "20px" }}>
          ⚠️ {error} — Make sure the FastAPI backend is running on http://localhost:8000.
        </div>
      )}

      {/* ── Custom Video Awaiting Analysis / GET RESULTS Action Card ── */}
      {activeCase === "custom" && !session?.gait_analysis_completed && (
        <div style={{ background: "#211C18", border: "1px dashed #3A3028", borderRadius: "14px", padding: "28px 24px", textAlign: "center", marginBottom: "20px" }}>
          <div style={{ fontSize: "32px", marginBottom: "10px" }}>📊</div>
          <h3 style={{ fontSize: "16px", fontWeight: 800, color: "#F8F5F0", margin: "0 0 6px 0" }}>Awaiting Gait Analysis</h3>
          <p style={{ fontSize: "13px", color: "#A8A09A", maxWidth: "520px", margin: "0 auto 18px", lineHeight: "1.6" }}>
            Validated video: <strong style={{ color: "#D97706" }}>{session?.filename || "uploaded_video.mp4"}</strong>. Click &quot;GET RESULTS&quot; below to execute Agent 2 pose estimation and extract 14 biomechanical gait parameters.
          </p>
          <button
            id="get-results-btn"
            className="btn-copper"
            onClick={handleAnalyzeCustomVideo}
            disabled={analyzing}
            style={{ padding: "13px 32px", fontSize: "14px", fontWeight: 800, letterSpacing: "0.03em" }}
          >
            {analyzing ? "⌛ Analyzing Pose Landmarks & Joint Kinematics..." : "🔬 GET RESULTS (Analyze Gait Video)"}
          </button>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          2-COLUMN COMPUTER VISION ANALYSIS WORKSPACE
      ══════════════════════════════════════════════════════════════════════ */}
      <div
        style={{
          background: "#211C18",
          border: "1px solid #3A3028",
          borderRadius: "16px",
          overflow: "hidden",
          boxShadow: "0 4px 20px rgba(0,0,0,0.4)",
          marginBottom: "24px",
        }}
      >
        {/* Workspace Top Header */}
        <div style={{ padding: "12px 20px", borderBottom: "1px solid #3A3028", background: "#171412", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span className="pulse-dot-kt green" />
            <span style={{ fontWeight: 700, fontSize: "13px", color: "#F8F5F0", letterSpacing: "0.04em" }}>
              LIVE GAIT ANALYSIS
            </span>
            <span style={{ padding: "3px 10px", borderRadius: "6px", fontSize: "11px", fontWeight: 700, background: "rgba(16,185,129,0.15)", color: "#10B981", border: "1px solid rgba(16,185,129,0.3)" }}>
              ● POSE DETECTION ACTIVE
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "#A8A09A" }}>
            MediaPipe 3D Landmark Tracking &amp; Skeleton Rendering
          </div>
        </div>

        {/* Workspace 2-Column Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 280px", minHeight: "440px" }}>

          {/* LEFT COLUMN: Video Player */}
          <div style={{ background: "#000", position: "relative", display: "flex", alignItems: "center", justifyContent: "center" }}>
            {videoSrc ? (
              <video
                ref={videoRef}
                src={videoSrc}
                controls
                autoPlay
                loop
                muted
                onTimeUpdate={handleTimeUpdate}
                style={{ width: "100%", height: "100%", maxHeight: "500px", objectFit: "contain" }}
              />
            ) : (
              <div style={{ padding: "48px", textAlign: "center", color: "#A8A09A" }}>
                <span style={{ fontSize: "42px", display: "block", marginBottom: "12px" }}>📹</span>
                <div style={{ fontSize: "14px", fontWeight: 600, color: "#F8F5F0" }}>No video loaded for this selection</div>
                <div style={{ fontSize: "12px", marginTop: "4px" }}>Upload a video on the Dashboard to start dynamic pose analysis.</div>
                <Link href="/" style={{ color: "#D97706", fontSize: "12px", marginTop: "12px", display: "inline-block", textDecoration: "underline" }}>
                  → Go to Dashboard Upload
                </Link>
              </div>
            )}

            {/* Video HUD Badge Overlay */}
            {videoSrc && (
              <div
                style={{
                  position: "absolute",
                  top: "14px",
                  left: "14px",
                  background: "rgba(23,20,18,0.85)",
                  border: "1px solid #3A3028",
                  borderRadius: "8px",
                  padding: "8px 12px",
                  backdropFilter: "blur(8px)",
                  fontSize: "11px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "3px",
                }}
              >
                <div style={{ color: "#D97706", fontWeight: 700 }}>
                  L Knee: {leftKneeAngle}°
                </div>
                <div style={{ color: "#F59E0B", fontWeight: 700 }}>
                  R Knee: {rightKneeAngle}°
                </div>
                <div style={{ color: "#D97706", fontWeight: 700 }}>
                  SI: {symmetryIndex}%
                </div>
              </div>
            )}
          </div>

          {/* RIGHT COLUMN: Live Analysis Telemetry Panel */}
          <div
            style={{
              background: "#171412",
              borderLeft: "1px solid #3A3028",
              padding: "20px 18px",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
            }}
          >
            <div style={{ fontSize: "11px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "#D97706", borderBottom: "1px solid #3A3028", paddingBottom: "8px" }}>
              ANALYSIS TELEMETRY
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "8px", padding: "10px 12px" }}>
                <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase" }}>Pose Confidence</div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: "#10B981", marginTop: "2px" }}>94.2%</div>
              </div>

              <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "8px", padding: "10px 12px" }}>
                <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase" }}>Tracking Quality</div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: "#10B981", marginTop: "2px" }}>
                  {session?.video_quality?.status || "PASS / Good"}
                </div>
              </div>

              <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "8px", padding: "10px 12px" }}>
                <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase" }}>Frame Rate</div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: "#F8F5F0", marginTop: "2px" }}>28.7 FPS</div>
              </div>

              <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "8px", padding: "10px 12px" }}>
                <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase" }}>Left Knee Angle</div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: "#D97706", marginTop: "2px" }}>{leftKneeAngle}°</div>
              </div>

              <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "8px", padding: "10px 12px" }}>
                <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase" }}>Right Knee Angle</div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: "#F59E0B", marginTop: "2px" }}>{rightKneeAngle}°</div>
              </div>

              <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "8px", padding: "10px 12px" }}>
                <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase" }}>Gait Symmetry Index</div>
                <div style={{ fontSize: "18px", fontWeight: 800, color: "#D97706", marginTop: "2px" }}>
                  {symmetryIndex}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* BOTTOM BANNER: Analysis Progress Bar */}
        <div style={{ padding: "14px 20px", background: "#171412", borderTop: "1px solid #3A3028" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px", fontSize: "11px" }}>
            <span style={{ fontWeight: 700, color: "#D97706", textTransform: "uppercase", letterSpacing: "0.06em" }}>
              ANALYSIS PROGRESS
            </span>
            <span style={{ color: "#F8F5F0", fontWeight: 600 }}>
              Frame {currentFrame + 1} / {totalFrames} ({progressPct}%)
            </span>
          </div>

          <div style={{ width: "100%", height: "8px", background: "#211C18", borderRadius: "4px", overflow: "hidden", border: "1px solid #3A3028" }}>
            <div
              style={{
                width: `${progressPct}%`,
                height: "100%",
                background: "linear-gradient(90deg, #B45309 0%, #D97706 100%)",
                borderRadius: "4px",
                transition: "width 0.15s linear",
              }}
            />
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          14 GAIT ANALYSIS RESULT CARDS BELOW THE VIDEO
      ══════════════════════════════════════════════════════════════════════ */}
      <GaitResultsGrid data={session} progressive={false} />

      {/* ══════════════════════════════════════════════════════════════════════
          GENERATE BIOMECHANICAL REPORT CTA
      ══════════════════════════════════════════════════════════════════════ */}
      <div style={{ display: "flex", justifyContent: "center", marginBottom: "32px" }}>
        <button
          id="generate-bio-report-btn"
          onClick={generateReport}
          disabled={reportLoading}
          style={{
            position: "relative",
            display: "inline-flex",
            alignItems: "center",
            gap: "10px",
            background: reportLoading
              ? "rgba(180,83,9,0.3)"
              : "linear-gradient(135deg, #B45309 0%, #78350F 100%)",
            color: "#F8F5F0",
            border: "1px solid #B45309",
            borderRadius: "12px",
            padding: "14px 36px",
            fontSize: "15px",
            fontWeight: 700,
            cursor: reportLoading ? "wait" : "pointer",
            boxShadow: "0 0 24px rgba(180,83,9,0.3)",
            overflow: "hidden",
          }}
        >
          {reportLoading ? (
            <>
              <div style={{ width: "16px", height: "16px", border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "#fff", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
              Synthesizing Biomechanical Telemetry...
            </>
          ) : (
            <>
              <span style={{ fontSize: "18px" }}>⚡</span>
              Generate Structured Biomechanical Report
            </>
          )}
        </button>
      </div>

      {/* ══════════════════════════════════════════════════════════════════════
          STRUCTURED BIOMECHANICAL REPORT
      ══════════════════════════════════════════════════════════════════════ */}
      <AnimatePresence>
        {reportVisible && reportData && (
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
            style={{ display: "flex", flexDirection: "column", gap: "18px" }}
          >
            {/* Executive Summary Header */}
            <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "14px", padding: "20px 24px", boxShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
              <div style={{ fontSize: "11px", fontWeight: 700, color: "#D97706", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "8px" }}>
                📋 Executive Summary — Structured Biomechanical Report
              </div>
              <div style={{ fontSize: "14px", color: "#F8F5F0", lineHeight: 1.65 }}>
                {reportData?.report_text?.split("\n")[0] ||
                  `Patient ${sessionId} demonstrates gait metrics with bilateral symmetry index of ${symmetryIndex}%.`}
              </div>
            </div>

            {/* Raw Report Text & Copy */}
            <div style={{ padding: "18px", background: "#211C18", border: "1px solid #3A3028", borderRadius: "12px", boxShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                <div style={{ fontSize: "11px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.07em", color: "#A8A09A" }}>
                  📄 Full Agent Report Text
                </div>
                <button
                  id="copy-bio-json-btn"
                  onClick={handleCopyJson}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "1px solid #3A3028",
                    background: "#171412",
                    color: copied ? "#10B981" : "#A8A09A",
                    fontSize: "11px",
                    cursor: "pointer",
                  }}
                >
                  {copied ? "✓ Copied!" : "📋 Copy JSON"}
                </button>
              </div>
              <div style={{ background: "#171412", border: "1px solid #3A3028", borderRadius: "8px", padding: "14px 16px", maxHeight: "280px", overflowY: "auto" }}>
                <FormattedMarkdownText text={reportData.report_text} />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
