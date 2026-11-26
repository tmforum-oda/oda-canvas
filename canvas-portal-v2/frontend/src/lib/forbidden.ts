// Helpers for 403 responses from the admin-only APIs (/api/helm/*, /api/conformance/*).
// The backend answers 403 when the user holds none of the names in
// backend.auth.adminGroups. client.ts handles 401 (refresh and retry); a 403
// is final, so pages use these helpers to tell the user what access they need.

// Default of backend.auth.adminGroups. The frontend cannot read the configured
// list, so the message names the default and points at the setting.
export const DEFAULT_ADMIN_GROUP = 'canvas-admin'

/** True if the error is an HTTP 403 response (axios error shape). */
export function isForbiddenError(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false
  const response = (error as { response?: { status?: unknown } }).response
  return response?.status === 403
}

/** Explains why a user without an admin group cannot use an admin page. */
export function adminAccessMessage(feature: string): string {
  return (
    `${feature} is limited to Canvas admins. Ask a Canvas administrator to add your account ` +
    `to the "${DEFAULT_ADMIN_GROUP}" group or give it the "${DEFAULT_ADMIN_GROUP}" realm role ` +
    `(or one of the names set in backend.auth.adminGroups), then sign out and sign in again.`
  )
}
