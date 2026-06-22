import apiClient from './client'

export interface AuthMe {
  username: string
  email: string
  groups: string[]
  authenticated: boolean
}

export async function fetchAuthMe(): Promise<AuthMe> {
  const { data } = await apiClient.get<AuthMe>('/auth/me')
  return data
}

export interface SecurityStatus {
  defaultCredentialsInUse: boolean
  username?: string | null
  realm?: string | null
}

export async function fetchSecurityStatus(): Promise<SecurityStatus> {
  const { data } = await apiClient.get<SecurityStatus>('/auth/security-status')
  return data
}
