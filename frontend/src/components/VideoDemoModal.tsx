"use client";

import React, { useRef, useState } from "react";

interface VideoDemoModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  patientId: string;
  videoUrl: string;
  riskStatus: string;
  riskBadgeColor: "green" | "copper" | "red";
  symmetry: string;
  kneeFlexion: string;
  hipFlexion: string;
}

export default function VideoDemoModal({
  isOpen,
  onClose,
  title,
  patientId,
  videoUrl,
  riskStatus,
  riskBadgeColor,
  symmetry,
  kneeFlexion,
  hipFlexion,
}: VideoDemoModalProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(true);

  if (!isOpen) return null;

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) { videoRef.current.play(); setIsPlaying(true); }
    else { videoRef.current.pause(); setIsPlaying(false); }
  };

  const getBadgeStyle = () => {
    if (riskBadgeColor === "green")  return { bg: "rgba(16,185,129,0.18)", color: "#10B981", border: "1px solid rgba(16,185,129,0.4)" };
    if (riskBadgeColor === "copper") return { bg: "rgba(180,83,9,0.20)",  color: "#D97706", border: "1px solid rgba(180,83,9,0.45)" };
    return                                  { bg: "rgba(239,68,68,0.18)",  color: "#EF4444", border: "1px solid rgba(239,68,68,0.4)"  };
  };

  const bs = getBadgeStyle();

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(23, 20, 18, 0.88)",
        backdropFilter: "blur(8px)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "860px",
          background: "#211C18",
          border: "1px solid #3A3028",
          borderRadius: "16px",
          overflow: "hidden",
          boxShadow: "0 20px 50px rgba(0,0,0,0.65)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header bar */}
        <div style={{ padding: "16px 24px", borderBottom: "1px solid #3A3028", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#F8F5F0", margin: 0 }}>{title}</h3>
              <span style={{ padding: "3px 8px", borderRadius: "4px", fontSize: "10px", fontWeight: 700, background: bs.bg, color: bs.color, border: bs.border }}>
                {riskStatus}
              </span>
            </div>
            <p style={{ fontSize: "12px", color: "#A8A09A", margin: "2px 0 0 0" }}>
              Patient ID: {patientId} · Markerless 3D Gait Pose Stream
            </p>
          </div>
          <button
            onClick={onClose}
            style={{ background: "#2D2621", border: "1px solid #3A3028", color: "#A8A09A", borderRadius: "50%", width: "32px", height: "32px", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "14px" }}
          >
            ✕
          </button>
        </div>

        {/* Video Player */}
        <div style={{ position: "relative", width: "100%", background: "#171412", height: "420px" }}>
          <video
            ref={videoRef}
            src={videoUrl}
            autoPlay
            loop
            muted
            playsInline
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
          <button
            onClick={togglePlay}
            style={{
              position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)",
              width: "60px", height: "60px", borderRadius: "50%",
              background: "rgba(33,28,24,0.78)", border: "2px solid #B45309",
              color: "#F8F5F0", fontSize: "22px", display: "flex", alignItems: "center", justifyContent: "center",
              cursor: "pointer", boxShadow: "0 0 20px rgba(180,83,9,0.4)",
              opacity: isPlaying ? 0.3 : 1, transition: "all 0.2s ease",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = "1")}
            onMouseLeave={(e) => { if (isPlaying) e.currentTarget.style.opacity = "0.3"; }}
          >
            {isPlaying ? "❚❚" : "▶"}
          </button>
        </div>

        {/* Telemetry Summary Footer */}
        <div style={{ padding: "16px 24px", background: "#171412", display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: "16px" }}>
          {[
            { label: "Gait Symmetry",    value: symmetry,    color: "#10B981" },
            { label: "Peak Knee Flexion", value: kneeFlexion, color: "#F8F5F0" },
            { label: "Hip Flexion ROM",   value: hipFlexion,  color: "#F8F5F0" },
          ].map(({ label, value, color }) => (
            <div key={label}>
              <div style={{ fontSize: "11px", color: "#A8A09A" }}>{label}</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color }}>{value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
