import React, { useState } from 'react';
import { Card, Form, Input, Button, Alert, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined, FireOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

const Login = ({ onLogin }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (values) => {
    setLoading(true);
    setError(null);

    const result = await onLogin(values.username, values.password);
    
    if (!result.success) {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <Card
        style={{
          width: '100%',
          maxWidth: 400,
          boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
          borderRadius: 10
        }}
        bodyStyle={{ padding: '40px' }}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <FireOutlined style={{ fontSize: '48px', color: '#667eea', marginBottom: '16px' }} />
            <Title level={2} style={{ margin: 0, color: '#333' }}>
              Thermal Inspection System
            </Title>
            <Text type="secondary">AI-powered thermal analysis for transmission lines</Text>
          </div>

          {error && (
            <Alert
              message="Login Failed"
              description={error}
              type="error"
              closable
              onClose={() => setError(null)}
            />
          )}

          <Form
            name="login"
            initialValues={{
              username: 'engineer',
              password: 'engineer123'
            }}
            onFinish={handleSubmit}
            size="large"
          >
            <Form.Item
              name="username"
              rules={[{ required: true, message: 'Please input your username!' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="Username"
                autoComplete="username"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[{ required: true, message: 'Please input your password!' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="Password"
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                style={{
                  width: '100%',
                  height: '45px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  fontSize: '16px'
                }}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>
            </Form.Item>
          </Form>

          <div style={{ textAlign: 'center', marginTop: '20px' }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              Demo Credentials: engineer / engineer123
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  );
};

export default Login; 