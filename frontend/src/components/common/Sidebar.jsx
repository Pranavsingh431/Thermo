import React from 'react';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  CameraOutlined,
  ExperimentOutlined,
  BankOutlined,
  FileTextOutlined,
  FireOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider } = Layout;

const Sidebar = ({ collapsed, currentPage, onPageChange }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      onClick: () => {
        navigate('/dashboard');
        onPageChange('dashboard');
      },
    },
    {
      key: 'thermal-scans',
      icon: <CameraOutlined />,
      label: 'Thermal Scans',
      onClick: () => {
        navigate('/thermal-scans');
        onPageChange('thermal-scans');
      },
    },
    {
      key: 'ai-results',
      icon: <ExperimentOutlined />,
      label: 'AI Analysis',
      onClick: () => {
        navigate('/ai-results');
        onPageChange('ai-results');
      },
    },
    {
      key: 'substations',
      icon: <BankOutlined />,
      label: 'Substations',
      onClick: () => {
        navigate('/substations');
        onPageChange('substations');
      },
    },
    {
      key: 'reports',
      icon: <FileTextOutlined />,
      label: 'Reports',
      onClick: () => {
        navigate('/reports');
        onPageChange('reports');
      },
    },
  ];

  // Get current route for highlighting
  const getCurrentKey = () => {
    const path = location.pathname;
    if (path.includes('dashboard')) return 'dashboard';
    if (path.includes('thermal-scans')) return 'thermal-scans';
    if (path.includes('ai-results')) return 'ai-results';
    if (path.includes('substations')) return 'substations';
    if (path.includes('reports')) return 'reports';
    return 'dashboard';
  };

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={collapsed}
      style={{
        background: '#001529',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        zIndex: 100,
      }}
      width={250}
    >
      <div
        style={{
          height: 64,
          background: 'rgba(255, 255, 255, 0.1)',
          margin: 16,
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 24,
        }}
      >
        <FireOutlined
          style={{
            fontSize: collapsed ? '24px' : '32px',
            color: '#667eea',
            marginRight: collapsed ? 0 : 8,
          }}
        />
        {!collapsed && (
          <span
            style={{
              color: 'white',
              fontSize: '18px',
              fontWeight: 'bold',
            }}
          >
            Thermal AI
          </span>
        )}
      </div>

      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[getCurrentKey()]}
        items={menuItems}
        style={{
          background: 'transparent',
          border: 'none',
        }}
      />
    </Sider>
  );
};

export default Sidebar; 