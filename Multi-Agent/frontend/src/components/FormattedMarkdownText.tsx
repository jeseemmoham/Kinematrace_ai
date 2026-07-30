"use client";

import React from "react";

interface FormattedMarkdownTextProps {
  text: string;
  className?: string;
  style?: React.CSSProperties;
}

export default function FormattedMarkdownText({ text, className, style }: FormattedMarkdownTextProps) {
  if (!text) return null;

  const lines = text.split("\n");
  const elements: React.ReactNode[] = [];
  let currentListItems: React.ReactNode[] = [];

  const flushList = (key: string) => {
    if (currentListItems.length > 0) {
      elements.push(
        <ul
          key={`ul-${key}`}
          style={{
            margin: "6px 0 10px 0",
            paddingLeft: "0px",
            listStyle: "none",
            display: "flex",
            flexDirection: "column",
            gap: "8px",
          }}
        >
          {currentListItems}
        </ul>
      );
      currentListItems = [];
    }
  };

  lines.forEach((rawLine, idx) => {
    const trimmed = rawLine.trim();

    if (!trimmed) {
      flushList(`${idx}`);
      return;
    }

    // Bullet point check: "- ...", "* ...", "• ..."
    const bulletMatch = trimmed.match(/^[-*•]\s+(.*)$/);
    if (bulletMatch) {
      const content = bulletMatch[1];
      currentListItems.push(
        <li
          key={`li-${idx}`}
          style={{
            display: "flex",
            alignItems: "flex-start",
            gap: "8px",
            fontSize: "12px",
            lineHeight: "1.65",
            color: "#E2D8CE",
          }}
        >
          <span
            style={{
              color: "#D97706",
              fontWeight: 800,
              fontSize: "14px",
              lineHeight: "1.2",
              marginTop: "2px",
            }}
          >
            •
          </span>
          <div style={{ flex: 1 }}>{parseInlineFormatting(content)}</div>
        </li>
      );
      return;
    }

    // Not a bullet line, flush any open list
    flushList(`${idx}`);

    // Standalone header check: "### Header", "**Agent 3 — Title:**", "**Section Title**"
    const isHeaderMatch =
      trimmed.startsWith("###") ||
      trimmed.startsWith("##") ||
      trimmed.startsWith("#") ||
      (trimmed.startsWith("**") && (trimmed.endsWith("**") || trimmed.endsWith(":**")));

    if (isHeaderMatch) {
      const titleText = trimmed
        .replace(/^[#*\s]+/, "")
        .replace(/[:*\s]+$/, "");

      elements.push(
        <div
          key={`hdr-${idx}`}
          style={{
            fontWeight: 700,
            fontSize: "13px",
            color: "#F8F5F0",
            padding: "6px 12px",
            background: "rgba(217, 119, 6, 0.12)",
            borderLeft: "3px solid #D97706",
            borderRadius: "4px",
            margin: "10px 0 6px 0",
            letterSpacing: "-0.01em",
          }}
        >
          {titleText}
        </div>
      );
      return;
    }

    // Normal paragraph line
    elements.push(
      <p
        key={`p-${idx}`}
        style={{
          margin: "4px 0 6px 0",
          fontSize: "12px",
          lineHeight: "1.65",
          color: "#E2D8CE",
        }}
      >
        {parseInlineFormatting(trimmed)}
      </p>
    );
  });

  flushList("end");

  return (
    <div className={className} style={{ display: "flex", flexDirection: "column", gap: "2px", ...style }}>
      {elements}
    </div>
  );
}

// Parses inline bold `**text**`, `code`, and risk badges
function parseInlineFormatting(text: string): React.ReactNode[] {
  // Regex splitting by `**bold**` or ``code``
  const tokens = text.split(/(\*\*.*?\*\*|`.*?`)/g);

  return tokens.map((token, i) => {
    if (!token) return null;

    if (token.startsWith("**") && token.endsWith("**")) {
      const inner = token.slice(2, -2).trim();
      if (!inner) return null;

      // Check if inner matches status or risk keywords for badge rendering
      const upper = inner.toUpperCase();
      if (
        upper.includes("NORMATIVE GAIT RISK") ||
        upper.includes("NORMATIVE RANGE") ||
        upper.includes("LOW RISK") ||
        upper === "NORMAL" ||
        upper === "LOW" ||
        upper === "PASS"
      ) {
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              padding: "2px 8px",
              borderRadius: "6px",
              background: "rgba(16, 185, 129, 0.18)",
              color: "#10B981",
              border: "1px solid rgba(16, 185, 129, 0.35)",
              fontSize: "11px",
              fontWeight: 800,
              letterSpacing: "0.02em",
              margin: "0 3px",
            }}
          >
            {inner}
          </span>
        );
      }

      if (
        upper.includes("HIGH RISK") ||
        upper.includes("ELEVATED") ||
        upper === "HIGH" ||
        upper === "SEVERE" ||
        upper === "FAIL" ||
        upper.includes("CRITICAL")
      ) {
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              padding: "2px 8px",
              borderRadius: "6px",
              background: "rgba(239, 68, 68, 0.18)",
              color: "#EF4444",
              border: "1px solid rgba(239, 68, 68, 0.35)",
              fontSize: "11px",
              fontWeight: 800,
              letterSpacing: "0.02em",
              margin: "0 3px",
            }}
          >
            {inner}
          </span>
        );
      }

      if (
        upper.includes("MEDIUM RISK") ||
        upper.includes("MODERATE") ||
        upper === "WARNING" ||
        upper === "STABLE"
      ) {
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              padding: "2px 8px",
              borderRadius: "6px",
              background: "rgba(245, 158, 11, 0.18)",
              color: "#F59E0B",
              border: "1px solid rgba(245, 158, 11, 0.35)",
              fontSize: "11px",
              fontWeight: 800,
              letterSpacing: "0.02em",
              margin: "0 3px",
            }}
          >
            {inner}
          </span>
        );
      }

      return (
        <strong key={i} style={{ fontWeight: 700, color: "#F8F5F0" }}>
          {inner}
        </strong>
      );
    }

    if (token.startsWith("`") && token.endsWith("`")) {
      return (
        <code
          key={i}
          style={{
            background: "rgba(255, 255, 255, 0.08)",
            padding: "2px 6px",
            borderRadius: "4px",
            fontSize: "11px",
            color: "#D97706",
            fontFamily: "monospace",
          }}
        >
          {token.slice(1, -1)}
        </code>
      );
    }

    return <React.Fragment key={i}>{token}</React.Fragment>;
  });
}
