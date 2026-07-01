/**
 * Analytics client for tracking user sessions and events
 * Place this file in your frontend repo and import it
 *
 * Usage:
 *   import { initAnalytics, trackEvent } from './analytics.js';
 *
 *   // On app start (e.g., in main.tsx or App.js)
 *   initAnalytics('http://localhost:8000'); // dev
 *   // or
 *   initAnalytics('https://your-api-domain.com'); // production
 *
 *   // Later, track API calls:
 *   trackEvent('api_call', '/report-generator', { lat: 28.5, lng: 77.5 });
 */

class AnalyticsClient {
  constructor(apiBaseUrl, isDev = false) {
    this.apiBaseUrl = apiBaseUrl;
    this.isDev = isDev;
    this.anonymousId = this.getOrCreateAnonymousId();
    this.sessionId = null;
    this.heartbeatInterval = null;
  }

  /**
   * Get anonymous ID from localStorage or create a new one
   */
  getOrCreateAnonymousId() {
    let id = localStorage.getItem("analytics_anonymous_id");
    if (!id) {
      id = this.generateUUID();
      localStorage.setItem("analytics_anonymous_id", id);
    }
    return id;
  }

  /**
   * Generate a UUID v4
   */
  generateUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
      /[xy]/g,
      function (c) {
        const r = (Math.random() * 16) | 0;
        const v = c === "x" ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      },
    );
  }

  /**
   * Start a new session on page load
   */
  async startSession() {
    try {
      const clientEnv = this.isDev ? "development" : "production";
      const userAgent = navigator.userAgent;
      const referrer = document.referrer || null;

      const response = await fetch(
        `${this.apiBaseUrl}/analytics/session/start`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(this.isDev && { "X-Client-Env": "development" }),
          },
          body: JSON.stringify({
            anonymous_id: this.anonymousId,
            client_env: clientEnv,
            user_agent: userAgent,
            referrer: referrer,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to start session: ${response.statusText}`);
      }

      const data = await response.json();
      this.sessionId = data.session_id;
      sessionStorage.setItem("analytics_session_id", this.sessionId);

      console.log("[Analytics] Session started:", this.sessionId);

      // Start heartbeat (every 30 seconds)
      this.startHeartbeat();

      // End session on page unload
      this.setupUnloadHandler();
    } catch (error) {
      console.error("[Analytics] Failed to start session:", error);
    }
  }

  /**
   * Send heartbeat to keep session alive
   */
  async sendHeartbeat() {
    if (!this.sessionId) return;

    try {
      const response = await fetch(`${this.apiBaseUrl}/analytics/heartbeat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(this.isDev && { "X-Client-Env": "development" }),
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          anonymous_id: this.anonymousId,
        }),
      });

      if (!response.ok) {
        console.warn("[Analytics] Heartbeat failed:", response.statusText);
      }
    } catch (error) {
      console.error("[Analytics] Heartbeat error:", error);
    }
  }

  /**
   * Start periodic heartbeat
   */
  startHeartbeat() {
    // Send heartbeat every 30 seconds
    this.heartbeatInterval = setInterval(() => {
      this.sendHeartbeat();
    }, 30000);
  }

  /**
   * Stop heartbeat
   */
  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * End the session
   */
  async endSession() {
    if (!this.sessionId) return;

    this.stopHeartbeat();

    try {
      // Use sendBeacon for reliable delivery even on page unload
      const data = JSON.stringify({
        session_id: this.sessionId,
        anonymous_id: this.anonymousId,
      });

      // Try sendBeacon first (most reliable on unload)
      if (navigator.sendBeacon) {
        navigator.sendBeacon(`${this.apiBaseUrl}/analytics/session/end`, data);
      } else {
        // Fallback to fetch
        await fetch(`${this.apiBaseUrl}/analytics/session/end`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: data,
          keepalive: true, // Keep connection alive during unload
        });
      }

      console.log("[Analytics] Session ended");
      sessionStorage.removeItem("analytics_session_id");
    } catch (error) {
      console.error("[Analytics] Failed to end session:", error);
    }
  }

  /**
   * Setup handlers for page unload
   */
  setupUnloadHandler() {
    // For modern browsers
    if ("onbeforeunload" in window) {
      window.addEventListener("beforeunload", () => {
        this.endSession();
      });
    }

    // Also try unload
    window.addEventListener("unload", () => {
      this.endSession();
    });

    // For SPAs, also handle route changes if using a router
    // This is framework-specific (React Router, Next.js, Vue Router, etc.)
  }

  /**
   * Track a custom event
   */
  async trackEvent(eventType, endpoint = null, metadata = null) {
    if (!this.sessionId) {
      console.warn("[Analytics] No active session, skipping event");
      return;
    }

    try {
      const response = await fetch(`${this.apiBaseUrl}/analytics/event`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(this.isDev && { "X-Client-Env": "development" }),
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          event_type: eventType,
          endpoint: endpoint,
          metadata: metadata,
        }),
      });

      if (!response.ok) {
        console.warn("[Analytics] Failed to track event:", response.statusText);
      }
    } catch (error) {
      console.error("[Analytics] Error tracking event:", error);
    }
  }
}

// Global instance
let analyticsClient = null;

/**
 * Initialize analytics client
 * Call this once on app startup
 */
export function initAnalytics(apiBaseUrl, isDev = false) {
  analyticsClient = new AnalyticsClient(apiBaseUrl, isDev);
  analyticsClient.startSession();
  return analyticsClient;
}

/**
 * Track an event
 */
export function trackEvent(eventType, endpoint = null, metadata = null) {
  if (analyticsClient) {
    analyticsClient.trackEvent(eventType, endpoint, metadata);
  }
}

/**
 * Get the current session ID (for debugging)
 */
export function getSessionId() {
  return analyticsClient?.sessionId || null;
}

/**
 * Get the current anonymous ID (for debugging)
 */
export function getAnonymousId() {
  return analyticsClient?.anonymousId || null;
}

export default {
  initAnalytics,
  trackEvent,
  getSessionId,
  getAnonymousId,
};
