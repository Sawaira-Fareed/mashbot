// Use the frontend origin in Docker; Nginx proxies /api to the backend service.
// This avoids browser CORS and localhost-origin differences between environments.
export const API = import.meta.env.VITE_API_URL || "/api";

export async function request(path, options = {}) {
  const { headers: optionHeaders = {}, ...requestOptions } = options;
  const response = await fetch(`${API}${path}`, {
    ...requestOptions,
    headers: { "Content-Type": "application/json", ...optionHeaders },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join(", ") : data.detail;
    throw new Error(detail || "Request failed");
  }
  return data;
}

export const authHeaders = (token) => ({ Authorization: `Bearer ${token}` });
