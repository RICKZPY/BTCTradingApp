import React, { useState, useEffect } from 'react';
import { useApi } from '../contexts/ApiContext';
import { useLanguage } from '../contexts/LanguageContext';

interface SystemHealth {
  overall_status: string;
  timestamp: string;
  components: {
    [key: string]: {
      status: string;
      [key: string]: any;
    };
  };
  metrics: {
    total_requests: number;
    successful_requests: number;
    error_rate: number;
    average_response_time_ms: number;
  };
}

interface SystemAlert {
  id: string;
  level: string;
  title: string;
  message: string;
  timestamp: string;
  component: string;
  resolved: boolean;
}

interface SystemMetrics {
  timestamp: string;
  system_resources: {
    cpu_usage_percent: number;
    memory_usage_percent: number;
    memory_used_mb: number;
    memory_total_mb: number;
    disk_usage_percent: number;
    disk_free_gb: number;
  };
  application_metrics: {
    uptime_seconds: number;
    total_requests: number;
    requests_per_minute: number;
    error_rate: number;
    average_response_time_ms: number;
    active_connections: number;
  };
  trading_metrics: {
    market_data_updates: number;
    last_price_update: string | null;
    cache_hit_rate: number;
    api_calls_today: number;
  };
}

const MonitoringPage: React.FC = () => {
  const { api } = useApi();
  const { t } = useLanguage();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMonitoringData = async () => {
    try {
      setError(null);
      
      const [healthResponse, alertsResponse, metricsResponse] = await Promise.all([
        api.getSystemHealth(),
        api.getSystemAlerts(),
        api.getSystemMetrics()
      ]);

      if (healthResponse.success) {
        setHealth(healthResponse.data);
      }

      if (alertsResponse.success) {
        setAlerts(alertsResponse.data.alerts);
      }

      if (metricsResponse.success) {
        setMetrics(metricsResponse.data);
      }

    } catch (err: any) {
      console.error('Error loading monitoring data:', err);
      setError('Failed to load monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMonitoringData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadMonitoringData, 30000);
    
    return () => clearInterval(interval);
  }, [api]);

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'warning':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      case 'unavailable':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-blue-600 bg-blue-100';
    }
  };

  const getAlertColor = (level: string) => {
    switch (level.toLowerCase()) {
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

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatBytes = (bytes: number) => {
    return `${(bytes / 1024).toFixed(1)} GB`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">{t('monitoring.loading_data')}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('monitoring.title')}</h1>
          <p className="text-gray-600">{t('monitoring.subtitle')}</p>
        </div>
        <button
          onClick={loadMonitoringData}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          {t('monitoring.refresh')}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {/* System Health Overview */}
      {health && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">{t('monitoring.system_health')}</h2>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(health.overall_status)}`}>
              {health.overall_status.toUpperCase()}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(health.components).map(([name, component]) => (
              <div key={name} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-sm font-medium text-gray-700 capitalize">
                    {name.replace('_', ' ')}
                  </h3>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(component.status)}`}>
                    {component.status}
                  </span>
                </div>
                
                <div className="text-xs text-gray-600 space-y-1">
                  {component.uptime_seconds && (
                    <div>Uptime: {formatUptime(component.uptime_seconds)}</div>
                  )}
                  {component.memory_usage_mb && (
                    <div>Memory: {component.memory_usage_mb}MB</div>
                  )}
                  {component.cpu_usage_percent && (
                    <div>CPU: {component.cpu_usage_percent}%</div>
                  )}
                  {component.last_update && (
                    <div>Last Update: {new Date(component.last_update).toLocaleTimeString()}</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">{t('monitoring.total_requests')}:</span>
              <span className="ml-2 font-semibold">{health.metrics.total_requests.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-600">Success Rate:</span>
              <span className="ml-2 font-semibold text-green-600">
                {((health.metrics.successful_requests / health.metrics.total_requests) * 100).toFixed(1)}%
              </span>
            </div>
            <div>
              <span className="text-gray-600">{t('monitoring.error_rate')}:</span>
              <span className="ml-2 font-semibold text-red-600">
                {(health.metrics.error_rate * 100).toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-gray-600">{t('monitoring.avg_response')}:</span>
              <span className="ml-2 font-semibold">{health.metrics.average_response_time_ms}ms</span>
            </div>
          </div>
        </div>
      )}

      {/* System Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* System Resources */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('monitoring.system_resources')}</h3>
            
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm">
                  <span>{t('monitoring.cpu_usage')}</span>
                  <span>{metrics.system_resources.cpu_usage_percent}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${metrics.system_resources.cpu_usage_percent}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm">
                  <span>{t('monitoring.memory_usage')}</span>
                  <span>{metrics.system_resources.memory_usage_percent}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-green-600 h-2 rounded-full" 
                    style={{ width: `${metrics.system_resources.memory_usage_percent}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  {metrics.system_resources.memory_used_mb}MB / {metrics.system_resources.memory_total_mb}MB
                </div>
              </div>
              
              <div>
                <div className="flex justify-between text-sm">
                  <span>{t('monitoring.disk_usage')}</span>
                  <span>{metrics.system_resources.disk_usage_percent}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-yellow-600 h-2 rounded-full" 
                    style={{ width: `${metrics.system_resources.disk_usage_percent}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-600 mt-1">
                  {formatBytes(metrics.system_resources.disk_free_gb * 1024 * 1024 * 1024)} free
                </div>
              </div>
            </div>
          </div>

          {/* Application Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('monitoring.application_metrics')}</h3>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.uptime')}:</span>
                <span className="text-sm font-semibold">{formatUptime(metrics.application_metrics.uptime_seconds)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.total_requests')}:</span>
                <span className="text-sm font-semibold">{metrics.application_metrics.total_requests.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.requests_per_min')}:</span>
                <span className="text-sm font-semibold">{metrics.application_metrics.requests_per_minute}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.error_rate')}:</span>
                <span className="text-sm font-semibold text-red-600">
                  {(metrics.application_metrics.error_rate * 100).toFixed(2)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.avg_response')}:</span>
                <span className="text-sm font-semibold">{metrics.application_metrics.average_response_time_ms}ms</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.active_connections')}:</span>
                <span className="text-sm font-semibold">{metrics.application_metrics.active_connections}</span>
              </div>
            </div>
          </div>

          {/* Trading Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('monitoring.trading_metrics')}</h3>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.market_updates')}:</span>
                <span className="text-sm font-semibold">{metrics.trading_metrics.market_data_updates}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.cache_hit_rate')}:</span>
                <span className="text-sm font-semibold text-green-600">
                  {(metrics.trading_metrics.cache_hit_rate * 100).toFixed(1)}%
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">{t('monitoring.api_calls_today')}:</span>
                <span className="text-sm font-semibold">{metrics.trading_metrics.api_calls_today.toLocaleString()}</span>
              </div>
              {metrics.trading_metrics.last_price_update && (
                <div>
                  <span className="text-sm text-gray-600">{t('monitoring.last_price_update')}:</span>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(metrics.trading_metrics.last_price_update).toLocaleString()}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* System Alerts */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">{t('monitoring.system_alerts')}</h2>
        </div>
        
        {alerts.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            {t('monitoring.no_alerts')}
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {alerts.map((alert) => (
              <div key={alert.id} className={`p-4 border-l-4 ${getAlertColor(alert.level)}`}>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center">
                      <h4 className="font-medium">{alert.title}</h4>
                      <span className={`ml-2 px-2 py-1 text-xs rounded-full ${
                        alert.resolved ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {alert.resolved ? t('monitoring.resolved') : t('monitoring.active')}
                      </span>
                    </div>
                    <p className="text-sm mt-1">{alert.message}</p>
                    <div className="flex items-center mt-2 text-xs text-gray-600">
                      <span>{t('monitoring.component')}: {alert.component}</span>
                      <span className="mx-2">•</span>
                      <span>{new Date(alert.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MonitoringPage;