"use client";

import React from "react";

export interface QualityCheck {
  full_body_visible: boolean;
  lighting: string;
  camera_stability: string;
  walking_duration: string;
  camera_angle: string;
  pose_detection: string;
  resolution: string;
  frame_rate: string;
}

export interface QualityIssue {
  criterion: string;
  reason: string;
  impact: string;
  recommendation: string;
}

export interface VideoQualityResult {
  status: "PASS" | "WARNING" | "FAIL";
  video_quality_score: number;
  checks: QualityCheck;
  metrics: {
    landmark_detection_rate: number;
    brightness_score: number;
    blur_score: number;
    camera_shake_score: number;
    duration_sec: number;
    width: number;
    height: number;
    fps: number;
  };
  issues: QualityIssue[];
  recommendation: string;
  full_body_visibility_status?: string;
}

interface VideoQualityGateProps {
  result: VideoQualityResult | null;
  loading: boolean;
  warningApproved: boolean;
  onApproveWarning: () => void;
  onReupload: () => void;
}

const SCORE_BAR_COLOR = (score: number) => {
  if (score >= 90) return "#15803D";
  if (score >= 70) return "#D97706";
  return "#B91C1C";
};

const CHECK_LABELS: Record<keyof QualityCheck, string> = {
  full_body_visible: "Full Body Visible",
  lighting: "Lighting",
  camera_stability: "Camera Stability",
  walking_duration: "Walking Duration",
  camera_angle: "Camera Angle",
  pose_detection: "Pose Detection",
  resolution: "Resolution",
  frame_rate: "Frame Rate",
};

const CHECK_ICONS: Record<keyof QualityCheck, string> = {
  full_body_visible: "👤",
  lighting: "💡",
  camera_stability: "📷",
  walking_duration: "⏱️",
  camera_angle: "📐",
  pose_detection: "🦴",
  resolution: "🖥️",
  frame_rate: "🎞️",
};

function getCheckValue(key: keyof QualityCheck, checks: QualityCheck): string {
  const val = checks[key];
  if (typeof val === "boolean") return val ? "Good" : "Poor";
  return String(val);
}

function getCheckColor(key: keyof QualityCheck, checks: QualityCheck, issues: QualityIssue[]): string {
  const isFailed = issues.some(
    (i) => i.criterion.toLowerCase().replace(/\s+/g, "_") === key.toLowerCase() ||
           i.criterion.toLowerCase().includes(key.toLowerCase().replace(/_/g, " "))
  );
  if (isFailed) return "#D97706";
  return "#15803D";
}

export default function VideoQualityGate({
  result,
  loading,
  warningApproved,
  onApproveWarning,
  onReupload,
}: VideoQualityGateProps) {
  if (loading) {
    return (
      <div
        style={{
          background: "#FFFFFF",
          border: "1px solid #D6D3D1",
          borderRadius: "12px",
          padding: "20px 18px",
          marginBottom: "14px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "14px" }}>
          <div className="spinner" style={{ width: "18px", height: "18px", flexShrink: 0 }} />
          <span
            style={{
              fontSize: "11px",
              fontWeight: 700,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              color: "#78350F",
            }}
          >
            Agent 1 — Validating Video Quality…
          </span>
        </div>
        <div
          style={{
            height: "4px",
            background: "#E7E5E4",
            borderRadius: "2px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              width: "40%",
              background: "#78350F",
              borderRadius: "2px",
              animation: "pulse 1.5s ease-in-out infinite",
            }}
          />
        </div>
      </div>
    );
  }

  if (!result) return null;

  const { status, video_quality_score: score, checks, issues, recommendation } = result;
  const barColor = SCORE_BAR_COLOR(score);

  // ── FAIL STATE ──────────────────────────────────────────────────────────────
  if (status === "FAIL") {
    return (
      <div
        style={{
          background: "#FEF2F2",
          border: "1px solid #FCA5A5",
          borderRadius: "12px",
          padding: "18px",
          marginBottom: "14px",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "18px" }}>❌</span>
            <div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#B91C1C", letterSpacing: "0.05em" }}>
                Video Quality Failed
              </div>
              <div style={{ fontSize: "10px", color: "#57534E", marginTop: "2px" }}>
                Agent 1 · Quality Validation Gate
              </div>
            </div>
          </div>
          <div
            style={{
              background: "#FFFFFF",
              border: "1px solid #FCA5A5",
              borderRadius: "6px",
              padding: "6px 12px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#B91C1C", fontVariantNumeric: "tabular-nums" }}>
              {score}
            </div>
            <div style={{ fontSize: "9px", color: "#B91C1C", fontWeight: 600 }}>/ 100</div>
          </div>
        </div>

        {/* Score bar */}
        <div style={{ marginBottom: "14px" }}>
          <div
            style={{
              height: "5px",
              background: "#E7E5E4",
              borderRadius: "3px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${score}%`,
                background: "#B91C1C",
                borderRadius: "3px",
              }}
            />
          </div>
        </div>

        {/* Recommendation */}
        <div
          style={{
            background: "#FFFFFF",
            border: "1px solid #FCA5A5",
            borderRadius: "6px",
            padding: "10px 12px",
            fontSize: "11px",
            color: "#B91C1C",
            marginBottom: "14px",
            lineHeight: 1.5,
          }}
        >
          {recommendation}
        </div>

        {/* Issues list */}
        {issues.length > 0 && (
          <div style={{ marginBottom: "14px" }}>
            <div
              style={{
                fontSize: "10px",
                fontWeight: 700,
                letterSpacing: "0.05em",
                textTransform: "uppercase",
                color: "#B91C1C",
                marginBottom: "8px",
              }}
            >
              Failed Criteria
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {issues.map((issue, i) => (
                <div
                  key={i}
                  style={{
                    background: "#FFFFFF",
                    border: "1px solid #FCA5A5",
                    borderRadius: "6px",
                    padding: "8px 10px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "3px" }}>
                    <span style={{ fontSize: "11px", fontWeight: 700, color: "#B91C1C" }}>
                      ✗ {issue.criterion}
                    </span>
                  </div>
                  <div style={{ fontSize: "10px", color: "#57534E", lineHeight: 1.4 }}>
                    {issue.reason}
                  </div>
                  <div style={{ fontSize: "10px", color: "#44403C", marginTop: "3px", lineHeight: 1.4 }}>
                    💡 {issue.recommendation}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Re-upload button */}
        <button
          id="quality-reupload-btn"
          onClick={onReupload}
          style={{
            width: "100%",
            padding: "10px",
            background: "#78350F",
            border: "none",
            borderRadius: "8px",
            color: "#FFFFFF",
            fontSize: "12px",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          📤 Upload New Video
        </button>
      </div>
    );
  }

  // ── WARNING STATE (not yet approved) ────────────────────────────────────────
  if (status === "WARNING" && !warningApproved) {
    return (
      <div
        style={{
          background: "#FEF3C7",
          border: "1px solid #F59E0B",
          borderRadius: "12px",
          padding: "18px",
          marginBottom: "14px",
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "14px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "18px" }}>⚠️</span>
            <div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#78350F", letterSpacing: "0.05em" }}>
                Video Quality Warning
              </div>
              <div style={{ fontSize: "10px", color: "#57534E", marginTop: "2px" }}>
                Agent 1 · Quality Validation Gate
              </div>
            </div>
          </div>
          <div
            style={{
              background: "#FFFFFF",
              border: "1px solid #F59E0B",
              borderRadius: "6px",
              padding: "6px 12px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: "20px", fontWeight: 800, color: "#78350F", fontVariantNumeric: "tabular-nums" }}>
              {score}
            </div>
            <div style={{ fontSize: "9px", color: "#78350F", fontWeight: 600 }}>/ 100</div>
          </div>
        </div>

        {/* Score bar */}
        <div style={{ marginBottom: "14px" }}>
          <div style={{ height: "5px", background: "#E7E5E4", borderRadius: "3px", overflow: "hidden" }}>
            <div
              style={{
                height: "100%",
                width: `${score}%`,
                background: "#D97706",
                borderRadius: "3px",
              }}
            />
          </div>
        </div>

        {/* Recommendation */}
        <div
          style={{
            background: "#FFFFFF",
            border: "1px solid #F59E0B",
            borderRadius: "6px",
            padding: "10px 12px",
            fontSize: "11px",
            color: "#78350F",
            marginBottom: "14px",
            lineHeight: 1.5,
          }}
        >
          {recommendation}
        </div>

        {/* Issues */}
        {issues.length > 0 && (
          <div style={{ marginBottom: "16px" }}>
            <div
              style={{
                fontSize: "10px",
                fontWeight: 700,
                letterSpacing: "0.05em",
                textTransform: "uppercase",
                color: "#78350F",
                marginBottom: "8px",
              }}
            >
              Quality Issues Detected
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {issues.map((issue, i) => (
                <div
                  key={i}
                  style={{
                    background: "#FFFFFF",
                    border: "1px solid #FCD34D",
                    borderRadius: "6px",
                    padding: "8px 10px",
                  }}
                >
                  <div style={{ fontSize: "11px", fontWeight: 700, color: "#78350F", marginBottom: "2px" }}>
                    ⚠️ {issue.criterion}
                  </div>
                  <div style={{ fontSize: "10px", color: "#57534E", lineHeight: 1.4 }}>{issue.reason}</div>
                  <div style={{ fontSize: "10px", color: "#44403C", marginTop: "3px" }}>💡 {issue.recommendation}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Decision buttons */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
          <button
            id="quality-continue-btn"
            onClick={onApproveWarning}
            style={{
              padding: "10px 8px",
              background: "#78350F",
              border: "none",
              borderRadius: "6px",
              color: "#FFFFFF",
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            ✓ Continue Analysis
          </button>
          <button
            id="quality-newvideo-btn"
            onClick={onReupload}
            style={{
              padding: "10px 8px",
              background: "#FFFFFF",
              border: "1px solid #D6D3D1",
              borderRadius: "6px",
              color: "#57534E",
              fontSize: "11px",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            📤 Upload New Video
          </button>
        </div>
      </div>
    );
  }

  // ── PASS STATE (or approved WARNING): collapsed summary expander ─────────────
  const isApprovedWarning = status === "WARNING" && warningApproved;
  const accentColor = isApprovedWarning ? "#78350F" : "#15803D";
  const accentBg = isApprovedWarning ? "#FEF3C7" : "#F0FDF4";
  const borderColor = isApprovedWarning ? "#F59E0B" : "#86EFAC";
  const statusLabel = isApprovedWarning ? "⚠️ WARNING — Analysis Approved" : "✅ PASS";

  return (
    <details style={{ marginBottom: "14px" }} open={false}>
      <summary
        id="quality-summary-toggle"
        style={{
          background: accentBg,
          border: `1px solid ${borderColor}`,
          borderRadius: "8px",
          padding: "10px 14px",
          cursor: "pointer",
          listStyle: "none",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          userSelect: "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "13px" }}>{isApprovedWarning ? "⚠️" : "✅"}</span>
          <div>
            <div style={{ fontSize: "11px", fontWeight: 700, color: accentColor }}>
              Video Quality: {statusLabel}
            </div>
            <div style={{ fontSize: "10px", color: "#57534E" }}>
              Agent 1 · Score {score}/100 · Click to expand
            </div>
          </div>
        </div>
        <div
          style={{
            background: "#FFFFFF",
            color: accentColor,
            borderRadius: "6px",
            padding: "3px 10px",
            fontSize: "13px",
            fontWeight: 800,
            fontVariantNumeric: "tabular-nums",
            border: `1px solid ${borderColor}`,
          }}
        >
          {score}
        </div>
      </summary>

      {/* Expanded content */}
      <div
        style={{
          background: "#FFFFFF",
          border: "1px solid #D6D3D1",
          borderTop: "none",
          borderRadius: "0 0 8px 8px",
          padding: "14px",
          boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        }}
      >
        {/* Score bar */}
        <div style={{ marginBottom: "14px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "#57534E", marginBottom: "4px" }}>
            <span>Quality Score</span>
            <span style={{ color: accentColor, fontWeight: 700 }}>{score} / 100</span>
          </div>
          <div style={{ height: "5px", background: "#E7E5E4", borderRadius: "3px", overflow: "hidden" }}>
            <div
              style={{
                height: "100%",
                width: `${score}%`,
                background: barColor,
                borderRadius: "3px",
              }}
            />
          </div>
        </div>

        {/* Check grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "6px",
            marginBottom: issues.length > 0 ? "12px" : "0",
          }}
        >
          {(Object.keys(CHECK_LABELS) as (keyof QualityCheck)[]).map((key) => {
            const color = getCheckColor(key, checks, issues);
            const value = getCheckValue(key, checks);
            return (
              <div
                key={key}
                style={{
                  background: "#F5F5F4",
                  border: "1px solid #D6D3D1",
                  borderRadius: "6px",
                  padding: "6px 8px",
                }}
              >
                <div style={{ fontSize: "9px", color: "#57534E", marginBottom: "2px" }}>
                  {CHECK_ICONS[key]} {CHECK_LABELS[key]}
                </div>
                <div style={{ fontSize: "10px", fontWeight: 700, color }}>{value}</div>
              </div>
            );
          })}
        </div>
      </div>
    </details>
  );
}
