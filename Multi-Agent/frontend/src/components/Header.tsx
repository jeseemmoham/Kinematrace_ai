"use client";

import React, { useState, useEffect } from "react";

export default function Header() {
  const [timeString, setTimeString] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const formatted =
        now.toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" }) +
        " " +
        now.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true });
      setTimeString(formatted);
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header
      className="no-print"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "16px 28px",
        background: "transparent",
        position: "relative",
        zIndex: 10,
      }}
    >
      {/* Clinician Greeting */}
      <div>
        <h1
          style={{
            fontSize: "20px",
            fontWeight: 700,
            color: "#F8F5F0",
            margin: 0,
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          Welcome back, Clinician <span style={{ fontSize: "20px" }}>👋</span>
        </h1>
        <p style={{ fontSize: "12px", color: "#A8A09A", margin: "4px 0 0 0" }}>
          AI-powered pediatric gait screening and progress analysis
        </p>
      </div>

      {/* Right Controls */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        {/* Date / Time Card */}
        <div
          style={{
            background: "#211C18",
            border: "1px solid #3A3028",
            borderRadius: "8px",
            padding: "6px 14px",
            fontSize: "11px",
            fontFamily: "monospace",
            color: "#A8A09A",
            letterSpacing: "0.02em",
          }}
        >
          {timeString}
        </div>

        {/* User Profile Avatar */}
        <button
          id="btn-user-profile"
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "50%",
            background: "#211C18",
            border: "1px solid #3A3028",
            color: "#A8A09A",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
          }}
        >
          <span style={{ fontSize: "16px" }}>👤</span>
        </button>
      </div>
    </header>
  );
}
