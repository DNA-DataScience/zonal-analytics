"use client";
import React, { FormEvent, useState } from "react";

type FeedbackButtonProps = {
  label?: string;
};

export function FeedbackButton({ label = "Feedback" }: FeedbackButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const form = event.currentTarget;
    const formData = new FormData(form);
    const name = formData.get("name")?.toString().trim() ?? "";
    const message = formData.get("message")?.toString().trim() ?? "";

    if (!name || !message) {
      setSubmitStatus("error");
      setErrorMessage("Please enter both name and message.");
      return;
    }

    const apiBaseUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

    setIsSubmitting(true);
    setSubmitStatus("idle");
    setErrorMessage(null);

    try {
      const response = await fetch(`${apiBaseUrl}/feedback/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name, message }),
      });

      if (!response.ok) {
        console.error(`Failed to submit feedback with status ${response.status}`);
        setSubmitStatus("error");
        setErrorMessage("Failed to submit feedback. Please try again.");
        return;
      }

      form.reset();
      setSubmitStatus("success");
    } catch (error) {
      console.error("Failed to submit feedback:", error);
      setSubmitStatus("error");
      setErrorMessage("Failed to submit feedback. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <button
        type="button"
        aria-label={label}
        onClick={() => {
          setSubmitStatus("idle");
          setErrorMessage(null);
          setIsOpen(true);
        }}
        style={{
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
              borderRadius: 16,
              boxShadow: "0 20px 50px rgba(2, 6, 23, 0.28)",
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
                maxLength={120}
                style={{ border: "1px solid #cbd5e1", borderRadius: 6, padding: "8px 10px" }}
              />
            </label>
            <label style={{ fontSize: 12, display: "grid", gap: 4 }}>
              Message
              <textarea
                name="message"
                required
                rows={5}
                maxLength={2000}
                style={{ border: "1px solid #cbd5e1", borderRadius: 6, padding: "8px 10px", resize: "vertical" }}
              />
            </label>

            {submitStatus === "success" && (
              <div style={{ fontSize: 12, color: "#15803d", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 6, padding: "8px 10px" }}>
                Feedback submitted successfully.
              </div>
            )}

            {submitStatus === "error" && errorMessage && (
              <div style={{ fontSize: 12, color: "#b91c1c", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 6, padding: "8px 10px" }}>
                {errorMessage}
              </div>
            )}

            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                disabled={isSubmitting}
                style={{
                  border: "1px solid #cbd5e1",
                  background: "#f8fafc",
                  color: "#0f172a",
                  borderRadius: 6,
                  padding: "8px 12px",
                  cursor: isSubmitting ? "not-allowed" : "pointer",
                  opacity: isSubmitting ? 0.7 : 1,
                }}
              >
                Close
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                style={{
                  border: "1px solid #2563eb",
                  background: "#2563eb",
                  color: "#ffffff",
                  borderRadius: 8,
                  padding: "8px 14px",
                  fontWeight: 600,
                  cursor: isSubmitting ? "not-allowed" : "pointer",
                  opacity: isSubmitting ? 0.7 : 1,
                }}
              >
                {isSubmitting ? "Submitting..." : "Submit"}
              </button>
            </div>
          </form>
        </div>
      )}
    </>
  );
}
