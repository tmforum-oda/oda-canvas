import React from 'react'
import {
  ApiOutlined,
  MonitorOutlined,
  ThunderboltOutlined,
  SafetyCertificateOutlined,
  DeploymentUnitOutlined,
  SyncOutlined,
} from '@ant-design/icons'
import { colors } from '@/theme'

const iconMap: Record<string, React.ReactNode> = {
  'Observability': <MonitorOutlined style={{ fontSize: 36 }} />,
  'API Gateway': <ApiOutlined style={{ fontSize: 36 }} />,
  'Rate Limiting': <ThunderboltOutlined style={{ fontSize: 36 }} />,
  'API Policies': <SafetyCertificateOutlined style={{ fontSize: 36 }} />,
  'Deploy Components': <DeploymentUnitOutlined style={{ fontSize: 36 }} />,
  'Lifecycle Management': <SyncOutlined style={{ fontSize: 36 }} />,
}

interface PlaceholderProps {
  title: string
  description?: string
  /** When true, renders without a page wrapper (inline within another page) */
  embedded?: boolean
}

export default function Placeholder({ title, description, embedded = false }: PlaceholderProps) {
  const icon = iconMap[title] || <ApiOutlined style={{ fontSize: 36 }} />

  const content = (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: embedded ? '48px 24px' : '80px 24px',
        textAlign: 'center',
        minHeight: embedded ? 240 : undefined,
      }}
    >
      {/* Icon */}
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: 20,
          background: colors.primarySurface,
          border: `1px solid ${colors.primaryBorder}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colors.primary,
          marginBottom: 20,
        }}
      >
        {icon}
      </div>

      {/* Title */}
      <h2
        style={{
          fontSize: embedded ? 18 : 22,
          fontWeight: 700,
          color: colors.textPrimary,
          margin: '0 0 10px',
        }}
      >
        {title}
      </h2>

      {/* Description */}
      {description && (
        <p
          style={{
            fontSize: 14,
            color: colors.textSecondary,
            maxWidth: 420,
            margin: '0 0 24px',
            lineHeight: 1.6,
          }}
        >
          {description}
        </p>
      )}

      {/* Coming soon badge */}
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          background: colors.primarySurface,
          border: `1px solid ${colors.primaryBorder}`,
          borderRadius: 999,
          padding: '6px 18px',
          fontSize: 13,
          color: colors.tmfText,
          fontWeight: 500,
        }}
      >
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: colors.tmfText,
            display: 'inline-block',
          }}
        />
        Coming Soon
      </div>

      {/* Decorative lines */}
      <div
        style={{
          marginTop: 40,
          display: 'flex',
          gap: 8,
          opacity: 0.3,
        }}
      >
        {[60, 100, 80, 40, 60].map((w, i) => (
          <div
            key={i}
            style={{
              width: w,
              height: 4,
              borderRadius: 2,
              background: colors.primary,
            }}
          />
        ))}
      </div>
    </div>
  )

  if (embedded) {
    return content
  }

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 12 }}>
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 8,
            background: colors.primaryGradient,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18,
            color: '#fff',
          }}
        >
          {iconMap[title] || <ApiOutlined />}
        </div>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>
            {title}
          </h1>
        </div>
      </div>

      {/* Content card */}
      <div
        style={{
          background: colors.bgCard,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          overflow: 'hidden',
        }}
      >
        {content}
      </div>
    </div>
  )
}
