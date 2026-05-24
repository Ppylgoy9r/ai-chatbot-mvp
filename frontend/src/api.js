/**
 * API Client — Centralized HTTP helper for all backend calls.
 * Automatically attaches JWT tokens from localStorage.
 */

const API_BASE = "/api";

function getToken() {
  return localStorage.getItem("access_token");
}

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const token = getToken();

  const headers = { ...options.headers };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  // Don't set Content-Type for FormData (browser sets boundary automatically)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.error || JSON.stringify(err));
  }

  // 204 No Content
  if (res.status === 204) return null;

  return res.json();
}

// ──────── Auth ────────

export const auth = {
  register: (data) => request("/auth/register/", { method: "POST", body: JSON.stringify(data) }),
  login: async (username, password) => {
    const res = await fetch(`${API_BASE}/auth/token/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) throw new Error("Invalid credentials");
    const data = await res.json();
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    return data;
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/login";
  },
  me: () => request("/auth/me/"),
};

// ──────── Chat ────────

export const chat = {
  listSessions: () => request("/chat/sessions/"),
  createSession: (title = "New Chat") => request("/chat/sessions/", { method: "POST", body: JSON.stringify({ title }) }),
  getSession: (id) => request(`/chat/sessions/${id}/`),
  deleteSession: (id) => request(`/chat/sessions/${id}/`, { method: "DELETE" }),
  getMessages: (sessionId) => request(`/chat/sessions/${sessionId}/messages/`),

  /**
   * Send a message and receive a streaming response via SSE.
   * Calls onToken(token) for each streamed token.
   * Calls onDone(metadata) when complete.
   * Returns an AbortController so the caller can cancel.
   */
  queryStream: (message, sessionId, { onToken, onDone, onError }) => {
    const controller = new AbortController();
    const token = getToken();

    (async () => {
      try {
        const res = await fetch(`${API_BASE}/chat/query/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({ message, session_id: sessionId }),
          signal: controller.signal,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.error || err.detail || "Query failed");
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) onToken(data.token);
              if (data.error) onError(new Error(data.error));
              if (data.done) onDone(data);
            } catch {
              // Skip malformed SSE lines
            }
          }
        }
      } catch (err) {
        if (err.name !== "AbortError") onError(err);
      }
    })();

    return controller;
  },
};

// ──────── Admin — Documents ────────

export const documents = {
  list: () => request("/admin/documents/"),
  get: (id) => request(`/admin/documents/${id}/`),
  upload: (file, title) => {
    const formData = new FormData();
    formData.append("file", file);
    if (title) formData.append("title", title);
    return request("/admin/documents/", { method: "POST", body: formData });
  },
  delete: (id) => request(`/admin/documents/${id}/`, { method: "DELETE" }),
};

// ──────── Admin — FAQs ────────

export const faqs = {
  list: () => request("/admin/faqs/"),
  create: (data) => request("/admin/faqs/", { method: "POST", body: JSON.stringify(data) }),
  update: (id, data) => request(`/admin/faqs/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id) => request(`/admin/faqs/${id}/`, { method: "DELETE" }),
};

// ──────── Admin — Navigation ────────

export const navigation = {
  list: () => request("/admin/navigation/"),
  create: (data) => request("/admin/navigation/", { method: "POST", body: JSON.stringify(data) }),
  update: (id, data) => request(`/admin/navigation/${id}/`, { method: "PATCH", body: JSON.stringify(data) }),
  delete: (id) => request(`/admin/navigation/${id}/`, { method: "DELETE" }),
};

// ──────── Admin — Chat Logs ────────

export const chatLogs = {
  list: () => request("/admin/chat-logs/"),
};

// ──────── Admin — AI Config ────────

export const aiConfig = {
  get: () => request("/admin/ai-config/"),
  update: (data) => request("/admin/ai-config/", { method: "PUT", body: JSON.stringify(data) }),
};
