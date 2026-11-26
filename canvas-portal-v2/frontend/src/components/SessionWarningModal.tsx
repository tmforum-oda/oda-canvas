import { Modal, Button, Progress } from 'antd'
import { ClockCircleOutlined } from '@ant-design/icons'
import { logout } from '@/lib/auth'
import { colors } from '@/theme'

interface Props {
  open: boolean
  secondsLeft: number
  onContinue: () => void
}

export default function SessionWarningModal({ open, secondsLeft, onContinue }: Props) {
  const totalSeconds = 120
  const percent = Math.round((secondsLeft / totalSeconds) * 100)
  const isUrgent = secondsLeft <= 30

  const mm = String(Math.floor(secondsLeft / 60)).padStart(2, '0')
  const ss = String(secondsLeft % 60).padStart(2, '0')

  return (
    <Modal
      open={open}
      closable={false}
      maskClosable={false}
      footer={null}
      centered
      width={400}
      styles={{
        content: { background: colors.bgCard, borderRadius: 16, padding: 32 },
        mask: { backdropFilter: 'blur(4px)' },
      }}
    >
      <div style={{ textAlign: 'center' }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: 16,
            background: isUrgent ? 'rgba(239,68,68,0.15)' : 'rgba(245,158,11,0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
          }}
        >
          <ClockCircleOutlined
            style={{
              fontSize: 26,
              color: isUrgent ? colors.statusDown : '#F59E0B',
            }}
          />
        </div>

        <h2 style={{ color: colors.textPrimary, margin: '0 0 8px', fontSize: 18, fontWeight: 700 }}>
          Session Expiring Soon
        </h2>
        <p style={{ color: colors.textSecondary, margin: '0 0 24px', fontSize: 14 }}>
          Your session will expire due to inactivity. Click below to continue.
        </p>

        <div
          style={{
            fontSize: 36,
            fontWeight: 700,
            fontVariantNumeric: 'tabular-nums',
            color: isUrgent ? colors.statusDown : colors.textPrimary,
            marginBottom: 16,
            letterSpacing: 2,
          }}
        >
          {mm}:{ss}
        </div>

        <Progress
          percent={percent}
          showInfo={false}
          strokeColor={isUrgent ? colors.statusDown : '#F59E0B'}
          trailColor={colors.border}
          style={{ marginBottom: 24 }}
        />

        <div style={{ display: 'flex', gap: 10 }}>
          <Button
            block
            style={{
              background: 'transparent',
              border: `1px solid ${colors.border}`,
              color: colors.textSecondary,
              borderRadius: 8,
            }}
            onClick={() => logout()}
          >
            Log Out
          </Button>
          <Button
            type="primary"
            block
            style={{
              background: colors.primaryGradient,
              border: 'none',
              borderRadius: 8,
              fontWeight: 600,
            }}
            onClick={onContinue}
          >
            Continue Session
          </Button>
        </div>
      </div>
    </Modal>
  )
}
