import React, { useState, useEffect } from 'react';
import { useApi } from '../contexts/ApiContext';

interface SystemConfig {
  trading: {
    enabled: boolean;
    max_position_size: number;
    risk_level: 'low' | 'medium' | 'high';
    stop_loss_percentage: number;
    take_profit_percentage: number;
    max_daily_trades: number;
  };
  analysis: {
    interval_seconds: number;
    sentiment_weight: number;
    technical_weight: number;
    confidence_threshold: number;
    enable_news_analysis: boolean;
    enable_technical_analysis: boolean;
  };
  risk_management: {
    max_drawdown_percentage: number;
    position_size_percentage: number;
    emergency_stop_loss: number;
    daily_loss_limit: number;
  };
  notifications: {
    enable_email: boolean;
    enable_webhook: boolean;
    alert_on_trades: boolean;
    alert_on_errors: boolean;
    alert_on_high_volatility: boolean;
  };
}

const SystemConfigPanel: React.FC = () => {
  const { api } = useApi();
  
  const [config, setConfig] = useState<SystemConfig>({
    trading: {
      enabled: false,
      max_position_size: 0.1,
      risk_level: 'medium',
      stop_loss_percentage: 5,
      take_profit_percentage: 10,
      max_daily_trades: 10,
    },
    analysis: {
      interval_seconds: 300,
      sentiment_weight: 0.4,
      technical_weight: 0.6,
      confidence_threshold: 0.7,
      enable_news_analysis: true,
      enable_technical_analysis: true,
    },
    risk_management: {
      max_drawdown_percentage: 10,
      position_size_percentage: 2,
      emergency_stop_loss: 15,
      daily_loss_limit: 1000,
    },
    notifications: {
      enable_email: false,
      enable_webhook: true,
      alert_on_trades: true,
      alert_on_errors: true,
      alert_on_high_volatility: false,
    }
  });
  
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<keyof SystemConfig>('trading');

  const handleConfigChange = (section: keyof SystemConfig, key: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
    setError(null);
    setSuccess(null);
  };

  const handleSaveConfig = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      
      // In a real implementation, you would save to the backend
      // For now, just simulate a save operation
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSuccess('系统配置已成功保存');
      
    } catch (err) {
      console.error('Error saving config:', err);
      setError('保存配置失败');
    } finally {
      setSaving(false);
    }
  };

  const handleResetConfig = () => {
    if (window.confirm('确定要重置所有配置到默认值吗？')) {
      // Reset to default values
      setConfig({
        trading: {
          enabled: false,
          max_position_size: 0.1,
          risk_level: 'medium',
          stop_loss_percentage: 5,
          take_profit_percentage: 10,
          max_daily_trades: 10,
        },
        analysis: {
          interval_seconds: 300,
          sentiment_weight: 0.4,
          technical_weight: 0.6,
          confidence_threshold: 0.7,
          enable_news_analysis: true,
          enable_technical_analysis: true,
        },
        risk_management: {
          max_drawdown_percentage: 10,
          position_size_percentage: 2,
          emergency_stop_loss: 15,
          daily_loss_limit: 1000,
        },
        notifications: {
          enable_email: false,
          enable_webhook: true,
          alert_on_trades: true,
          alert_on_errors: true,
          alert_on_high_volatility: false,
        }
      });
      setSuccess('配置已重置为默认值');
    }
  };

  const tabs = [
    { key: 'trading', label: '交易设置', icon: '📈' },
    { key: 'analysis', label: '分析设置', icon: '🔍' },
    { key: 'risk_management', label: '风险管理', icon: '⚠️' },
    { key: 'notifications', label: '通知设置', icon: '🔔' },
  ];

  const renderTradingConfig = () => (
    <div className="space-y-4">
      <div className="flex items-center">
        <input
          type="checkbox"
          id="trading-enabled"
          checked={config.trading.enabled}
          onChange={(e) => handleConfigChange('trading', 'enabled', e.target.checked)}
          className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
        />
        <label htmlFor="trading-enabled" className="ml-2 text-sm font-medium text-gray-700">
          启用自动交易
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          最大持仓大小 (BTC)
        </label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={config.trading.max_position_size}
          onChange={(e) => handleConfigChange('trading', 'max_position_size', parseFloat(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          风险等级
        </label>
        <select
          value={config.trading.risk_level}
          onChange={(e) => handleConfigChange('trading', 'risk_level', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="low">低风险</option>
          <option value="medium">中等风险</option>
          <option value="high">高风险</option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            止损百分比 (%)
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="100"
            value={config.trading.stop_loss_percentage}
            onChange={(e) => handleConfigChange('trading', 'stop_loss_percentage', parseFloat(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            止盈百分比 (%)
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="1000"
            value={config.trading.take_profit_percentage}
            onChange={(e) => handleConfigChange('trading', 'take_profit_percentage', parseFloat(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          每日最大交易次数
        </label>
        <input
          type="number"
          min="1"
          max="100"
          value={config.trading.max_daily_trades}
          onChange={(e) => handleConfigChange('trading', 'max_daily_trades', parseInt(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
    </div>
  );

  const renderAnalysisConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          分析间隔 (秒)
        </label>
        <input
          type="number"
          min="60"
          max="3600"
          value={config.analysis.interval_seconds}
          onChange={(e) => handleConfigChange('analysis', 'interval_seconds', parseInt(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">最小60秒，最大3600秒</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            情绪分析权重
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="1"
            value={config.analysis.sentiment_weight}
            onChange={(e) => handleConfigChange('analysis', 'sentiment_weight', parseFloat(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            技术分析权重
          </label>
          <input
            type="number"
            step="0.1"
            min="0"
            max="1"
            value={config.analysis.technical_weight}
            onChange={(e) => handleConfigChange('analysis', 'technical_weight', parseFloat(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          置信度阈值
        </label>
        <input
          type="number"
          step="0.1"
          min="0"
          max="1"
          value={config.analysis.confidence_threshold}
          onChange={(e) => handleConfigChange('analysis', 'confidence_threshold', parseFloat(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">只有置信度高于此值的信号才会被执行</p>
      </div>

      <div className="space-y-2">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="enable-news"
            checked={config.analysis.enable_news_analysis}
            onChange={(e) => handleConfigChange('analysis', 'enable_news_analysis', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          />
          <label htmlFor="enable-news" className="ml-2 text-sm font-medium text-gray-700">
            启用新闻情绪分析
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="enable-technical"
            checked={config.analysis.enable_technical_analysis}
            onChange={(e) => handleConfigChange('analysis', 'enable_technical_analysis', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          />
          <label htmlFor="enable-technical" className="ml-2 text-sm font-medium text-gray-700">
            启用技术指标分析
          </label>
        </div>
      </div>
    </div>
  );

  const renderRiskManagementConfig = () => (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          最大回撤百分比 (%)
        </label>
        <input
          type="number"
          step="0.1"
          min="0"
          max="50"
          value={config.risk_management.max_drawdown_percentage}
          onChange={(e) => handleConfigChange('risk_management', 'max_drawdown_percentage', parseFloat(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">达到此回撤时将暂停交易</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          单笔交易仓位百分比 (%)
        </label>
        <input
          type="number"
          step="0.1"
          min="0.1"
          max="10"
          value={config.risk_management.position_size_percentage}
          onChange={(e) => handleConfigChange('risk_management', 'position_size_percentage', parseFloat(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">每笔交易占总资金的百分比</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          紧急止损百分比 (%)
        </label>
        <input
          type="number"
          step="0.1"
          min="5"
          max="50"
          value={config.risk_management.emergency_stop_loss}
          onChange={(e) => handleConfigChange('risk_management', 'emergency_stop_loss', parseFloat(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">触发紧急止损的损失百分比</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          每日损失限额 (USD)
        </label>
        <input
          type="number"
          min="100"
          max="10000"
          value={config.risk_management.daily_loss_limit}
          onChange={(e) => handleConfigChange('risk_management', 'daily_loss_limit', parseFloat(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <p className="text-xs text-gray-500 mt-1">达到此损失额度将停止当日交易</p>
      </div>
    </div>
  );

  const renderNotificationsConfig = () => (
    <div className="space-y-4">
      <div className="space-y-3">
        <div className="flex items-center">
          <input
            type="checkbox"
            id="enable-email"
            checked={config.notifications.enable_email}
            onChange={(e) => handleConfigChange('notifications', 'enable_email', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          />
          <label htmlFor="enable-email" className="ml-2 text-sm font-medium text-gray-700">
            启用邮件通知
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="enable-webhook"
            checked={config.notifications.enable_webhook}
            onChange={(e) => handleConfigChange('notifications', 'enable_webhook', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          />
          <label htmlFor="enable-webhook" className="ml-2 text-sm font-medium text-gray-700">
            启用Webhook通知
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="alert-trades"
            checked={config.notifications.alert_on_trades}
            onChange={(e) => handleConfigChange('notifications', 'alert_on_trades', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          />
          <label htmlFor="alert-trades" className="ml-2 text-sm font-medium text-gray-700">
            交易执行时通知
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="alert-errors"
            checked={config.notifications.alert_on_errors}
            onChange={(e) => handleConfigChange('notifications', 'alert_on_errors', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          />
          <label htmlFor="alert-errors" className="ml-2 text-sm font-medium text-gray-700">
            系统错误时通知
          </label>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="alert-volatility"
            checked={config.notifications.alert_on_high_volatility}
            onChange={(e) => handleConfigChange('notifications', 'alert_on_high_volatility', e.target.checked)}
            className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
          />
          <label htmlFor="alert-volatility" className="ml-2 text-sm font-medium text-gray-700">
            高波动性时通知
          </label>
        </div>
      </div>
    </div>
  );

  const renderConfigContent = () => {
    switch (activeTab) {
      case 'trading':
        return renderTradingConfig();
      case 'analysis':
        return renderAnalysisConfig();
      case 'risk_management':
        return renderRiskManagementConfig();
      case 'notifications':
        return renderNotificationsConfig();
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">系统参数配置</h3>
      </div>

      {/* Messages */}
      {error && (
        <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-md p-3">
          <div className="text-red-800 text-sm">{error}</div>
        </div>
      )}
      
      {success && (
        <div className="mx-6 mt-4 bg-green-50 border border-green-200 rounded-md p-3">
          <div className="text-green-800 text-sm">{success}</div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as keyof SystemConfig)}
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
      <div className="p-6">
        {renderConfigContent()}
      </div>

      {/* Actions */}
      <div className="px-6 py-4 border-t border-gray-200 flex justify-between">
        <button
          onClick={handleResetConfig}
          className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
        >
          重置为默认值
        </button>
        
        <button
          onClick={handleSaveConfig}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? '保存中...' : '保存配置'}
        </button>
      </div>
    </div>
  );
};

export default SystemConfigPanel;