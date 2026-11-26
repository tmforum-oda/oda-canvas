import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, Spin } from 'antd';
import { queryClient } from '@/lib/queryClient';
import { ThemeModeProvider, useThemeMode } from '@/theme';
import { refreshAccessToken } from '@/lib/auth';
import LoginPage from '@/pages/Login';
import App from './App';
import { useSessionManager } from '@/hooks/useSessionManager';
import SessionWarningModal from '@/components/SessionWarningModal';
import DefaultCredentialWarning from '@/components/DefaultCredentialWarning';
import './app.css';

function Root() {
  const [authState, setAuthState] = useState<'loading' | 'authed' | 'login'>('loading');

  useEffect(() => {
    let cancelled = false;
    // Restore the session from the httpOnly refresh cookie — the access token
    // is memory-only, so it's gone after a reload.
    refreshAccessToken().then((ok) => {
      if (!cancelled) setAuthState(ok ? 'authed' : 'login');
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (authState === 'loading') {
    return (
      <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (authState === 'login') {
    return <LoginPage onSuccess={() => setAuthState('authed')} />;
  }

  return <AuthenticatedRoot />;
}

function AuthenticatedRoot() {
  const { showWarning, secondsLeft, continueSession } = useSessionManager();
  return (
    <>
      <App />
      <DefaultCredentialWarning />
      <SessionWarningModal
        open={showWarning}
        secondsLeft={secondsLeft}
        onContinue={continueSession}
      />
    </>
  );
}

function ThemedRoot() {
  const { antdTheme } = useThemeMode();

  return (
    <ConfigProvider theme={antdTheme}>
      <Root />
    </ConfigProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeModeProvider>
        <ThemedRoot />
      </ThemeModeProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
