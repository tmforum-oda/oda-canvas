import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Modal, Button } from 'antd'
import { WarningOutlined } from '@ant-design/icons'
import { fetchSecurityStatus } from '@/api/auth'
import { colors } from '@/theme'

// Show the warning at most once per login session. The key is cleared on
// logout (see lib/auth.ts) so it reappears on the next sign-in.
const WARNED_KEY = 'canvas-portal.default-cred-warned'

export default function DefaultCredentialWarning() {
  const { data } = useQuery({
    queryKey: ['auth', 'security-status'],
    queryFn: fetchSecurityStatus,
    staleTime: 5 * 60_000,
    retry: 0,
  })

  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!data?.defaultCredentialsInUse) return
    if (sessionStorage.getItem(WARNED_KEY)) return
    sessionStorage.setItem(WARNED_KEY, '1')
    setOpen(true)
  }, [data])

  return (
    <Modal
      open={open}
      onCancel={() => setOpen(false)}
      footer={null}
      centered
      width={440}
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
            background: 'rgba(239,68,68,0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
          }}
        >
          <WarningOutlined style={{ fontSize: 26, color: colors.statusDown }} />
        </div>

        <h2 style={{ color: colors.textPrimary, margin: '0 0 8px', fontSize: 18, fontWeight: 700 }}>
          Default ODA Canvas credentials in use
        </h2>
        <p style={{ color: colors.textSecondary, margin: '0 0 12px', fontSize: 14, lineHeight: 1.6 }}>
          You are signed in as
          {' '}
          <strong style={{ color: colors.textPrimary }}>{data?.username ?? 'admin'}</strong>
          {data?.realm ? <> in the <strong style={{ color: colors.textPrimary }}>{data.realm}</strong> realm</> : null}
          {' '}
          using the default ODA Canvas password, which is publicly documented in
          the oda-canvas repository. This can be used to access this portal and
          your cluster.
        </p>
        <p style={{ color: colors.textSecondary, margin: '0 0 24px', fontSize: 14, lineHeight: 1.6 }}>
          Please change this password in Keycloak as soon as possible.
        </p>

        <Button
          type="primary"
          block
          style={{
            background: colors.primaryGradient,
            border: 'none',
            borderRadius: 8,
            fontWeight: 600,
            height: 44,
          }}
          onClick={() => setOpen(false)}
        >
          I understand
        </Button>
      </div>
    </Modal>
  )
}
