"use client";

import React from "react";

interface TelemetryData {
  gait_symmetry_pct: number;
  peak_knee_flexion_deg: number;
  hip_flexion_rom_deg: number;
  risk_status?: string;
  risk_color?: string;
}

interface PatientInfo {
  id: string;
  age: string;
  case: string;
}

interface EHRHeaderProps {
  patientInfo: PatientInfo;
  telemetry: TelemetryData;
  sessionLabel?: string;
}

const getRiskBadge = (status: string) => {
  if (!status) return null;
  const lower = status.toLowerCase();
  if (lower.includes("high") || lower.includes("critical")) return "badge-red";
  if (lower.includes("moderate") || lower.includes("medium")) return "badge-amber";
  return "badge-green";
};

export default function EHRHeader({ patientInfo, telemetry, sessionLabel = "Outpatient Gait Screening" }: EHRHeaderProps) {
  const symPct = telemetry.gait_symmetry_pct ?? 87.5;
  const kneeFlx = telemetry.peak_knee_flexion_deg ?? 89.1;
  const hipRom = telemetry.hip_flexion_rom_deg ?? 125.1;
  const riskStatus = telemetry.risk_status ?? "UNKNOWN";

  return (
    <header
      style={{
        background: "#FFFFFF",
        borderBottom: "1px solid #E7E5E4",
        padding: "0 24px",
        zIndex: 100,
        position: "sticky",
        top: 0,
      }}
    >
      {/* Top mocha stripe */}
      <div
        style={{
          height: "3px",
          background: "#78350F",
        }}
      />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "12px 0",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "8px",
              background: "#78350F",
              color: "#FFFFFF",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "18px",
              fontWeight: 800,
              flexShrink: 0,
            }}
          >
            🩺
          </div>
          <div>
            <div style={{ fontSize: "16px", fontWeight: 700, letterSpacing: "-0.01em", color: "#1C1917" }}>
              KinemaTrace <span style={{ color: "#78350F" }}>AI</span>
            </div>
            <div style={{ fontSize: "11px", color: "#57534E", letterSpacing: "0.05em", textTransform: "uppercase" }}>
              Pediatric Gait Screening Platform
            </div>
          </div>
        </div>

        {/* Patient Info Banner */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            background: "#F5F5F4",
            border: "1px solid #D6D3D1",
            borderRadius: "8px",
            padding: "8px 16px",
            flexWrap: "wrap",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <div className="pulse-dot green" />
            <span style={{ color: "#57534E", fontSize: "12px" }}>Patient ID:</span>
            <span style={{ color: "#1C1917", fontSize: "12px", fontWeight: 700, fontFamily: "monospace" }}>
              {patientInfo.id}
            </span>
          </div>
          <span style={{ color: "#D6D3D1" }}>|</span>
          <span style={{ color: "#57534E", fontSize: "12px" }}>Age: <strong style={{ color: "#1C1917" }}>{patientInfo.age}</strong></span>
          <span style={{ color: "#D6D3D1" }}>|</span>
          <span style={{ color: "#57534E", fontSize: "12px" }}>Session: <strong style={{ color: "#1C1917" }}>{sessionLabel}</strong></span>
          {riskStatus && riskStatus !== "UNKNOWN" && (
            <>
              <span style={{ color: "#D6D3D1" }}>|</span>
              <span className={`badge ${getRiskBadge(riskStatus)}`}>{riskStatus}</span>
            </>
          )}
        </div>

        {/* Telemetry Badges */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          <TelemetryBadge
            icon="⚖️"
            label="Gait Symmetry"
            value={`${symPct.toFixed(1)}%`}
            badgeClass={symPct >= 90 ? "badge-green" : symPct >= 80 ? "badge-amber" : "badge-red"}
          />
          <TelemetryBadge
            icon="🦵"
            label="Peak Knee Flexion"
            value={`${kneeFlx.toFixed(1)}°`}
            badgeClass={kneeFlx >= 100 ? "badge-green" : kneeFlx >= 85 ? "badge-amber" : "badge-red"}
          />
          <TelemetryBadge
            icon="🦴"
            label="Hip Flexion ROM"
            value={`${hipRom.toFixed(1)}°`}
            badgeClass="badge-blue"
          />
        </div>
      </div>
    </header>
  );
}

function TelemetryBadge({
  icon,
  label,
  value,
  badgeClass,
}: {
  icon: string;
  label: string;
  value: string;
  badgeClass: string;
}) {
  return (
    <div
      className={`badge ${badgeClass}`}
      style={{ flexDirection: "column", borderRadius: "6px", padding: "6px 12px", gap: "2px" }}
    >
      <span style={{ fontSize: "10px", opacity: 0.8, fontWeight: 500 }}>
        {icon} {label}
      </span>
      <span style={{ fontSize: "13px", fontWeight: 700 }}>{value}</span>
    </div>
  );
}
