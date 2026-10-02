import React from 'react'
import { RobotOutlined } from '@ant-design/icons'
import { colors } from '@/theme'

export default function TMFAIAgentsPage() {
  const plannedAgents = [
    {
      name: 'canvas-ops-agent',
      summary: 'Diagnoses operator and component issues, suggests remediations, and triages incidents.',
    },
    {
      name: 'release-advisor',
      summary: 'Compares chart versions and produces a delta summary before lifecycle upgrades.',
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
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
            <RobotOutlined />
          </div>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 700, color: colors.textPrimary, margin: 0 }}>TMF AI Agents</h1>
            <p style={{ fontSize: 12, color: colors.textMuted, margin: '2px 0 0' }}>
              Non-TMF AI agents that augment the Canvas
            </p>
          </div>
        </div>
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            background: '#fef3c7',
            border: '1px solid #fcd34d',
            borderRadius: 999,
            padding: '6px 14px',
            fontSize: 12,
            fontWeight: 600,
            color: '#92400e',
          }}
        >
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#f59e0b' }} />
          Work in progress
        </div>
      </div>

      <div
        style={{
          background: colors.bgCard,
          border: `1px solid ${colors.border}`,
          borderRadius: 12,
          padding: 24,
        }}
      >
        <h3 style={{ fontSize: 14, fontWeight: 650, color: colors.textPrimary, margin: '0 0 14px' }}>
          Planned agents
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
          {plannedAgents.map((agent) => (
            <div
              key={agent.name}
              style={{
                border: `1px dashed ${colors.border}`,
                borderRadius: 10,
                padding: 14,
                background: colors.surfaceSubtle,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                <code style={{ fontSize: 12, fontWeight: 700, color: colors.textPrimary }}>{agent.name}</code>
                <span style={{ fontSize: 10, color: colors.textMuted, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Planned
                </span>
              </div>
              <p style={{ fontSize: 12, color: colors.textSecondary, margin: 0, lineHeight: 1.55 }}>{agent.summary}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
