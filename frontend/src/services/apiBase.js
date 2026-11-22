const configuredApiUrl = import.meta.env.VITE_API_URL?.trim()

export const API_BASE_URL = (configuredApiUrl || "/api").replace(/\/+$/, "")

export function apiUrl(path) {
  const normalizedPath = path.startsWith("/api/")
    ? path.slice("/api".length)
    : path === "/api"
      ? ""
      : path
  const suffix = normalizedPath.startsWith("/") ? normalizedPath : `/${normalizedPath}`

  return `${API_BASE_URL}${suffix}`
}
