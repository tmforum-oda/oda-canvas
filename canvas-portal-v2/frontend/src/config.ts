type RuntimeConfig = {
  API_BASE_URL?: string
  KEYCLOAK_URL?: string
  KEYCLOAK_REALM?: string
  KEYCLOAK_CLIENT_ID?: string
}

function getRuntimeConfig(): RuntimeConfig {
  if (typeof window === 'undefined') {
    return {}
  }

  return window.__APP_CONFIG__ ?? {}
}

function trimTrailingSlash(value?: string): string {
  return value ? value.replace(/\/+$/, '') : ''
}

function withLeadingSlash(path: string): string {
  return path.startsWith('/') ? path : `/${path}`
}

export function getApiBaseUrl(): string {
  const runtimeValue = trimTrailingSlash(getRuntimeConfig().API_BASE_URL)
  const viteValue = trimTrailingSlash(import.meta.env.VITE_API_URL)
  return runtimeValue || viteValue
}

export function buildApiUrl(path: string): string {
  const baseUrl = getApiBaseUrl()
  const normalizedPath = withLeadingSlash(path)
  return baseUrl ? `${baseUrl}${normalizedPath}` : normalizedPath
}

export function getKeycloakUrl(): string {
  const runtimeValue = trimTrailingSlash(getRuntimeConfig().KEYCLOAK_URL)
  const viteValue = trimTrailingSlash(import.meta.env.VITE_KEYCLOAK_URL)
  return runtimeValue || viteValue || '/auth'
}

export function getKeycloakRealm(): string {
  return getRuntimeConfig().KEYCLOAK_REALM || import.meta.env.VITE_KEYCLOAK_REALM || 'canvas'
}

export function getKeycloakClientId(): string {
  return getRuntimeConfig().KEYCLOAK_CLIENT_ID || import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'canvas-portal'
}
