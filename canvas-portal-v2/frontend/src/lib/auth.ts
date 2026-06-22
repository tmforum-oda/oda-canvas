// Token handling for the SPA. The access token is kept in memory only (never
// localStorage), and the refresh token lives in an httpOnly cookie set by the
// backend — so neither is reachable by page JavaScript / XSS. Login, refresh,
// and logout all go through the backend (/auth/*), not Keycloak directly.

import { buildApiUrl } from '@/config'

interface JwtPayload {
  exp?: number
}

// Access token is held only in memory, for the life of the page.
let accessToken: string | null = null

function decodeJwtPayload(token: string): JwtPayload | null {
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
    return JSON.parse(window.atob(padded)) as JwtPayload
  } catch {
    return null
  }
}

function isTokenExpired(token: string): boolean {
  const exp = decodeJwtPayload(token)?.exp
  if (!exp) return false
  return Date.now() >= exp * 1000
}

export function storeTokensFromResponse(tokens: { access_token?: string }): void {
  accessToken = typeof tokens.access_token === 'string' ? tokens.access_token : null
}

export function getToken(): string | null {
  if (!accessToken) return null
  if (isTokenExpired(accessToken)) {
    accessToken = null
    return null
  }
  return accessToken
}

export function getTokenExpiry(): number | null {
  if (!accessToken) return null
  return decodeJwtPayload(accessToken)?.exp ?? null
}

export function isAuthenticated(): boolean {
  return !!getToken()
}

// Exchange the httpOnly refresh cookie for a fresh access token. Used on app
// startup (to restore a session after a reload) and on 401 / near-expiry.
export async function refreshAccessToken(): Promise<boolean> {
  try {
    const res = await fetch(buildApiUrl('/auth/refresh'), {
      method: 'POST',
      credentials: 'include',
    })
    if (!res.ok) {
      accessToken = null
      return false
    }
    const data = await res.json().catch(() => ({}))
    if (typeof data.access_token === 'string') {
      accessToken = data.access_token
      return true
    }
    accessToken = null
    return false
  } catch {
    accessToken = null
    return false
  }
}

export async function login(username: string, password: string): Promise<void> {
  const res = await fetch(buildApiUrl('/auth/login'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    // 409 surfaces "Account is not fully set up" so the UI shows the
    // set-a-new-password step; anything else is a normal auth failure.
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Login failed')
  }
  if (typeof data.access_token !== 'string') {
    throw new Error('No access token returned')
  }
  accessToken = data.access_token
}

export async function logout(): Promise<void> {
  try {
    await fetch(buildApiUrl('/auth/logout'), { method: 'POST', credentials: 'include' })
  } catch {
    // best-effort — clear locally regardless
  }
  accessToken = null
  // Reset the once-per-session default-credential warning so it shows again on
  // the next sign-in (key kept in sync with DefaultCredentialWarning.tsx).
  sessionStorage.removeItem('canvas-portal.default-cred-warned')
  window.location.assign('/')
}
