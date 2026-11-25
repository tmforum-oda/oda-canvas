import { Result } from 'antd'
import { useAuth } from '@/hooks/useAuth'
import { adminAccessMessage } from '@/lib/forbidden'
import { colors } from '@/theme'

interface AdminAccessRequiredProps {
  /** What the page offers, for example "Deploying components with Helm". */
  feature: string
}

// Shown in place of an admin-only page when its API answers 403.
export default function AdminAccessRequired({ feature }: AdminAccessRequiredProps) {
  const { username, groups } = useAuth()

  return (
    <Result
      status="403"
      title={<span style={{ color: colors.textPrimary }}>Admin access required</span>}
      subTitle={
        <div style={{ color: colors.textSecondary, maxWidth: 560, margin: '0 auto' }}>
          <p>{adminAccessMessage(feature)}</p>
          {username && (
            <p style={{ color: colors.textMuted, fontSize: 12, marginBottom: 0 }}>
              Signed in as {username}
              {groups.length > 0 ? ` (groups and roles: ${groups.join(', ')})` : ' (no groups or roles)'}.
            </p>
          )}
        </div>
      }
    />
  )
}
