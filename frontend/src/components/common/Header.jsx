import React from 'react';
import { Layout, Button, Typography, Space, Avatar, Dropdown } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

const Header = ({ collapsed, onCollapse, user, onLogout }) => {
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: onLogout,
    },
  ];

  return (
    <AntHeader
      style={{
        padding: '0 24px',
        background: '#fff',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid #f0f0f0',
        boxShadow: '0 1px 4px rgba(0,21,41,.08)',
      }}
    >
      <Space>
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={onCollapse}
          style={{
            fontSize: '16px',
            width: 64,
            height: 64,
          }}
        />
      </Space>

      <Space>
        {user && (
          <Space>
            <Text style={{ marginRight: 8 }}>
              Welcome, <strong>{user.full_name}</strong>
            </Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {user.role} | {user.department}
            </Text>
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={['click']}
            >
              <Avatar
                style={{
                  backgroundColor: '#667eea',
                  cursor: 'pointer',
                }}
                icon={<UserOutlined />}
              />
            </Dropdown>
          </Space>
        )}
      </Space>
    </AntHeader>
  );
};

export default Header; 