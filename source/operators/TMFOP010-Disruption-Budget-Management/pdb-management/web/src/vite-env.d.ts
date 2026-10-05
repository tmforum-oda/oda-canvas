/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_MCP_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
  readonly hot?: {
    accept(): void
    dispose(cb: () => void): void
  }
}