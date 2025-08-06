import React, { useState, useEffect } from 'react';
import { Table, Card, Tag, Button, Space, Input, DatePicker, Select, Modal, Progress, Tooltip, Row, Col, Statistic } from 'antd';
import { SearchOutlined, FileImageOutlined, EyeOutlined, DownloadOutlined, FilterOutlined } from '@ant-design/icons';
import { useThermalScans } from '../hooks/useDashboard';
import './ThermalScans.css';

const { Search } = Input;
const { RangePicker } = DatePicker;
const { Option } = Select;

const ThermalScans = () => {
  const [searchText, setSearchText] = useState('');
  const [dateRange, setDateRange] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [substationFilter, setSubstationFilter] = useState('all');
  const [selectedScan, setSelectedScan] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);

  const { data: thermalScans, isLoading, error, refetch } = useThermalScans({ limit: 50 });

  // Use real data from API, fallback to mock only if absolutely necessary
  const realScans = thermalScans || [];
  const mockScans = realScans.length === 0 ? [
    {
      id: 1,
      filename: 'FLIR0650.jpg',
      substation_name: 'Salsette Camp',
      capture_timestamp: '2025-01-05T12:38:31',
      processing_status: 'completed',
      file_size: '2.4 MB',
      ambient_temperature: 34.0,
      batch_id: 'batch_20250105_123831',
      ai_analysis: {
        overall_risk_level: 'critical',
        quality_score: 0.95,
        total_hotspots: 3,
        critical_hotspots: 1,
        max_temperature_detected: 78.5
      }
    },
    {
      id: 2,
      filename: 'FLIR1273.jpg', 
      substation: 'Salsette Camp',
      upload_date: '2025-01-05T10:15:22',
      processing_status: 'completed',
      file_size_mb: 2.1,
      ambient_temperature: 34.0,
      batch_id: 'batch_20250105_101522',
      ai_analysis: {
        overall_risk_level: 'medium',
        quality_score: 0.88,
        total_hotspots: 2,
        critical_hotspots: 0,
        max_temperature_detected: 65.2
      }
    },
    {
      id: 3,
      filename: 'FLIR1267.jpg',
      substation: 'Salsette Camp', 
      upload_date: '2025-01-05T09:45:10',
      processing_status: 'processing',
      file_size_mb: 2.3,
      ambient_temperature: 34.0,
      batch_id: 'batch_20250105_094510',
      ai_analysis: null
    },
    {
      id: 4,
      filename: 'FLIR0637.jpg',
      substation: 'Salsette Camp',
      upload_date: '2025-01-04T16:22:33',
      processing_status: 'completed',
      file_size_mb: 2.6,
      ambient_temperature: 33.5,
      batch_id: 'batch_20250104_162233',
      ai_analysis: {
        overall_risk_level: 'low',
        quality_score: 0.92,
        total_hotspots: 1,
        critical_hotspots: 0,
        max_temperature_detected: 42.1
      }
    }
  ] : [];

  // Prioritize real API data, only use mock if no real data available
  const scansData = realScans.length > 0 ? realScans : mockScans;

  const getRiskColor = (risk) => {
    switch(risk) {
      case 'critical': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'default';
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'completed': return 'green';
      case 'processing': return 'blue';
      case 'failed': return 'red';
      case 'pending': return 'orange';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: 'Image',
      dataIndex: 'filename',
      key: 'filename',
      render: (filename) => (
        <Space>
          <FileImageOutlined />
          <span>{filename}</span>
        </Space>
      ),
      sorter: (a, b) => a.filename.localeCompare(b.filename),
    },
    {
      title: 'Substation',
      dataIndex: 'substation_name',
      key: 'substation_name',
      render: (name) => name || 'Unknown',
      filters: [
        { text: 'Salsette Camp', value: 'Salsette Camp' },
        { text: 'Versova', value: 'Versova' },
        { text: 'Bandra', value: 'Bandra' },
        { text: 'Powai', value: 'Powai' },
      ],
      onFilter: (value, record) => record.substation_name === value,
    },
    {
      title: 'Capture Date',
      dataIndex: 'capture_timestamp',
      key: 'capture_timestamp',
      render: (date) => date ? new Date(date).toLocaleString() : 'Unknown',
      sorter: (a, b) => new Date(a.capture_timestamp || 0) - new Date(b.capture_timestamp || 0),
    },
    {
      title: 'Status',
      dataIndex: 'processing_status',
      key: 'processing_status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status.toUpperCase()}
          {status === 'processing' && <Progress size="small" percent={65} style={{ marginLeft: 8, width: 60 }} />}
        </Tag>
      ),
      filters: [
        { text: 'Completed', value: 'completed' },
        { text: 'Processing', value: 'processing' },
        { text: 'Failed', value: 'failed' },
        { text: 'Pending', value: 'pending' },
      ],
      onFilter: (value, record) => record.processing_status === value,
    },
    {
      title: 'Risk Level',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (risk) => {
        if (!risk) return <Tag>Pending</Tag>;
        return <Tag color={getRiskColor(risk)}>{risk?.toUpperCase()}</Tag>;
      },
      filters: [
        { text: 'Critical', value: 'critical' },
        { text: 'Medium', value: 'medium' },
        { text: 'Low', value: 'low' },
      ],
      onFilter: (value, record) => record.risk_level === value,
    },
    {
      title: 'Max Temp (°C)',
      dataIndex: 'max_temperature',
      key: 'max_temp',
      render: (temp) => {
        if (!temp) return '-';
        const color = temp > 70 ? 'red' : temp > 50 ? 'orange' : 'green';
        return <span style={{ color }}>{temp?.toFixed(1)}°C</span>;
      },
      sorter: (a, b) => (a.max_temperature || 0) - (b.max_temperature || 0),
    },
    {
      title: 'Hotspots',
      dataIndex: 'critical_hotspots',
      key: 'hotspots',
      render: (critical, record) => {
        if (critical === null || critical === undefined) return '-';
        return (
          <Tooltip title={`${critical} critical hotspots detected`}>
            <Space>
              <span>{critical}</span>
              {critical > 0 && <Tag color="red" size="small">{critical}</Tag>}
            </Space>
          </Tooltip>
        );
      },
      sorter: (a, b) => (a.critical_hotspots || 0) - (b.critical_hotspots || 0),
    },
    {
      title: 'Components',
      dataIndex: 'total_components',
      key: 'components',
      render: (components) => {
        if (!components) return '-';
        return (
          <Tooltip title={`${components} transmission components detected by YOLO-NAS`}>
            <Tag color="blue">{components}</Tag>
          </Tooltip>
        );
      },
      sorter: (a, b) => (a.total_components || 0) - (b.total_components || 0),
    },
    {
      title: 'Quality',
      dataIndex: 'quality_score',
      key: 'quality',
      render: (score) => {
        if (!score) return '-';
        const percentage = Math.round(score * 100);
        return (
          <Progress 
            percent={percentage} 
            size="small" 
            status={percentage > 80 ? 'success' : percentage > 60 ? 'normal' : 'exception'}
            style={{ width: 60 }}
          />
        );
      },
    },
    {
      title: 'File Size',
      dataIndex: 'file_size',
      key: 'file_size',
      render: (size) => size || '-',
      sorter: (a, b) => {
        const aSize = parseFloat(a.file_size?.replace(' MB', '') || 0);
        const bSize = parseFloat(b.file_size?.replace(' MB', '') || 0);
        return aSize - bSize;
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="link" 
            icon={<EyeOutlined />} 
            onClick={() => showScanDetails(record)}
          >
            View
          </Button>
          <Button 
            type="link" 
            icon={<DownloadOutlined />}
            onClick={() => downloadScan(record)}
          >
            Download
          </Button>
        </Space>
      ),
    },
  ];

  const showScanDetails = (scan) => {
    setSelectedScan(scan);
    setModalVisible(true);
  };

  const downloadScan = (scan) => {
    // Mock download functionality
    console.log('Downloading scan:', scan.filename);
    // In real implementation, would trigger file download
  };

  const filteredScans = scansData.filter(scan => {
    const matchesSearch = scan.filename.toLowerCase().includes(searchText.toLowerCase()) ||
                         (scan.substation_name || '').toLowerCase().includes(searchText.toLowerCase());
    const matchesStatus = statusFilter === 'all' || scan.processing_status === statusFilter;
    const matchesSubstation = substationFilter === 'all' || scan.substation_name === substationFilter;
    
    return matchesSearch && matchesStatus && matchesSubstation;
  });

  const stats = {
    total: scansData.length,
    completed: scansData.filter(s => s.processing_status === 'completed').length,
    processing: scansData.filter(s => s.processing_status === 'processing').length,
    critical: scansData.filter(s => s.risk_level === 'critical').length,
  };

  return (
    <div className="thermal-scans-page">
      <div className="page-header">
        <h1>Thermal Image Scans</h1>
        <p>Manage and analyze thermal inspection images from transmission line surveys</p>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="Total Scans" value={stats.total} prefix={<FileImageOutlined />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Completed" value={stats.completed} valueStyle={{ color: '#3f8600' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Processing" value={stats.processing} valueStyle={{ color: '#1890ff' }} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Critical Issues" value={stats.critical} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="middle" wrap>
          <Search
            placeholder="Search by filename or substation"
            allowClear
            style={{ width: 300 }}
            onChange={(e) => setSearchText(e.target.value)}
            prefix={<SearchOutlined />}
          />
          
          <Select
            placeholder="Filter by status"
            style={{ width: 150 }}
            value={statusFilter}
            onChange={setStatusFilter}
          >
            <Option value="all">All Status</Option>
            <Option value="completed">Completed</Option>
            <Option value="processing">Processing</Option>
            <Option value="failed">Failed</Option>
            <Option value="pending">Pending</Option>
          </Select>

          <Select
            placeholder="Filter by substation"
            style={{ width: 150 }}
            value={substationFilter}
            onChange={setSubstationFilter}
          >
            <Option value="all">All Substations</Option>
            <Option value="Salsette Camp">Salsette Camp</Option>
            <Option value="Versova">Versova</Option>
            <Option value="Bandra">Bandra</Option>
            <Option value="Powai">Powai</Option>
          </Select>

          <RangePicker
            placeholder={['Start Date', 'End Date']}
            onChange={setDateRange}
          />

          <Button icon={<FilterOutlined />} onClick={() => refetch()}>
            Refresh
          </Button>
        </Space>
      </Card>

      {/* Scans Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={filteredScans}
          rowKey="id"
          loading={isLoading}
          pagination={{
            total: filteredScans.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} scans`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Scan Details Modal */}
      <Modal
        title={`Scan Details: ${selectedScan?.filename}`}
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            Close
          </Button>,
          <Button key="download" type="primary" icon={<DownloadOutlined />}>
            Download Report
          </Button>
        ]}
        width={800}
      >
        {selectedScan && (
          <div className="scan-details">
            <Row gutter={16}>
              <Col span={12}>
                <h3>Image Information</h3>
                <p><strong>Filename:</strong> {selectedScan.filename}</p>
                <p><strong>Substation:</strong> {selectedScan.substation}</p>
                <p><strong>Upload Date:</strong> {new Date(selectedScan.upload_date).toLocaleString()}</p>
                <p><strong>File Size:</strong> {selectedScan.file_size_mb} MB</p>
                <p><strong>Ambient Temperature:</strong> {selectedScan.ambient_temperature}°C</p>
                <p><strong>Batch ID:</strong> {selectedScan.batch_id}</p>
              </Col>
              <Col span={12}>
                {selectedScan.ai_analysis ? (
                  <>
                    <h3>AI Analysis Results</h3>
                    <p><strong>Risk Level:</strong> <Tag color={getRiskColor(selectedScan.ai_analysis.overall_risk_level)}>{selectedScan.ai_analysis.overall_risk_level.toUpperCase()}</Tag></p>
                    <p><strong>Quality Score:</strong> {(selectedScan.ai_analysis.quality_score * 100).toFixed(1)}%</p>
                    <p><strong>Max Temperature:</strong> {selectedScan.ai_analysis.max_temperature_detected}°C</p>
                    <p><strong>Total Hotspots:</strong> {selectedScan.ai_analysis.total_hotspots}</p>
                    <p><strong>Critical Hotspots:</strong> {selectedScan.ai_analysis.critical_hotspots}</p>
                  </>
                ) : (
                  <div>
                    <h3>Processing Status</h3>
                    <p>AI analysis is still in progress...</p>
                    <Progress percent={65} status="active" />
                  </div>
                )}
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ThermalScans; 