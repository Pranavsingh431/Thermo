import React from 'react';
import { Typography, Card } from 'antd';

const { Title } = Typography;

const Substations = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>🏭 Substations Management</Title>
      <Card>
        <p>Substations page - Coming soon!</p>
        <p>This will show detailed substation information, GPS boundaries, and inspection history.</p>
      </Card>
    </div>
  );
};

export default Substations; 