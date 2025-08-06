import React, { useState } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Upload,
  Button,
  Progress,
  List,
  Tag,
  Space,
  Alert,
  Typography,
  message,
} from 'antd';
import {
  CameraOutlined,
  FireOutlined,
  BankOutlined,
  ThunderboltOutlined,
  UploadOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import { useDashboardStats, useRecentAnalyses, useSubstations } from '../hooks/useDashboard';
import { uploadService } from '../services/uploadService';

const { Dragger } = Upload;
const { Title, Text } = Typography;

const Dashboard = () => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [currentBatch, setCurrentBatch] = useState(null);

  // Fetch dashboard data
  const { data: stats, isLoading: statsLoading, error: statsError } = useDashboardStats();
  const { data: analyses, isLoading: analysesLoading, refetch: refetchAnalyses } = useRecentAnalyses(5);
  const { data: substations, isLoading: substationsLoading } = useSubstations();

  // Handle file upload
  const handleUpload = async (options) => {
    const { fileList } = options;
    
    if (fileList.length === 0) return;
    
    try {
      setUploading(true);
      setUploadProgress(0);
      
      const files = fileList.map(file => file.originFileObj || file);
      
      const result = await uploadService.uploadThermalImages(files, {
        ambientTemperature: '34.0',
        notes: 'Dashboard upload',
        onProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        },
      });
      
      setCurrentBatch(result.batch_id);
      message.success(`Upload successful! ${result.successful_uploads} files uploaded.`);
      
      // Monitor batch processing
      monitorBatchProcessing(result.batch_id);
      
    } catch (error) {
      console.error('Upload failed:', error);
      message.error('Upload failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  // Monitor batch processing
  const monitorBatchProcessing = async (batchId) => {
    let attempts = 0;
    const maxAttempts = 20;
    
    const checkStatus = async () => {
      try {
        const status = await uploadService.getBatchStatus(batchId);
        
        if (status.status === 'completed' || status.status === 'failed') {
          // Refresh analyses data
          refetchAnalyses();
          return;
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(checkStatus, 3000);
        }
      } catch (error) {
        console.error('Error checking batch status:', error);
      }
    };
    
    setTimeout(checkStatus, 2000);
  };

  const uploadProps = {
    name: 'files',
    multiple: true,
    accept: '.jpg,.jpeg,.png,.tiff,.bmp',
    beforeUpload: () => false, // Prevent auto upload
    onChange: handleUpload,
    showUploadList: false,
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'critical': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'blue';
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2} style={{ marginBottom: '24px' }}>
        🔥 Thermal Inspection Dashboard
      </Title>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Images"
              value={stats?.total_images_processed || 0}
              prefix={<CameraOutlined style={{ color: '#1890ff' }} />}
              loading={statsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Critical Issues"
              value={stats?.critical_issues || 0}
              prefix={<FireOutlined style={{ color: '#ff4d4f' }} />}
              loading={statsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Substations"
              value={stats?.total_substations || 0}
              prefix={<BankOutlined style={{ color: '#52c41a' }} />}
              loading={statsLoading}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Batches"
              value={stats?.active_batches || 0}
              prefix={<ThunderboltOutlined style={{ color: '#fa8c16' }} />}
              loading={statsLoading}
            />
          </Card>
        </Col>
      </Row>

      {statsError && (
        <Alert
          message="Failed to load dashboard statistics"
          description="The dashboard API endpoints might not be available. Backend connectivity issues detected."
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      <Row gutter={[16, 16]}>
        {/* Upload Section */}
        <Col xs={24} lg={12}>
          <Card title="🚀 Upload Thermal Images" style={{ height: '400px' }}>
            <Dragger
              {...uploadProps}
              style={{ height: '200px' }}
              disabled={uploading}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined style={{ fontSize: '48px', color: '#1890ff' }} />
              </p>
              <p className="ant-upload-text">
                Click or drag FLIR images to this area to upload
              </p>
              <p className="ant-upload-hint">
                Support for single or bulk upload. Maximum 5000 files per batch.
                Supported formats: JPG, PNG, TIFF, BMP
              </p>
            </Dragger>

            {uploading && (
              <div style={{ marginTop: '16px' }}>
                <Progress percent={uploadProgress} status="active" />
                <Text type="secondary">Uploading thermal images...</Text>
              </div>
            )}

            {currentBatch && (
              <Alert
                message={`Upload completed! Batch ID: ${currentBatch}`}
                description="Your images are being processed. Results will appear in the recent analyses section."
                type="success"
                style={{ marginTop: '16px' }}
              />
            )}
          </Card>
        </Col>

        {/* Recent Analyses */}
        <Col xs={24} lg={12}>
          <Card title="🔍 Recent Analyses" style={{ height: '400px' }}>
            <List
              loading={analysesLoading}
              dataSource={analyses || []}
              locale={{ emptyText: 'No analyses yet. Upload some thermal images to get started!' }}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Text strong>{item.filename}</Text>
                        <Tag color={getRiskColor(item.risk_level)}>
                          {item.risk_level}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <Text type="secondary">
                          Critical: {item.critical_hotspots} | 
                          Quality: {(item.quality_score * 100).toFixed(1)}%
                        </Text>
                        {item.substation_name && (
                          <div>
                            <Text type="secondary">📍 {item.substation_name}</Text>
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* Substations Overview */}
      <Row style={{ marginTop: '24px' }}>
        <Col span={24}>
          <Card title="🏭 Substations Overview">
            <Row gutter={[16, 16]}>
              {substationsLoading && <Col span={24}><Text>Loading substations...</Text></Col>}
              {substations?.map((substation) => (
                <Col xs={24} sm={12} lg={8} xl={6} key={substation.id}>
                  <Card size="small" style={{ borderLeft: '4px solid #1890ff' }}>
                    <Title level={5} style={{ marginBottom: '8px' }}>
                      {substation.name}
                    </Title>
                    <Space direction="vertical" size="small">
                      <Text type="secondary">Code: {substation.code}</Text>
                      <Text>Total Scans: {substation.total_scans}</Text>
                      <Text>Critical: {substation.critical_count}</Text>
                      <Text>Potential: {substation.potential_count}</Text>
                      {substation.avg_quality_score && (
                        <Text>Avg Quality: {(substation.avg_quality_score * 100).toFixed(1)}%</Text>
                      )}
                    </Space>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard; 