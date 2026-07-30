"use client";

import React from "react";
import FormattedMarkdownText from "./FormattedMarkdownText";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface RechartsDataPoint {
  metric: string;
  Patient: number;
  Normative: number;
}

interface ClinicalRiskPayload {
  risk_level: "HIGH" | "MEDIUM" | "LOW";
  severity: string;
  asymmetry_percentage: number;
  peak_asymmetry_percentage: number;
  affected_side: string;
  triggered_measurements: string[];
  reasoning: string;
  recommendation: string;
  thresholds_used: {
    low_risk_max_si_pct: number;
    high_risk_min_si_pct: number;
    rom_deficit_flag_deg: number;
  };
}

interface PatientProgressPayload {
  patient_id: string;
  trend: "IMPROVING" | "STABLE" | "WORSENING" | "INSUFFICIENT_DATA" | "FLUCTUATING";
  data_available: boolean;
  total_history_sessions: number;
  current_asymmetry: number;
  previous_asymmetry?: number;
  asymmetry_change?: number;
  current_risk_level: string;
  previous_risk_level?: string;
  risk_change?: string;
  key_changes: string[];
  explanation: string;
  recommendation: string;
  chart_data: Array<{
    session: number;
    date: string;
    asymmetry_pct: number;
    risk_score: number;
    risk_level: string;
    is_current?: boolean;
  }>;
}

interface VideoQualityPayload {
  video_quality_score: number;
  status: "PASS" | "WARNING" | "FAIL";
  checks: Record<string, string>;
  metrics: Record<string, number>;
  issues: Array<{
    criterion: string;
    reason: string;
    impact: string;
    recommendation: string;
  }>;
  recommendation: string;
}

interface AgentReport {
  agent_id: string;
  agent_name: string;
  agent_role: string;
  report_text: string;
  metrics: Record<string, number | string>;
  recharts_data: RechartsDataPoint[];
  executive_summary?: string;
  video_quality?: VideoQualityPayload;
  clinical_risk?: ClinicalRiskPayload;
  patient_progress?: PatientProgressPayload;
}

interface AgentCommandCenterProps {
  caseId: string;
  report: AgentReport | null;
  loadingAgent: string | null;
  onFetchAgent: (agentId: string) => void;
  activeSource?: "custom" | "case1" | "case2";
  filePath?: string | null;
  pipelineState?: {
    agent1: "COMPLETED" | "ACTIVE" | "PENDING" | "FAILED";
    agent2: "COMPLETED" | "ACTIVE" | "PENDING";
    agent3: "COMPLETED" | "ACTIVE" | "PENDING";
    agent4: "PENDING" | "ACTIVE" | "COMPLETED";
  };
}

const AGENTS = [
  { id: "quality",       icon: "🎥", label: "Video Quality\nAgent 1",       num: "01" },
  { id: "analyst",       icon: "🔬", label: "Gait Analysis\nAgent 2",       num: "02" },
  { id: "clinical-risk", icon: "🛡️", label: "Clinical Risk\nAgent 3",       num: "03" },
  { id: "progress",      icon: "📊", label: "Gait Progress\nAgent 4",       num: "04" },
  { id: "assistant",     icon: "🤖", label: "Clinical AI\nAgent 5",         num: "05" },
];

export default function AgentCommandCenter({
  caseId,
  report,
  loadingAgent,
  onFetchAgent,
  activeSource = "case2",
  filePath = null,
  pipelineState,
}: AgentCommandCenterProps) {
  const [activeAgent, setActiveAgent] = React.useState<string | null>(null);

  const handleSelect = (agentId: string) => {
    setActiveAgent(agentId);
    onFetchAgent(agentId);
  };

  const defaultState = activeSource === "custom" ? {
    agent1: "COMPLETED" as const,
    agent2: "COMPLETED" as const,
    agent3: "COMPLETED" as const,
    agent4: "PENDING" as const,
    agent5: "COMPLETED" as const,
  } : {
    agent1: "COMPLETED" as const,
    agent2: "COMPLETED" as const,
    agent3: "COMPLETED" as const,
    agent4: "PENDING" as const,
    agent5: "COMPLETED" as const,
  };

  const pState = pipelineState ? { ...defaultState, ...pipelineState } : defaultState;

  const getStatusBadge = (status: "COMPLETED" | "ACTIVE" | "PENDING" | "FAILED") => {
    switch (status) {
      case "COMPLETED":
        return { text: "COMPLETED", bg: "rgba(16,185,129,0.15)", color: "#10B981", border: "rgba(16,185,129,0.3)" };
      case "ACTIVE":
        return { text: "ACTIVE", bg: "rgba(217,119,6,0.18)", color: "#D97706", border: "rgba(217,119,6,0.4)" };
      case "FAILED":
        return { text: "FAILED", bg: "rgba(239,68,68,0.18)", color: "#EF4444", border: "rgba(239,68,68,0.4)" };
      default:
        return { text: "PENDING", bg: "rgba(120,110,101,0.2)", color: "#A8A09A", border: "rgba(120,110,101,0.3)" };
    }
  };

  return (
    <div
      className="glass-card"
      style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden" }}
    >
      {/* Panel header */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid var(--ehr-border)",
          background: "rgba(15,20,35,0.6)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <div style={{ fontWeight: 600, fontSize: "13px", marginBottom: "2px" }}>
              🤖 Multi-Agent Clinical Command Center
            </div>
            <div style={{ fontSize: "11px", color: activeSource === "custom" ? "#D97706" : "var(--ehr-muted)" }}>
              {activeSource === "custom"
                ? "🔒 Processing Custom Uploaded Video"
                : `Active Mode: ${caseId === "case1" ? "Case 1 (Normative Control)" : "Case 2 (Asymmetric Gait)"}`}
            </div>
          </div>
        </div>

        {/* Dynamic Pipeline Stepper Header */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: "4px", marginTop: "10px" }}>
          {[
            { name: "Agent 1 Quality", status: pState.agent1 },
            { name: "Agent 2 Gait", status: pState.agent2 },
            { name: "Agent 3 Risk", status: pState.agent3 },
            { name: "Agent 4 Progress", status: pState.agent4 },
            { name: "Agent 5 AI", status: "COMPLETED" as const },
          ].map((st, i) => {
            const b = getStatusBadge(st.status);
            return (
              <div
                key={i}
                style={{
                  background: b.bg,
                  border: `1px solid ${b.border}`,
                  borderRadius: "6px",
                  padding: "4px 4px",
                  textAlign: "center",
                }}
              >
                <div style={{ fontSize: "9px", color: "#F8F5F0", fontWeight: 600, whiteSpace: "nowrap" }}>
                  {st.name}
                </div>
                <div style={{ fontSize: "8px", fontWeight: 800, color: b.color, marginTop: "1px" }}>
                  {b.text}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Horizontal agent nav */}
      <div
        style={{
          display: "flex",
          gap: "6px",
          padding: "10px 12px",
          borderBottom: "1px solid var(--ehr-border)",
          overflowX: "auto",
        }}
      >
        {AGENTS.map((a) => (
          <button
            key={a.id}
            id={`agent-tab-${a.id}`}
            className={`agent-tab${activeAgent === a.id ? " active" : ""}`}
            onClick={() => handleSelect(a.id)}
            disabled={!!loadingAgent}
            title={a.label.replace("\n", " ")}
          >
            <span style={{ fontSize: "18px" }}>{a.icon}</span>
            <span style={{ fontSize: "9px", opacity: 0.6, fontWeight: 700 }}>{a.num}</span>
            <span style={{ lineHeight: 1.2, textAlign: "center", whiteSpace: "pre-line", fontSize: "10px" }}>
              {a.label}
            </span>
          </button>
        ))}
      </div>

      {/* Content area */}
      <div style={{ flex: 1, overflow: "auto", padding: "16px" }}>
        {loadingAgent ? (
          <AgentThinkingState agentId={loadingAgent} />
        ) : !activeAgent ? (
          <AgentPlaceholder />
        ) : activeAgent === "assistant" || activeAgent === "clinical-assistant" ? (
          <AgentAssistantView report={report} />
        ) : !report ? (
          <AgentPlaceholder />
        ) : activeAgent === "quality" || activeAgent === "video-quality" ? (
          <AgentVideoQualityView report={report} />
        ) : activeAgent === "analyst" ? (
          <AgentAnalystView report={report} />
        ) : activeAgent === "clinical-risk" ? (
          <AgentClinicalRiskView report={report} />
        ) : activeAgent === "progress" || activeAgent === "therapist" ? (
          <AgentProgressView report={report} />
        ) : activeAgent === "risk" ? (
          <AgentRiskView report={report} />
        ) : (
          <AgentSynthesizerView report={report} />
        )}
      </div>
    </div>
  );
}

/* ─── Thinking Spinner ─── */
function AgentThinkingState({ agentId }: { agentId: string }) {
  const agent = AGENTS.find((a) => a.id === agentId);
  return (
    <div
      className="fade-in"
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        gap: "20px",
        paddingTop: "40px",
      }}
    >
      <div style={{ position: "relative" }}>
        <div className="spinner" style={{ width: "52px", height: "52px" }} />
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "22px",
          }}
        >
          {agent?.icon}
        </div>
      </div>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontWeight: 600, fontSize: "14px", marginBottom: "6px" }}>
          AI Clinical Agent Processing…
        </div>
        <div style={{ color: "var(--ehr-muted)", fontSize: "12px" }}>
          {agent?.label.replace("\n", " ")} is analyzing kinematic data
        </div>
      </div>
      <div
        style={{
          display: "flex",
          gap: "6px",
          alignItems: "center",
        }}
      >
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: "8px",
              height: "8px",
              borderRadius: "50%",
              background: "var(--ehr-accent)",
              animation: `pulseAnim 1.2s ${i * 0.2}s infinite`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

/* ─── Empty state ─── */
function AgentPlaceholder() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        gap: "12px",
        color: "var(--ehr-muted)",
        paddingTop: "40px",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "48px", opacity: 0.3 }}>🤖</div>
      <div style={{ fontSize: "14px", fontWeight: 500 }}>No Agent Selected</div>
      <div style={{ fontSize: "12px", maxWidth: "240px", lineHeight: 1.6 }}>
        Select an agent from the command bar above to generate a specialized clinical report.
      </div>
    </div>
  );
}

/* ─── Agent 1: Video Quality Validation ─── */
function AgentVideoQualityView({ report }: { report: AgentReport }) {
  const vq = report.video_quality;
  const status = vq?.status || "PASS";
  const score = vq?.video_quality_score ?? 100;
  const emoji = status === "PASS" ? "✅" : status === "WARNING" ? "⚠️" : "❌";

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
      <AgentRoleHeader report={report} color="#3b82f6" />
      <div className="glass-card" style={{ padding: "16px", display: "flex", alignItems: "center", gap: "16px" }}>
        <div style={{ fontSize: "28px" }}>{emoji}</div>
        <div>
          <div style={{ fontSize: "16px", fontWeight: 700 }}>Quality Score: {score} / 100</div>
          <div style={{ fontSize: "12px", color: "var(--ehr-muted)" }}>{vq?.recommendation || "Video technical quality inspection complete."}</div>
        </div>
      </div>
      <ReportTextBox text={report.report_text} />
    </div>
  );
}

/* ─── Agent 1: Biomechanical Analyst ─── */
function AgentAnalystView({ report }: { report: AgentReport }) {
  const downloadJson = () => {
    const blob = new Blob([JSON.stringify({ report: report.report_text, metrics: report.metrics }, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "kinematrace_biomechanical_data.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const metrics = report.metrics;

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
      <AgentRoleHeader report={report} color="#3b82f6" />

      {/* Metric cards */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
        <MetricCard
          label="Left Knee Max Flexion"
          value={`${metrics.left_max_flexion_deg ?? "—"}°`}
          sub="Peak ROM"
          color="#fbbf24"
        />
        <MetricCard
          label="Right Knee Max Flexion"
          value={`${metrics.right_max_flexion_deg ?? "—"}°`}
          sub="Peak ROM"
          color="#60a5fa"
        />
        <MetricCard
          label="Mean Symmetry Index"
          value={`${metrics.mean_symmetry_index_pct ?? "—"}%`}
          sub={Number(metrics.mean_symmetry_index_pct) > 15 ? "⚠ Asymmetric" : "✓ Normal"}
          color={Number(metrics.mean_symmetry_index_pct) > 15 ? "#f87171" : "#34d399"}
        />
        <MetricCard
          label="Bilateral ROM Delta"
          value={`${metrics.bilateral_rom_delta_deg ?? "—"}°`}
          sub="L vs R difference"
          color="#a78bfa"
        />
      </div>

      {/* Report text */}
      <ReportTextBox text={report.report_text} />

      {/* Download */}
      <button
        id="download-biomechanical-json"
        onClick={downloadJson}
        style={downloadBtnStyle("#3b82f6")}
      >
        📥 Download Raw Data (.JSON)
      </button>
    </div>
  );
}

/* ─── Agent 2: Clinical Risk Assessment ─── */
const RISK_PALETTE_ACC: Record<string, { bg: string; border: string; text: string; emoji: string }> = {
  HIGH:   { bg: "#3A1F1A",                 border: "#B45309",               text: "#EF4444", emoji: "🔴" },
  MEDIUM: { bg: "rgba(217,119,6,0.12)",   border: "rgba(217,119,6,0.4)",   text: "#D97706", emoji: "🟠" },
  LOW:    { bg: "rgba(16,185,129,0.12)",  border: "rgba(16,185,129,0.4)",  text: "#10B981", emoji: "🟢" },
};

function AgentClinicalRiskView({ report }: { report: AgentReport }) {
  const cr = report.clinical_risk;

  if (!cr) {
    return (
      <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <AgentRoleHeader report={report} color="#B45309" />
        <ReportTextBox text={report.report_text} />
      </div>
    );
  }

  const palette = RISK_PALETTE_ACC[cr.risk_level] ?? RISK_PALETTE_ACC.LOW;
  const severityColor = cr.severity === "SIGNIFICANT" ? "#EF4444" : cr.severity === "MODERATE" ? "#D97706" : "#10B981";

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <AgentRoleHeader report={report} color="#B45309" />

      {/* Risk level banner */}
      <div
        style={{
          padding: "16px 18px",
          borderRadius: "10px",
          background: palette.bg,
          border: `1px solid ${palette.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "10px",
        }}
      >
        <div>
          <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>
            Screening Risk Level
          </div>
          <div style={{ fontSize: "22px", fontWeight: 800, color: palette.text }}>
            {palette.emoji} {cr.risk_level} RISK
          </div>
          <div style={{ fontSize: "11px", color: "#A8A09A", marginTop: "2px" }}>
            Severity: <span style={{ color: severityColor, fontWeight: 700 }}>{cr.severity}</span>
            {" · "}Side: <span style={{ color: "#F8F5F0", fontWeight: 600 }}>{cr.affected_side}</span>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
          <div style={{ textAlign: "center", padding: "8px 14px", borderRadius: "8px", background: "rgba(0,0,0,0.4)" }}>
            <div style={{ fontSize: "18px", fontWeight: 800, color: palette.text }}>{cr.asymmetry_percentage.toFixed(1)}%</div>
            <div style={{ fontSize: "10px", color: "#A8A09A" }}>Mean SI</div>
          </div>
          <div style={{ textAlign: "center", padding: "8px 14px", borderRadius: "8px", background: "rgba(0,0,0,0.4)" }}>
            <div style={{ fontSize: "18px", fontWeight: 800, color: palette.text }}>{cr.peak_asymmetry_percentage.toFixed(1)}%</div>
            <div style={{ fontSize: "10px", color: "#A8A09A" }}>Peak SI</div>
          </div>
        </div>
      </div>

      {/* Key risk factors */}
      <div>
        <div style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: palette.text, marginBottom: "8px" }}>
          🔸 Key Risk Factors
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {cr.triggered_measurements.map((m, i) => (
            <div
              key={i}
              style={{
                padding: "8px 12px",
                borderRadius: "7px",
                background: palette.bg,
                border: `1px solid ${palette.border}`,
                fontSize: "12px",
                color: "#F8F5F0",
                lineHeight: 1.4,
              }}
            >
              • {m}
            </div>
          ))}
        </div>
      </div>

      {/* Reasoning summary */}
      <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "10px", padding: "12px 14px" }}>
        <div style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "#D97706", marginBottom: "8px" }}>
          💡 Explainable Reasoning
        </div>
        <div style={{ fontSize: "12px", lineHeight: 1.7, color: "#F8F5F0", whiteSpace: "pre-line" }}>
          {cr.reasoning}
        </div>
      </div>

      {/* Recommendation */}
      <div style={{ background: palette.bg, border: `1px solid ${palette.border}`, borderRadius: "9px", padding: "12px 14px" }}>
        <div style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: palette.text, marginBottom: "6px" }}>
          📋 Recommended Next Step
        </div>
        <div style={{ fontSize: "12px", lineHeight: 1.6, color: "#F8F5F0", fontWeight: 500 }}>{cr.recommendation}</div>
      </div>

      {/* Disclaimer */}
      <div style={{ fontSize: "11px", color: "#A8A09A", fontStyle: "italic", padding: "8px 12px", borderRadius: "6px", border: "1px solid #3A3028", background: "rgba(180,83,9,0.12)" }}>
        ⚕️ This is a screening decision-support result only. It does not constitute a medical diagnosis. All clinical decisions must be made by a licensed healthcare professional.
      </div>
    </div>
  );
}

/* ─── Agent 3: Patient Progress Monitoring ─── */
const PROGRESS_PALETTE_ACC: Record<string, { bg: string; border: string; text: string; emoji: string }> = {
  IMPROVING:         { bg: "rgba(16,185,129,0.12)",  border: "rgba(16,185,129,0.4)",  text: "#10B981", emoji: "🟢" },
  IMPROVED:          { bg: "rgba(16,185,129,0.12)",  border: "rgba(16,185,129,0.4)",  text: "#10B981", emoji: "🟢" },
  STABLE:            { bg: "rgba(217,119,6,0.12)",   border: "rgba(217,119,6,0.4)",   text: "#D97706", emoji: "🔵" },
  WORSENING:         { bg: "#3A1F1A",                border: "#B45309",               text: "#EF4444", emoji: "🔴" },
  WORSENED:          { bg: "#3A1F1A",                border: "#B45309",               text: "#EF4444", emoji: "🔴" },
  INSUFFICIENT_DATA: { bg: "#211C18",                border: "#3A3028",               text: "#A8A09A", emoji: "⚪" },
  FLUCTUATING:        { bg: "rgba(217,119,6,0.12)",   border: "rgba(217,119,6,0.4)",   text: "#D97706", emoji: "🟡" },
};

function AgentProgressView({ report }: { report: AgentReport }) {
  const pr = report.patient_progress;

  if (!pr) {
    return (
      <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <AgentRoleHeader report={report} color="#B45309" />
        <ReportTextBox text={report.report_text} />
      </div>
    );
  }

  const palette = PROGRESS_PALETTE_ACC[pr.trend] ?? PROGRESS_PALETTE_ACC.INSUFFICIENT_DATA;

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <AgentRoleHeader report={report} color="#B45309" />

      {/* Progress Trend Banner */}
      <div
        style={{
          padding: "16px 18px",
          borderRadius: "10px",
          background: palette.bg,
          border: `1px solid ${palette.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: "10px",
        }}
      >
        <div>
          <div style={{ fontSize: "10px", color: "#A8A09A", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "4px" }}>
            Longitudinal Progress Trend
          </div>
          <div style={{ fontSize: "22px", fontWeight: 800, color: palette.text }}>
            {palette.emoji} {pr.trend.replace(/_/g, " ")}
          </div>
          <div style={{ fontSize: "11px", color: "#A8A09A", marginTop: "2px" }}>
            Patient ID: <span style={{ color: "#F8F5F0", fontWeight: 700 }}>{pr.patient_id}</span>
            {" · "}Sessions: <span style={{ color: "#F8F5F0", fontWeight: 600 }}>{pr.total_history_sessions}</span>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
          <div style={{ textAlign: "center", padding: "8px 14px", borderRadius: "8px", background: "rgba(0,0,0,0.4)" }}>
            <div style={{ fontSize: "18px", fontWeight: 800, color: palette.text }}>{pr.current_asymmetry?.toFixed(1)}%</div>
            <div style={{ fontSize: "10px", color: "#A8A09A" }}>Current SI</div>
          </div>
          <div style={{ textAlign: "center", padding: "8px 14px", borderRadius: "8px", background: "rgba(0,0,0,0.4)" }}>
            <div style={{ fontSize: "18px", fontWeight: 800, color: pr.asymmetry_change !== undefined && pr.asymmetry_change < 0 ? "#10B981" : pr.asymmetry_change !== undefined && pr.asymmetry_change > 0 ? "#EF4444" : "#A8A09A" }}>
              {pr.asymmetry_change !== undefined ? `${pr.asymmetry_change > 0 ? "+" : ""}${pr.asymmetry_change.toFixed(1)} pp` : "—"}
            </div>
            <div style={{ fontSize: "10px", color: "#A8A09A" }}>Δ Change</div>
          </div>
        </div>
      </div>

      {/* Key changes */}
      {pr.key_changes && pr.key_changes.length > 0 && (
        <div>
          <div style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "#D97706", marginBottom: "8px" }}>
            🔸 Key Observed Changes
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {pr.key_changes.map((c: string, i: number) => (
              <div
                key={i}
                style={{
                  padding: "8px 12px",
                  borderRadius: "7px",
                  background: palette.bg,
                  border: `1px solid ${palette.border}`,
                  fontSize: "12px",
                  color: "#F8F5F0",
                  lineHeight: 1.4,
                }}
              >
                • {c}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Explanation summary */}
      <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "10px", padding: "12px 14px" }}>
        <div style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "#D97706", marginBottom: "8px" }}>
          💡 Progress Explanation
        </div>
        <div style={{ fontSize: "12px", lineHeight: 1.7, color: "#F8F5F0", whiteSpace: "pre-line" }}>
          {pr.explanation}
        </div>
      </div>

      {/* Recommendation */}
      <div style={{ background: palette.bg, border: `1px solid ${palette.border}`, borderRadius: "9px", padding: "12px 14px" }}>
        <div style={{ fontSize: "10px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: palette.text, marginBottom: "6px" }}>
          📋 Recommended Next Step
        </div>
        <div style={{ fontSize: "12px", lineHeight: 1.6, color: "#F8F5F0", fontWeight: 500 }}>{pr.recommendation}</div>
      </div>

      {/* Disclaimer */}
      <div style={{ fontSize: "11px", color: "#A8A09A", fontStyle: "italic", padding: "8px 12px", borderRadius: "6px", border: "1px solid #3A3028", background: "rgba(180,83,9,0.12)" }}>
        ⚕️ Progress monitoring flags measurement changes over time. It is not a medical diagnosis. All findings require review by a licensed healthcare professional.
      </div>
    </div>
  );
}

/* ─── Legacy Agent 3 / Fallback: Physical Therapist ─── */
function AgentTherapistView({ report }: { report: AgentReport }) {
  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
      <AgentRoleHeader report={report} color="#06b6d4" />

      {/* Recharts bar chart — Patient vs Normative */}
      <div
        className="metric-card"
        style={{ padding: "14px" }}
      >
        <div
          style={{
            fontSize: "11px",
            color: "var(--ehr-muted)",
            fontWeight: 600,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            marginBottom: "12px",
          }}
        >
          📊 Patient vs Pediatric Normative Baseline
        </div>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={report.recharts_data} margin={{ top: 4, right: 8, left: -10, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2a42" />
            <XAxis dataKey="metric" tick={{ fontSize: 10, fill: "#64748b" }} />
            <YAxis tick={{ fontSize: 10, fill: "#64748b" }} />
            <Tooltip
              contentStyle={{
                background: "#0f1423",
                border: "1px solid #1e2a42",
                borderRadius: "8px",
                fontSize: "12px",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "11px" }} />
            <Bar dataKey="Patient" name="Patient" radius={[4, 4, 0, 0]}>
              {report.recharts_data.map((entry, index) => {
                const isBelow = entry.Patient < entry.Normative;
                return <Cell key={`p-${index}`} fill={isBelow ? "#f59e0b" : "#10b981"} />;
              })}
            </Bar>
            <Bar dataKey="Normative" name="Normative" fill="#3b82f6" radius={[4, 4, 0, 0]} opacity={0.6} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <ReportTextBox text={report.report_text} />
    </div>
  );
}

/* ─── Agent 5: Clinical Assistant Chatbot View ─── */
function AgentAssistantView({ report }: { report: AgentReport | null }) {
  const [chatInput, setChatInput] = React.useState("");
  const [chatLoading, setChatLoading] = React.useState(false);
  const [chatLog, setChatLog] = React.useState<Array<{ sender: "user" | "bot"; text: string }>>([
    {
      sender: "bot",
      text: "👋 **Hello! I am KinemaTrace AI Clinical Assistant (Agent 5).**\n\nI consume structured outputs from Agents 1–4 to answer your questions, explain risk findings, interpret gait metrics, and generate reports.\n\nAsk me any question about the current patient's analysis!",
    },
  ]);

  const handleSendChat = async (presetText?: string) => {
    const text = presetText || chatInput;
    if (!text.trim() || chatLoading) return;

    setChatLog((prev) => [...prev, { sender: "user", text }]);
    if (!presetText) setChatInput("");
    setChatLoading(true);

    try {
      let sessionData = {};
      try {
        const stored = localStorage.getItem("kt_session");
        if (stored) sessionData = JSON.parse(stored);
      } catch (e) {}

      const res = await fetch("http://localhost:8000/api/agents/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, context: sessionData }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setChatLog((prev) => [...prev, { sender: "bot", text: data.response || "No response." }]);
    } catch (err: any) {
      setChatLog((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Unable to reach Clinical Assistant backend server." },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <AgentRoleHeader
        report={{
          agent_id: "assistant",
          agent_name: "Agent 5: KinemaTrace AI Clinical Assistant",
          agent_role: "Conversational Intelligence & Decision Support Specialist",
          report_text: "",
          metrics: {},
          recharts_data: [],
        }}
        color="#B45309"
      />

      {/* Preset Action Buttons */}
      <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
        {[
          { label: "🛡️ Explain Risk", text: "Why is this patient high risk and what caused it?" },
          { label: "📋 Generate Report", text: "Generate a full pediatric gait screening report for this patient" },
          { label: "📊 Compare Progress", text: "Has the patient improved compared to previous assessment?" },
          { label: "💡 Summarize", text: "Give me a clinician-friendly summary of this patient" },
        ].map((btn) => (
          <button
            key={btn.label}
            onClick={() => handleSendChat(btn.text)}
            disabled={chatLoading}
            style={{
              padding: "6px 12px",
              borderRadius: "8px",
              background: "#211C18",
              border: "1px solid #3A3028",
              color: "#F8F5F0",
              fontSize: "11px",
              fontWeight: 600,
              cursor: chatLoading ? "wait" : "pointer",
            }}
          >
            {btn.label}
          </button>
        ))}
      </div>

      {/* Chat Messages Log */}
      <div
        style={{
          background: "#171412",
          border: "1px solid #3A3028",
          borderRadius: "10px",
          padding: "14px",
          minHeight: "220px",
          maxHeight: "340px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        {chatLog.map((m, i) => (
          <div
            key={i}
            style={{
              alignSelf: m.sender === "user" ? "flex-end" : "flex-start",
              maxWidth: "85%",
              background: m.sender === "user" ? "linear-gradient(135deg, #B45309 0%, #78350F 100%)" : "#211C18",
              border: m.sender === "user" ? "1px solid #B45309" : "1px solid #3A3028",
              borderRadius: "8px",
              padding: "10px 12px",
              color: "#F8F5F0",
              fontSize: "12px",
              lineHeight: 1.6,
            }}
          >
            <FormattedMarkdownText text={m.text} />
          </div>
        ))}
      </div>

      {/* Input Field */}
      <div style={{ display: "flex", gap: "8px" }}>
        <input
          type="text"
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
          placeholder="Ask Agent 5 about this patient's analysis..."
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: "8px",
            background: "#211C18",
            border: "1px solid #3A3028",
            color: "#F8F5F0",
            fontSize: "12px",
            outline: "none",
          }}
        />
        <button
          onClick={() => handleSendChat()}
          disabled={chatLoading || !chatInput.trim()}
          style={{
            padding: "10px 18px",
            borderRadius: "8px",
            background: "linear-gradient(135deg, #B45309 0%, #78350F 100%)",
            color: "#F8F5F0",
            border: "1px solid #B45309",
            fontWeight: 700,
            fontSize: "12px",
            cursor: chatLoading || !chatInput.trim() ? "not-allowed" : "pointer",
          }}
        >
          {chatLoading ? "…" : "Send ▶"}
        </button>
      </div>
    </div>
  );
}

/* ─── Agent 3: Orthopedic Risk ─── */
function AgentRiskView({ report }: { report: AgentReport }) {
  const lines = report.report_text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const critical: string[] = [];
  const moderate: string[] = [];
  const info: string[] = [];

  lines.forEach((line) => {
    const lower = line.toLowerCase();
    if (lower.includes("critical") || lower.includes("high risk") || lower.includes("immediate")) {
      critical.push(line);
    } else if (lower.includes("moderate") || lower.includes("asymm") || lower.includes("abnormal") || lower.includes("⚠")) {
      moderate.push(line);
    } else {
      info.push(line);
    }
  });

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
      <AgentRoleHeader report={report} color="#f59e0b" />

      {/* Warning banner */}
      <div
        style={{
          background: "rgba(245,158,11,0.08)",
          border: "1px solid rgba(245,158,11,0.3)",
          borderRadius: "10px",
          padding: "12px 14px",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          fontSize: "12px",
          color: "#fbbf24",
        }}
      >
        <span style={{ fontSize: "18px" }}>⚕️</span>
        <span>
          Clinical screening flags are informational only. All findings require physician review before diagnosis or treatment.
        </span>
      </div>

      {/* Risk blocks */}
      {critical.length > 0 && (
        <div>
          <RiskSectionHeader label="🔴 Critical Flags" color="#ef4444" />
          {critical.map((line, i) => (
            <div key={i} className="risk-block critical" style={{ marginBottom: "8px" }}>
              <span style={{ fontSize: "12px", color: "#fca5a5" }}>{line}</span>
            </div>
          ))}
        </div>
      )}

      {moderate.length > 0 && (
        <div>
          <RiskSectionHeader label="🟡 Moderate Flags" color="#f59e0b" />
          {moderate.map((line, i) => (
            <div key={i} className="risk-block" style={{ marginBottom: "8px" }}>
              <span style={{ fontSize: "12px", color: "#fde68a" }}>{line}</span>
            </div>
          ))}
        </div>
      )}

      {info.length > 0 && (
        <div>
          <RiskSectionHeader label="🔵 Clinical Observations" color="#3b82f6" />
          <div
            style={{
              background: "rgba(59,130,246,0.07)",
              border: "1px solid rgba(59,130,246,0.2)",
              borderRadius: "8px",
              padding: "12px 14px",
            }}
          >
            {info.map((line, i) => (
              <div key={i} style={{ fontSize: "12px", color: "#93c5fd", marginBottom: "6px" }}>
                {line}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function RiskSectionHeader({ label, color }: { label: string; color: string }) {
  return (
    <div
      style={{
        fontSize: "11px",
        fontWeight: 700,
        letterSpacing: "0.06em",
        textTransform: "uppercase",
        color,
        marginBottom: "8px",
        marginTop: "4px",
      }}
    >
      {label}
    </div>
  );
}

/* ─── Agent 4: Care Plan Synthesizer ─── */
function AgentSynthesizerView({ report }: { report: AgentReport }) {
  const printReport = () => {
    const text = report.report_text;
    const win = window.open("", "_blank");
    if (win) {
      win.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>KinemaTrace AI — Clinical Care Plan</title>
          <style>
            body { font-family: 'Times New Roman', Georgia, serif; color: #1a1a2e; margin: 40px; font-size: 13px; }
            h1 { font-size: 18px; border-bottom: 2px solid #1a1a2e; padding-bottom: 8px; }
            pre { white-space: pre-wrap; font-family: inherit; font-size: 13px; }
          </style>
        </head>
        <body>
          <h1>KinemaTrace AI — Pediatric Clinical Care Plan</h1>
          <pre>${text}</pre>
        </body>
        </html>
      `);
      win.document.close();
      win.print();
    }
  };

  return (
    <div className="fade-in" style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
      <AgentRoleHeader report={report} color="#10b981" />

      {/* Formal clinical document */}
      <div className="clinical-doc">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            borderBottom: "1px solid #d1d5db",
            paddingBottom: "12px",
            marginBottom: "16px",
          }}
        >
          <div>
            <div style={{ fontSize: "14px", fontWeight: 700, marginBottom: "2px" }}>
              KinemaTrace AI — Pediatric Rehabilitation Clinic
            </div>
            <div style={{ fontSize: "11px", color: "#6b7280" }}>
              Multi-Agent Clinical Intelligence Report
            </div>
          </div>
          <div
            style={{
              background: "#f3f4f6",
              border: "1px solid #d1d5db",
              borderRadius: "6px",
              padding: "6px 12px",
              fontSize: "11px",
              color: "#6b7280",
              textAlign: "right",
            }}
          >
            <div>CONFIDENTIAL — EHR DOCUMENT</div>
            <div>{new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })}</div>
          </div>
        </div>

        <pre
          style={{
            whiteSpace: "pre-wrap",
            fontFamily: "inherit",
            fontSize: "12px",
            lineHeight: 1.8,
            color: "#1a1a2e",
            margin: 0,
          }}
        >
          {report.report_text}
        </pre>

        <div
          style={{
            marginTop: "20px",
            paddingTop: "12px",
            borderTop: "1px solid #d1d5db",
            fontSize: "10px",
            color: "#9ca3af",
          }}
        >
          ⚠ This AI-generated report is for clinical screening purposes only. It does not constitute a medical diagnosis. All findings must be reviewed and validated by a licensed physician before clinical use.
        </div>
      </div>

      <button
        id="download-care-plan-pdf"
        onClick={printReport}
        style={downloadBtnStyle("#10b981")}
      >
        🖨️ Print / Download Official Care Plan (.PDF)
      </button>
    </div>
  );
}

/* ─── Shared sub-components ─── */

function AgentRoleHeader({ report, color }: { report: AgentReport; color: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        padding: "12px 14px",
        background: `${color}12`,
        border: `1px solid ${color}30`,
        borderRadius: "10px",
      }}
    >
      <div
        style={{
          width: "36px",
          height: "36px",
          borderRadius: "8px",
          background: `${color}22`,
          border: `1px solid ${color}44`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "18px",
          flexShrink: 0,
        }}
      >
        {report.agent_id === "analyst" ? "🔬"
          : report.agent_id === "clinical-risk" ? "🛡️"
          : report.agent_id === "progress" || report.agent_id === "therapist" ? "📊"
          : report.agent_id === "risk" ? "🩺"
          : "📋"}
      </div>
      <div>
        <div style={{ fontWeight: 700, fontSize: "13px", color: color }}>
          {report.agent_name}
        </div>
        <div style={{ fontSize: "11px", color: "var(--ehr-muted)" }}>{report.agent_role}</div>
      </div>
      <div className={`badge ${color === "#10b981" ? "badge-green" : color === "#f59e0b" ? "badge-amber" : color === "#06b6d4" ? "badge-teal" : "badge-blue"}`} style={{ marginLeft: "auto" }}>
        AI Active
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  sub,
  color,
}: {
  label: string;
  value: string;
  sub: string;
  color: string;
}) {
  return (
    <div className="metric-card">
      <div style={{ fontSize: "10px", color: "var(--ehr-muted)", marginBottom: "4px" }}>{label}</div>
      <div style={{ fontSize: "22px", fontWeight: 700, color, fontVariantNumeric: "tabular-nums" }}>
        {value}
      </div>
      <div style={{ fontSize: "11px", color: "var(--ehr-muted)", marginTop: "2px" }}>{sub}</div>
    </div>
  );
}

function ReportTextBox({ text }: { text: string }) {
  return (
    <div
      style={{
        background: "rgba(10,14,26,0.6)",
        border: "1px solid var(--ehr-border)",
        borderRadius: "10px",
        padding: "14px 16px",
        maxHeight: "280px",
        overflowY: "auto",
      }}
    >
      <FormattedMarkdownText text={text} />
    </div>
  );
}

function downloadBtnStyle(color: string): React.CSSProperties {
  return {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    padding: "11px 18px",
    borderRadius: "10px",
    border: `1px solid ${color}55`,
    background: `${color}18`,
    color: color,
    fontWeight: 600,
    fontSize: "13px",
    cursor: "pointer",
    transition: "all 0.2s",
    width: "100%",
  };
}
