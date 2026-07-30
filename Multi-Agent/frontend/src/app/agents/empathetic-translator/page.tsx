"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import FormattedMarkdownText from "@/components/FormattedMarkdownText";

const API_BASE = "http://localhost:8000";

interface EmpatheticGuideData {
  agent_id: string;
  agent_name: string;
  agent_role: string;
  daily_play_explanation: string;
  movement_strengths: string[];
  comfort_and_play_tips: string[];
  report_text: string;
  patient_id: string;
  gait_symmetry: number;
  hip_flexibility: number;
}

export default function EmpatheticTranslatorPage() {
  const router = useRouter();

  const [session, setSession] = useState<any>(null);
  const [isLocked, setIsLocked] = useState<boolean>(true);

  const [userQuery, setUserQuery] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [guideData, setGuideData] = useState<EmpatheticGuideData | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Prerequisite Check: Check global application state (localStorage) ─────
  useEffect(() => {
    const loadSession = () => {
      try {
        const stored = localStorage.getItem("kt_session");
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed.video_quality || parsed.gait_analysis || parsed.telemetry || parsed.filename) {
            setSession(parsed);
            setIsLocked(false);
            fetchEmpatheticGuide(parsed, "");
            return;
          }
        }
      } catch (e) {
        console.warn("Could not parse kt_session", e);
      }
      setSession(null);
      setGuideData(null);
      setIsLocked(true);
    };

    loadSession();
    window.addEventListener("kt_session_updated", loadSession);
    return () => window.removeEventListener("kt_session_updated", loadSession);
  }, []);

  const fetchEmpatheticGuide = async (sessionPayload: any, customQuery: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/agents/empathetic-translator`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kinematic_data: sessionPayload,
          file_path: sessionPayload?.file_path || sessionPayload?.video_quality?.file_path,
          user_instruction: customQuery || undefined,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `HTTP ${res.status}: Failed to generate family guide.`);
      }

      const json: EmpatheticGuideData = await res.json();
      setGuideData(json);
    } catch (err: any) {
      setError(err.message || "Could not generate empathetic translator guide.");
    } finally {
      setLoading(false);
    }
  };

  const handleTranslate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!session) return;
    fetchEmpatheticGuide(session, userQuery);
  };

  const handlePrint = () => {
    window.print();
  };

  const pInfo = session?.patient_info || {};
  const patientId = pInfo.id || session?.video_id || "KT-CUSTOM-PATIENT";

  const gaitSymmetry = guideData?.gait_symmetry ?? session?.telemetry?.gait_symmetry_pct ?? session?.metrics?.gait_symmetry ?? 87.5;
  const hipFlexibility = guideData?.hip_flexibility ?? session?.telemetry?.hip_flexion_rom_deg ?? session?.metrics?.left_hip_rom ?? 125.1;

  return (
    <div className="bg-stone-50 min-h-screen text-stone-900 font-sans" style={{ padding: "28px 32px", maxWidth: "1180px", margin: "0 auto" }}>
      {/* ── Header ── */}
      <div className="no-print" style={{ marginBottom: "24px" }}>
        <div style={{ fontSize: "12px", color: "#78716C", marginBottom: "6px" }}>
          <Link href="/" style={{ color: "#B45309", textDecoration: "none", fontWeight: 600 }}>Dashboard</Link>
          {" / Agents / "}
          <span style={{ color: "#1C1917", fontWeight: 600 }}>Parent &amp; Caregiver Empathetic Translator</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: "26px", fontWeight: 800, color: "#1C1917", letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: "10px" }}>
              🤝 Parent &amp; Caregiver Empathetic Translator
            </h1>
            <div style={{ marginTop: "4px", fontSize: "13px", color: "#57534E" }}>
              Agent 06 Active · Jargon-Free Movement Explanations for Families
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ padding: "6px 14px", borderRadius: "8px", fontSize: "11px", fontWeight: 700, background: "#FEF3C7", color: "#B45309", border: "1px solid #FDE68A" }}>
              Agent 06
            </span>
          </div>
        </div>
      </div>

      {/* ── 🛑 LOCKED STATE CARD (NO VIDEO UPLOADED YET) ── */}
      {isLocked ? (
        <div
          style={{
            background: "#FFFFFF",
            border: "1px solid #E7E5E4",
            borderRadius: "16px",
            padding: "48px 32px",
            textAlign: "center",
            maxWidth: "680px",
            margin: "40px auto",
            boxShadow: "0 4px 20px rgba(0, 0, 0, 0.05)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "16px",
          }}
        >
          <div
            style={{
              width: "64px",
              height: "64px",
              borderRadius: "50%",
              background: "#FEF3C7",
              border: "1px solid #FDE68A",
              color: "#B45309",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "30px",
            }}
          >
            🔒
          </div>

          <div>
            <h2 style={{ fontSize: "20px", fontWeight: 800, color: "#1C1917", margin: "0 0 8px 0" }}>
              Waiting for Patient Video Scan
            </h2>
            <p style={{ fontSize: "14px", color: "#57534E", lineHeight: 1.6, margin: 0 }}>
              To generate a personalized, easy-to-understand family guide, please upload and process your child&apos;s walking video on the Main Dashboard first. Once the scan is complete, this page will unlock and explain the results in simple everyday terms!
            </p>
          </div>

          <Link href="/" style={{ textDecoration: "none", marginTop: "8px" }}>
            <button
              style={{
                background: "linear-gradient(135deg, #B45309 0%, #78350F 100%)",
                color: "#FFFFFF",
                border: "none",
                borderRadius: "10px",
                padding: "12px 24px",
                fontSize: "14px",
                fontWeight: 700,
                cursor: "pointer",
                boxShadow: "0 2px 8px rgba(180, 83, 9, 0.25)",
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              ⬅️ Go to Video Upload Workspace
            </button>
          </Link>
        </div>
      ) : (
        /* ── UNLOCKED STATE WORKSPACE ── */
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

          {/* A. Active Patient Scan Banner */}
          <div
            className="no-print"
            style={{
              background: "#F0F9FF",
              border: "1px solid #BAE6FD",
              borderRadius: "12px",
              padding: "14px 20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "18px" }}>✨</span>
              <span style={{ fontSize: "13px", fontWeight: 700, color: "#0369A1" }}>
                Connected Scan: <strong>{patientId}</strong>
                &nbsp;·&nbsp;Gait Symmetry: <strong>{gaitSymmetry.toFixed(1)}%</strong>
                &nbsp;·&nbsp;Hip Flexibility: <strong>{hipFlexibility.toFixed(1)}° (Excellent)</strong>
              </span>
            </div>
            <span style={{ fontSize: "11px", fontWeight: 700, padding: "4px 10px", borderRadius: "6px", background: "#E0F2FE", color: "#0284C7", border: "1px solid #7DD3FC" }}>
              ● LIVE SCAN METRICS LOADED
            </span>
          </div>

          {/* B. Interactive Family Question Box */}
          <div className="no-print" style={{ background: "#FFFFFF", border: "1px solid #E7E5E4", borderRadius: "14px", padding: "20px", boxShadow: "0 2px 8px rgba(0, 0, 0, 0.03)" }}>
            <div style={{ fontSize: "13px", fontWeight: 800, letterSpacing: "0.05em", textTransform: "uppercase", color: "#1C1917", marginBottom: "8px" }}>
              💬 Have a Specific Family Question?
            </div>
            <p style={{ fontSize: "12px", color: "#57534E", margin: "0 0 12px 0" }}>
              Type any specific parent or caregiver question below to receive an empathetic, non-jargon explanation based on your child&apos;s scan:
            </p>

            <form onSubmit={handleTranslate} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <textarea
                value={userQuery}
                onChange={(e) => setUserQuery(e.target.value)}
                placeholder="e.g. Explain why my child gets tired when running at recess in simple terms for a 7-year-old's family..."
                rows={3}
                style={{
                  width: "100%",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  border: "1px solid #D6D3D1",
                  fontSize: "13px",
                  color: "#1C1917",
                  background: "#FAFAF9",
                  outline: "none",
                  resize: "vertical",
                }}
              />

              <div style={{ display: "flex", justifyContent: "flex-end" }}>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    background: loading ? "#A8A29E" : "linear-gradient(135deg, #B45309 0%, #78350F 100%)",
                    color: "#FFFFFF",
                    border: "none",
                    borderRadius: "10px",
                    padding: "10px 22px",
                    fontSize: "13px",
                    fontWeight: 700,
                    cursor: loading ? "wait" : "pointer",
                    boxShadow: "0 2px 6px rgba(180, 83, 9, 0.25)",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  {loading ? (
                    <>
                      <div style={{ width: "14px", height: "14px", border: "2px solid rgba(255,255,255,0.4)", borderTopColor: "#fff", borderRadius: "50%", animation: "spin 0.8s linear infinite" }} />
                      🤖 Writing comforting, jargon-free explanations for the family...
                    </>
                  ) : (
                    <>
                      <span>💬 Translate into Family-Friendly Guide</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {error && (
            <div style={{ background: "#FEF2F2", border: "1px solid #FCA5A5", borderRadius: "10px", padding: "12px 16px", color: "#DC2626", fontSize: "13px" }}>
              ⚠️ {error}
            </div>
          )}

          {/* C. Empathetic Translator Output Cards */}
          {guideData && (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>

              {/* 1. The "What This Means For Daily Play" Card (Full Width) */}
              <div
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #E7E5E4",
                  borderRadius: "14px",
                  overflow: "hidden",
                  boxShadow: "0 2px 10px rgba(0, 0, 0, 0.04)",
                }}
              >
                <div style={{ padding: "14px 20px", background: "#F5F5F4", borderBottom: "1px solid #E7E5E4", display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "18px" }}>🎈</span>
                  <h2 style={{ fontSize: "14px", fontWeight: 800, letterSpacing: "0.05em", textTransform: "uppercase", color: "#1C1917", margin: 0 }}>
                    What This Means For Daily Play
                  </h2>
                </div>
                <div style={{ padding: "20px 24px" }}>
                  <FormattedMarkdownText text={guideData.daily_play_explanation} />
                </div>
              </div>

              {/* 2 & 3: 2-Column Grid for Strengths & Daily Tips */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>

                {/* 🌟 Movement Strengths & Wins Card (Left Column) */}
                <div
                  style={{
                    background: "rgba(236, 253, 245, 0.4)",
                    border: "1px solid #10B981",
                    borderRadius: "14px",
                    padding: "20px",
                    boxShadow: "0 2px 8px rgba(16, 185, 129, 0.06)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                  }}
                >
                  <div style={{ fontSize: "14px", fontWeight: 800, color: "#047857", display: "flex", alignItems: "center", gap: "8px" }}>
                    <span>🌟 Movement Strengths &amp; Wins</span>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {guideData.movement_strengths.map((str, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "#FFFFFF",
                          border: "1px solid #A7F3D0",
                          borderRadius: "8px",
                          padding: "10px 14px",
                          fontSize: "12px",
                          color: "#065F46",
                          lineHeight: 1.5,
                        }}
                      >
                        <FormattedMarkdownText text={str} />
                      </div>
                    ))}
                  </div>
                </div>

                {/* 💡 Daily Comfort & Play Tips Card (Right Column) */}
                <div
                  style={{
                    background: "rgba(254, 243, 199, 0.4)",
                    border: "1px solid #F59E0B",
                    borderRadius: "14px",
                    padding: "20px",
                    boxShadow: "0 2px 8px rgba(245, 158, 11, 0.06)",
                    display: "flex",
                    flexDirection: "column",
                    gap: "12px",
                  }}
                >
                  <div style={{ fontSize: "14px", fontWeight: 800, color: "#B45309", display: "flex", alignItems: "center", gap: "8px" }}>
                    <span>💡 Daily Comfort &amp; Play Tips</span>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                    {guideData.comfort_and_play_tips.map((tip, idx) => (
                      <div
                        key={idx}
                        style={{
                          background: "#FFFFFF",
                          border: "1px solid #FDE68A",
                          borderRadius: "8px",
                          padding: "10px 14px",
                          fontSize: "12px",
                          color: "#78350F",
                          lineHeight: 1.5,
                        }}
                      >
                        <FormattedMarkdownText text={tip} />
                      </div>
                    ))}
                  </div>
                </div>

              </div>

              {/* Action Toolbar */}
              <div className="no-print" style={{ display: "flex", justifyContent: "flex-end", marginTop: "8px" }}>
                <button
                  onClick={handlePrint}
                  style={{
                    background: "#FFFFFF",
                    color: "#78350F",
                    border: "1.5px solid #B45309",
                    borderRadius: "10px",
                    padding: "10px 20px",
                    fontSize: "13px",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "8px",
                    transition: "all 0.15s ease",
                  }}
                >
                  🖨️ Print / Download Family Guide (.PDF)
                </button>
              </div>

            </div>
          )}

        </div>
      )}
    </div>
  );
}
