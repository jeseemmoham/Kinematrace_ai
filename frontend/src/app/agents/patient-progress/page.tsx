"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Cell,
} from "recharts";

const API_BASE = "http://localhost:8000";

interface GaitComparisonResult {
  comparison_status: "COMPLETED" | "FAILED";
  overall_progress: "IMPROVED" | "STABLE" | "WORSENED";
  score: number;
  old_video: {
    file_name: string;
    video_url: string;
    gait_asymmetry: number;
    left_knee_max_flexion: number;
    right_knee_max_flexion: number;
    left_rom: number;
    right_rom: number;
    rom_deficit_deg: number;
    risk_level: string;
    quality_status: string;
    quality_score: number;
  };
  new_video: {
    file_name: string;
    video_url: string;
    gait_asymmetry: number;
    left_knee_max_flexion: number;
    right_knee_max_flexion: number;
    left_rom: number;
    right_rom: number;
    rom_deficit_deg: number;
    risk_level: string;
    quality_status: string;
    quality_score: number;
  };
  comparison: {
    asymmetry_change: number;
    left_knee_max_flexion_change: number;
    right_knee_max_flexion_change: number;
    left_rom_change: number;
    right_rom_change: number;
    rom_deficit_change: number;
    risk_change?: string;
  };
  key_findings: string[];
  summary: string;
  recommendation: string;
  comparability_warning?: string;
  stability_threshold_used: number;
  message?: string;
}

const PROGRESS_PALETTE = {
  IMPROVED: {
    bg: "rgba(16, 185, 129, 0.12)",
    border: "rgba(16, 185, 129, 0.4)",
    text: "#10B981",
    badge: "rgba(16, 185, 129, 0.2)",
    emoji: "🟢",
    label: "IMPROVED",
    subtitle: "Gait asymmetry and movement symmetry show positive objective progress.",
  },
  STABLE: {
    bg: "rgba(217, 119, 6, 0.12)",
    border: "rgba(217, 119, 6, 0.4)",
    text: "#D97706",
    badge: "rgba(217, 119, 6, 0.2)",
    emoji: "🔵",
    label: "STABLE",
    subtitle: "No significant kinematic variation detected between assessments.",
  },
  WORSENED: {
    bg: "#3A1F1A",
    border: "#B45309",
    text: "#EF4444",
    badge: "rgba(239, 68, 68, 0.2)",
    emoji: "🔴",
    label: "WORSENED",
    subtitle: "Gait asymmetry or ROM deficit increased compared to previous assessment.",
  },
};

// ─── Metric Tile Helper ───────────────────────────────────────────────────────
function MetricTile({
  label,
  valOld,
  valNew,
  deltaStr,
  deltaGood,
}: {
  label: string;
  valOld: string;
  valNew: string;
  deltaStr: string;
  deltaGood?: boolean | null;
}) {
  const deltaColor =
    deltaGood === true ? "#10B981" : deltaGood === false ? "#EF4444" : "#A8A09A";

  return (
    <div
      style={{
        background: "#211C18",
        border: "1px solid #3A3028",
        borderRadius: "12px",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
      }}
    >
      <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700 }}>
        {label}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "2px" }}>
        <span style={{ fontSize: "12px", color: "#A8A09A", textDecoration: "line-through" }}>{valOld}</span>
        <span style={{ fontSize: "20px", fontWeight: 800, color: "#F8F5F0" }}>➔ {valNew}</span>
      </div>
      <div style={{ fontSize: "11px", fontWeight: 700, color: deltaColor, marginTop: "2px" }}>
        {deltaStr}
      </div>
    </div>
  );
}

export default function GaitProgressComparisonPage() {
  const [mode, setMode] = useState<"preset" | "upload">("preset");

  // Preset state
  const [oldCaseId, setOldCaseId] = useState<string>("case2");
  const [newCaseId, setNewCaseId] = useState<string>("case1");

  // Upload files state
  const [oldFile, setOldFile] = useState<File | null>(null);
  const [newFile, setNewFile] = useState<File | null>(null);

  // Drag states
  const [dragOld, setDragOld] = useState(false);
  const [dragNew, setDragNew] = useState(false);

  // Processing state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<GaitComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const oldInputRef = useRef<HTMLInputElement>(null);
  const newInputRef = useRef<HTMLInputElement>(null);

  const handleRunComparison = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();

      if (mode === "upload") {
        if (!oldFile || !newFile) {
          setError("Please upload both Old Video and New Video before running comparison.");
          setLoading(false);
          return;
        }
        formData.append("old_video", oldFile);
        formData.append("new_video", newFile);
      } else {
        formData.append("old_case_id", oldCaseId);
        formData.append("new_case_id", newCaseId);
      }

      const res = await fetch(`${API_BASE}/api/compare-progress`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (!res.ok || data.comparison_status === "FAILED") {
        setError(data.message || "Gait progress comparison failed.");
        if (data.quality) {
          setResult(data);
        }
      } else {
        setResult(data);
        try {
          localStorage.setItem("kt_progress_session", JSON.stringify(data));
        } catch (e) {
          console.warn("Could not save kt_progress_session to localStorage", e);
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to communicate with FastAPI backend server.");
    } finally {
      setLoading(false);
    }
  }, [mode, oldFile, newFile, oldCaseId, newCaseId]);

  useEffect(() => {
    handleRunComparison();
  }, []);

  const overall = result?.overall_progress || "STABLE";
  const palette = PROGRESS_PALETTE[overall];

  const asymmetryChartData = result
    ? [
        { name: "Old Assessment", Asymmetry: result.old_video.gait_asymmetry, fill: "#D97706" },
        { name: "New Assessment", Asymmetry: result.new_video.gait_asymmetry, fill: "#10B981" },
      ]
    : [];

  const romChartData = result
    ? [
        {
          metric: "Left Knee ROM (°)",
          Old: result.old_video.left_rom,
          New: result.new_video.left_rom,
        },
        {
          metric: "Right Knee ROM (°)",
          Old: result.old_video.right_rom,
          New: result.new_video.right_rom,
        },
        {
          metric: "Left Peak Flex (°)",
          Old: result.old_video.left_knee_max_flexion,
          New: result.new_video.left_knee_max_flexion,
        },
        {
          metric: "Right Peak Flex (°)",
          Old: result.old_video.right_knee_max_flexion,
          New: result.new_video.right_knee_max_flexion,
        },
      ]
    : [];

  return (
    <div style={{ padding: "24px", maxWidth: "1280px", margin: "0 auto", background: "#171412", minHeight: "100vh" }}>
      {/* Breadcrumbs & Header */}
      <div style={{ marginBottom: "20px" }}>
        <div style={{ fontSize: "12px", color: "#A8A09A", marginBottom: "4px" }}>
          <Link href="/" style={{ color: "#D97706", textDecoration: "none" }}>
            Dashboard
          </Link>
          {" / Agents / "}
          <span style={{ color: "#F8F5F0" }}>Agent 4: Patient Gait Progress Comparison</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: "24px",
                fontWeight: 800,
                color: "#F8F5F0",
                display: "flex",
                alignItems: "center",
                gap: "10px",
              }}
            >
              <span>📊</span> Patient Gait Progress Comparison Workspace
            </h1>
            <div style={{ fontSize: "12px", color: "#A8A09A", marginTop: "4px" }}>
              Agent 4 · Objective Dual-Video Kinematic Comparison &amp; Longitudinal Progress Classifier
            </div>
          </div>

          {result && result.comparison_status !== "FAILED" && (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "8px 18px",
                borderRadius: "10px",
                background: palette.bg,
                border: `1px solid ${palette.border}`,
              }}
            >
              <span style={{ fontSize: "24px" }}>{palette.emoji}</span>
              <div>
                <div style={{ fontSize: "16px", fontWeight: 800, color: palette.text }}>
                  {palette.label}
                </div>
                <div style={{ fontSize: "11px", color: "#A8A09A" }}>
                  Asymmetry Δ: {result.comparison.asymmetry_change > 0 ? "+" : ""}
                  {result.comparison.asymmetry_change}%
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mode Selection & Inputs */}
      <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "12px", padding: "20px", marginBottom: "24px", boxShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px", flexWrap: "wrap", gap: "12px" }}>
          <div style={{ fontSize: "13px", fontWeight: 700, color: "#F8F5F0", display: "flex", alignItems: "center", gap: "8px" }}>
            <span>🎬</span> Select Assessment Videos to Compare
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={() => setMode("preset")}
              style={{
                padding: "6px 14px",
                borderRadius: "6px",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                border: mode === "preset" ? "1px solid #D97706" : "1px solid #3A3028",
                background: mode === "preset" ? "rgba(217,119,6,0.15)" : "#171412",
                color: mode === "preset" ? "#D97706" : "#A8A09A",
              }}
            >
              ⚡ Preset Demo Cases
            </button>
            <button
              onClick={() => setMode("upload")}
              style={{
                padding: "6px 14px",
                borderRadius: "6px",
                fontSize: "12px",
                fontWeight: 600,
                cursor: "pointer",
                border: mode === "upload" ? "1px solid #D97706" : "1px solid #3A3028",
                background: mode === "upload" ? "rgba(217,119,6,0.15)" : "#171412",
                color: mode === "upload" ? "#D97706" : "#A8A09A",
              }}
            >
              📹 Upload Custom Videos
            </button>
          </div>
        </div>

        {mode === "preset" ? (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
            {/* Old Video Preset */}
            <div style={{ background: "#171412", padding: "14px", borderRadius: "8px", border: "1px solid #3A3028" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#D97706", marginBottom: "8px" }}>
                📹 Previous / Old Assessment Video
              </div>
              <select
                value={oldCaseId}
                onChange={(e) => setOldCaseId(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  background: "#211C18",
                  border: "1px solid #3A3028",
                  color: "#F8F5F0",
                  fontSize: "13px",
                }}
              >
                <option value="case2">Patient Case 2: Asymmetrical Limp (Previous - High Asymmetry 16.0%)</option>
                <option value="case1">Patient Case 1: Normative Control (Previous - Low Asymmetry 0.0%)</option>
              </select>
            </div>

            {/* New Video Preset */}
            <div style={{ background: "#171412", padding: "14px", borderRadius: "8px", border: "1px solid #3A3028" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#10B981", marginBottom: "8px" }}>
                📹 Current / New Assessment Video
              </div>
              <select
                value={newCaseId}
                onChange={(e) => setNewCaseId(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  background: "#211C18",
                  border: "1px solid #3A3028",
                  color: "#F8F5F0",
                  fontSize: "13px",
                }}
              >
                <option value="case1">Patient Case 1: Normative Control (Current - Normative Symmetry 0.0%)</option>
                <option value="case2">Patient Case 2: Asymmetrical Limp (Current - High Asymmetry 16.0%)</option>
              </select>
            </div>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
            {/* Old Video Upload */}
            <div
              onDragOver={(e) => { e.preventDefault(); setDragOld(true); }}
              onDragLeave={() => setDragOld(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOld(false);
                if (e.dataTransfer.files?.[0]) setOldFile(e.dataTransfer.files[0]);
              }}
              onClick={() => oldInputRef.current?.click()}
              style={{
                border: dragOld ? "2px dashed #D97706" : "2px dashed #3A3028",
                background: dragOld ? "rgba(217,119,6,0.12)" : "#171412",
                padding: "20px",
                borderRadius: "8px",
                textAlign: "center",
                cursor: "pointer",
              }}
            >
              <input
                ref={oldInputRef}
                type="file"
                accept="video/*"
                onChange={(e) => e.target.files?.[0] && setOldFile(e.target.files[0])}
                style={{ display: "none" }}
              />
              <div style={{ fontSize: "24px", marginBottom: "6px" }}>📹</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#D97706" }}>
                {oldFile ? oldFile.name : "Upload Previous / Old Walking Video"}
              </div>
              <div style={{ fontSize: "11px", color: "#A8A09A", marginTop: "4px" }}>
                {oldFile ? `${(oldFile.size / 1024 / 1024).toFixed(1)} MB` : "Drag & drop .mp4 or .webm file here"}
              </div>
            </div>

            {/* New Video Upload */}
            <div
              onDragOver={(e) => { e.preventDefault(); setDragNew(true); }}
              onDragLeave={() => setDragNew(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragNew(false);
                if (e.dataTransfer.files?.[0]) setNewFile(e.dataTransfer.files[0]);
              }}
              onClick={() => newInputRef.current?.click()}
              style={{
                border: dragNew ? "2px dashed #10B981" : "2px dashed #3A3028",
                background: dragNew ? "rgba(16,185,129,0.12)" : "#171412",
                padding: "20px",
                borderRadius: "8px",
                textAlign: "center",
                cursor: "pointer",
              }}
            >
              <input
                ref={newInputRef}
                type="file"
                accept="video/*"
                onChange={(e) => e.target.files?.[0] && setNewFile(e.target.files[0])}
                style={{ display: "none" }}
              />
              <div style={{ fontSize: "24px", marginBottom: "6px" }}>📹</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#10B981" }}>
                {newFile ? newFile.name : "Upload Current / New Walking Video"}
              </div>
              <div style={{ fontSize: "11px", color: "#A8A09A", marginTop: "4px" }}>
                {newFile ? `${(newFile.size / 1024 / 1024).toFixed(1)} MB` : "Drag & drop .mp4 or .webm file here"}
              </div>
            </div>
          </div>
        )}

        {/* Action Button */}
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button
            onClick={handleRunComparison}
            disabled={loading || (mode === "upload" && (!oldFile || !newFile))}
            style={{
              padding: "10px 24px",
              fontSize: "14px",
              fontWeight: 700,
              borderRadius: "8px",
              background: loading ? "rgba(180,83,9,0.3)" : "linear-gradient(135deg, #B45309 0%, #78350F 100%)",
              color: "#F8F5F0",
              border: "1px solid #B45309",
              cursor: loading || (mode === "upload" && (!oldFile || !newFile)) ? "not-allowed" : "pointer",
              boxShadow: "0 0 16px rgba(180,83,9,0.3)",
              opacity: loading || (mode === "upload" && (!oldFile || !newFile)) ? 0.5 : 1,
            }}
          >
            {loading ? "⏳ Running Dual-Video Analysis..." : "📊 Compare Gait Progress"}
          </button>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div
          style={{
            background: "rgba(239,68,68,0.15)",
            border: "1px solid rgba(239,68,68,0.4)",
            padding: "16px",
            borderRadius: "8px",
            color: "#EF4444",
            fontSize: "13px",
            marginBottom: "24px",
            whiteSpace: "pre-line",
          }}
        >
          {error}
        </div>
      )}

      {/* Comparability Warning Alert */}
      {result?.comparability_warning && (
        <div
          style={{
            background: "rgba(180,83,9,0.12)",
            border: "1px solid #3A3028",
            padding: "16px",
            borderRadius: "8px",
            color: "#F8F5F0",
            fontSize: "13px",
            marginBottom: "24px",
            display: "flex",
            gap: "12px",
            alignItems: "flex-start",
          }}
        >
          <span style={{ fontSize: "20px" }}>⚠️</span>
          <div>
            <div style={{ fontWeight: 700, color: "#D97706", marginBottom: "4px" }}>Comparison Warning</div>
            <div>{result.comparability_warning}</div>
          </div>
        </div>
      )}

      {/* Results Dashboard */}
      {result && result.comparison_status !== "FAILED" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Verdict Card */}
          <div
            style={{
              padding: "24px",
              background: palette.bg,
              border: `1px solid ${palette.border}`,
              borderRadius: "12px",
              textAlign: "center",
              boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
            }}
          >
            <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.05em", color: "#A8A09A", textTransform: "uppercase", marginBottom: "8px" }}>
              OVERALL GAIT PROGRESS CLASSIFICATION
            </div>
            <div style={{ fontSize: "36px", fontWeight: 900, color: palette.text, marginBottom: "6px" }}>
              {palette.emoji} {palette.label}
            </div>
            <div style={{ fontSize: "14px", color: "#F8F5F0", maxWidth: "600px", margin: "0 auto 12px auto" }}>
              {palette.subtitle}
            </div>
            <div style={{ fontSize: "12px", color: "#A8A09A", fontVariantNumeric: "tabular-nums" }}>
              Gait Asymmetry Change: <strong>{result.old_video.gait_asymmetry}%</strong> (Old) ➔ <strong>{result.new_video.gait_asymmetry}%</strong> (New) | Delta: <strong style={{ color: palette.text }}>{result.comparison.asymmetry_change > 0 ? "+" : ""}{result.comparison.asymmetry_change} % points</strong>
            </div>
          </div>

          {/* Side-by-Side Video Players */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            {/* Old Video Player */}
            <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "12px", padding: "16px", boxShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#D97706", marginBottom: "10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>📹 PREVIOUS / OLD ASSESSMENT: {result.old_video.file_name}</span>
                <span style={{ background: "rgba(217,119,6,0.15)", border: "1px solid rgba(217,119,6,0.4)", color: "#D97706", padding: "2px 8px", borderRadius: "4px", fontSize: "10px", fontWeight: 700 }}>
                  Asymmetry: {result.old_video.gait_asymmetry}%
                </span>
              </div>
              <div style={{ width: "100%", height: "260px", background: "#000", borderRadius: "8px", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center" }}>
                {result.old_video.video_url ? (
                  <video
                    src={`${API_BASE}${result.old_video.video_url}`}
                    controls
                    autoPlay
                    loop
                    muted
                    style={{ width: "100%", height: "100%", objectFit: "contain" }}
                  />
                ) : (
                  <span style={{ color: "#A8A09A", fontSize: "12px" }}>No video URL available</span>
                )}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginTop: "12px", fontSize: "11px" }}>
                <div style={{ background: "#171412", border: "1px solid #3A3028", padding: "6px 10px", borderRadius: "6px" }}>
                  <span style={{ color: "#A8A09A" }}>Left ROM:</span> <strong style={{ color: "#F8F5F0" }}>{result.old_video.left_rom}°</strong>
                </div>
                <div style={{ background: "#171412", border: "1px solid #3A3028", padding: "6px 10px", borderRadius: "6px" }}>
                  <span style={{ color: "#A8A09A" }}>Right ROM:</span> <strong style={{ color: "#F8F5F0" }}>{result.old_video.right_rom}°</strong>
                </div>
              </div>
            </div>

            {/* New Video Player */}
            <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "12px", padding: "16px", boxShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#10B981", marginBottom: "10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span>📹 CURRENT / NEW ASSESSMENT: {result.new_video.file_name}</span>
                <span style={{ background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.4)", color: "#10B981", padding: "2px 8px", borderRadius: "4px", fontSize: "10px", fontWeight: 700 }}>
                  Asymmetry: {result.new_video.gait_asymmetry}%
                </span>
              </div>
              <div style={{ width: "100%", height: "260px", background: "#000", borderRadius: "8px", overflow: "hidden", display: "flex", alignItems: "center", justifyContent: "center" }}>
                {result.new_video.video_url ? (
                  <video
                    src={`${API_BASE}${result.new_video.video_url}`}
                    controls
                    autoPlay
                    loop
                    muted
                    style={{ width: "100%", height: "100%", objectFit: "contain" }}
                  />
                ) : (
                  <span style={{ color: "#A8A09A", fontSize: "12px" }}>No video URL available</span>
                )}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginTop: "12px", fontSize: "11px" }}>
                <div style={{ background: "#171412", border: "1px solid #3A3028", padding: "6px 10px", borderRadius: "6px" }}>
                  <span style={{ color: "#A8A09A" }}>Left ROM:</span> <strong style={{ color: "#F8F5F0" }}>{result.new_video.left_rom}°</strong>
                </div>
                <div style={{ background: "#171412", border: "1px solid #3A3028", padding: "6px 10px", borderRadius: "6px" }}>
                  <span style={{ color: "#A8A09A" }}>Right ROM:</span> <strong style={{ color: "#F8F5F0" }}>{result.new_video.right_rom}°</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Metric Comparison Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "14px" }}>
            <MetricTile
              label="Gait Symmetry Index"
              valOld={`${result.old_video.gait_asymmetry}%`}
              valNew={`${result.new_video.gait_asymmetry}%`}
              deltaStr={`${result.comparison.asymmetry_change > 0 ? "+" : ""}${result.comparison.asymmetry_change}% pts`}
              deltaGood={result.comparison.asymmetry_change <= -5.0}
            />
            <MetricTile
              label="Left Knee Peak ROM"
              valOld={`${result.old_video.left_rom}°`}
              valNew={`${result.new_video.left_rom}°`}
              deltaStr={`${result.comparison.left_rom_change > 0 ? "+" : ""}${result.comparison.left_rom_change}°`}
              deltaGood={result.comparison.left_rom_change > 0}
            />
            <MetricTile
              label="Right Knee Peak ROM"
              valOld={`${result.old_video.right_rom}°`}
              valNew={`${result.new_video.right_rom}°`}
              deltaStr={`${result.comparison.right_rom_change > 0 ? "+" : ""}${result.comparison.right_rom_change}°`}
              deltaGood={result.comparison.right_rom_change > 0}
            />
            <MetricTile
              label="Bilateral ROM Deficit"
              valOld={`${result.old_video.rom_deficit_deg}°`}
              valNew={`${result.new_video.rom_deficit_deg}°`}
              deltaStr={`${result.comparison.rom_deficit_change > 0 ? "+" : ""}${result.comparison.rom_deficit_change}°`}
              deltaGood={result.comparison.rom_deficit_change < 0}
            />
          </div>

          {/* Kinematic Matrix Table */}
          <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "12px", padding: "20px", boxShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
            <div style={{ fontWeight: 700, fontSize: "14px", color: "#F8F5F0", marginBottom: "14px" }}>
              📋 Detailed Kinematic Comparison Matrix
            </div>

            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid #3A3028", color: "#A8A09A", textAlign: "left" }}>
                  <th style={{ padding: "10px 12px" }}>Metric</th>
                  <th style={{ padding: "10px 12px" }}>OLD ASSESSMENT</th>
                  <th style={{ padding: "10px 12px" }}>NEW ASSESSMENT</th>
                  <th style={{ padding: "10px 12px" }}>CHANGE / DELTA</th>
                </tr>
              </thead>
              <tbody>
                {[
                  {
                    name: "Gait Asymmetry Index (SI)",
                    oldVal: `${result.old_video.gait_asymmetry}%`,
                    newVal: `${result.new_video.gait_asymmetry}%`,
                    change: `${result.comparison.asymmetry_change > 0 ? "+" : ""}${result.comparison.asymmetry_change} % pts`,
                    good: result.comparison.asymmetry_change <= -5.0,
                    bad: result.comparison.asymmetry_change >= 5.0,
                  },
                  {
                    name: "Left Knee Peak Flexion",
                    oldVal: `${result.old_video.left_knee_max_flexion}°`,
                    newVal: `${result.new_video.left_knee_max_flexion}°`,
                    change: `${result.comparison.left_knee_max_flexion_change > 0 ? "+" : ""}${result.comparison.left_knee_max_flexion_change}°`,
                    good: result.comparison.left_knee_max_flexion_change > 0,
                    bad: result.comparison.left_knee_max_flexion_change < -5.0,
                  },
                  {
                    name: "Right Knee Peak Flexion",
                    oldVal: `${result.old_video.right_knee_max_flexion}°`,
                    newVal: `${result.new_video.right_knee_max_flexion}°`,
                    change: `${result.comparison.right_knee_max_flexion_change > 0 ? "+" : ""}${result.comparison.right_knee_max_flexion_change}°`,
                    good: result.comparison.right_knee_max_flexion_change > 0,
                    bad: result.comparison.right_knee_max_flexion_change < -5.0,
                  },
                  {
                    name: "Bilateral ROM Deficit",
                    oldVal: `${result.old_video.rom_deficit_deg}°`,
                    newVal: `${result.new_video.rom_deficit_deg}°`,
                    change: `${result.comparison.rom_deficit_change > 0 ? "+" : ""}${result.comparison.rom_deficit_change}°`,
                    good: result.comparison.rom_deficit_change < 0,
                    bad: result.comparison.rom_deficit_change > 2.0,
                  },
                  {
                    name: "Screening Risk Classification",
                    oldVal: result.old_video.risk_level,
                    newVal: result.new_video.risk_level,
                    change: result.comparison.risk_change || "STABLE",
                    good: result.comparison.risk_change?.includes("IMPROVED"),
                    bad: result.comparison.risk_change?.includes("WORSENED"),
                  },
                ].map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #171412" }}>
                    <td style={{ padding: "12px", fontWeight: 600, color: "#F8F5F0" }}>{row.name}</td>
                    <td style={{ padding: "12px", color: "#D97706", fontVariantNumeric: "tabular-nums" }}>{row.oldVal}</td>
                    <td style={{ padding: "12px", color: "#10B981", fontVariantNumeric: "tabular-nums" }}>{row.newVal}</td>
                    <td style={{ padding: "12px" }}>
                      <span
                        style={{
                          fontWeight: 700,
                          color: row.good ? "#10B981" : row.bad ? "#EF4444" : "#A8A09A",
                        }}
                      >
                        {row.change}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Visual Charts */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            {/* Chart 1 */}
            <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "12px", padding: "20px", boxShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
              <div style={{ fontWeight: 700, fontSize: "13px", color: "#F8F5F0", marginBottom: "14px" }}>
                📊 Gait Asymmetry Comparison (% SI)
              </div>
              <div style={{ width: "100%", height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={asymmetryChartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#3A3028" />
                    <XAxis dataKey="name" stroke="#A8A09A" tick={{ fontSize: 12 }} />
                    <YAxis stroke="#A8A09A" tick={{ fontSize: 12 }} unit="%" />
                    <Tooltip contentStyle={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "6px", color: "#F8F5F0" }} />
                    <Bar dataKey="Asymmetry" radius={[4, 4, 0, 0]}>
                      {asymmetryChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2 */}
            <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "12px", padding: "20px", boxShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
              <div style={{ fontWeight: 700, fontSize: "13px", color: "#F8F5F0", marginBottom: "14px" }}>
                📐 Knee ROM &amp; Peak Flexion Comparison (Degrees)
              </div>
              <div style={{ width: "100%", height: 220 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={romChartData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#3A3028" />
                    <XAxis dataKey="metric" stroke="#A8A09A" tick={{ fontSize: 10 }} />
                    <YAxis stroke="#A8A09A" tick={{ fontSize: 12 }} unit="°" />
                    <Tooltip contentStyle={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "6px", color: "#F8F5F0" }} />
                    <Legend wrapperStyle={{ fontSize: "11px", color: "#A8A09A" }} />
                    <Bar dataKey="Old" fill="#D97706" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="New" fill="#10B981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Explainable AI Key Findings & Summary */}
          <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "12px", padding: "20px", boxShadow: "0 2px 8px rgba(0,0,0,0.3)" }}>
            <div style={{ fontWeight: 700, fontSize: "14px", color: "#F8F5F0", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>💡</span> Agent 4 Key Findings &amp; Clinical Progress Summary
            </div>

            <div style={{ marginBottom: "16px" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#D97706", marginBottom: "8px", textTransform: "uppercase" }}>
                KEY KINEMATIC FINDINGS:
              </div>
              <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "13px", color: "#F8F5F0", lineHeight: 1.65 }}>
                {result.key_findings.map((item, idx) => (
                  <li key={idx} style={{ marginBottom: "6px" }}>{item}</li>
                ))}
              </ul>
            </div>

            <div style={{ borderTop: "1px solid #3A3028", paddingTop: "12px", marginBottom: "12px" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#A8A09A", marginBottom: "4px", textTransform: "uppercase" }}>
                EXPLAINABLE AI SUMMARY:
              </div>
              <div style={{ fontSize: "13px", color: "#F8F5F0", lineHeight: 1.6 }}>
                {result.summary}
              </div>
            </div>

            <div style={{ borderTop: "1px solid #3A3028", paddingTop: "12px" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#10B981", marginBottom: "4px", textTransform: "uppercase" }}>
                CLINICAL RECOMMENDATION:
              </div>
              <div style={{ fontSize: "13px", color: "#10B981", fontWeight: 600, lineHeight: 1.6 }}>
                {result.recommendation}
              </div>
            </div>
          </div>

          {/* Medical Safety Disclaimer */}
          <div
            style={{
              padding: "14px 18px",
              borderRadius: "10px",
              background: "rgba(180,83,9,0.12)",
              border: "1px solid #3A3028",
              fontSize: "12px",
              color: "#F8F5F0",
              lineHeight: 1.6,
              textAlign: "left",
            }}
          >
            ⚕️ <strong style={{ color: "#D97706" }}>MEDICAL SAFETY DISCLAIMER:</strong> Agent 4 provides objective screening progress measurements by comparing two walking videos.
            It does not formulate medical diagnoses or claim clinical cure. All treatment decisions must be made by a licensed healthcare professional.
          </div>
        </div>
      )}
    </div>
  );
}
