"use client";
import React from "react";

type FeedbackButtonProps = {
  href: string;
  label?: string;
};

export function FeedbackButton({
  href,
  label = "Feedback",
}: FeedbackButtonProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={label}
      style={{
        position: "fixed",
        bottom: 12,
        left: 12,
        zIndex: 1000,
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
      <svg
        aria-hidden="true"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-7 13h-2v-2h2v2zm0-4h-2V7h2v4z" />
      </svg>
      <span>{label}</span>
    </a>
  );
}
