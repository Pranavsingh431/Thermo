import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout, Spin, message, ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// Components
import Header from './components/common/Header';
import Sidebar from './components/common/Sidebar';
import Dashboard from './pages/Dashboard';
import ThermalScans from './pages/ThermalScans';
import AIResults from './pages/AIResults';
import Substations from './pages/Substations';
import Reports from './pages/Reports';
import Login from './pages/Login';

// Hooks and Services
import { useAuth } from './hooks/useAuth';

// Styles
import './App.css';

const { Content } = Layout;

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Ant Design theme configuration
const theme = {
  token: {
    colorPrimary: '#667eea',
    borderRadius: 6,
  },
  components: {
    Layout: {
      siderBg: '#001529',
      triggerBg: '#002140',
    },
  },
};

function AppContent() {
  const { user, loading, login, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [currentPage, setCurrentPage] = useState('dashboard');

  useEffect(() => {
    // Show success message when login is successful
    if (user) {
      message.success(`Welcome back, ${user.full_name}!`);
    }
  }, [user]);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <Spin size="large" tip="Loading Thermal Inspection System..." />
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={login} />;
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar 
        collapsed={collapsed}
        currentPage={currentPage}
        onPageChange={setCurrentPage}
      />
      
      <Layout className={`site-layout ${collapsed ? 'collapsed' : ''}`}>
        <Header 
          collapsed={collapsed}
          onCollapse={() => setCollapsed(!collapsed)}
          user={user}
          onLogout={logout}
        />
        
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            background: '#fff',
            minHeight: 280,
            borderRadius: 8,
          }}
        >
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/thermal-scans" element={<ThermalScans />} />
            <Route path="/ai-results" element={<AIResults />} />
            <Route path="/substations" element={<Substations />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

function App() {
  return (
    <ConfigProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <Router>
          <AppContent />
        </Router>
        <ReactQueryDevtools initialIsOpen={false} />
      </QueryClientProvider>
    </ConfigProvider>
  );
}

export default App; 