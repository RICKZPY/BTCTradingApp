import React, { useEffect, useState } from 'react';
import { useApi } from '../contexts/ApiContext';
import { useWebSocket, ConnectionState } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import ManualTradingPanel from '../components/ManualTradingPanel';
import SystemConfigPanel from '../components/SystemConfigPanel';
import AlertsPanel from '../components/AlertsPanel';

const SettingsPage: React.FC = () => {
  const { api } = useApi();
  const { t } = useLanguage();
  const { 
    connectionState, 
    connectionId, 
    messageCount, 
    lastMessageTime,
    connect,
    disconnect 
  } = useWebSocket();
  
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('system');

  const tabs = [
    { key: 'system', label: t('settings.system_control'), icon: '⚙️' },
    { key: 'trading', label: t('settings.manual_trading'), icon: '📈' },
    { key: 'config', label: t('settings.config'), icon: '🔧' },
    { key: 'alerts', label: t('settings.alerts'), icon: '🚨' },
  ];

  // Load system status and settings
  const loadSystemData = async () => {
    try {
      setError(null);
      
      // Load system status
      const status = await api.getSystemStatus();
      setSystemStatus(status);
      
    } catch (err) {
      console.error('Error loading system data:', err);
      setError('加载系统数据失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSystemData();
  }, [api]);

  const handleSystemControl = async (action: string) => {
    try {
      setError(null);
      const response = await api.controlSystem(action);
      
      if (response.success) {
        setSuccess(`系统${action}命令已成功发送`);
        // Reload system status after a delay
        setTimeout(() => {
          loadSystemData();
        }, 2000);
      } else {
        setError(response.message || `系统${action}失败`);
      }
    } catch (err: any) {
      console.error(`Error ${action} system:`, err);
      setError(err.response?.data?.message || `系统${action}失败`);
    }
  };

  const handleWebSocketControl = (action: 'connect' | 'disconnect') => {
    if (action === 'connect') {
      connect();
    } else {
      disconnect();
    }
  };

  const renderSystemControl = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Control */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">系统控制</h2>
          
          <div className="space-y-4">
            {/* System Status */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">系统状态</h3>
              <div className="flex items-center space-x-4">
                <div className={`w-4 h-4 rounded-full ${
                  systemStatus?.system_state === 'running' ? 'bg-green-500' : 
                  systemStatus?.system_state === 'starting' ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
                <span className="text-gray-900 font-medium">
                  {systemStatus?.system_state || '未知'}
                </span>
                {systemStatus?.uptime_seconds && (
                  <span className="text-sm text-gray-500">
                    运行时间: {Math.floor(systemStatus.uptime_seconds / 3600)}小时 {Math.floor((systemStatus.uptime_seconds % 3600) / 60)}分钟
                  </span>
                )}
              </div>
            </div>

            {/* System Controls */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">系统操作</h3>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleSystemControl('start')}
                  className="px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm"
                >
                  启动
                </button>
                <button
                  onClick={() => handleSystemControl('stop')}
                  className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm"
                >
                  停止
                </button>
                <button
                  onClick={() => handleSystemControl('restart')}
                  className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                >
                  重启
                </button>
              </div>
            </div>

            {/* Component Health */}
            {systemStatus?.components && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">组件健康状态</h3>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">总组件数</span>
                    <span className="text-sm font-medium">{systemStatus.components.total}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">健康</span>
                    <span className="text-sm font-medium text-green-600">{systemStatus.components.healthy}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">异常</span>
                    <span className="text-sm font-medium text-red-600">{systemStatus.components.unhealthy}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* WebSocket Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">WebSocket连接</h2>
          
          <div className="space-y-4">
            {/* Connection Status */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">连接状态</h3>
              <div className="flex items-center space-x-4">
                <div className={`w-4 h-4 rounded-full ${
                  connectionState === ConnectionState.CONNECTED ? 'bg-green-500' : 
                  connectionState === ConnectionState.CONNECTING ? 'bg-yellow-500' : 'bg-red-500'
                }`}></div>
                <span className="text-gray-900 font-medium">
                  {connectionState === ConnectionState.CONNECTED ? '已连接' :
                   connectionState === ConnectionState.CONNECTING ? '连接中' :
                   connectionState === ConnectionState.ERROR ? '连接错误' : '未连接'}
                </span>
                {connectionId && (
                  <span className="text-sm text-gray-500">
                    ID: {connectionId.slice(-8)}
                  </span>
                )}
              </div>
            </div>

            {/* Connection Controls */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">连接操作</h3>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleWebSocketControl('connect')}
                  disabled={connectionState === ConnectionState.CONNECTED}
                  className="px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm disabled:opacity-50"
                >
                  连接
                </button>
                <button
                  onClick={() => handleWebSocketControl('disconnect')}
                  disabled={connectionState === ConnectionState.DISCONNECTED}
                  className="px-3 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm disabled:opacity-50"
                >
                  断开
                </button>
              </div>
            </div>

            {/* Connection Stats */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">连接统计</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">接收消息数</span>
                  <span className="text-sm font-medium">{messageCount}</span>
                </div>
                {lastMessageTime && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">最后消息时间</span>
                    <span className="text-sm font-medium">{lastMessageTime.toLocaleTimeString('zh-CN')}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'system':
        return renderSystemControl();
      case 'trading':
        return <ManualTradingPanel />;
      case 'config':
        return <SystemConfigPanel />;
      case 'alerts':
        return <AlertsPanel />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">加载设置中...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('settings.title')}</h1>
        <p className="text-gray-600">{t('settings.subtitle')}</p>
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}
      
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="text-green-800">{success}</div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div>
        {renderTabContent()}
      </div>
    </div>
  );
};

export default SettingsPage;