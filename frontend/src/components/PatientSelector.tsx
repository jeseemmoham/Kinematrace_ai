"use client";

import React from "react";

interface Case {
  id: string;
  name: string;
  patient_info: { id: string; age: string; case: string };
  telemetry_default: {
    symmetry_index: number;
    peak_knee_flexion: number;
    hip_flexion_rom: number;
  };
}

interface PatientSelectorProps {
  cases: Case[];
  selectedCase: string;
  onSelect: (caseId: string) => void;
  loading?: boolean;
}

export default function PatientSelector({
  cases,
  selectedCase,
  onSelect,
  loading,
}: PatientSelectorProps) {
  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #D6D3D1",
        borderRadius: "12px",
        padding: "16px",
        marginBottom: "16px",
        boxShadow: "0 1px 3px rgba(0,0,0,0.07)",
      }}
    >
      <div
        style={{
          fontSize: "11px",
          color: "#57534E",
          fontWeight: 700,
          letterSpacing: "0.05em",
          textTransform: "uppercase",
          marginBottom: "12px",
          display: "flex",
          alignItems: "center",
          gap: "6px",
        }}
      >
        <span>📁</span> Patient Case Selection
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {cases.map((c) => {
          const isSelected = selectedCase === c.id;
          return (
            <button
              key={c.id}
              id={`case-selector-${c.id}`}
              onClick={() => !loading && onSelect(c.id)}
              style={{
                textAlign: "left",
                padding: "12px 14px",
                borderRadius: "8px",
                border: isSelected ? "1px solid #78350F" : "1px solid #D6D3D1",
                background: isSelected ? "#FEF3C7" : "#F5F5F4",
                color: isSelected ? "#78350F" : "#1C1917",
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading && !isSelected ? 0.6 : 1,
                transition: "all 0.15s ease",
                width: "100%",
              }}
            >
              <div style={{ fontWeight: 700, fontSize: "13px", marginBottom: "2px" }}>
                {isSelected && "✓ "}{c.patient_info.id}
              </div>
              <div style={{ fontSize: "11px", color: isSelected ? "#92400E" : "#57534E" }}>
                {c.patient_info.case} · {c.patient_info.age}
              </div>
              <div
                style={{
                  marginTop: "8px",
                  display: "flex",
                  gap: "6px",
                  flexWrap: "wrap",
                }}
              >
                <Pill label="SI" value={`${c.telemetry_default.symmetry_index}%`} />
                <Pill label="Knee" value={`${c.telemetry_default.peak_knee_flexion}°`} />
                <Pill label="Hip" value={`${c.telemetry_default.hip_flexion_rom}°`} />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function Pill({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <span
      style={{
        fontSize: "10px",
        fontWeight: 600,
        padding: "2px 8px",
        borderRadius: "4px",
        background: "#FFFFFF",
        color: "#57534E",
        border: "1px solid #D6D3D1",
      }}
    >
      {label}: {value}
    </span>
  );
}
