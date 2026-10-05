import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Chip,
  Alert,
  Snackbar,
  Tooltip,
  alpha,
  Collapse,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Chat as ChatIcon,
  Build as BuildIcon,
  Policy as PolicyIcon,
  Analytics as AnalyticsIcon,
  Settings as SettingsIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  Circle as CircleIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';

import { useAppStore, useNotificationStore } from '@/store';
import mcpClient from '@/api/mcp';
import ChatInterface from '@/components/ChatInterface';
import ToolExplorer from '@/components/ToolExplorer';
import PolicyManager from '@/components/PolicyManager';
import ClusterAnalysis from '@/components/ClusterAnalysis';

// Dashboard component
const Dashboard: React.FC = () => {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => mcpClient.checkHealth(),
    refetchInterval: 30000,
  });

  const { data: serverInfo } = useQuery({
    queryKey: ['serverInfo'],
    queryFn: () => mcpClient.getServerInfo(),
    enabled: health?.status === 'healthy',
  });

  const stats = [
    {
      label: 'Status',
      value: health?.status || 'Unknown',
      color: health?.status === 'healthy' ? 'success' : 'error',
    },
    { label: 'Tools', value: serverInfo?.tools?.length || 0 },
    { label: 'Resources', value: serverInfo?.resources?.length || 0 },
    {
      label: 'Uptime',
      value: health?.uptime
        ? `${Math.floor(health.uptime / 3600)}h ${Math.floor((health.uptime % 3600) / 60)}m`
        : '-'
    },
  ];

  const checks = [
    { name: 'MCP Server', status: health?.checks?.mcp },
    { name: 'Kubernetes', status: health?.checks?.kubernetes },
    { name: 'Database', status: health?.checks?.database },
  ];

  return (
    <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto' }}>
      <Box sx={{ mb: 6 }}>
        <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
          Overview
        </Typography>
        <Typography variant="h3" sx={{ mb: 1 }}>
          PDB Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor and manage Pod Disruption Budgets across your Kubernetes cluster.
        </Typography>
      </Box>

      {/* Stats Grid */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 2,
          mb: 5,
        }}
      >
        {stats.map((stat) => (
          <Box
            key={stat.label}
            sx={{
              p: 3,
              borderRadius: 3,
              bgcolor: 'background.paper',
              border: 1,
              borderColor: 'divider',
            }}
          >
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              {stat.label}
            </Typography>
            {stat.color ? (
              <Chip
                label={String(stat.value)}
                color={stat.color as any}
                size="small"
              />
            ) : (
              <Typography variant="h4">
                {stat.value}
              </Typography>
            )}
          </Box>
        ))}
      </Box>

      {/* Health Checks */}
      <Box sx={{ mb: 5 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          System Health
        </Typography>
        <Box
          sx={{
            display: 'flex',
            gap: 2,
            flexWrap: 'wrap',
          }}
        >
          {checks.map((check) => (
            <Box
              key={check.name}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
                px: 2.5,
                py: 1.5,
                borderRadius: 2,
                bgcolor: 'background.paper',
                border: 1,
                borderColor: 'divider',
              }}
            >
              <CircleIcon
                sx={{
                  fontSize: 10,
                  color: check.status ? 'success.main' : 'error.main'
                }}
              />
              <Typography variant="body2" fontWeight={500}>
                {check.name}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Quick Actions */}
      <Box>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Quick Actions
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 2 }}>
          {[
            {
              title: 'Explore Tools',
              desc: 'Discover and execute MCP tools',
              path: '/tools',
              icon: <BuildIcon />,
            },
            {
              title: 'AI Assistant',
              desc: 'Chat with AI to manage PDBs',
              path: '/chat',
              icon: <ChatIcon />,
            },
            {
              title: 'Manage Policies',
              desc: 'Create and configure availability policies',
              path: '/policies',
              icon: <PolicyIcon />,
            },
            {
              title: 'Cluster Analysis',
              desc: 'View PDB coverage and insights',
              path: '/analysis',
              icon: <AnalyticsIcon />,
            },
          ].map((action) => {
            const navigate = useNavigate();
            return (
              <Box
                key={action.path}
                onClick={() => navigate(action.path)}
                sx={{
                  p: 3,
                  borderRadius: 3,
                  bgcolor: 'background.paper',
                  border: 1,
                  borderColor: 'divider',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: (theme) => alpha(theme.palette.primary.main, 0.02),
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1 }}>
                  <Box sx={{ color: 'primary.main' }}>{action.icon}</Box>
                  <Typography variant="h6">{action.title}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {action.desc}
                </Typography>
              </Box>
            );
          })}
        </Box>
      </Box>
    </Box>
  );
};

// Settings component
const Settings: React.FC = () => {
  const { theme, setTheme, aiConfig, setAIConfig } = useAppStore();
  const [showApiKey, setShowApiKey] = useState(false);
  const [localApiKey, setLocalApiKey] = useState(aiConfig.apiKey || '');
  const [saved, setSaved] = useState(false);

  const aiProviders = [
    { value: 'claude', label: 'Anthropic Claude', models: [
      'claude-sonnet-4-5-20250929',   // Claude Sonnet 4.5 (latest, best for coding)
      'claude-opus-4-5-20251101',     // Claude Opus 4.5
      'claude-haiku-4-5-20251015',    // Claude Haiku 4.5 (fast & cheap)
      'claude-sonnet-4-20250514',     // Claude Sonnet 4
      'claude-opus-4-20250514',       // Claude Opus 4
      'claude-3-7-sonnet-20250219',   // Claude 3.7 Sonnet (hybrid reasoning)
      'claude-3-5-haiku-20241022',    // Claude 3.5 Haiku
    ]},
    { value: 'openai', label: 'OpenAI', models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'o1', 'o1-mini'] },
    { value: 'azure-openai', label: 'Azure OpenAI', models: ['gpt-4o', 'gpt-4', 'gpt-35-turbo'] },
    { value: 'gemini', label: 'Google Gemini', models: ['gemini-2.0-flash', 'gemini-1.5-pro', 'gemini-1.5-flash'] },
  ];

  const currentProvider = aiProviders.find(p => p.value === aiConfig.provider) || aiProviders[0];

  const handleSaveApiKey = () => {
    setAIConfig({ ...aiConfig, apiKey: localApiKey });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <Box sx={{ p: 4, maxWidth: 800, mx: 'auto' }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="overline" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
          Preferences
        </Typography>
        <Typography variant="h3" sx={{ mb: 1 }}>
          Settings
        </Typography>
      </Box>

      {/* Appearance */}
      <Box
        sx={{
          p: 3,
          borderRadius: 3,
          bgcolor: 'background.paper',
          border: 1,
          borderColor: 'divider',
          mb: 3,
        }}
      >
        <Typography variant="h6" sx={{ mb: 3 }}>Appearance</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="body1" fontWeight={500}>Theme</Typography>
            <Typography variant="body2" color="text.secondary">
              Choose between light and dark mode
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton
              onClick={() => setTheme('light')}
              sx={{
                bgcolor: theme === 'light' ? 'primary.main' : 'transparent',
                color: theme === 'light' ? 'primary.contrastText' : 'text.secondary',
                '&:hover': {
                  bgcolor: theme === 'light' ? 'primary.dark' : 'action.hover',
                },
              }}
            >
              <LightModeIcon />
            </IconButton>
            <IconButton
              onClick={() => setTheme('dark')}
              sx={{
                bgcolor: theme === 'dark' ? 'primary.main' : 'transparent',
                color: theme === 'dark' ? 'primary.contrastText' : 'text.secondary',
                '&:hover': {
                  bgcolor: theme === 'dark' ? 'primary.dark' : 'action.hover',
                },
              }}
            >
              <DarkModeIcon />
            </IconButton>
          </Box>
        </Box>
      </Box>

      {/* AI Configuration */}
      <Box
        sx={{
          p: 3,
          borderRadius: 3,
          bgcolor: 'background.paper',
          border: 1,
          borderColor: 'divider',
          mb: 3,
        }}
      >
        <Typography variant="h6" sx={{ mb: 3 }}>AI Provider</Typography>

        {/* Provider Selection */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Select AI Provider
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {aiProviders.map((provider) => (
              <Chip
                key={provider.value}
                label={provider.label}
                onClick={() => setAIConfig({ ...aiConfig, provider: provider.value as any, model: provider.models[0] })}
                color={aiConfig.provider === provider.value ? 'primary' : 'default'}
                variant={aiConfig.provider === provider.value ? 'filled' : 'outlined'}
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Box>
        </Box>

        {/* Model Selection */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Model
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {currentProvider.models.map((model) => (
              <Chip
                key={model}
                label={model}
                onClick={() => setAIConfig({ ...aiConfig, model })}
                color={aiConfig.model === model ? 'primary' : 'default'}
                variant={aiConfig.model === model ? 'filled' : 'outlined'}
                size="small"
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Box>
        </Box>

        {/* API Key */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            API Key {aiConfig.apiKey ? '(configured)' : '(not set)'}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Box
              component="input"
              type={showApiKey ? 'text' : 'password'}
              value={localApiKey}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setLocalApiKey(e.target.value)}
              placeholder={`Enter your ${currentProvider.label} API key`}
              sx={{
                flex: 1,
                px: 2,
                py: 1.5,
                borderRadius: 2,
                border: 1,
                borderColor: 'divider',
                bgcolor: 'background.default',
                color: 'text.primary',
                fontSize: '0.875rem',
                outline: 'none',
                '&:focus': {
                  borderColor: 'primary.main',
                },
              }}
            />
            <IconButton onClick={() => setShowApiKey(!showApiKey)} size="small">
              {showApiKey ? <DarkModeIcon fontSize="small" /> : <LightModeIcon fontSize="small" />}
            </IconButton>
            <Chip
              label={saved ? 'Saved!' : 'Save'}
              onClick={handleSaveApiKey}
              color={saved ? 'success' : 'primary'}
              sx={{ cursor: 'pointer', minWidth: 80 }}
            />
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Your API key is stored locally in your browser and never sent to our servers.
          </Typography>
        </Box>

        {/* Advanced Settings */}
        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Advanced Settings
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Box sx={{ minWidth: 150 }}>
              <Typography variant="caption" color="text.secondary">Max Tokens</Typography>
              <Box
                component="input"
                type="number"
                value={aiConfig.maxTokens || 4000}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAIConfig({ ...aiConfig, maxTokens: parseInt(e.target.value) || 4000 })}
                sx={{
                  width: '100%',
                  px: 2,
                  py: 1,
                  borderRadius: 1,
                  border: 1,
                  borderColor: 'divider',
                  bgcolor: 'background.default',
                  color: 'text.primary',
                  fontSize: '0.875rem',
                }}
              />
            </Box>
            <Box sx={{ minWidth: 150 }}>
              <Typography variant="caption" color="text.secondary">Temperature</Typography>
              <Box
                component="input"
                type="number"
                step="0.1"
                min="0"
                max="2"
                value={aiConfig.temperature || 0.7}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAIConfig({ ...aiConfig, temperature: parseFloat(e.target.value) || 0.7 })}
                sx={{
                  width: '100%',
                  px: 2,
                  py: 1,
                  borderRadius: 1,
                  border: 1,
                  borderColor: 'divider',
                  bgcolor: 'background.default',
                  color: 'text.primary',
                  fontSize: '0.875rem',
                }}
              />
            </Box>
          </Box>
        </Box>
      </Box>

      {/* MCP Connection */}
      <Box
        sx={{
          p: 3,
          borderRadius: 3,
          bgcolor: 'background.paper',
          border: 1,
          borderColor: 'divider',
        }}
      >
        <Typography variant="h6" sx={{ mb: 2 }}>MCP Connection</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          The MCP server connects to your Kubernetes cluster to manage Pod Disruption Budgets.
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <CircleIcon sx={{ fontSize: 10, color: 'success.main' }} />
          <Typography variant="body2">
            Connected to MCP at /api/mcp
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

// Navigation items
const navigationItems = [
  { label: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  { label: 'AI Chat', icon: <ChatIcon />, path: '/chat' },
  { label: 'Tools', icon: <BuildIcon />, path: '/tools' },
  { label: 'Policies', icon: <PolicyIcon />, path: '/policies' },
  { label: 'Analysis', icon: <AnalyticsIcon />, path: '/analysis' },
  { label: 'Settings', icon: <SettingsIcon />, path: '/settings' },
];

const SIDEBAR_WIDTH = 260;
const SIDEBAR_COLLAPSED_WIDTH = 72;

const App: React.FC = () => {
  const {
    theme,
    sidebarOpen,
    mcpConnected,
    setTheme,
    toggleSidebar,
    setMCPConnected,
    setWSConnected,
  } = useAppStore();

  const { notifications, removeNotification } = useNotificationStore();
  const navigate = useNavigate();
  const location = useLocation();

  // Check MCP connection status
  const { data: health, error } = useQuery({
    queryKey: ['health'],
    queryFn: () => mcpClient.checkHealth(),
    refetchInterval: 30000,
  });

  useEffect(() => {
    if (health) {
      setMCPConnected(health.status === 'healthy');
    } else if (error) {
      setMCPConnected(false);
    }
  }, [health, error, setMCPConnected]);

  useEffect(() => {
    setWSConnected(false);
  }, [setWSConnected]);

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const sidebarWidth = sidebarOpen ? SIDEBAR_WIDTH : SIDEBAR_COLLAPSED_WIDTH;

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      {/* Sidebar */}
      <Box
        component="nav"
        sx={{
          width: sidebarWidth,
          flexShrink: 0,
          transition: 'width 0.2s ease',
          borderRight: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
          display: 'flex',
          flexDirection: 'column',
          position: 'fixed',
          height: '100vh',
          zIndex: 1200,
        }}
      >
        {/* Logo Area */}
        <Box
          sx={{
            p: 2.5,
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            borderBottom: 1,
            borderColor: 'divider',
            minHeight: 72,
          }}
        >
          <Box
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              bgcolor: 'primary.main',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'primary.contrastText',
              fontWeight: 700,
              fontSize: '0.875rem',
              flexShrink: 0,
            }}
          >
            PDB
          </Box>
          <Collapse in={sidebarOpen} orientation="horizontal" unmountOnExit>
            <Typography variant="h6" noWrap sx={{ fontWeight: 600 }}>
              MCP Manager
            </Typography>
          </Collapse>
        </Box>

        {/* Navigation */}
        <Box sx={{ flex: 1, py: 2, px: 1.5, overflow: 'auto' }}>
          <List disablePadding>
            {navigationItems.map((item) => {
              const isSelected = location.pathname === item.path;
              return (
                <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
                  <Tooltip
                    title={sidebarOpen ? '' : item.label}
                    placement="right"
                    arrow
                  >
                    <ListItemButton
                      selected={isSelected}
                      onClick={() => handleNavigation(item.path)}
                      sx={{
                        minHeight: 44,
                        px: 1.5,
                        justifyContent: sidebarOpen ? 'initial' : 'center',
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          minWidth: 0,
                          mr: sidebarOpen ? 2 : 0,
                          justifyContent: 'center',
                          color: isSelected ? 'primary.main' : 'text.secondary',
                        }}
                      >
                        {item.icon}
                      </ListItemIcon>
                      {sidebarOpen && (
                        <ListItemText
                          primary={item.label}
                          primaryTypographyProps={{
                            fontSize: '0.875rem',
                            fontWeight: isSelected ? 600 : 500,
                          }}
                        />
                      )}
                    </ListItemButton>
                  </Tooltip>
                </ListItem>
              );
            })}
          </List>
        </Box>

        {/* Bottom Actions */}
        <Box
          sx={{
            p: 2,
            borderTop: 1,
            borderColor: 'divider',
          }}
        >
          {/* Connection Status */}
          <Tooltip title={`MCP: ${mcpConnected ? 'Connected' : 'Disconnected'}`} placement="right">
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1.5,
                mb: 2,
                px: 1,
              }}
            >
              <CircleIcon
                sx={{
                  fontSize: 8,
                  color: mcpConnected ? 'success.main' : 'error.main',
                }}
              />
              {sidebarOpen && (
                <Typography variant="caption" color="text.secondary">
                  {mcpConnected ? 'Connected' : 'Disconnected'}
                </Typography>
              )}
            </Box>
          </Tooltip>

          {/* Theme Toggle & Collapse */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`} placement="right">
              <IconButton
                size="small"
                onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                sx={{ color: 'text.secondary' }}
              >
                {theme === 'light' ? <DarkModeIcon fontSize="small" /> : <LightModeIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
            <Box sx={{ flex: 1 }} />
            <Tooltip title={sidebarOpen ? 'Collapse' : 'Expand'} placement="right">
              <IconButton
                size="small"
                onClick={toggleSidebar}
                sx={{ color: 'text.secondary' }}
              >
                {sidebarOpen ? <ChevronLeftIcon fontSize="small" /> : <ChevronRightIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Box>

      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          ml: `${sidebarWidth}px`,
          transition: 'margin-left 0.2s ease',
          minHeight: '100vh',
        }}
      >
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/chat" element={<ChatInterface />} />
          <Route path="/tools" element={<ToolExplorer />} />
          <Route path="/policies" element={<PolicyManager />} />
          <Route path="/analysis" element={<ClusterAnalysis />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Box>

      {/* Notifications */}
      {notifications.map((notification, index) => (
        <Snackbar
          key={notification.id}
          open={true}
          autoHideDuration={notification.duration || 5000}
          onClose={() => removeNotification(notification.id)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          sx={{ bottom: { xs: 16 + index * 60, sm: 24 + index * 60 } }}
        >
          <Alert
            onClose={() => removeNotification(notification.id)}
            severity={notification.type}
            variant="filled"
            sx={{
              minWidth: 300,
              boxShadow: 3,
            }}
          >
            <Typography variant="body2" fontWeight={600}>
              {notification.title}
            </Typography>
            {notification.message && (
              <Typography variant="caption">{notification.message}</Typography>
            )}
          </Alert>
        </Snackbar>
      ))}
    </Box>
  );
};

export default App;
