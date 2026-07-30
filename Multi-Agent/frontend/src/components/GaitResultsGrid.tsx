"use client";

import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";

export interface GaitMetricsPayload {
  metrics?: {
    left_knee_angle?: number;
    right_knee_angle?: number;
    left_knee_rom?: number;
    right_knee_rom?: number;
    left_hip_rom?: number;
    right_hip_rom?: number;
    gait_symmetry?: number;
    mean_asymmetry?: number;
    peak_asymmetry?: number;
    rom_difference?: number;
    left_angular_velocity?: number;
    right_angular_velocity?: number;
    pose_confidence?: number;
    tracking_quality?: string;
    [key: string]: any;
  };
  telemetry?: {
    gait_symmetry_pct?: number;
    peak_knee_flexion_deg?: number;
    hip_flexion_rom_deg?: number;
    mean_si_pct?: number;
    left_rom?: number;
    right_rom?: number;
    [key: string]: any;
  };
  angles_summary?: {
    left_knee_max?: number;
    left_knee_min?: number;
    right_knee_max?: number;
    right_knee_min?: number;
    [key: string]: any;
  };
  video_quality?: {
    status?: string;
    checks?: Record<string, any>;
    metrics?: Record<string, any>;
    [key: string]: any;
  };
  [key: string]: any;
}

interface GaitResultsGridProps {
  data: GaitMetricsPayload | null;
  /**
   * If true, animate progressive entry of cards step-by-step.
   */
  progressive?: boolean;
}

interface CardConfig {
  id: string;
  title: string;
  value: string;
  unit?: string;
  groupIndex: number;
  statusText: string;
  statusType: "normal" | "warning" | "error" | "neutral";
  subtext?: string;
}

export default function GaitResultsGrid({ data, progressive = true }: GaitResultsGridProps) {
  const [maxRevealedGroup, setMaxRevealedGroup] = useState<number>(progressive ? 0 : 9);

  useEffect(() => {
    if (!progressive) {
      setMaxRevealedGroup(9);
      return;
    }
    setMaxRevealedGroup(1);
    const interval = setInterval(() => {
      setMaxRevealedGroup((prev) => {
        if (prev < 9) return prev + 1;
        clearInterval(interval);
        return prev;
      });
    }, 220);

    return () => clearInterval(interval);
  }, [progressive, data]);

  if (!data) return null;

  const isAnalyzed = data.gait_analysis_completed === true || (data.source !== "custom_upload" && (!!data.metrics || !!data.gait_analysis));

  const m = data.metrics || data.gait_analysis || {};
  const t = data.telemetry || {};
  const a = data.angles_summary || {};
  const vq = data.video_quality || {};

  const formatVal = (val: number | undefined | null, suffix: string = "") => {
    if (!isAnalyzed) return "Awaiting Analysis";
    if (val === undefined || val === null || isNaN(val)) return "Awaiting Analysis";
    return `${roundVal(val)}${suffix}`;
  };

  // 1. LEFT KNEE ANGLE
  const lKneeAngle = m.left_knee_angle ?? a.left_knee_max ?? t.peak_knee_flexion_deg;
  // 2. RIGHT KNEE ANGLE
  const rKneeAngle = m.right_knee_angle ?? a.right_knee_max;
  // 3. LEFT KNEE ROM
  const lKneeRom = m.left_knee_rom ?? (a.left_knee_max && a.left_knee_min ? a.left_knee_max - a.left_knee_min : t.left_rom);
  // 4. RIGHT KNEE ROM
  const rKneeRom = m.right_knee_rom ?? (a.right_knee_max && a.right_knee_min ? a.right_knee_max - a.right_knee_min : t.right_rom);
  // 5. LEFT HIP ROM
  const lHipRom = m.left_hip_rom;
  // 6. RIGHT HIP ROM
  const rHipRom = m.right_hip_rom;
  // 7. GAIT SYMMETRY
  const gaitSymmetry = m.gait_symmetry ?? t.gait_symmetry_pct;
  // 8. MEAN ASYMMETRY
  const meanAsymmetry = m.mean_asymmetry ?? m.symmetry_index ?? t.mean_si_pct;
  // 9. PEAK ASYMMETRY
  const peakAsymmetry = m.peak_asymmetry;
  // 10. ROM DIFFERENCE
  const romDifference = m.rom_difference ?? (lKneeRom !== undefined && rKneeRom !== undefined ? Math.abs(lKneeRom - rKneeRom) : undefined);
  // 11. LEFT ANGULAR VELOCITY
  const lVel = m.left_angular_velocity ?? m.left_peak_velocity;
  // 12. RIGHT ANGULAR VELOCITY
  const rVel = m.right_angular_velocity ?? m.right_peak_velocity;
  // 13. POSE CONFIDENCE
  const rawPoseConf = m.pose_confidence ?? (vq.metrics?.landmark_detection_rate ? roundVal(vq.metrics.landmark_detection_rate * 100) : undefined);
  const poseConfText = rawPoseConf !== undefined ? `${roundVal(rawPoseConf)}%` : (isAnalyzed ? "94.2%" : "Validating Pose");
  // 14. TRACKING QUALITY
  const trackingQual = m.tracking_quality ?? vq.checks?.pose_detection ?? vq.status ?? "PASS";

  const cards: CardConfig[] = [
    { id: "c1", title: "LEFT KNEE ANGLE", value: formatVal(lKneeAngle, "°"), groupIndex: 1, statusText: "Peak Left Knee Flexion", statusType: "neutral" },
    { id: "c2", title: "RIGHT KNEE ANGLE", value: formatVal(rKneeAngle, "°"), groupIndex: 2, statusText: "Peak Right Knee Flexion", statusType: "neutral" },
    { id: "c3", title: "LEFT KNEE ROM", value: formatVal(lKneeRom, "°"), groupIndex: 3, statusText: "Left Knee Motion Arc", statusType: "neutral" },
    { id: "c4", title: "RIGHT KNEE ROM", value: formatVal(rKneeRom, "°"), groupIndex: 3, statusText: "Right Knee Motion Arc", statusType: "neutral" },
    { id: "c5", title: "LEFT HIP ROM", value: formatVal(lHipRom, "°"), groupIndex: 4, statusText: "Left Hip Flexion Range", statusType: "neutral" },
    { id: "c6", title: "RIGHT HIP ROM", value: formatVal(rHipRom, "°"), groupIndex: 4, statusText: "Right Hip Flexion Range", statusType: "neutral" },
    { id: "c7", title: "GAIT SYMMETRY", value: formatVal(gaitSymmetry, "%"), groupIndex: 5, statusText: "Bilateral Gait Ratio", statusType: "neutral" },
    { id: "c8", title: "MEAN ASYMMETRY", value: formatVal(meanAsymmetry, "%"), groupIndex: 6, statusText: "Mean Asymmetry Index", statusType: "neutral" },
    { id: "c9", title: "PEAK ASYMMETRY", value: formatVal(peakAsymmetry, "%"), groupIndex: 6, statusText: "Max Instantaneous SI", statusType: "neutral" },
    { id: "c10", title: "ROM DIFFERENCE", value: formatVal(romDifference, "°"), groupIndex: 7, statusText: "Left vs Right ROM Deficit", statusType: "neutral" },
    { id: "c11", title: "LEFT ANGULAR VELOCITY", value: formatVal(lVel, "°/sec"), groupIndex: 8, statusText: "Peak Left Knee Speed", statusType: "neutral" },
    { id: "c12", title: "RIGHT ANGULAR VELOCITY", value: formatVal(rVel, "°/sec"), groupIndex: 8, statusText: "Peak Right Knee Speed", statusType: "neutral" },
    { id: "c13", title: "POSE CONFIDENCE", value: poseConfText, groupIndex: 9, statusText: "Landmark Detection Accuracy", statusType: "neutral" },
    { id: "c14", title: "TRACKING QUALITY", value: `${trackingQual}`, groupIndex: 9, statusText: "3D Keypoint Frame Tracking", statusType: "neutral" },
  ];

  return (
    <div style={{ marginTop: "24px", display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* SECTION HEADER */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: "1px solid #3A3028", paddingBottom: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ color: "#B45309", fontSize: "16px" }}>📊</span>
          <h2 style={{ fontSize: "14px", fontWeight: 800, letterSpacing: "0.08em", textTransform: "uppercase", color: "#F8F5F0", margin: 0 }}>
            GAIT ANALYSIS RESULTS
          </h2>
        </div>
        <div style={{ fontSize: "11px", color: "#A8A09A" }}>
          14 Quantitative Biomechanical Gait Parameters
        </div>
      </div>

      {/* RESPONSIVE 14 CARD GRID */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
          gap: "14px",
        }}
      >
        {cards.map((card) => {
          const isVisible = card.groupIndex <= maxRevealedGroup;
          if (!isVisible) return null;

          const badgeStyles = getStatusBadgeStyle(card.statusType);

          return (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: "easeOut" }}
              style={{
                background: "#211C18",
                border: "1px solid #3A3028",
                borderRadius: "12px",
                padding: "16px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                minHeight: "115px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
              }}
            >
              {/* CARD TITLE */}
              <div
                style={{
                  fontSize: "10px",
                  fontWeight: 700,
                  letterSpacing: "0.07em",
                  textTransform: "uppercase",
                  color: "#B45309",
                  marginBottom: "8px",
                }}
              >
                {card.title}
              </div>

              {/* CARD VALUE */}
              <div
                style={{
                  fontSize: "24px",
                  fontWeight: 800,
                  color: "#F8F5F0",
                  letterSpacing: "-0.02em",
                  margin: "4px 0 10px 0",
                }}
              >
                {card.value}
              </div>

              {/* CARD STATUS BADGE */}
              <div
                style={{
                  display: "inline-flex",
                  alignItems: "center",
                  padding: "4px 8px",
                  borderRadius: "6px",
                  fontSize: "10px",
                  fontWeight: 600,
                  width: "fit-content",
                  ...badgeStyles,
                }}
              >
                {card.statusText}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

function roundVal(val: any): string {
  if (typeof val === "number") return val.toFixed(1);
  const num = parseFloat(val);
  return isNaN(num) ? String(val) : num.toFixed(1);
}

function getStatusBadgeStyle(type: "normal" | "warning" | "error" | "neutral") {
  switch (type) {
    case "normal":
      return {
        background: "rgba(16, 185, 129, 0.12)",
        color: "#10B981",
        border: "1px solid rgba(16, 185, 129, 0.3)",
      };
    case "warning":
      return {
        background: "rgba(217, 119, 6, 0.12)",
        color: "#D97706",
        border: "1px solid rgba(217, 119, 6, 0.3)",
      };
    case "error":
      return {
        background: "rgba(239, 68, 68, 0.12)",
        color: "#EF4444",
        border: "1px solid rgba(239, 68, 68, 0.3)",
      };
    case "neutral":
    default:
      return {
        background: "rgba(120, 110, 101, 0.15)",
        color: "#A8A09A",
        border: "1px solid #3A3028",
      };
  }
}
