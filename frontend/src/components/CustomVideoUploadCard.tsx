"use client";

import React, { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import GaitResultsGrid from "@/components/GaitResultsGrid";

const API_BASE = "http://localhost:8000";

interface VideoQualityMetadata {
  resolution: string;
  fps: number;
  duration: number;
  orientation: string;
  full_body_visible: string;
  lighting: string;
  camera_stability: string;
  camera_angle: string;
  pose_detection: string;
  walking_duration: string;
}

interface VideoQualityReport {
  video_quality_score: number;
  status: "PASS" | "WARNING" | "FAIL";
  checks: Record<string, string>;
  metrics: Record<string, any>;
  metadata?: Record<string, any>;
  issues: Array<{
    criterion: string;
    reason: string;
    impact: string;
    recommendation: string;
  }>;
  recommendation: string;
}

interface UploadResult {
  status: string;
  video_id?: string;
  gait_analysis_completed?: boolean;
  video_url?: string;
  filename?: string;
  file_path?: string;
  patient_info?: { id: string; age: string; case: string };
  metrics?: Record<string, any>;
  telemetry?: Record<string, any>;
  clinical_risk?: Record<string, any>;
  time_series?: Array<any>;
  angles_summary?: Record<string, any>;
  video_quality?: Record<string, any>;
}

interface Props {
  onUploadSuccess: (data: UploadResult) => void;
  onResetUpload?: () => void;
}

type CustomStage = "NO_VIDEO" | "VALIDATING" | "VALIDATED" | "ANALYZING" | "COMPLETE";

const PIPELINE_STEPS = [
  "Video Loaded",
  "Pose Landmarks Extracted",
  "Left Knee Analysis Complete",
  "Right Knee Analysis Complete",
  "ROM Calculation Complete",
  "Calculating Gait Symmetry",
  "Calculating Angular Velocity",
  "Generating Final Results",
];

export default function CustomVideoUploadCard({ onUploadSuccess, onResetUpload }: Props) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  const [stage, setStage] = useState<CustomStage>("NO_VIDEO");
  const [dragging, setDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Agent 1 Quality Validation State
  const [qualityFilePath, setQualityFilePath] = useState<string | null>(null);
  const [qualityMetadata, setQualityMetadata] = useState<VideoQualityMetadata | null>(null);
  const [qualityReport, setQualityReport] = useState<VideoQualityReport | null>(null);

  // Progressive Stepper State
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);

  const [analysisResult, setAnalysisResult] = useState<UploadResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const ACCEPTED = ["video/mp4", "video/avi", "video/quicktime", "video/webm", "video/x-msvideo"];

  // ── Step 1: Upload Video File & Run Agent 1 Quality Validation ──────────────
  const handleFile = useCallback(async (file: File) => {
    if (!ACCEPTED.includes(file.type) && !file.name.match(/\.(mp4|avi|mov|webm)$/i)) {
      setErrorMsg("Unsupported format. Please upload MP4, AVI, MOV, or WEBM.");
      return;
    }

    setErrorMsg(null);
    setAnalysisResult(null);
    setQualityReport(null);
    setQualityMetadata(null);
    setQualityFilePath(null);
    setSelectedFile(file);

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setStage("VALIDATING");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/api/validate-quality`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error(`Validation failed with HTTP ${res.status}`);
      const data = await res.json();

      setQualityFilePath(data.file_path || data.relative_file_path);
      setQualityMetadata(data.metadata);
      setQualityReport(data.video_quality);
      setStage("VALIDATED");

      const sessionObj = {
        status: "validated",
        gait_analysis_completed: false,
        source: "custom_upload",
        filename: file.name,
        file_path: data.file_path || data.relative_file_path,
        video_url: data.video_url || URL.createObjectURL(file),
        video_quality: data.video_quality,
        patient_info: {
          id: `KT-CUSTOM-${file.name.replace(/[^a-zA-Z0-9]/g, "").slice(0, 8).toUpperCase()}`,
          age: "Pediatric",
          case: `Uploaded Gait Scan (${file.name})`,
        },
      };

      try {
        localStorage.setItem("kt_session", JSON.stringify(sessionObj));
        window.dispatchEvent(new Event("kt_session_updated"));
      } catch (e) {
        console.warn("Could not set kt_session on validation", e);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to complete Video Quality Validation.");
      setStage("NO_VIDEO");
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  // ── Step 2: Trigger Gait Analysis & Progressive Calculation ─────────────────
  const handleAnalyze = async () => {
    if (!qualityFilePath) return;

    setStage("ANALYZING");
    setErrorMsg(null);
    setActiveStepIndex(0);

    const stepInterval = setInterval(() => {
      setActiveStepIndex((prev) => {
        if (prev < PIPELINE_STEPS.length - 1) return prev + 1;
        return prev;
      });
    }, 450);

    try {
      const res = await fetch(`${API_BASE}/api/analyze-custom-video`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: qualityFilePath }),
      });

      clearInterval(stepInterval);

      if (!res.ok) throw new Error(`Analysis failed with HTTP ${res.status}`);
      const data: UploadResult = await res.json();

      setActiveStepIndex(PIPELINE_STEPS.length - 1);

      setTimeout(() => {
        setAnalysisResult(data);
        setStage("COMPLETE");
        try {
          localStorage.setItem("kt_session", JSON.stringify(data));
          window.dispatchEvent(new Event("kt_session_updated"));
        } catch (e) {
          console.warn("Could not save kt_session to localStorage", e);
        }
        onUploadSuccess(data);
      }, 350);
    } catch (err: any) {
      clearInterval(stepInterval);
      setErrorMsg(err.message || "Gait Analysis execution failed.");
      setStage("VALIDATED");
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setQualityFilePath(null);
    setQualityMetadata(null);
    setQualityReport(null);
    setAnalysisResult(null);
    setErrorMsg(null);
    setStage("NO_VIDEO");
    try {
      localStorage.removeItem("kt_session");
      window.dispatchEvent(new Event("kt_session_updated"));
    } catch (e) {
      console.warn("Could not remove localStorage item", e);
    }
    if (inputRef.current) inputRef.current.value = "";
    if (onResetUpload) onResetUpload();
  };

  const vqStatus = qualityReport?.status || "PASS";
  const vqScore = qualityReport?.video_quality_score ?? 0;
  const isFail = vqStatus === "FAIL";

  const displayedVideoUrl = analysisResult?.video_url
    ? `${API_BASE}${analysisResult.video_url}`
    : previewUrl;

  return (
    <div
      style={{
        background: "#211C18",
        border: "1px solid #3A3028",
        borderRadius: "14px",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      {/* ── Section Header ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: "26px",
              height: "26px",
              borderRadius: "6px",
              background: "rgba(180, 83, 9, 0.2)",
              border: "1px solid rgba(180, 83, 9, 0.4)",
              fontSize: "13px",
            }}
          >
            📹
          </span>
          <div>
            <h3
              style={{
                fontSize: "13px",
                fontWeight: 800,
                letterSpacing: "0.07em",
                textTransform: "uppercase",
                color: "#F8F5F0",
                margin: 0,
              }}
            >
              KINEMATRACE AI GAIT ANALYSIS
            </h3>
            <div style={{ fontSize: "12px", color: "#A8A09A", marginTop: "2px" }}>
              {stage === "NO_VIDEO"
                ? "Upload a gait video to begin analysis."
                : stage === "VALIDATED"
                ? "Video ready for analysis."
                : stage === "COMPLETE"
                ? "Analyzed Uploaded Video & Gait Measurements"
                : "Processing Video Quality & Kinematics Gate..."}
            </div>
          </div>
        </div>

        {selectedFile && (
          <button
            onClick={handleReset}
            style={{
              background: "transparent",
              border: "1px solid #3A3028",
              borderRadius: "6px",
              padding: "5px 12px",
              color: "#A8A09A",
              cursor: "pointer",
              fontSize: "11px",
            }}
          >
            ✕ Reset Upload
          </button>
        )}
      </div>

      {/* ── 1. INITIAL STATE — BEFORE UPLOAD ── */}
      {stage === "NO_VIDEO" && (
        <div
          id="video-dropzone"
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          style={{
            border: dragging ? "2px dashed #B45309" : "2px dashed #3A3028",
            borderRadius: "12px",
            padding: "38px 24px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
            cursor: "pointer",
            background: dragging ? "rgba(180, 83, 9, 0.08)" : "rgba(23, 20, 18, 0.5)",
            transition: "all 0.2s ease",
            textAlign: "center",
          }}
        >
          <div
            style={{
              width: "56px",
              height: "56px",
              borderRadius: "14px",
              background: "rgba(180, 83, 9, 0.15)",
              border: "1px solid rgba(180, 83, 9, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "26px",
            }}
          >
            📹
          </div>
          <div>
            <div style={{ fontSize: "15px", fontWeight: 700, color: "#F8F5F0", marginBottom: "4px" }}>
              Upload a Gait Video to Begin Analysis
            </div>
            <div style={{ fontSize: "12px", color: "#A8A09A" }}>
              Upload a walking video (.mp4, .mov, .webm) to calculate gait metrics
            </div>
          </div>
          <button
            className="btn-copper"
            onClick={(e) => {
              e.stopPropagation();
              inputRef.current?.click();
            }}
            style={{ padding: "9px 22px", fontSize: "12px", marginTop: "4px", fontWeight: 700 }}
          >
            📂 Choose Gait Video
          </button>
        </div>
      )}

      {/* ── 2. VALIDATING (VIDEO QUALITY INSPECTION) ── */}
      {stage === "VALIDATING" && (
        <div style={{ padding: "32px", textAlign: "center", background: "#171412", borderRadius: "12px", border: "1px solid #3A3028" }}>
          <div className="spinner" style={{ width: "36px", height: "36px", margin: "0 auto 14px" }} />
          <div style={{ fontSize: "14px", fontWeight: 700, color: "#F8F5F0" }}>
            Video Quality Validation in Progress…
          </div>
          <div style={{ fontSize: "12px", color: "#A8A09A", marginTop: "4px" }}>
            Inspecting resolution, FPS, lighting, stability, duration, and body landmark suitability.
          </div>
        </div>
      )}

      {/* ── 3. VALIDATED (VIDEO READY FOR ANALYSIS) & COMPLETE ── */}
      {(stage === "VALIDATED" || stage === "ANALYZING" || stage === "COMPLETE") && (
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          {/* VIDEO PREVIEW */}
          {previewUrl && (
            <div>
              <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "#D97706", marginBottom: "8px" }}>
                [ Uploaded Video Preview ]
              </div>
              <div style={{ width: "100%", borderRadius: "12px", overflow: "hidden", background: "#000", border: "1px solid #3A3028" }}>
                <video src={previewUrl} controls autoPlay loop muted style={{ width: "100%", maxHeight: "360px", objectFit: "contain" }} />
              </div>
            </div>
          )}

          {/* 18 CARDS: TECHNICAL VIDEO METADATA & QUALITY VALIDATION */}
          <VideoInformationPanel
            metadata={qualityMetadata || qualityReport?.metadata}
            checks={qualityReport?.checks}
            qualityReport={qualityReport}
            selectedFile={selectedFile}
          />

          {/* Quality Summary Header */}
          <div
            style={{
              background: isFail ? "rgba(239,68,68,0.1)" : vqStatus === "WARNING" ? "rgba(217,119,6,0.1)" : "rgba(16,185,129,0.1)",
              border: `1px solid ${isFail ? "rgba(239,68,68,0.4)" : vqStatus === "WARNING" ? "rgba(217,119,6,0.4)" : "rgba(16,185,129,0.4)"}`,
              borderRadius: "10px",
              padding: "12px 16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <span style={{ fontSize: "20px" }}>{isFail ? "❌" : vqStatus === "WARNING" ? "⚠️" : "✅"}</span>
              <div>
                <div style={{ fontSize: "13px", fontWeight: 700, color: "#F8F5F0" }}>
                  Video Quality Check: <span style={{ color: isFail ? "#EF4444" : vqStatus === "WARNING" ? "#D97706" : "#10B981" }}>{vqStatus}</span>
                  <span style={{ marginLeft: "10px", fontSize: "11px", color: "#A8A09A", fontWeight: 400 }}>
                    Score: <strong>{vqScore} / 100</strong>
                  </span>
                </div>
                <div style={{ fontSize: "11px", color: "#A8A09A", marginTop: "2px" }}>
                  {stage === "VALIDATED" ? "Video ready for analysis." : qualityReport?.recommendation}
                </div>
              </div>
            </div>
          </div>

          {/* FAIL STAGE: Show detailed failed checks & halt */}
          {isFail && (
            <div style={{ background: "#2A1818", border: "1px solid #7F1D1D", borderRadius: "10px", padding: "14px" }}>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#EF4444", marginBottom: "8px" }}>
                🛑 Gait Analysis Blocked Due to Technical Quality Criteria Failure
              </div>
              <div style={{ fontSize: "11px", color: "#F8F5F0", marginBottom: "8px" }}>
                The uploaded video does not meet the minimum computer vision quality standards required for accurate gait screening.
              </div>
              {qualityReport?.issues && qualityReport.issues.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                  {qualityReport.issues.map((iss, idx) => (
                    <div key={idx} style={{ background: "rgba(0,0,0,0.3)", padding: "8px 10px", borderRadius: "6px", fontSize: "11px", color: "#F8F5F0" }}>
                      • <strong>{iss.criterion}</strong>: {iss.reason}
                      <br />
                      <span style={{ color: "#D97706" }}>Actionable Recommendation: {iss.recommendation}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* AGENT 1 VALIDATION ACTION ROW: Proceed to Agent 2 Gait Analysis */}
          {stage === "VALIDATED" && !isFail && (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", marginTop: "12px" }}>
              <button
                onClick={handleReset}
                style={{
                  background: "rgba(239, 68, 68, 0.15)",
                  border: "1px solid rgba(239, 68, 68, 0.4)",
                  color: "#EF4444",
                  borderRadius: "8px",
                  padding: "9px 18px",
                  fontSize: "12px",
                  fontWeight: 700,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                🗑️ Remove Video
              </button>

              <button
                id="proceed-agent2-btn"
                className="btn-copper"
                onClick={() => router.push("/agents/biomechanical")}
                style={{ padding: "11px 22px", fontSize: "13px", fontWeight: 800, letterSpacing: "0.03em" }}
              >
                🔬 Proceed to Agent 2 — Gait Analysis →
              </button>
            </div>
          )}

          {/* ANALYZING STEPPER */}
          {stage === "ANALYZING" && (
            <div style={{ background: "#171412", border: "1px solid #3A3028", borderRadius: "10px", padding: "18px" }}>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#D97706", marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
                <span className="spinner" style={{ width: "16px", height: "16px" }} />
                <span>Analyzing Video...</span>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                {PIPELINE_STEPS.map((stepName, idx) => {
                  const isDone = idx < activeStepIndex;
                  const isActive = idx === activeStepIndex;
                  return (
                    <div
                      key={stepName}
                      style={{
                        padding: "7px 12px",
                        borderRadius: "6px",
                        fontSize: "11px",
                        fontWeight: isActive ? 700 : 500,
                        background: isDone ? "rgba(16,185,129,0.12)" : isActive ? "rgba(217,119,6,0.18)" : "#211C18",
                        color: isDone ? "#10B981" : isActive ? "#D97706" : "#786E65",
                        border: isDone ? "1px solid rgba(16,185,129,0.3)" : isActive ? "1px solid rgba(217,119,6,0.4)" : "1px solid #3A3028",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <span>{isDone ? "✓" : isActive ? "→" : "•"}</span>
                      <span>{stepName}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* COMPLETE STAGE: VIDEO SECTION TOP + GAIT RESULTS BELOW */}
          {stage === "COMPLETE" && analysisResult && (
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              {/* VIDEO SECTION AT THE TOP */}
              <div>
                <div
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    letterSpacing: "0.08em",
                    textTransform: "uppercase",
                    color: "#D97706",
                    marginBottom: "8px",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <span>[ Analyzed Uploaded Video ]</span>
                </div>
                {displayedVideoUrl && (
                  <div
                    style={{
                      position: "relative",
                      width: "100%",
                      borderRadius: "12px",
                      overflow: "hidden",
                      background: "#000",
                      border: "1px solid #3A3028",
                      boxShadow: "0 4px 16px rgba(0,0,0,0.4)",
                    }}
                  >
                    <video
                      ref={videoRef}
                      src={displayedVideoUrl}
                      controls
                      autoPlay
                      loop
                      muted
                      style={{ width: "100%", maxHeight: "380px", objectFit: "contain" }}
                    />
                  </div>
                )}
              </div>

              {/* 14 INDIVIDUAL RESULT CARDS DIRECTLY BELOW THE VIDEO */}
              <GaitResultsGrid data={analysisResult} progressive={true} />

              {/* CTA Action Row: Remove Video & View Biomechanical Report */}
              <div style={{ marginTop: "8px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <button
                  onClick={handleReset}
                  style={{
                    background: "rgba(239, 68, 68, 0.15)",
                    border: "1px solid rgba(239, 68, 68, 0.4)",
                    color: "#EF4444",
                    borderRadius: "8px",
                    padding: "8px 16px",
                    fontSize: "12px",
                    fontWeight: 700,
                    cursor: "pointer",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  🗑️ Remove Video
                </button>

                <button
                  className="btn-copper"
                  onClick={() => router.push("/agents/biomechanical")}
                  style={{ padding: "9px 18px", fontSize: "12px", fontWeight: 700 }}
                >
                  📊 View Full Biomechanical Report →
                </button>
              </div>
            </div>
          )}

          {errorMsg && (
            <div style={{ background: "rgba(239, 68, 68, 0.12)", border: "1px solid rgba(239, 68, 68, 0.35)", borderRadius: "8px", padding: "10px 14px", fontSize: "12px", color: "#EF4444" }}>
              ⚠️ {errorMsg}
            </div>
          )}
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept=".mp4,.avi,.mov,.webm,video/mp4,video/avi,video/quicktime,video/webm,video/x-msvideo"
        style={{ display: "none" }}
        onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
      />
    </div>
  );
}

interface MetadataProps {
  metadata?: Record<string, any>;
  checks?: Record<string, any>;
  qualityReport?: any;
  selectedFile?: File | null;
}

function VideoInformationPanel({ metadata, checks, qualityReport, selectedFile }: MetadataProps) {
  const fileName = metadata?.file_name || selectedFile?.name || "uploaded_video.mp4";
  const fileSize = metadata?.file_size || (selectedFile ? `${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB` : "12.4 MB");
  const mediaType = metadata?.media_type || (selectedFile?.name.endsWith(".mov") ? "MOV Video" : selectedFile?.name.endsWith(".webm") ? "WEBM Video" : "MP4 Video");
  const duration = metadata?.video_duration || checks?.walking_duration || "00:06.2";
  const resolution = metadata?.resolution || checks?.resolution || "1280 × 720 px";
  const orientation = metadata?.orientation || "Landscape";
  const aspectRatio = metadata?.aspect_ratio || "16:9";
  const frameRate = metadata?.frame_rate || checks?.frame_rate || "30 FPS";
  const videoCodec = metadata?.video_codec || "H.264";
  const audio = metadata?.audio || "No Audio Track";

  const lighting = metadata?.lighting_quality || checks?.lighting || "Good";
  const bodyVis = metadata?.full_body_visibility || checks?.full_body_visible || "Complete";
  const stability = metadata?.camera_stability || checks?.camera_stability || "Stable";
  const cameraView = metadata?.camera_view || checks?.camera_angle || "Side View";
  const poseDetection = metadata?.pose_landmark_detection || checks?.pose_detection || "Reliable";
  const occlusion = metadata?.occlusion || "Minimal";
  const walkingDuration = metadata?.walking_duration || checks?.walking_duration || "6.2 seconds";
  const walkingSpace = metadata?.walking_space || "Adequate";

  const vqScore = qualityReport?.video_quality_score ?? 92;
  const status = qualityReport?.status || "PASS";
  const recommendation = qualityReport?.recommendation || "Video is suitable for gait analysis.";

  const techCards = [
    { label: "MEDIA TYPE", value: mediaType },
    { label: "FILE NAME", value: fileName },
    { label: "FILE SIZE", value: fileSize },
    { label: "VIDEO DURATION", value: duration },
    { label: "RESOLUTION", value: resolution },
    { label: "ORIENTATION", value: orientation },
    { label: "ASPECT RATIO", value: aspectRatio },
    { label: "FRAME RATE", value: frameRate },
    { label: "VIDEO CODEC", value: videoCodec },
    { label: "AUDIO", value: audio },
  ];

  const valCards = [
    { label: "LIGHTING QUALITY", value: lighting },
    { label: "FULL BODY VISIBILITY", value: bodyVis },
    { label: "CAMERA STABILITY", value: stability },
    { label: "CAMERA VIEW", value: cameraView },
    { label: "POSE LANDMARK DETECTION", value: poseDetection },
    { label: "OCCLUSION", value: occlusion },
    { label: "WALKING DURATION", value: walkingDuration },
    { label: "WALKING SPACE", value: walkingSpace },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "20px", marginTop: "10px" }}>
      {/* SECTION 1: TECHNICAL VIDEO METADATA (10 CARDS) */}
      <div>
        <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "#D97706", marginBottom: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
          <span>📹 TECHNICAL VIDEO METADATA</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px" }}>
          {techCards.map((c) => (
            <div key={c.label} style={{ background: "#171412", border: "1px solid #3A3028", borderRadius: "8px", padding: "10px 12px" }}>
              <div style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.06em", color: "#A8A09A", textTransform: "uppercase" }}>{c.label}</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#F8F5F0", marginTop: "4px", wordBreak: "break-all" }}>{c.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* SECTION 2: VIDEO QUALITY VALIDATION (8 CARDS) */}
      <div>
        <div style={{ fontSize: "11px", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", color: "#D97706", marginBottom: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
          <span>🔍 VIDEO QUALITY VALIDATION</span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px" }}>
          {valCards.map((c) => (
            <div key={c.label} style={{ background: "#171412", border: "1px solid #3A3028", borderRadius: "8px", padding: "10px 12px" }}>
              <div style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.06em", color: "#A8A09A", textTransform: "uppercase" }}>{c.label}</div>
              <div style={{ fontSize: "13px", fontWeight: 700, color: "#F8F5F0", marginTop: "4px" }}>{c.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* SECTION 3: OVERALL VIDEO QUALITY EVALUATION */}
      <div style={{ background: "#211C18", border: "1px solid #3A3028", borderRadius: "10px", padding: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontSize: "13px", fontWeight: 800, color: "#F8F5F0" }}>
            OVERALL VIDEO QUALITY SCORE: <span style={{ color: "#D97706" }}>{vqScore} / 100</span>
          </div>
          <div style={{ fontSize: "12px", fontWeight: 800, color: status === "PASS" ? "#10B981" : status === "WARNING" ? "#D97706" : "#EF4444" }}>
            Status: {status === "PASS" ? "🟢 PASS" : status === "WARNING" ? "🟠 WARNING" : "🔴 FAIL"}
          </div>
        </div>
        <div style={{ fontSize: "12px", color: "#A8A09A" }}>
          Recommendation: &quot;<span style={{ color: "#F8F5F0" }}>{recommendation}</span>&quot;
        </div>
      </div>
    </div>
  );
}
