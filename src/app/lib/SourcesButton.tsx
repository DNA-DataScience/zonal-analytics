"use client";
import React from "react";

type SourcesButtonProps = {
  href: string;
  label?: string;
};

export function SourcesButton({
  href,
  label = "Sources",
}: SourcesButtonProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "6px 10px",
        background: "rgba(0,0,0,0.6)",
        color: "#fff",
        borderRadius: 8,
        textDecoration: "none",
        fontSize: 12,
        lineHeight: 1,
        border: "1px solid rgba(255,255,255,0.2)",
        backdropFilter: "blur(4px)",
      }}
    >
      {/* Document / sources icon */}
      <svg
        aria-hidden="true"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6zm2-5h8v1.5H8V15zm0-3h8v1.5H8V12zm0-3h4v1.5H8V9z" />
      </svg>
      <span>{label}</span>
    </a>
  );
}
