"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard & Capture", icon: "📹", id: "nav-dashboard" },
  { href: "/agents/biomechanical", label: "Gait Analysis", icon: "🔬", id: "nav-biomechanical" },
  { href: "/agents/clinical-risk", label: "Clinical Risk", icon: "🛡️", id: "nav-clinical-risk" },
  { href: "/agents/patient-progress", label: "Patient Progress", icon: "📊", id: "nav-patient-progress" },
  { href: "/agents/empathetic-translator", label: "Family Guide", icon: "🤝", id: "nav-empathetic-translator" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav
      className="no-print"
      style={{
        background: "#FFFFFF",
        borderBottom: "1px solid #E7E5E4",
        padding: "10px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Brand logo & title */}
      <Link
        href="/"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          textDecoration: "none",
          color: "#1C1917",
        }}
      >
        <div
          style={{
            width: "36px",
            height: "36px",
            borderRadius: "8px",
            background: "#78350F",
            color: "#FFFFFF",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "18px",
            fontWeight: 800,
          }}
        >
          K
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: "15px", letterSpacing: "-0.01em", color: "#1C1917" }}>
            KinemaTrace <span style={{ color: "#78350F" }}>AI</span>
          </div>
          <div style={{ fontSize: "10px", color: "#57534E", letterSpacing: "0.05em", textTransform: "uppercase" }}>
            Pediatric Gait Screening Platform
          </div>
        </div>
      </Link>

      {/* Navigation Links */}
      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              id={item.id}
              href={item.href}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 14px",
                borderRadius: "8px",
                fontSize: "12px",
                fontWeight: isActive ? 700 : 500,
                textDecoration: "none",
                transition: "all 0.15s ease",
                background: isActive ? "#78350F" : "#F5F5F4",
                color: isActive ? "#FFFFFF" : "#57534E",
                border: isActive ? "1px solid #78350F" : "1px solid #D6D3D1",
              }}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      {/* Status indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div className="badge badge-green">
          <span className="pulse-dot green" />
          Clinical Precision System
        </div>
      </div>
    </nav>
  );
}
