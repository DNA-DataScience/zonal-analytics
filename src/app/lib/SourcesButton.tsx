"use client";
import React from "react";

type SourcesButtonProps = {
  href: string;
  label?: string;
};

export function SourcesButton({
  href,
  label = "Airports Source",
}: SourcesButtonProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      style={{
        position: "fixed",
        bottom: 12,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 1000,
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "9px 14px",
        background: "rgba(255,255,255,0.92)",
        color: "#0f172a",
        borderRadius: 10,
        textDecoration: "none",
        fontSize: 13,
        fontWeight: 600,
        lineHeight: 1,
        border: "1px solid rgba(15,23,42,0.08)",
        boxShadow: "0 6px 18px rgba(2,6,23,0.12)",
        backdropFilter: "blur(16px) saturate(170%)",
        WebkitBackdropFilter: "blur(16px) saturate(170%)",
      }}
    >
      <svg
        aria-hidden="true"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9L2 14v2l8-2.5V19l-2 1.5V22l3-1 3 1v-1.5L13 19v-5.5l8 2.5z" />
      </svg>
      <span>{label}</span>
    </a>
  );
}
