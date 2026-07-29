"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import FormattedMarkdownText from "./FormattedMarkdownText";

const API_BASE = "http://localhost:8000";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  category?: string;
  hasPdfReport?: boolean;
  timestamp: string;
}

export default function ClinicalAssistantChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Active session context from localStorage
  const [session, setSession] = useState<any>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-1",
      sender: "assistant",
      text: "👋 **Hello! I am KinemaTrace AI Clinical Assistant (Agent 5).**\n\nI access persistent outputs from Agents 1–4 to answer clinical questions, explain risk findings, interpret gait metrics against normal baselines, compare longitudinal progress, and generate patient PDF reports.\n\nHow can I assist you with the current patient today?",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);

  // Sync active patient & progress comparison context from localStorage on open / mount
  const syncSession = () => {
    try {
      const storedSession = localStorage.getItem("kt_session");
      const storedProgress = localStorage.getItem("kt_progress_session");

      let mergedContext: any = {};
      if (storedSession) {
        try {
          mergedContext = JSON.parse(storedSession);
        } catch (e) {}
      }

      if (storedProgress) {
        try {
          const prog = JSON.parse(storedProgress);
          mergedContext.progress_session = prog;
          mergedContext.patient_progress = prog;
          mergedContext.comparison = prog.comparison;
          mergedContext.old_video = prog.old_video;
          mergedContext.new_video = prog.new_video;
          mergedContext.overall_progress = prog.overall_progress;
          mergedContext.key_findings = prog.key_findings;
          mergedContext.summary = prog.summary;
        } catch (e) {}
      }

      setSession(mergedContext);
    } catch (e) {
      console.warn("Could not read localStorage items", e);
    }
  };

  useEffect(() => {
    syncSession();
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen]);

  const patientId = session?.patient_info?.id || "KT-2026-P902";
  const caseName = session?.patient_info?.case || "Outpatient Gait Screening";
  const currentVideoName = session?.filename || session?.video_name || (session?.patient_info?.id === "PED-2026-001" ? "demo_normative.mp4" : "demo_asymmetric.mp4");
  const baselineVideoName = session?.old_video?.file_name || session?.old_video?.filename || null;

  const handleSend = async (customQuery?: string) => {
    const textToSend = customQuery || input;
    if (!textToSend.trim() || loading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customQuery) setInput("");
    setLoading(true);

    try {
      const currentSession = session || {};
      const res = await fetch(`${API_BASE}/api/agents/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: textToSend,
          context: currentSession,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const botMsg: Message = {
        id: `assistant-${Date.now()}`,
        sender: "assistant",
        text: data.response || data.report_text || "No response received.",
        category: data.category,
        hasPdfReport: data.has_pdf_report || data.category === "report_generation" || textToSend.toLowerCase().includes("report") || textToSend.toLowerCase().includes("pdf"),
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        sender: "assistant",
        text: `⚠️ Error: Could not connect to Clinical AI Assistant server. Ensure the backend is running on http://localhost:8000.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyText = (msgId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleDownloadPdf = async () => {
    try {
      const currentSession = session || {};
      const res = await fetch(`${API_BASE}/api/generate-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: patientId,
          context: currentSession,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `KinemaTrace_Report_${patientId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (e) {
      console.error("Failed to download PDF report:", e);
      window.open(`${API_BASE}/api/generate-pdf?patient_id=${patientId}`, "_blank");
    }
  };

  const quickActionButtons = [
    { label: "📊 Summarize Patient", query: "Summarize this patient." },
    { label: "⚠️ Explain Risk", query: "Why is this patient high risk?" },
    { label: "📈 Analyze Progress", query: "Has the patient improved?" },
    { label: "🔍 Compare With Normal", query: "Compare this patient with normal values." },
    { label: "🦵 Explain Gait Metrics", query: "What is the patient's left knee ROM and gait symmetry?" },
    { label: "📄 Generate PDF Report", query: "Generate a patient report PDF." },
  ];

  return (
    <div style={{ position: "fixed", bottom: "24px", right: "24px", zIndex: 9999 }}>
      {/* ── Chat Window Modal ──────────────────────────────────────────────── */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
            style={{
              width: "440px",
              height: "640px",
              background: "#171412",
              border: "1px solid #3A3028",
              borderRadius: "16px",
              boxShadow: "0 12px 40px rgba(0,0,0,0.6), 0 0 30px rgba(180,83,9,0.15)",
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
              marginBottom: "14px",
            }}
          >
            {/* Header */}
            <div
              style={{
                padding: "14px 18px",
                background: "#211C18",
                borderBottom: "1px solid #3A3028",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div
                  style={{
                    width: "34px",
                    height: "34px",
                    borderRadius: "8px",
                    background: "linear-gradient(135deg, #B45309 0%, #78350F 100%)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "18px",
                    boxShadow: "0 0 12px rgba(180,83,9,0.4)",
                  }}
                >
                  🤖
                </div>
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 800, color: "#F8F5F0", letterSpacing: "-0.01em" }}>
                    KinemaTrace AI Assistant
                  </div>
                  <div style={{ fontSize: "11px", color: "#A8A09A" }}>
                    Agent 5 · Clinical Conversational Intelligence
                  </div>
                </div>
              </div>

              <button
                onClick={() => setIsOpen(false)}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#A8A09A",
                  fontSize: "18px",
                  cursor: "pointer",
                  padding: "4px 8px",
                  borderRadius: "6px",
                }}
              >
                ✕
              </button>
            </div>

            {/* Active Patient Context Badge Bar */}
            <div
              style={{
                padding: "8px 16px",
                background: "#171412",
                borderBottom: "1px solid #3A3028",
                fontSize: "11px",
                color: "#A8A09A",
                display: "flex",
                flexDirection: "column",
                gap: "4px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div>
                  Patient ID: <strong style={{ color: "#D97706" }}>{patientId}</strong>
                </div>
                <div style={{ color: "#786E65", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {caseName}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", fontSize: "10px", color: "#786E65" }}>
                <div>Current: <span style={{ color: "#F8F5F0" }}>{currentVideoName}</span></div>
                {baselineVideoName && <div>Baseline: <span style={{ color: "#F8F5F0" }}>{baselineVideoName}</span></div>}
              </div>
            </div>

            {/* Quick Action Chips Bar */}
            <div
              style={{
                padding: "8px 12px",
                background: "#211C18",
                borderBottom: "1px solid #3A3028",
                display: "flex",
                gap: "6px",
                overflowX: "auto",
                whiteSpace: "nowrap",
              }}
            >
              {quickActionButtons.map((chip) => (
                <button
                  key={chip.label}
                  onClick={() => handleSend(chip.query)}
                  disabled={loading}
                  style={{
                    padding: "5px 10px",
                    borderRadius: "14px",
                    border: "1px solid #3A3028",
                    background: "#171412",
                    color: "#F8F5F0",
                    fontSize: "10px",
                    fontWeight: 600,
                    cursor: loading ? "wait" : "pointer",
                    transition: "all 0.2s",
                  }}
                >
                  {chip.label}
                </button>
              ))}
            </div>

            {/* Message Feed */}
            <div
              style={{
                flex: 1,
                padding: "16px",
                overflowY: "auto",
                display: "flex",
                flexDirection: "column",
                gap: "14px",
                background: "#171412",
              }}
            >
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    alignItems: msg.sender === "user" ? "flex-end" : "flex-start",
                  }}
                >
                  <div
                    style={{
                      maxWidth: "88%",
                      padding: "12px 14px",
                      borderRadius: msg.sender === "user" ? "14px 14px 2px 14px" : "14px 14px 14px 2px",
                      background: msg.sender === "user" ? "linear-gradient(135deg, #B45309 0%, #78350F 100%)" : "#211C18",
                      border: msg.sender === "user" ? "1px solid #B45309" : "1px solid #3A3028",
                      color: "#F8F5F0",
                      fontSize: "12px",
                      lineHeight: 1.6,
                      boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
                      position: "relative",
                    }}
                  >
                    <FormattedMarkdownText text={msg.text} />

                    {/* PDF Report Download Button Inside Chat Response */}
                    {msg.sender === "assistant" && (msg.hasPdfReport || msg.category === "report_generation" || msg.text.includes("PEDIATRIC GAIT SCREENING REPORT")) && (
                      <div style={{ marginTop: "12px", paddingTop: "10px", borderTop: "1px solid #3A3028" }}>
                        <button
                          onClick={handleDownloadPdf}
                          style={{
                            width: "100%",
                            padding: "8px 12px",
                            borderRadius: "8px",
                            background: "linear-gradient(135deg, #10B981 0%, #047857 100%)",
                            border: "1px solid #059669",
                            color: "#FFFFFF",
                            fontSize: "11px",
                            fontWeight: 700,
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            gap: "6px",
                            boxShadow: "0 2px 8px rgba(16,185,129,0.3)",
                          }}
                        >
                          📄 Download PDF Report
                        </button>
                      </div>
                    )}

                    {msg.sender === "assistant" && (
                      <div style={{ marginTop: "8px", display: "flex", justifyContent: "flex-end" }}>
                        <button
                          onClick={() => handleCopyText(msg.id, msg.text)}
                          style={{
                            background: "transparent",
                            border: "none",
                            color: copiedId === msg.id ? "#10B981" : "#A8A09A",
                            fontSize: "10px",
                            cursor: "pointer",
                          }}
                        >
                          {copiedId === msg.id ? "✓ Copied" : "📋 Copy"}
                        </button>
                      </div>
                    )}
                  </div>
                  <div style={{ fontSize: "9px", color: "#786E65", marginTop: "4px", paddingInline: "4px" }}>
                    {msg.timestamp}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Box */}
            <div
              style={{
                padding: "12px 16px",
                background: "#211C18",
                borderTop: "1px solid #3A3028",
                display: "flex",
                gap: "10px",
                alignItems: "center",
              }}
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Ask about this patient's analysis..."
                disabled={loading}
                style={{
                  flex: 1,
                  padding: "10px 14px",
                  borderRadius: "8px",
                  background: "#171412",
                  border: "1px solid #3A3028",
                  color: "#F8F5F0",
                  fontSize: "12px",
                  outline: "none",
                }}
              />
              <button
                onClick={() => handleSend()}
                disabled={loading || !input.trim()}
                style={{
                  padding: "10px 16px",
                  borderRadius: "8px",
                  background: loading || !input.trim() ? "#3A3028" : "linear-gradient(135deg, #B45309 0%, #78350F 100%)",
                  color: "#F8F5F0",
                  border: "none",
                  fontSize: "12px",
                  fontWeight: 700,
                  cursor: loading || !input.trim() ? "not-allowed" : "pointer",
                }}
              >
                {loading ? "…" : "▶"}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Floating Toggle Button ─────────────────────────────────────────── */}
      <button
        id="open-clinical-chatbot-btn"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: "56px",
          height: "56px",
          borderRadius: "28px",
          background: "linear-gradient(135deg, #B45309 0%, #78350F 100%)",
          border: "2px solid #D97706",
          color: "#F8F5F0",
          fontSize: "24px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          boxShadow: "0 6px 20px rgba(180,83,9,0.4), 0 0 30px rgba(180,83,9,0.2)",
          position: "relative",
        }}
      >
        💬
        <span
          style={{
            position: "absolute",
            top: "-4px",
            right: "-4px",
            background: "#10B981",
            color: "#000",
            fontSize: "9px",
            fontWeight: 800,
            padding: "2px 6px",
            borderRadius: "10px",
            border: "1px solid #171412",
          }}
        >
          A5
        </span>
      </button>
    </div>
  );
}
