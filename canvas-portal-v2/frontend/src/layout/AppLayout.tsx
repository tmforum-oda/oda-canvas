import React, { useState } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import { Dropdown, Avatar, Spin } from 'antd'
import {
  UserOutlined,
  LogoutOutlined,
  CaretDownOutlined,
} from '@ant-design/icons'
import type { MenuProps } from 'antd'
import Sidebar from './Sidebar'
import { useAuth } from '@/hooks/useAuth'
import { logout } from '@/lib/auth'
import { colors } from '@/theme'

type RouteMeta = {
  eyebrow: string
  title: string
  description: string
}

function getRouteMeta(pathname: string): RouteMeta {
  if (pathname.startsWith('/components/deploy')) {
    return { eyebrow: 'Components', title: 'Deploy', description: 'Install chart-backed components' }
  }
  if (pathname.startsWith('/components/lifecycle')) {
    return { eyebrow: 'Components', title: 'Lifecycle', description: 'Upgrade, uninstall, history' }
  }
  if (pathname.startsWith('/components/')) {
    return { eyebrow: 'Components', title: 'Component Detail', description: 'Runtime, API, pods, events' }
  }
  if (pathname.startsWith('/components')) {
    return { eyebrow: 'Components', title: 'Inventory', description: '' }
  }
  if (pathname.startsWith('/exposedapis')) {
    return { eyebrow: 'APIs', title: 'Exposed APIs', description: '' }
  }
  if (pathname.startsWith('/gateway')) {
    return { eyebrow: 'APIs', title: 'Gateway', description: '' }
  }
  if (pathname.startsWith('/servicemesh')) {
    return { eyebrow: 'APIs', title: 'Service Mesh', description: '' }
  }
  if (pathname.startsWith('/policies') || pathname.startsWith('/ratelimiting')) {
    return { eyebrow: 'APIs', title: 'Policies', description: '' }
  }
  if (pathname.startsWith('/observability')) {
    return { eyebrow: 'Platform', title: 'Observability', description: '' }
  }
  if (pathname.startsWith('/operators/')) {
    return { eyebrow: 'Platform', title: 'Operator Detail', description: 'Deployment, pods, logs' }
  }
  if (pathname.startsWith('/operators')) {
    return { eyebrow: 'Platform', title: 'Operators', description: '' }
  }
  if (pathname.startsWith('/bdd')) {
    return { eyebrow: 'Platform', title: 'BDD', description: 'Work in progress' }
  }
  return { eyebrow: 'Dashboard', title: 'Dashboard', description: '' }
}

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const { username, email, isLoading } = useAuth()
  const location = useLocation()
  const meta = getRouteMeta(location.pathname)

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: (
        <div>
          <div style={{ fontWeight: 600, color: colors.textPrimary }}>{username}</div>
          <div style={{ fontSize: 12, color: colors.textMuted }}>{email}</div>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Sign Out',
      danger: true,
      onClick: () => logout(),
    },
  ]

  return (
    <div
      style={{
        display: 'flex',
        height: '100vh',
        background: `linear-gradient(180deg, ${colors.bgBase} 0%, #EEF4F8 100%)`,
        overflow: 'hidden',
      }}
    >
      {/* Sidebar */}
      <Sidebar collapsed={collapsed} onCollapse={setCollapsed} />

      {/* Main content area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        {/* Topbar */}
        <header
          style={{
            height: 68,
            background: 'rgba(255,255,255,0.94)',
            backdropFilter: 'blur(14px)',
            borderBottom: `1px solid ${colors.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 28px',
            flexShrink: 0,
            zIndex: 10,
            boxShadow: '0 1px 2px rgba(16,24,40,0.04)',
          }}
        >
          <div style={{ minWidth: 0 }}>
            <div
              style={{
                fontSize: 11,
                color: colors.textMuted,
                fontWeight: 700,
                letterSpacing: 0.7,
                lineHeight: 1.1,
                marginBottom: 4,
                textTransform: 'uppercase',
              }}
            >
              {meta.eyebrow}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
              <h1
                style={{
                  fontSize: 17,
                  fontWeight: 750,
                  color: colors.textPrimary,
                  margin: 0,
                  lineHeight: 1.2,
                  whiteSpace: 'nowrap',
                }}
              >
                {meta.title}
              </h1>
              <span
                style={{
                  color: colors.textSecondary,
                  fontSize: 13,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {meta.description}
              </span>
            </div>
          </div>

          {/* Right: user */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            {/* User menu */}
            {isLoading ? (
              <Spin size="small" />
            ) : (
              <Dropdown menu={{ items: userMenuItems }} trigger={['click']} placement="bottomRight">
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    cursor: 'pointer',
                    height: 40,
                    padding: '0 12px 0 6px',
                    borderRadius: 8,
                    border: `1px solid ${colors.border}`,
                    background: colors.bgCard,
                    transition: 'background 0.15s',
                  }}
                  onMouseEnter={(e) => {
                    ;(e.currentTarget as HTMLElement).style.background = colors.hoverSurface
                  }}
                  onMouseLeave={(e) => {
                    ;(e.currentTarget as HTMLElement).style.background = colors.bgCard
                  }}
                >
                  <Avatar
                    size={30}
                    style={{
                      background: colors.primaryGradient,
                      fontSize: 12,
                      fontWeight: 600,
                      flexShrink: 0,
                    }}
                  >
                    {username.charAt(0).toUpperCase()}
                  </Avatar>
                  <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.2 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: colors.textPrimary }}>
                      {username}
                    </span>
                    {email && (
                      <span style={{ fontSize: 11, color: colors.textMuted, maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {email}
                      </span>
                    )}
                  </div>
                  <CaretDownOutlined style={{ fontSize: 10, color: colors.textMuted }} />
                </div>
              </Dropdown>
            )}
          </div>
        </header>

        {/* Page content */}
        <main
          style={{
            flex: 1,
            overflow: 'auto',
            padding: 28,
            background: 'transparent',
          }}
        >
          <div className="portal-main">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
