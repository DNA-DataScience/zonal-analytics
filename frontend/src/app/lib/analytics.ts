type EventMetadata = Record<string, unknown> | null;

class AnalyticsClient {
  private apiBaseUrl: string;
  private isDev: boolean;
  private anonymousId: string;
  private sessionId: string | null;
  private heartbeatInterval: ReturnType<typeof setInterval> | null;
  private unloadHandlerAttached: boolean;

  constructor(apiBaseUrl: string, isDev = false) {
    this.apiBaseUrl = apiBaseUrl.replace(/\/$/, "");
    this.isDev = isDev;
    this.anonymousId = this.getOrCreateAnonymousId();
    this.sessionId = null;
    this.heartbeatInterval = null;
    this.unloadHandlerAttached = false;
  }

  private getOrCreateAnonymousId(): string {
    if (typeof window === "undefined") {
      return this.generateUUID();
    }

    let id = localStorage.getItem("analytics_anonymous_id");
    if (!id) {
      id = this.generateUUID();
      localStorage.setItem("analytics_anonymous_id", id);
    }
    return id;
  }

  private generateUUID(): string {
    if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }

    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  private getHeaders(): Record<string, string> {
    return {
      "Content-Type": "application/json",
      ...(this.isDev ? { "X-Client-Env": "development" } : {}),
    };
  }

  async startSession(): Promise<void> {
    if (typeof window === "undefined") {
      return;
    }

    try {
      const clientEnv = this.isDev ? "development" : "production";
      const userAgent = navigator.userAgent;
      const referrer = document.referrer || null;

      const response = await fetch(`${this.apiBaseUrl}/analytics/session/start`, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify({
          anonymous_id: this.anonymousId,
          client_env: clientEnv,
          user_agent: userAgent,
          referrer,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to start session: ${response.statusText}`);
      }

      const data = (await response.json()) as { session_id?: string };
      if (!data.session_id) {
        throw new Error("Session start response missing session_id");
      }

      this.sessionId = data.session_id;
      sessionStorage.setItem("analytics_session_id", this.sessionId);

      this.startHeartbeat();
      this.setupUnloadHandler();
    } catch (error) {
      console.error("[Analytics] Failed to start session:", error);
    }
  }

  private async sendHeartbeat(): Promise<void> {
    if (!this.sessionId) {
      return;
    }

    try {
      const response = await fetch(`${this.apiBaseUrl}/analytics/heartbeat`, {
        method: "POST",
        headers: this.getHeaders(),
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

  private startHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  async endSession(): Promise<void> {
    if (!this.sessionId || typeof window === "undefined") {
      return;
    }

    this.stopHeartbeat();

    try {
      const payload = JSON.stringify({
        session_id: this.sessionId,
        anonymous_id: this.anonymousId,
      });

      if (navigator.sendBeacon) {
        const blob = new Blob([payload], { type: "application/json" });
        navigator.sendBeacon(`${this.apiBaseUrl}/analytics/session/end`, blob);
      } else {
        await fetch(`${this.apiBaseUrl}/analytics/session/end`, {
          method: "POST",
          headers: this.getHeaders(),
          body: payload,
          keepalive: true,
        });
      }

      sessionStorage.removeItem("analytics_session_id");
      this.sessionId = null;
    } catch (error) {
      console.error("[Analytics] Failed to end session:", error);
    }
  }

  private setupUnloadHandler(): void {
    if (this.unloadHandlerAttached || typeof window === "undefined") {
      return;
    }

    const handleUnload = () => {
      void this.endSession();
    };

    window.addEventListener("beforeunload", handleUnload);
    window.addEventListener("unload", handleUnload);
    this.unloadHandlerAttached = true;
  }

  async trackEvent(
    eventType: string,
    endpoint: string | null = null,
    metadata: EventMetadata = null,
  ): Promise<void> {
    void eventType;
    void endpoint;
    void metadata;
  }

  getSessionId(): string | null {
    return this.sessionId;
  }

  getAnonymousId(): string {
    return this.anonymousId;
  }
}

let analyticsClient: AnalyticsClient | null = null;

export function initAnalytics(apiBaseUrl: string, isDev = false): AnalyticsClient {
  if (!analyticsClient) {
    analyticsClient = new AnalyticsClient(apiBaseUrl, isDev);
    void analyticsClient.startSession();
  }
  return analyticsClient;
}

export function trackEvent(
  eventType: string,
  endpoint: string | null = null,
  metadata: EventMetadata = null,
): void {
  if (analyticsClient) {
    void analyticsClient.trackEvent(eventType, endpoint, metadata);
  }
}

export function getSessionId(): string | null {
  return analyticsClient?.getSessionId() ?? null;
}

export function getAnonymousId(): string | null {
  return analyticsClient?.getAnonymousId() ?? null;
}
