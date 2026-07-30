"use client";

import React, { useState, useRef } from "react";
import { VideoQualityResult } from "./VideoQualityGate";

interface UploadMetrics {
  symmetry_index: number;
  peak_knee_flexion: number;
  hip_flexion_rom: number;
}

interface UploadResponse {
  status: string;
  filename: string;
  file_path: string;
  video_url: string;
  video_quality?: VideoQualityResult;
  patient_info: { id: string; age: string; case: string };
  metrics: UploadMetrics;
  telemetry: {
    gait_symmetry_pct: number;
    peak_knee_flexion_deg: number;
    hip_flexion_rom_deg: number;
    mean_si_pct: number;
    left_rom: number;
    right_rom: number;
    risk_status: string;
    risk_color: string;
  };
  time_series: Array<{ frame: number; leftKnee: number; rightKnee: number; symmetryIndex: number }>;
  angles_summary: {
    left_knee_max: number;
    left_knee_min: number;
    right_knee_max: number;
    right_knee_min: number;
  };
}

interface VideoUploaderProps {
  onUploadSuccess: (data: UploadResponse) => void;
  apiBase?: string;
}

export default function VideoUploader({
  onUploadSuccess,
  apiBase = "http://localhost:8000",
}: VideoUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progressText, setProgressText] = useState("");
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploadedFilename, setUploadedFilename] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [qualityBadge, setQualityBadge] = useState<{ status: string; score: number } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFileUpload = async (file: File) => {
    setUploadError(null);
    setUploading(true);
    setProgressText("Uploading video file...");

    try {
      const formData = new FormData();
      formData.append("file", file);

      setProgressText("Validating video quality...");
      const res = await fetch(`${apiBase}/api/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed with status ${res.status}`);
      }

      const data: UploadResponse = await res.json();

      if (data.status === "FAIL" && data.video_quality) {
        setQualityBadge({ status: "FAIL", score: data.video_quality.video_quality_score });
        onUploadSuccess(data);
        return;
      }

      setUploadedFilename(data.filename);
      setPreviewUrl(`${apiBase}${data.video_url}`);

      if (data.video_quality) {
        setQualityBadge({
          status: data.video_quality.status,
          score: data.video_quality.video_quality_score,
        });
      }

      setProgressText("Extracting 3D pose landmarks via MediaPipe...");
      onUploadSuccess(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setUploadError(msg);
    } finally {
      setUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith("video/") || /\.(mp4|avi|mov|webm|mkv)$/i.test(file.name)) {
        processFileUpload(file);
      } else {
        setUploadError("Please upload a valid video file (.mp4, .avi, .mov, .webm)");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFileUpload(e.target.files[0]);
    }
  };

  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #D6D3D1",
        borderRadius: "12px",
        padding: "14px",
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
          marginBottom: "10px",
          display: "flex",
          alignItems: "center",
          gap: "6px",
        }}
      >
        <span>📤</span> Custom Gait Scan Upload
      </div>

      {/* Drag and Drop Zone */}
      <div
        id="video-dropzone"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !uploading && fileInputRef.current?.click()}
        style={{
          border: `2px dashed ${isDragging ? "#78350F" : "#A8A29E"}`,
          background: isDragging ? "#FEF3C7" : "#F5F5F4",
          borderRadius: "8px",
          padding: "16px 12px",
          textAlign: "center",
          cursor: uploading ? "wait" : "pointer",
          transition: "all 0.15s ease",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "8px",
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/mp4,video/avi,video/quicktime,video/webm,.mp4,.avi,.mov,.webm,.mkv"
          onChange={handleFileChange}
          style={{ display: "none" }}
          id="custom-video-input"
        />

        {uploading ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <div className="spinner" style={{ width: "28px", height: "28px" }} />
            <span style={{ fontSize: "11px", color: "#78350F", fontWeight: 600 }}>
              {progressText}
            </span>
          </div>
        ) : (
          <>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "6px",
                background: "#78350F",
                color: "#FFFFFF",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "18px",
              }}
            >
              📤
            </div>
            <div>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#1C1917" }}>
                Drag & Drop gait video here
              </div>
              <div style={{ fontSize: "10px", color: "#57534E", marginTop: "2px" }}>
                or click to browse (.mp4, .avi, .mov, .webm)
              </div>
            </div>
          </>
        )}
      </div>

      {/* Quality Badge after upload */}
      {qualityBadge && !uploading && (
        <div
          style={{
            marginTop: "8px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "6px 10px",
            borderRadius: "6px",
            background:
              qualityBadge.status === "PASS"
                ? "#F0FDF4"
                : qualityBadge.status === "WARNING"
                ? "#FEF3C7"
                : "#FEF2F2",
            border: `1px solid ${
              qualityBadge.status === "PASS"
                ? "#86EFAC"
                : qualityBadge.status === "WARNING"
                ? "#FCD34D"
                : "#FCA5A5"
            }`,
            fontSize: "11px",
            fontWeight: 700,
            color:
              qualityBadge.status === "PASS"
                ? "#15803D"
                : qualityBadge.status === "WARNING"
                ? "#78350F"
                : "#B91C1C",
          }}
        >
          <span>
            {qualityBadge.status === "PASS" ? "✅" : qualityBadge.status === "WARNING" ? "⚠️" : "❌"}
          </span>
          Quality {qualityBadge.status} — Score {qualityBadge.score}/100
        </div>
      )}

      {/* Upload Error Banner */}
      {uploadError && (
        <div
          style={{
            marginTop: "8px",
            background: "#FEF2F2",
            border: "1px solid #FCA5A5",
            borderRadius: "6px",
            padding: "8px 10px",
            fontSize: "11px",
            color: "#B91C1C",
          }}
        >
          ⚠️ {uploadError}
        </div>
      )}

      {/* Uploaded Video Preview */}
      {previewUrl && !uploading && (
        <div style={{ marginTop: "12px" }}>
          <div
            style={{
              fontSize: "11px",
              color: "#15803D",
              fontWeight: 600,
              marginBottom: "4px",
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            ✓ Upload complete: {uploadedFilename}
          </div>
          <video
            controls
            src={previewUrl}
            style={{
              width: "100%",
              borderRadius: "6px",
              border: "1px solid #D6D3D1",
              maxHeight: "130px",
              objectFit: "cover",
              background: "#F5F5F4",
            }}
          />
        </div>
      )}
    </div>
  );
}
