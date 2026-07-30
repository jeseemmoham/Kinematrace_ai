"use client";

import React, { useRef, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface TimeSeriesPoint {
  frame: number;
  leftKnee: number;
  rightKnee: number;
  symmetryIndex: number;
}

interface AnglesSummary {
  left_knee_max: number;
  left_knee_min: number;
  right_knee_max: number;
  right_knee_min: number;
}

interface VideoKinematicsPlayerProps {
  videoUrl: string | null;
  timeSeries: TimeSeriesPoint[];
  anglesSummary: AnglesSummary | null;
  loading?: boolean;
}

const ASYMMETRY_THRESHOLD = 15;

export default function VideoKinematicsPlayer({
  videoUrl,
  timeSeries,
  anglesSummary,
  loading,
}: VideoKinematicsPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [currentFrame, setCurrentFrame] = useState(0);

  const handleTimeUpdate = () => {
    if (videoRef.current && timeSeries.length > 0) {
      const pct = videoRef.current.currentTime / (videoRef.current.duration || 1);
      const idx = Math.min(Math.floor(pct * timeSeries.length), timeSeries.length - 1);
      setCurrentFrame(idx);
    }
  };

  const chartData = timeSeries.map((pt) => ({
    ...pt,
    name: `F${pt.frame}`,
    asymmetryLine: ASYMMETRY_THRESHOLD,
  }));

  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #D6D3D1",
        borderRadius: "12px",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
      }}
    >
      {/* Panel header */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid #E7E5E4",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "#F5F5F4",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "14px" }}>📹</span>
          <span style={{ fontWeight: 700, fontSize: "13px", color: "#1C1917" }}>Video Analysis Workspace</span>
          <span
            className="badge badge-blue"
            style={{ fontSize: "10px", padding: "2px 8px" }}
          >
            MediaPipe 3D
          </span>
        </div>
        {anglesSummary && (
          <div style={{ display: "flex", gap: "12px", fontSize: "11px", color: "#57534E" }}>
            <span>
              Left ROM: <strong style={{ color: "#78350F" }}>
                {(anglesSummary.left_knee_max - anglesSummary.left_knee_min).toFixed(1)}°
              </strong>
            </span>
            <span>
              Right ROM: <strong style={{ color: "#44403C" }}>
                {(anglesSummary.right_knee_max - anglesSummary.right_knee_min).toFixed(1)}°
              </strong>
            </span>
          </div>
        )}
      </div>

      {/* Video Screen Container */}
      <div
        style={{
          background: "#1C1917",
          position: "relative",
          aspectRatio: "16/9",
          flexShrink: 0,
        }}
      >
        {loading ? (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "14px",
              color: "#A8A29E",
            }}
          >
            <div className="spinner" />
            <span style={{ fontSize: "13px" }}>Processing video analysis pipeline…</span>
          </div>
        ) : videoUrl ? (
          <video
            ref={videoRef}
            src={`http://localhost:8000${videoUrl}`}
            controls
            autoPlay
            loop
            muted
            onTimeUpdate={handleTimeUpdate}
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        ) : (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#A8A29E",
              fontSize: "13px",
            }}
          >
            Select a patient case to load video analysis
          </div>
        )}

        {/* Frame Telemetry Overlay */}
        {!loading && videoUrl && timeSeries[currentFrame] && (
          <div
            style={{
              position: "absolute",
              top: "8px",
              left: "8px",
              background: "rgba(28, 25, 23, 0.85)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "6px",
              padding: "6px 10px",
              fontSize: "11px",
              color: "#F8F9FA",
            }}
          >
            <div style={{ color: "#FDE68A" }}>
              L Knee: {timeSeries[currentFrame].leftKnee.toFixed(1)}°
            </div>
            <div style={{ color: "#D6D3D1" }}>
              R Knee: {timeSeries[currentFrame].rightKnee.toFixed(1)}°
            </div>
            <div
              style={{
                color:
                  timeSeries[currentFrame].symmetryIndex > ASYMMETRY_THRESHOLD
                    ? "#FCA5A5"
                    : "#86EFAC",
                fontWeight: 600,
              }}
            >
              SI: {timeSeries[currentFrame].symmetryIndex.toFixed(1)}%
            </div>
          </div>
        )}
      </div>

      {/* Kinematics Time-Series Chart */}
      <div style={{ padding: "14px 16px", flex: 1, minHeight: 0 }}>
        <div
          style={{
            fontSize: "11px",
            color: "#57534E",
            fontWeight: 700,
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            marginBottom: "10px",
          }}
        >
          📈 Real-Time Knee Angle Time-Series (Degrees)
        </div>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={chartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="leftGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#78350F" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#78350F" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="rightGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#78716C" stopOpacity={0.25} />
                  <stop offset="95%" stopColor="#78716C" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E7E5E4" />
              <XAxis dataKey="frame" tick={{ fontSize: 9, fill: "#57534E" }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 9, fill: "#57534E" }} domain={[0, 180]} />
              <Tooltip
                contentStyle={{
                  background: "#FFFFFF",
                  border: "1px solid #D6D3D1",
                  borderRadius: "6px",
                  fontSize: "12px",
                  color: "#1C1917",
                  boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
                }}
                labelStyle={{ color: "#57534E" }}
              />
              <Legend wrapperStyle={{ fontSize: "11px", color: "#57534E" }} />
              <ReferenceLine y={110} stroke="#A8A29E" strokeDasharray="4 4" strokeWidth={1} label={{ value: "Norm 110°", fontSize: 9, fill: "#A8A29E" }} />
              <Area type="monotone" dataKey="leftKnee"  name="Left Knee (°)"  stroke="#78350F" fill="url(#leftGrad)"  strokeWidth={2} dot={false} />
              <Area type="monotone" dataKey="rightKnee" name="Right Knee (°)" stroke="#78716C" fill="url(#rightGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div
            style={{
              height: "160px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#A8A29E",
              fontSize: "13px",
            }}
          >
            Awaiting kinematic frame data…
          </div>
        )}
      </div>
    </div>
  );
}
