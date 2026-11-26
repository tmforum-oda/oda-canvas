import { useState } from 'react';
import { Form, Input, Button, Alert, Typography } from 'antd';
import {
  CloudServerOutlined,
  LockOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { login, storeTokensFromResponse } from '@/lib/auth';
import { colors } from '@/theme';
import apiClient from '@/api/client';

const { Title, Text } = Typography;

export default function LoginPage({ onSuccess }: { onSuccess: () => void }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step: 'login' = normal login, 'set-password' = first-time password change
  const [step, setStep] = useState<'login' | 'set-password'>('login');
  const [savedCredentials, setSavedCredentials] = useState<{ username: string; password: string } | null>(null);

  const onLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    setError('');
    try {
      await login(values.username, values.password);
      onSuccess();
    } catch (e: unknown) {
      const msg = (e as Error).message || '';
      if (msg.toLowerCase().includes('not fully set up')) {
        setSavedCredentials(values);
        setStep('set-password');
      } else {
        setError(msg || 'Invalid credentials');
      }
    } finally {
      setLoading(false);
    }
  };

  const onSetPassword = async (values: { new_password: string; confirm_password: string }) => {
    if (!savedCredentials) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await apiClient.post('/auth/set-initial-password', {
        username: savedCredentials.username,
        current_password: savedCredentials.password,
        new_password: values.new_password,
      });
      storeTokensFromResponse(data);
      onSuccess();
    } catch (e: unknown) {
      const msg = (e as Error).message || 'Failed to update password';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    background: colors.inputBg,
    border: `1px solid ${colors.border}`,
    color: colors.textPrimary,
    borderRadius: 8,
  };

  return (
    <div className="login-shell">
      <div
        className="login-brand-panel"
      >
        <div>
          <img
            src="/TM_Forum_logo_RGB_WO.png"
            alt="TM Forum"
            style={{ height: 34, width: 'auto', display: 'block', marginBottom: 46 }}
          />
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              height: 30,
              padding: '0 10px',
              borderRadius: 8,
              background: 'rgba(255,255,255,0.08)',
              border: '1px solid rgba(255,255,255,0.12)',
              color: 'rgba(255,255,255,0.74)',
              fontSize: 12,
              fontWeight: 700,
              marginBottom: 18,
            }}
          >
            <CloudServerOutlined />
            ODA Canvas
          </div>
          <h1
            style={{
              color: '#FFFFFF',
              margin: 0,
              fontSize: 36,
              lineHeight: 1.08,
              fontWeight: 760,
              maxWidth: 420,
            }}
          >
            Control plane for TM Forum components
          </h1>
          <p
            style={{
              color: 'rgba(255,255,255,0.64)',
              margin: '16px 0 0',
              fontSize: 14,
              lineHeight: 1.7,
              maxWidth: 420,
            }}
          >
            Secure access to component inventory, API exposure, operators, and observability.
          </p>
        </div>

      </div>

      <div className="login-form-panel">
        <div
          style={{
            width: 420,
            maxWidth: '100%',
            background: colors.bgCard,
            borderRadius: 8,
            padding: 36,
            border: `1px solid ${colors.border}`,
            boxShadow: colors.shadow,
          }}
        >
        {/* TM Forum Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
            <img
              src="/TM_Forum_logo_primary_RGB.png"
              alt="TM Forum"
              style={{ height: 62, width: 'auto', display: 'block' }}
            />
          </div>
          <Title level={3} style={{ color: colors.textPrimary, margin: 0 }}>
            Canvas Portal
          </Title>
          <Text style={{ color: colors.textMuted }}>TM Forum ODA Canvas Management</Text>
        </div>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{
              marginBottom: 24,
              background: colors.statusDownBg,
              border: `1px solid ${colors.statusDown}`,
            }}
          />
        )}

        {step === 'login' && (
          <Form onFinish={onLogin} layout="vertical" requiredMark={false}>
            <Form.Item name="username" rules={[{ required: true, message: 'Enter username' }]}>
              <Input
                prefix={<UserOutlined style={{ color: colors.textMuted }} />}
                placeholder="Username"
                size="large"
                style={inputStyle}
              />
            </Form.Item>

            <Form.Item name="password" rules={[{ required: true, message: 'Enter password' }]}>
              <Input.Password
                prefix={<LockOutlined style={{ color: colors.textMuted }} />}
                placeholder="Password"
                size="large"
                style={inputStyle}
              />
            </Form.Item>

            <Button
              type="primary" htmlType="submit" loading={loading}
              size="large" block
              style={{
                background: colors.primaryGradient,
                border: 'none',
                borderRadius: 8,
                height: 48,
                fontSize: 16,
                fontWeight: 700,
                marginTop: 8,
              }}
            >
              Sign In
            </Button>
          </Form>
        )}

        {step === 'set-password' && (
          <>
            <Alert
              type="info"
              showIcon
              message="Set a new password"
              description="Your account requires a password change before you can continue."
              style={{ marginBottom: 24 }}
            />
            <Form onFinish={onSetPassword} layout="vertical" requiredMark={false}>
              <Form.Item
                name="new_password"
                label={<span style={{ color: colors.textSecondary }}>New Password</span>}
                rules={[
                  { required: true, message: 'Enter a new password' },
                  { min: 8, message: 'Minimum 8 characters' },
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined style={{ color: colors.textMuted }} />}
                  placeholder="New password (min. 8 characters)"
                  size="large"
                  style={inputStyle}
                />
              </Form.Item>

              <Form.Item
                name="confirm_password"
                label={<span style={{ color: colors.textSecondary }}>Confirm Password</span>}
                dependencies={['new_password']}
                rules={[
                  { required: true, message: 'Confirm your new password' },
                  ({ getFieldValue }) => ({
                    validator(_, value) {
                      if (!value || getFieldValue('new_password') === value) {
                        return Promise.resolve();
                      }
                      return Promise.reject(new Error('Passwords do not match'));
                    },
                  }),
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined style={{ color: colors.textMuted }} />}
                  placeholder="Confirm new password"
                  size="large"
                  style={inputStyle}
                />
              </Form.Item>

              <Button
                type="primary" htmlType="submit" loading={loading}
                size="large" block
                style={{
                  background: colors.primaryGradient,
                  border: 'none',
                  borderRadius: 8,
                  height: 48,
                  fontSize: 16,
                  fontWeight: 700,
                  marginTop: 8,
                }}
              >
                Set Password & Sign In
              </Button>

              <Button
                type="text" block
                style={{ marginTop: 8, color: colors.textSecondary }}
                onClick={() => { setStep('login'); setError(''); }}
              >
                Back to login
              </Button>
            </Form>
          </>
        )}

        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Text style={{ color: colors.textMuted, fontSize: 12 }}>
            Canvas v5.2.1 · ODA R5
          </Text>
        </div>
        </div>
      </div>
    </div>
  );
}
