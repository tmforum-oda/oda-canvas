import Keycloak from 'keycloak-js'

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || 'http://localhost:8180/auth',
  realm: import.meta.env.VITE_KEYCLOAK_REALM || 'canvas',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || 'canvas-portal',
})

export let keycloakInitialized = false

export async function initKeycloak(): Promise<boolean> {
  try {
    const authenticated = await keycloak.init({
      onLoad: 'login-required',
      checkLoginIframe: false,
      pkceMethod: 'S256',
    })
    keycloakInitialized = true

    // Schedule token refresh 60s before expiry
    if (authenticated) {
      scheduleTokenRefresh()
    }

    return authenticated
  } catch (err) {
    console.error('Keycloak init failed:', err)
    throw err
  }
}

function scheduleTokenRefresh() {
  setInterval(async () => {
    try {
      const refreshed = await keycloak.updateToken(70)
      if (refreshed) {
        console.debug('Keycloak token refreshed')
      }
    } catch (err) {
      console.error('Failed to refresh Keycloak token:', err)
      keycloak.logout()
    }
  }, 60_000)
}

export function getToken(): string | undefined {
  return keycloak.token
}

export function logout() {
  keycloak.logout({ redirectUri: window.location.origin })
}

export function getUsername(): string {
  return keycloak.tokenParsed?.preferred_username || keycloak.tokenParsed?.email || 'Unknown'
}

export function getEmail(): string {
  return keycloak.tokenParsed?.email || ''
}

export default keycloak
