import { useEffect, useRef, useState, useCallback } from 'react'
import { getTokenExpiry, refreshAccessToken, logout } from '@/lib/auth'

// Show warning this many ms before the access token expires
const WARN_BEFORE_MS = 2 * 60 * 1000   // 2 minutes
// Silently refresh when this close to expiry AND user is active
const SILENT_REFRESH_MS = 60 * 1000    // 60 seconds
// How often the background check runs
const CHECK_INTERVAL_MS = 15_000
// Events that count as user activity
const ACTIVITY_EVENTS = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll'] as const

export function useSessionManager() {
  const [showWarning, setShowWarning]   = useState(false)
  const [secondsLeft, setSecondsLeft]   = useState(120)

  const lastActivityRef  = useRef<number>(Date.now())
  const showWarningRef   = useRef(false)        // mirrors state without stale closure
  const countdownRef     = useRef<ReturnType<typeof setInterval> | null>(null)
  const refreshingRef    = useRef(false)

  // Keep ref in sync with state
  useEffect(() => { showWarningRef.current = showWarning }, [showWarning])

  // ── Activity tracking ──────────────────────────────────────────────────────
  const handleActivity = useCallback(() => {
    lastActivityRef.current = Date.now()
  }, [])

  useEffect(() => {
    ACTIVITY_EVENTS.forEach(e => window.addEventListener(e, handleActivity, { passive: true }))
    return () => ACTIVITY_EVENTS.forEach(e => window.removeEventListener(e, handleActivity))
  }, [handleActivity])

  // ── Countdown while warning is visible ────────────────────────────────────
  useEffect(() => {
    if (!showWarning) return
    countdownRef.current = setInterval(() => {
      setSecondsLeft(prev => {
        if (prev <= 1) { logout(); return 0 }
        return prev - 1
      })
    }, 1000)
    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current)
    }
  }, [showWarning])

  // ── Background session check ───────────────────────────────────────────────
  useEffect(() => {
    const check = async () => {
      const exp = getTokenExpiry()
      if (!exp) return

      const now = Date.now()
      const msLeft = exp * 1000 - now

      if (msLeft <= 0) { logout(); return }

      const isActive = (now - lastActivityRef.current) < 60_000

      if (msLeft <= SILENT_REFRESH_MS && isActive && !refreshingRef.current) {
        // User is active — refresh silently
        refreshingRef.current = true
        const ok = await refreshAccessToken()
        refreshingRef.current = false
        if (!ok) logout()
        return
      }

      if (msLeft <= WARN_BEFORE_MS && !isActive && !showWarningRef.current) {
        // Inactive and token about to expire — show warning
        setSecondsLeft(Math.min(Math.floor(msLeft / 1000), 120))
        setShowWarning(true)
      }
    }

    const interval = setInterval(check, CHECK_INTERVAL_MS)
    check()
    return () => clearInterval(interval)
  }, []) // run once — refs handle stale closures

  // ── Public API ─────────────────────────────────────────────────────────────
  const continueSession = useCallback(async () => {
    const ok = await refreshAccessToken()
    if (ok) {
      lastActivityRef.current = Date.now()
      setShowWarning(false)
    } else {
      logout()
    }
  }, [])

  return { showWarning, secondsLeft, continueSession }
}
