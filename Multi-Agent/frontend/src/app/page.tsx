"use client";

import React, { useState } from "react";
import Link from "next/link";
import VideoDemoModal from "@/components/VideoDemoModal";
import CustomVideoUploadCard from "@/components/CustomVideoUploadCard";

const API_BASE = "http://localhost:8000";

const C = {
  bg:        "#171412",
  card:      "#211C18",
  border:    "#3A3028",
  copper:    "#B45309",
  copperHov: "#D97706",
  text:      "#F8F5F0",
  sub:       "#A8A09A",
  muted:     "#786E65",
  green:     "#10B981",
  red:       "#EF4444",
  purple:    "#A855F7",
};

/* ── Sparkline SVG helper ────────────────────────────────────────────── */
function Sparkline({ color, path }: { color: string; path: string }) {
  return (
    <svg width="100%" height="16" viewBox="0 0 60 16" fill="none">
      <path d={path} stroke={color} strokeWidth="1.5" fill="none" />
    </svg>
  );
}

/* ── Skeleton pose SVG ────────────────────────────────────────────────── */
function SkeletonFigure({ side }: { side: "left" | "right" }) {
  const asymmetric = side === "right";
  return (
    <svg width="100" height="145" viewBox="0 0 100 140" fill="none">
      <circle cx="50" cy="20" r="7" stroke="#C8BFB4" strokeWidth="2" fill="none" />
      <line x1="50" y1="27" x2="50" y2="70" stroke="#C8BFB4" strokeWidth="2" />
      <line x1="30" y1="40" x2="70" y2="40" stroke="#C8BFB4" strokeWidth="2" />
      <line x1="30" y1="40" x2={asymmetric ? "22" : "20"} y2="65" stroke="#C8BFB4" strokeWidth="2" />
      <line x1="70" y1="40" x2={asymmetric ? "78" : "80"} y2="65" stroke="#C8BFB4" strokeWidth="2" />
      <line x1="38" y1="70" x2="62" y2="70" stroke="#C8BFB4" strokeWidth="2" />
      <line x1="42" y1="70" x2={asymmetric ? "32" : "35"} y2="105" stroke="#C8BFB4" strokeWidth="2" />
      <line x1={asymmetric ? "32" : "35"} y1="105" x2={asymmetric ? "38" : "42"} y2="135" stroke="#C8BFB4" strokeWidth="2" />
      <line x1="58" y1="70" x2={asymmetric ? "72" : "65"} y2="108" stroke={asymmetric ? C.red : "#C8BFB4"} strokeWidth={asymmetric ? 2.5 : 2} />
      <line x1={asymmetric ? "72" : "65"} y1="108" x2={asymmetric ? "62" : "55"} y2="135" stroke={asymmetric ? C.red : "#C8BFB4"} strokeWidth={asymmetric ? 2.5 : 2} />
      <circle cx="42" cy="70" r="3.5" fill={C.copper} />
      <circle cx="58" cy="70" r="3.5" fill={C.copper} />
      <circle cx={asymmetric ? "32" : "35"} cy="105" r="3.5" fill={C.copper} />
      <circle cx={asymmetric ? "72" : "65"} cy="108" r={asymmetric ? 4 : 3.5} fill={asymmetric ? C.red : C.copper} />
    </svg>
  );
}

/* ── Case card component ────────────────────────────────────────────── */
interface CaseCardProps {
  caseId: "case1" | "case2";
  title: string;
  risk: "LOW" | "HIGH";
  patientId: string;
  date: string;
  symmetry: string;
  kneeFlexion: string;
  hipFlexion: string;
  symmetryColor: string;
  kneeColor: string;
  hipColor: string;
  riskColor: string;
  onWatchDemo: () => void;
}

function CaseCard({ caseId, title, risk, patientId, date, symmetry, kneeFlexion, hipFlexion, symmetryColor, kneeColor, hipColor, riskColor, onWatchDemo }: CaseCardProps) {
  const isHigh = risk === "HIGH";
  const badgeBg    = isHigh ? "rgba(239,68,68,0.18)" : "rgba(16,185,129,0.15)";
  const badgeColor = isHigh ? C.red : C.green;
  const badgeBorder= isHigh ? "rgba(239,68,68,0.4)" : "rgba(16,185,129,0.4)";

  return (
    <div
      style={{
        background: C.card,
        border: `1px solid ${C.border}`,
        borderRadius: "12px",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
      }}
    >
      {/* Title + Risk Badge */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ fontSize: "11px", fontWeight: 700, color: C.text, letterSpacing: "0.04em" }}>{title}</div>
        <span style={{ padding: "3px 8px", borderRadius: "4px", fontSize: "10px", fontWeight: 700, background: badgeBg, color: badgeColor, border: `1px solid ${badgeBorder}` }}>
          {risk} RISK
        </span>
      </div>

      {/* Skeleton Preview Player */}
      <div
        style={{
          position: "relative",
          width: "100%",
          height: "180px",
          background: C.bg,
          borderRadius: "8px",
          border: `1px solid ${C.border}`,
          overflow: "hidden",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "space-around", padding: "10px", opacity: 0.9 }}>
          <SkeletonFigure side="left" />
          <SkeletonFigure side={isHigh ? "right" : "left"} />
        </div>
        <button
          onClick={onWatchDemo}
          style={{
            position: "relative", zIndex: 5,
            width: "42px", height: "42px",
            borderRadius: "50%",
            background: "rgba(33,28,24,0.8)",
            border: "1.5px solid #C8BFB4",
            color: C.text, fontSize: "16px",
            display: "flex", alignItems: "center", justifyContent: "center",
            cursor: "pointer",
            transition: "transform 0.15s ease",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.12)")}
          onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
        >▶</button>
        {/* Scrub bar */}
        <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, padding: "5px 10px", background: "rgba(23,20,18,0.85)", display: "flex", alignItems: "center", gap: "8px", zIndex: 4 }}>
          <span style={{ fontSize: "10px", color: C.sub }}>▶</span>
          <div style={{ flex: 1, height: "3px", background: "rgba(200,191,180,0.2)", borderRadius: "2px" }}>
            <div style={{ width: isHigh ? "20%" : "35%", height: "100%", background: C.copper, borderRadius: "2px" }} />
          </div>
          <span style={{ fontSize: "10px", color: C.sub, fontFamily: "monospace" }}>0:00 / 0:10</span>
          <span style={{ fontSize: "10px", color: C.sub }}>⤢</span>
        </div>
      </div>

      {/* Patient Metadata */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "11px", borderBottom: `1px solid ${C.border}`, paddingBottom: "10px" }}>
        <div><div style={{ color: C.muted, fontSize: "10px" }}>Patient ID</div><div style={{ fontWeight: 600, color: C.text }}>{patientId}</div></div>
        <div><div style={{ color: C.muted, fontSize: "10px" }}>Age</div><div style={{ fontWeight: 600, color: C.text }}>7 y/o</div></div>
        <div><div style={{ color: C.muted, fontSize: "10px" }}>Date</div><div style={{ fontWeight: 600, color: C.text }}>{date}</div></div>
      </div>

      {/* 4 Metric Tiles */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "7px" }}>
        {[
          { label: "Gait Symmetry",    value: symmetry,    color: symmetryColor, path: "M0 12 C10 12, 15 4, 25 8 C35 12, 45 3, 60 10" },
          { label: "Peak Knee Flexion", value: kneeFlexion, color: kneeColor,    path: "M0 10 C12 6, 20 14, 35 5 C45 10, 52 4, 60 8" },
          { label: "Hip Flexion ROM",   value: hipFlexion,  color: hipColor,     path: "M0 14 C15 4, 25 14, 40 6 C50 10, 55 5, 60 12" },
          { label: "Risk Level",        value: risk,        color: riskColor,    path: null },
        ].map(({ label, value, color, path }) => (
          <div key={label} style={{ background: C.bg, padding: "8px", borderRadius: "6px", border: `1px solid ${C.border}` }}>
            <div style={{ fontSize: "9px", color: C.muted, marginBottom: "2px" }}>{label}</div>
            <div style={{ fontSize: "14px", fontWeight: 700, color, margin: "2px 0" }}>{value}</div>
            {path && <Sparkline color={color} path={path} />}
          </div>
        ))}
      </div>

      {/* Watch Demo Button */}
      <button
        className="btn-copper-outline"
        onClick={onWatchDemo}
        style={{ width: "100%", marginTop: "2px", padding: "9px 14px", fontSize: "12px" }}
      >
        ▶ Watch Demo Video
      </button>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════ */

export default function DashboardPage() {
  const [modalOpen, setModalOpen]   = useState(false);
  const [activeDemo, setActiveDemo] = useState<"case1" | "case2">("case1");
  const [uploadedResult, setUploadedResult] = useState<Record<string, unknown> | null>(null);

  const openModal = (id: "case1" | "case2") => {
    setActiveDemo(id);
    setModalOpen(true);
    try {
      const caseData = id === "case1" ? {
        source_type: "case1",
        case_id: "case1",
        patient_info: { id: "PED-2026-001", age: "7 y/o", case: "Normative Control" },
        filename: "demo_normative.mp4"
      } : {
        source_type: "case2",
        case_id: "case2",
        patient_info: { id: "KT-2026-P902", age: "7 y/o", case: "Post-Injury Asymmetric Gait" },
        filename: "demo_asymmetric.mp4"
      };
      localStorage.setItem("kt_session", JSON.stringify(caseData));
    } catch (e) {}
  };

  const demo = {
    case1: {
      title: "CASE 1 - NORMATIVE CONTROL",
      patientId: "PED-2026-001",
      videoUrl: `${API_BASE}/api/video/demo_normative_annotated.webm`,
      riskStatus: "LOW RISK",
      riskBadgeColor: "green" as const,
      symmetry: "87.5%", kneeFlexion: "89.1°", hipFlexion: "125.1°",
    },
    case2: {
      title: "CASE 2 - POST-INJURY ASYMMETRIC GAIT",
      patientId: "KT-2026-P902",
      videoUrl: `${API_BASE}/api/video/demo_asymmetric_annotated.webm`,
      riskStatus: "HIGH RISK",
      riskBadgeColor: "red" as const,
      symmetry: "62.3%", kneeFlexion: "64.2°", hipFlexion: "98.7°",
    },
  };

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      {/* Main 2-column grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: "24px", alignItems: "start" }}>

        {/* ── LEFT COLUMN ─────────────────────────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

          {/* SECTION: Recent Analyses */}
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
              <span style={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: "20px", height: "20px", borderRadius: "4px", background: "rgba(180,83,9,0.15)", color: C.copper, fontSize: "12px", border: "1px solid rgba(180,83,9,0.3)" }}>
                ⇡
              </span>
              <h2 style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.text, margin: 0 }}>
                RECENT ANALYSES
              </h2>
            </div>
            <p style={{ fontSize: "12px", color: C.sub, margin: 0 }}>Select a case to view analysis demo</p>
          </div>

          {/* Two Demo Case Cards side-by-side */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: "16px" }}>
            <CaseCard
              caseId="case1"
              title="CASE 1 - NORMATIVE CONTROL"
              risk="LOW"
              patientId="PED-2026-001"
              date="May 28, 2026"
              symmetry="87.5%"   symmetryColor={C.green}
              kneeFlexion="89.1°" kneeColor={C.green}
              hipFlexion="125.1°" hipColor={C.green}
              riskColor={C.green}
              onWatchDemo={() => openModal("case1")}
            />
            <CaseCard
              caseId="case2"
              title="CASE 2 - POST-INJURY ASYMMETRIC GAIT"
              risk="HIGH"
              patientId="KT-2026-P902"
              date="May 27, 2026"
              symmetry="62.3%"   symmetryColor={C.copperHov}
              kneeFlexion="64.2°" kneeColor={C.copperHov}
              hipFlexion="98.7°"  hipColor={C.copperHov}
              riskColor={C.red}
              onWatchDemo={() => openModal("case2")}
            />
          </div>

          {/* CUSTOM VIDEO UPLOAD */}
          <CustomVideoUploadCard
            onUploadSuccess={(data) => setUploadedResult(data as unknown as Record<string, unknown>)}
            onResetUpload={() => setUploadedResult(null)}
          />

          {/* Upload success notice with direct link to Gait Results */}
          {uploadedResult && (
            <div
              style={{
                background: "rgba(16,185,129,0.1)",
                border: "1px solid rgba(16,185,129,0.35)",
                borderRadius: "10px",
                padding: "14px 16px",
                fontSize: "12px",
                color: C.green,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "10px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span>✅</span>
                <span>Custom video quality validated &amp; gait analysis complete! Pose landmarks and joint kinematics are active.</span>
              </div>
              <Link href="/agents/biomechanical" style={{ textDecoration: "none" }}>
                <button className="btn-copper" style={{ padding: "6px 14px", fontSize: "12px", fontWeight: 700 }}>
                  📊 View Gait Results →
                </button>
              </Link>
            </div>
          )}
        </div>

        {/* ── RIGHT COLUMN: AI Agent Pipeline ─────────────────────────── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div style={{ background: C.card, border: `1px solid ${C.border}`, borderRadius: "12px", padding: "18px", display: "flex", flexDirection: "column", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "16px" }}>🤖</span>
              <h3 style={{ fontSize: "12px", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: C.text, margin: 0 }}>
                AI AGENT PIPELINE
              </h3>
            </div>

            {/* Pipeline Steps */}
            {[
              {
                num: "✓", color: C.green, borderColor: "rgba(16,185,129,0.35)", bg: "rgba(16,185,129,0.08)",
                title: "Video Quality & Biomechanical Analyst",
                badge: "COMPLETED", badgeBg: "rgba(16,185,129,0.15)", badgeColor: C.green, badgeBorder: "rgba(16,185,129,0.4)",
                desc: "Quantitative telemetry grids, ROM curves, and video quality validation.",
                href: "/agents/biomechanical",
                numBg: C.green,
              },
              {
                num: "2", color: C.copper, borderColor: "rgba(180,83,9,0.45)", bg: "rgba(180,83,9,0.1)",
                title: "Gait Kinematic Analysis Agent",
                badge: "ACTIVE", badgeBg: "rgba(180,83,9,0.2)", badgeColor: C.copperHov, badgeBorder: "rgba(180,83,9,0.5)",
                desc: "3D pose estimation, joint angle calculation, and gait metrics extraction.",
                href: "/agents/biomechanical",
                numBg: C.copper,
              },
              {
                num: "3", color: C.sub, borderColor: C.border, bg: C.bg,
                title: "Clinical Risk Assessment Agent",
                badge: "PENDING", badgeBg: "rgba(120,110,101,0.2)", badgeColor: C.sub, badgeBorder: "rgba(120,110,101,0.4)",
                desc: "Risk classification and clinical reasoning based on gait data.",
                href: "/agents/clinical-risk",
                numBg: "#3A3028",
              },
              {
                num: "4", color: C.sub, borderColor: C.border, bg: C.bg,
                title: "Patient Gait Progress Comparison Agent",
                badge: "PENDING", badgeBg: "rgba(120,110,101,0.2)", badgeColor: C.sub, badgeBorder: "rgba(120,110,101,0.4)",
                desc: "Compare old vs new gait videos to track progress objectively.",
                href: "/agents/patient-progress",
                numBg: "#3A3028",
              },
              {
                num: "6", color: C.sub, borderColor: C.border, bg: C.bg,
                title: "Empathetic Parent & Caregiver Translator Agent",
                badge: "ACTIVE", badgeBg: "rgba(180,83,9,0.2)", badgeColor: C.copperHov, badgeBorder: "rgba(180,83,9,0.5)",
                desc: "Jargon-free family guides explaining movement metrics for daily play.",
                href: "/agents/empathetic-translator",
                numBg: C.copper,
              },
            ].map((step) => (
              <Link key={step.num} href={step.href} style={{ textDecoration: "none" }}>
                <div
                  style={{
                    background: step.bg,
                    border: `1px solid ${step.borderColor}`,
                    borderRadius: "10px",
                    padding: "12px 14px",
                    transition: "all 0.15s ease",
                    cursor: "pointer",
                    boxShadow: step.num === "2" ? "0 0 12px rgba(180,83,9,0.1)" : "none",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = C.copper; }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = step.borderColor; }}
                >
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "6px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <div style={{ width: "22px", height: "22px", borderRadius: "50%", background: step.numBg, color: "#F8F5F0", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "11px", fontWeight: 700, boxShadow: step.num === "2" ? `0 0 8px ${C.copper}` : "none" }}>
                        {step.num}
                      </div>
                      <span style={{ fontWeight: step.num === "2" ? 700 : 600, fontSize: "12px", color: step.num === "2" ? C.text : "#C8BFB4" }}>
                        {step.title}
                      </span>
                    </div>
                    <span style={{ padding: "2px 7px", borderRadius: "4px", fontSize: "9px", fontWeight: 700, background: step.badgeBg, color: step.badgeColor, border: `1px solid ${step.badgeBorder}`, whiteSpace: "nowrap" }}>
                      {step.badge}
                    </span>
                  </div>
                  <p style={{ fontSize: "11px", color: "#786E65", margin: "4px 0 0 32px", lineHeight: 1.4 }}>
                    {step.desc}
                  </p>
                </div>
              </Link>
            ))}

            {/* View Full Pipeline Button */}
            <Link href="/agents/biomechanical" style={{ textDecoration: "none", marginTop: "4px" }}>
              <button className="btn-copper-outline" style={{ width: "100%" }}>
                View Full Pipeline →
              </button>
            </Link>
          </div>
        </div>
      </div>

      {/* Demo Video Modal */}
      <VideoDemoModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        {...demo[activeDemo]}
      />
    </div>
  );
}
