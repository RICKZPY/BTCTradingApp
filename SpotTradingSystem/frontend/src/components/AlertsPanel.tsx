import React, { useState, useEffect } from 'react';
import { useWebSocket, SubscriptionType, SystemAlert } from '../contexts/WebSocketContext';

interface AlertFilter {
  level: 'all' | 'error' | 'warning' | 'info';
  component: string;
  timeRange: 'all' | '1h' | '24h' | '7d';
}

const AlertsPanel: React.FC = () => {
  const { systemAlerts, subscribe, subscriptions } = useWebSocket();
  const [filter, setFilter] = useState<AlertFilter>({
    level: 'all',
    component: 'all',
    timeRange: '24h'
  });
  const [filteredAlerts, setFilteredAlerts] = useState<SystemAlert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<SystemAlert | null>(null);

  // Subscribe to system alerts
  useEffect(() => {
    if (!subscriptions.has(SubscriptionType.SYSTEM_ALERTS)) {
      subscribe(SubscriptionType.SYSTEM_ALERTS);
    }
  }, [subscribe, subscriptions]);

  // Filter alerts based on current filter settings
  useEffect(() => {
    let filtered = [...systemAlerts];

    // Filter by level
    if (filter.level !== 'all') {
      filtered = filtered.filter(alert => alert.level === filter.level);
    }

    // Filter by component
    if (filter.component !== 'all') {
      filtered = filtered.filter(alert => alert.component === filter.component);
    }

    // Filter by time range
    if (filter.timeRange !== 'all') {
      const now = new Date();
      const timeRangeMs = {
        '1h': 60 * 60 * 1000,
        '24h': 24 * 60 * 60 * 1000,
        '7d': 7 * 24 * 60 * 60 * 1000
      }[filter.timeRange] || 0;

      filtered = filtered.filter(alert => {
        const alertTime = new Date(alert.timestamp);
        return now.getTime() - alertTime.getTime() <= timeRangeMs;
      });
    }

    // Sort by timestamp (newest first)
    filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

    setFilteredAlerts(filtered);
  }, [systemAlerts, filter]);

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'error':
        return '🚨';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '📢';
    }
  };

  const getAlertColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getBadgeColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'info':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getUniqueComponents = () => {
    const components = new Set(systemAlerts.map(alert => alert.component).filter(Boolean));
    return Array.from(components);
  };

  const getAlertStats = () => {
    const stats = {
      total: filteredAlerts.length,
      error: filteredAlerts.filter(a => a.level === 'error').length,
      warning: filteredAlerts.filter(a => a.level === 'warning').length,
      info: filteredAlerts.filter(a => a.level === 'info').length,
    };
    return stats;
  };

  const handleClearAlerts = () => {
    if (window.confirm('确定要清除所有告警记录吗？')) {
      // In a real implementation, you would call an API to clear alerts
      console.log('Clear alerts requested');
    }
  };

  const handleExportAlerts = () => {
    const dataStr = JSON.stringify(filteredAlerts, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `alerts_${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const stats = getAlertStats();

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold text-gray-900">系统告警与异常处理</h3>
          <div className="flex space-x-2">
            <button
              onClick={handleExportAlerts}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              导出
            </button>
            <button
              onClick={handleClearAlerts}
              className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
            >
              清除
            </button>
          </div>
        </div>
      </div>

      {/* Alert Statistics */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-sm text-gray-600">总计</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{stats.error}</div>
            <div className="text-sm text-gray-600">错误</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-600">{stats.warning}</div>
            <div className="text-sm text-gray-600">警告</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.info}</div>
            <div className="text-sm text-gray-600">信息</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              告警级别
            </label>
            <select
              value={filter.level}
              onChange={(e) => setFilter(prev => ({ ...prev, level: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部</option>
              <option value="error">错误</option>
              <option value="warning">警告</option>
              <option value="info">信息</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              组件
            </label>
            <select
              value={filter.component}
              onChange={(e) => setFilter(prev => ({ ...prev, component: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部组件</option>
              {getUniqueComponents().map(component => (
                <option key={component} value={component}>
                  {component}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              时间范围
            </label>
            <select
              value={filter.timeRange}
              onChange={(e) => setFilter(prev => ({ ...prev, timeRange: e.target.value as any }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部时间</option>
              <option value="1h">最近1小时</option>
              <option value="24h">最近24小时</option>
              <option value="7d">最近7天</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts List */}
      <div className="max-h-96 overflow-y-auto">
        {filteredAlerts.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            {systemAlerts.length === 0 ? '暂无系统告警' : '没有符合筛选条件的告警'}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredAlerts.map((alert, index) => (
              <div
                key={index}
                className={`p-4 hover:bg-gray-50 cursor-pointer ${
                  selectedAlert === alert ? 'bg-blue-50' : ''
                }`}
                onClick={() => setSelectedAlert(selectedAlert === alert ? null : alert)}
              >
                <div className="flex items-start space-x-3">
                  <div className="text-2xl">{getAlertIcon(alert.level)}</div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getBadgeColor(alert.level)}`}>
                        {alert.level.toUpperCase()}
                      </span>
                      {alert.component && (
                        <span className="inline-flex px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded-full">
                          {alert.component}
                        </span>
                      )}
                      <span className="text-xs text-gray-500">
                        {new Date(alert.timestamp).toLocaleString('zh-CN')}
                      </span>
                    </div>
                    
                    <h4 className="text-sm font-medium text-gray-900 mb-1">
                      {alert.title}
                    </h4>
                    
                    <p className="text-sm text-gray-600 line-clamp-2">
                      {alert.message}
                    </p>
                    
                    {selectedAlert === alert && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-md">
                        <div className="space-y-2 text-sm">
                          <div>
                            <span className="font-medium text-gray-700">事件类型:</span>
                            <span className="ml-2 text-gray-600">{alert.event_type}</span>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">完整消息:</span>
                            <div className="mt-1 p-2 bg-white rounded border text-gray-800 font-mono text-xs">
                              {alert.message}
                            </div>
                          </div>
                          <div>
                            <span className="font-medium text-gray-700">时间戳:</span>
                            <span className="ml-2 text-gray-600 font-mono text-xs">
                              {alert.timestamp}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      {filteredAlerts.length > 0 && (
        <div className="px-6 py-4 border-t border-gray-200">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-600">
              显示 {filteredAlerts.length} 条告警记录
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setFilter({ level: 'error', component: 'all', timeRange: '24h' })}
                className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200"
              >
                仅显示错误
              </button>
              <button
                onClick={() => setFilter({ level: 'all', component: 'all', timeRange: '1h' })}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                最近1小时
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertsPanel;