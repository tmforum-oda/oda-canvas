export {}

declare global {
  interface Window {
    __APP_CONFIG__?: {
      API_BASE_URL?: string
      KEYCLOAK_URL?: string
      KEYCLOAK_REALM?: string
      KEYCLOAK_CLIENT_ID?: string
    }
  }
}
