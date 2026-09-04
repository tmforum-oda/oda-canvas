import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  ClusterOutlined,
  AppstoreOutlined,
  ApiOutlined,
  NodeIndexOutlined,
  MonitorOutlined,
  DeploymentUnitOutlined,
  SyncOutlined,
  GlobalOutlined,
  LinkOutlined,
  SafetyCertificateOutlined,
  ControlOutlined,
  ExperimentOutlined,
  RobotOutlined,
  RightOutlined,
  DownOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import { colors } from '@/theme'

interface NavItem {
  key: string
  label: string
  icon: React.ReactNode
  path?: string
  children?: NavItem[]
  section?: string
}

const navItems: NavItem[] = [
  // DASHBOARD
  { key: 'dashboard', label: 'Dashboard', icon: <ClusterOutlined />, path: '/', section: 'DASHBOARD' },

  // COMPONENTS
  { key: 'components-inventory', label: 'Inventory', icon: <AppstoreOutlined />, path: '/components', section: 'COMPONENTS' },
  { key: 'components-deploy', label: 'Deploy', icon: <DeploymentUnitOutlined />, path: '/components/deploy', section: 'COMPONENTS' },
  { key: 'components-lifecycle', label: 'Lifecycle', icon: <SyncOutlined />, path: '/components/lifecycle', section: 'COMPONENTS' },

  // APIS
  { key: 'exposedapis', label: 'Exposed APIs', icon: <GlobalOutlined />, path: '/exposedapis', section: 'APIS' },
  { key: 'dependentapis', label: 'Dependent APIs', icon: <LinkOutlined />, path: '/dependentapis', section: 'APIS' },
  { key: 'gateway', label: 'Gateway', icon: <NodeIndexOutlined />, path: '/gateway', section: 'APIS' },
  { key: 'servicemesh', label: 'Service Mesh', icon: <ApiOutlined />, path: '/servicemesh', section: 'APIS' },
  { key: 'policies', label: 'Policies', icon: <SafetyCertificateOutlined />, path: '/policies', section: 'APIS' },

  // AI
  { key: 'model-gateway', label: 'Model Gateway', icon: <RobotOutlined />, path: '/model-gateway-services', section: 'AI' },
  { key: 'tmf-ai-agents', label: 'TMF AI Agents', icon: <RobotOutlined />, path: '/tmf-ai-agents', section: 'AI' },

  // PLATFORM
  { key: 'operators', label: 'Operators', icon: <ControlOutlined />, path: '/operators', section: 'PLATFORM' },
  { key: 'observability', label: 'Observability', icon: <MonitorOutlined />, path: '/observability', section: 'PLATFORM' },
  { key: 'bdd', label: 'BDD', icon: <ExperimentOutlined />, path: '/bdd', section: 'PLATFORM' },
]

function isActive(path: string | undefined, location: string): boolean {
  if (!path) return false
  if (path === '/') return location === '/'
  return location.startsWith(path)
}

function isGroupActive(item: NavItem, location: string): boolean {
  if (item.path) return isActive(item.path, location)
  if (item.children) return item.children.some((c) => isActive(c.path, location))
  return false
}

interface SidebarProps {
  collapsed: boolean
  onCollapse: (v: boolean) => void
}

export default function Sidebar({ collapsed, onCollapse }: SidebarProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const visibleNavItems = navItems
  const logoSrc = '/TM_Forum_logo_RGB_WO.png'
  const sidebarBorder = 'rgba(255,255,255,0.08)'
  const sidebarText = 'rgba(255,255,255,0.78)'
  const sidebarMuted = 'rgba(255,255,255,0.48)'
  const sidebarHover = 'rgba(255,255,255,0.07)'
  const sidebarActive = 'rgba(0,114,206,0.24)'
  const sidebarActiveBorder = 'rgba(0,168,142,0.78)'

  const defaultOpen = visibleNavItems
    .filter((item) => item.children && isGroupActive(item, location.pathname))
    .map((item) => item.key)

  const [openGroups, setOpenGroups] = useState<string[]>(defaultOpen)

  function toggleGroup(key: string) {
    setOpenGroups((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    )
  }

  function handleNav(path: string) {
    navigate(path)
  }

  const sections = ['DASHBOARD', 'COMPONENTS', 'APIS', 'AI', 'PLATFORM']

  return (
    <div
      style={{
        width: collapsed ? 68 : 264,
        minHeight: '100vh',
        background: colors.bgSidebar,
        borderRight: `1px solid ${sidebarBorder}`,
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s ease',
        overflow: 'hidden',
        flexShrink: 0,
      }}
    >
      {/* Logo / Header */}
      <div
        style={{
          height: 68,
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          borderBottom: `1px solid ${sidebarBorder}`,
          gap: 12,
          flexShrink: 0,
          overflow: 'hidden',
        }}
      >
        {collapsed ? (
          <svg
            width="28"
            height="28"
            viewBox="0 0 28 28"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ flexShrink: 0 }}
          >
            <defs>
              <linearGradient id="tm-sidebar-mark" x1="2" x2="26" y1="2" y2="26">
                <stop stopColor="#E4002B" />
                <stop offset="0.58" stopColor="#0072CE" />
                <stop offset="1" stopColor="#00A88E" />
              </linearGradient>
            </defs>
            <rect x="2" y="2" width="24" height="24" rx="6" fill="url(#tm-sidebar-mark)" />
            <text
              x="14"
              y="19"
              textAnchor="middle"
              fontFamily="sans-serif"
              fontSize="12"
              fontWeight="700"
              fill="#FFFFFF"
            >
              tm
            </text>
          </svg>
        ) : (
          <>
            <img
              src={logoSrc}
              alt="TM Forum"
              style={{ height: 30, width: 'auto', display: 'block', flexShrink: 0 }}
            />
            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  color: '#FFFFFF',
                  fontSize: 13,
                  fontWeight: 750,
                  lineHeight: 1.1,
                  whiteSpace: 'nowrap',
                }}
              >
                Canvas Portal
              </div>
              <div
                style={{
                  color: sidebarMuted,
                  fontSize: 10,
                  letterSpacing: 0.7,
                  textTransform: 'uppercase',
                  whiteSpace: 'nowrap',
                  marginTop: 3,
                }}
              >
                TM Forum ODA
              </div>
            </div>
          </>
        )}
      </div>

      {/* Nav Items */}
      <div style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', padding: '14px 0' }}>
        {sections.map((section) => {
          const items = visibleNavItems.filter((item) => item.section === section)
          return (
            <div key={section}>
              {!collapsed && (
                <div
                  style={{
                    padding: '8px 20px 4px',
                    fontSize: 10,
                    fontWeight: 700,
                    color: sidebarMuted,
                    letterSpacing: 1.5,
                    textTransform: 'uppercase',
                  }}
                >
                  {section}
                </div>
              )}
              {collapsed && section !== 'DASHBOARD' && (
                <div style={{ height: 1, background: sidebarBorder, margin: '10px 14px' }} />
              )}
              {items.map((item) => {
                const active = isGroupActive(item, location.pathname)
                const isOpen = openGroups.includes(item.key)
                const hasChildren = !!item.children

                return (
                  <div key={item.key}>
                    {/* Parent item */}
                    <div
                      onClick={() => {
                        if (hasChildren) {
                          if (collapsed && item.children?.[0]?.path) handleNav(item.children[0].path)
                          else if (!collapsed) toggleGroup(item.key)
                        } else if (item.path) {
                          handleNav(item.path)
                        }
                      }}
                      title={collapsed ? item.label : undefined}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 10,
                        padding: collapsed ? '11px 0' : '10px 14px',
                        cursor: 'pointer',
                        borderRadius: 8,
                        margin: collapsed ? '2px 10px' : '2px 10px',
                        background: active ? sidebarActive : 'transparent',
                        color: active ? '#FFFFFF' : sidebarText,
                        transition: 'all 0.15s ease',
                        position: 'relative',
                        userSelect: 'none',
                        justifyContent: collapsed ? 'center' : 'flex-start',
                      }}
                      onMouseEnter={(e) => {
                        if (!active) {
                          ;(e.currentTarget as HTMLElement).style.background = sidebarHover
                          ;(e.currentTarget as HTMLElement).style.color = '#FFFFFF'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!active) {
                          ;(e.currentTarget as HTMLElement).style.background = 'transparent'
                          ;(e.currentTarget as HTMLElement).style.color = sidebarText
                        }
                      }}
                    >
                      {active && (
                        <div
                          style={{
                            position: 'absolute',
                            left: -10,
                            top: '50%',
                            transform: 'translateY(-50%)',
                            width: 3,
                            height: 22,
                            background: sidebarActiveBorder,
                            borderRadius: 2,
                          }}
                        />
                      )}
                      <span style={{ fontSize: 16, flexShrink: 0 }}>{item.icon}</span>
                      {!collapsed && (
                        <>
                          <span style={{ flex: 1, fontSize: 13.5, fontWeight: active ? 600 : 400 }}>
                            {item.label}
                          </span>
                          {hasChildren && (
                            <span style={{ fontSize: 10, color: sidebarMuted }}>
                              {isOpen ? <DownOutlined /> : <RightOutlined />}
                            </span>
                          )}
                        </>
                      )}
                    </div>

                    {/* Children */}
                    {hasChildren && !collapsed && isOpen && (
                      <div style={{ padding: '2px 0 4px 8px' }}>
                        {item.children!.map((child) => {
                          const childActive = isActive(child.path, location.pathname)
                          return (
                            <div
                              key={child.key}
                              onClick={() => child.path && handleNav(child.path)}
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 10,
                                padding: '8px 14px 8px 30px',
                                cursor: 'pointer',
                                borderRadius: 8,
                                margin: '1px 10px',
                                background: childActive
                                  ? sidebarActive
                                  : 'transparent',
                                color: childActive ? '#FFFFFF' : sidebarText,
                                position: 'relative',
                                transition: 'all 0.15s ease',
                                userSelect: 'none',
                              }}
                              onMouseEnter={(e) => {
                                if (!childActive) {
                                  ;(e.currentTarget as HTMLElement).style.background = sidebarHover
                                  ;(e.currentTarget as HTMLElement).style.color = '#FFFFFF'
                                }
                              }}
                              onMouseLeave={(e) => {
                                if (!childActive) {
                                  ;(e.currentTarget as HTMLElement).style.background = 'transparent'
                                  ;(e.currentTarget as HTMLElement).style.color = sidebarText
                                }
                              }}
                            >
                              {childActive && (
                                <div
                                  style={{
                                    position: 'absolute',
                                    left: 0,
                                    top: '50%',
                                    transform: 'translateY(-50%)',
                                    width: 3,
                                    height: 16,
                                    background: sidebarActiveBorder,
                                    borderRadius: 2,
                                  }}
                                />
                              )}
                              <span style={{ fontSize: 13, flexShrink: 0, color: 'inherit' }}>
                                {child.icon}
                              </span>
                              <span style={{ fontSize: 13, fontWeight: childActive ? 600 : 400 }}>
                                {child.label}
                              </span>
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )
        })}
      </div>

      {/* Collapse toggle */}
      <div
        style={{
          borderTop: `1px solid ${sidebarBorder}`,
          padding: '12px 16px',
          display: 'flex',
          justifyContent: collapsed ? 'center' : 'flex-end',
        }}
      >
        <button
          onClick={() => onCollapse(!collapsed)}
          style={{
            background: 'rgba(255,255,255,0.06)',
            border: `1px solid ${sidebarBorder}`,
            borderRadius: 8,
            color: sidebarText,
            cursor: 'pointer',
            padding: '6px 8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.15s ease',
          }}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <MenuUnfoldOutlined style={{ fontSize: 14 }} /> : <MenuFoldOutlined style={{ fontSize: 14 }} />}
        </button>
      </div>
    </div>
  )
}
