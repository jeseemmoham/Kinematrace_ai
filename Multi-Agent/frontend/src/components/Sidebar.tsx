"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  href: string;
  label: string;
  icon: string;
  id: string;
}

const MAIN_NAV: NavItem[] = [
  { href: "/", label: "Dashboard", icon: "🏠", id: "nav-dashboard" },
  { href: "/agents/biomechanical", label: "Video Analysis", icon: "📹", id: "nav-video-analysis" },
  { href: "/agents/biomechanical", label: "Gait Results", icon: "📊", id: "nav-gait-results" },
  { href: "/agents/clinical-risk", label: "Risk Assessment", icon: "🛡️", id: "nav-risk-assessment" },
  { href: "/agents/patient-progress", label: "Progress Comparison", icon: "📈", id: "nav-progress-comparison" },
  { href: "/agents/empathetic-translator", label: "Family Guide", icon: "🤝", id: "nav-empathetic-translator" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside
      className="no-print"
      style={{
        width: "240px",
        minWidth: "240px",
        height: "100vh",
        position: "sticky",
        top: 0,
        backgroundColor: "#171412",
        borderRight: "1px solid #3A3028",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "20px 16px",
        zIndex: 50,
      }}
    >
      {/* Top Brand Logo */}
      <div>
        <Link
          href="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "12px",
            textDecoration: "none",
            marginBottom: "28px",
            padding: "4px 8px",
          }}
        >
          {/* Glowing Copper Logo Icon */}
          <div
            style={{
              width: "38px",
              height: "38px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #B45309 0%, #78350F 100%)",
              boxShadow: "0 0 14px rgba(180, 83, 9, 0.4)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "18px",
              color: "#F8F5F0",
              fontWeight: 800,
              flexShrink: 0,
            }}
          >
            🎯
          </div>
          <div>
            <div
              style={{
                fontWeight: 700,
                fontSize: "16px",
                color: "#F8F5F0",
                letterSpacing: "-0.01em",
                lineHeight: 1.2,
              }}
            >
              KinemaTrace <span style={{ color: "#B45309" }}>AI</span>
            </div>
            <div
              style={{
                fontSize: "10px",
                color: "#A8A09A",
                letterSpacing: "0.03em",
                fontWeight: 500,
              }}
            >
              Pediatric Gait Intelligence
            </div>
          </div>
        </Link>

        {/* Main Navigation Links */}
        <nav style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          {MAIN_NAV.map((item) => {
            const isActive = pathname === item.href;

            return (
              <Link
                key={item.id}
                id={item.id}
                href={item.href}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "10px 14px",
                  borderRadius: "8px",
                  fontSize: "13px",
                  fontWeight: isActive ? 700 : 500,
                  textDecoration: "none",
                  transition: "all 0.15s ease",
                  background: isActive ? "#211C18" : "transparent",
                  color: isActive ? "#F8F5F0" : "#A8A09A",
                  borderLeft: isActive ? "3px solid #B45309" : "3px solid transparent",
                }}
              >
                <span
                  style={{
                    fontSize: "16px",
                    color: isActive ? "#B45309" : "#A8A09A",
                  }}
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom Section: System Status */}
      <div>
        {/* System Status Indicator Box */}
        <div
          style={{
            background: "#211C18",
            border: "1px solid #3A3028",
            borderRadius: "10px",
            padding: "12px 14px",
          }}
        >
          <div
            style={{
              fontSize: "11px",
              fontWeight: 600,
              color: "#A8A09A",
              marginBottom: "4px",
            }}
          >
            System Status
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "12px",
              fontWeight: 600,
              color: "#10B981",
            }}
          >
            <span className="pulse-dot-kt green" />
            <span>All Systems Operational</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
