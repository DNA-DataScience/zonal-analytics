"use client";
import React, { FormEvent, useState } from "react";

type FeedbackButtonProps = {
  label?: string;
};

export function FeedbackButton({ label = "Feedback" }: FeedbackButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitted(true);
  };

  return (
    <>
      <button
        type="button"
        aria-label={label}
        onClick={() => {
          setSubmitted(false);
          setIsOpen(true);
        }}
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
          cursor: "pointer",
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
      </button>

      {isOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="Feedback form"
          onClick={() => setIsOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15, 23, 42, 0.5)",
            zIndex: 1200,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 16,
          }}
        >
          <form
            onSubmit={handleSubmit}
            onClick={(event) => event.stopPropagation()}
            style={{
              width: "100%",
              maxWidth: 440,
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: 12,
              boxShadow: "0 10px 30px rgba(15, 23, 42, 0.2)",
              padding: 16,
              display: "grid",
              gap: 10,
              color: "#0f172a",
            }}
          >
            <div style={{ fontSize: 16, fontWeight: 600 }}>Share Feedback</div>
            <label style={{ fontSize: 12, display: "grid", gap: 4 }}>
              Name
              <input
                type="text"
                name="name"
                required
                style={{ border: "1px solid #cbd5e1", borderRadius: 6, padding: "8px 10px" }}
              />
            </label>
            <label style={{ fontSize: 12, display: "grid", gap: 4 }}>
              Email (optional)
              <input
                type="email"
                name="email"
                style={{ border: "1px solid #cbd5e1", borderRadius: 6, padding: "8px 10px" }}
              />
            </label>
            <label style={{ fontSize: 12, display: "grid", gap: 4 }}>
              Message
              <textarea
                name="message"
                required
                rows={5}
                style={{ border: "1px solid #cbd5e1", borderRadius: 6, padding: "8px 10px", resize: "vertical" }}
              />
            </label>

            {submitted && (
              <div style={{ fontSize: 12, color: "#15803d", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 6, padding: "8px 10px" }}>
                Feedback captured in UI. Backend submission will be wired later.
              </div>
            )}

            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                style={{
                  border: "1px solid #cbd5e1",
                  background: "#f8fafc",
                  color: "#0f172a",
                  borderRadius: 6,
                  padding: "8px 12px",
                  cursor: "pointer",
                }}
              >
                Close
              </button>
              <button
                type="submit"
                style={{
                  border: "1px solid #0f172a",
                  background: "#0f172a",
                  color: "#ffffff",
                  borderRadius: 6,
                  padding: "8px 12px",
                  cursor: "pointer",
                }}
              >
                Submit
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
