import React from 'react'
import { colors } from '@/theme'

type StatusVariant =
  | 'live'
  | 'ready'
  | 'running'
  | 'active'
  | 'deprecated'
  | 'warning'
  | 'down'
  | 'error'
  | 'not-ready'
  | 'degraded'
  | 'pending'
  | 'unknown'
  | string

interface StatusBadgeProps {
  status: StatusVariant
  /** Override label text */
  label?: string
  /** Show a pulsing dot */
  dot?: boolean
  size?: 'sm' | 'md'
}

function resolveVariant(status: string): {
  bg: string
  color: string
  dot: string
  displayLabel: string
} {
  const s = status.toLowerCase()

  if (['live', 'ready', 'running', 'active', 'healthy', 'succeeded', 'bound', 'complete', 'deployed'].includes(s)) {
    return {
      bg: colors.statusLiveBg,
      color: colors.statusLive,
      dot: colors.statusLive,
      displayLabel:
        s === 'ready'
          ? 'Ready'
          : s === 'running'
          ? 'Running'
          : s === 'active'
          ? 'Active'
          : s === 'complete'
          ? 'Complete'
          : s === 'deployed'
          ? 'Deployed'
          : 'Live',
    }
  }

  if (['deprecated', 'warning', 'degraded', 'partial', 'superseded', 'uninstalling'].includes(s)) {
    return {
      bg: colors.statusDeprecatedBg,
      color: colors.statusDeprecated,
      dot: colors.statusDeprecated,
      displayLabel:
        s === 'superseded'
          ? 'Superseded'
          : s === 'uninstalling'
          ? 'Uninstalling'
          : s.charAt(0).toUpperCase() + s.slice(1),
    }
  }

  if (['down', 'error', 'failed', 'not-ready', 'crashloopbackoff', 'oomkilled', 'evicted', 'uninstalled'].includes(s)) {
    return {
      bg: colors.statusDownBg,
      color: colors.statusDown,
      dot: colors.statusDown,
      displayLabel:
        s === 'not-ready'
          ? 'Down'
          : s === 'uninstalled'
          ? 'Uninstalled'
          : s.charAt(0).toUpperCase() + s.slice(1),
    }
  }

  if (['pending', 'initializing', 'containercreating', 'podscheduled', 'in progress', 'progressing', 'pending-install', 'pending-upgrade', 'pending-rollback'].includes(s)) {
    return {
      bg: colors.infoSurface,
      color: colors.infoText,
      dot: colors.infoText,
      displayLabel:
        s === 'in progress'
          ? 'In Progress'
          : s === 'progressing'
          ? 'Progressing'
          : s === 'pending-install'
          ? 'Pending Install'
          : s === 'pending-upgrade'
          ? 'Pending Upgrade'
          : s === 'pending-rollback'
          ? 'Pending Rollback'
          : 'Pending',
    }
  }

  // unknown / default
  return {
    bg: 'rgba(100,116,139,0.15)',
    color: colors.textMuted,
    dot: colors.textMuted,
    displayLabel: status,
  }
}

export default function StatusBadge({ status, label, dot: showDot = true, size = 'md' }: StatusBadgeProps) {
  const variant = resolveVariant(status)
  const text = label ?? variant.displayLabel

  const padding = size === 'sm' ? '2px 8px' : '3px 10px'
  const fontSize = size === 'sm' ? 11 : 12

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        background: variant.bg,
        color: variant.color,
        border: `1px solid ${variant.color}30`,
        borderRadius: 999,
        padding,
        fontSize,
        fontWeight: 600,
        letterSpacing: 0.3,
        whiteSpace: 'nowrap',
        lineHeight: 1.4,
      }}
    >
      {showDot && (
        <span
          style={{
            width: size === 'sm' ? 5 : 6,
            height: size === 'sm' ? 5 : 6,
            borderRadius: '50%',
            background: variant.dot,
            flexShrink: 0,
            display: 'inline-block',
          }}
        />
      )}
      {text.toUpperCase()}
    </span>
  )
}
