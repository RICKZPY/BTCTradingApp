import React, { useEffect, useState } from 'react';
import { useApi } from '../contexts/ApiContext';
import { useWebSocket, SubscriptionType } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import PriceChart from '../components/PriceChart';

interface DashboardStats {
  totalValue: number;
  availableBalance: number;
  unrealizedPnl: number;
  unrealizedPnlPercent: number;
  currentPrice: number;
  priceChange24h: number;
  systemStatus: string;
}

const Dashboard: React.FC = () => {
  const { api } = useApi();
  const { t } = useLanguage();
  const { 
    latestPrice, 
    latestPortfolio, 
    systemAlerts, 
    connectionState,
    subscribe,
    subscriptions 
  } = useWebSocket();
  
  const [stats, setStats] = useState<DashboardStats>({
    totalValue: 0,
    availableBalance: 0,
    unrealizedPnl: 0,
    unrealizedPnlPercent: 0,
    currentPrice: 0,
    priceChange24h: 0,
    systemStatus: 'Unknown'
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Subscribe to real-time updates
  useEffect(() => {
    if (!subscriptions.has(SubscriptionType.PRICE_DATA)) {
      subscribe(SubscriptionType.PRICE_DATA);
    }
    if (!subscriptions.has(SubscriptionType.PORTFOLIO_UPDATES)) {
      subscribe(SubscriptionType.PORTFOLIO_UPDATES);
    }
    if (!subscriptions.has(SubscriptionType.SYSTEM_ALERTS)) {
      subscribe(SubscriptionType.SYSTEM_ALERTS);
    }
  }, [subscribe, subscriptions]);

  // Load initial data
  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Load system status
        const systemStatus = await api.getSystemStatus();
        
        // Load portfolio
        const portfolio = await api.getPortfolio();
        
        // Load market data
        const marketData = await api.getMarketData('BTCUSDT');

        setStats({
          totalValue: portfolio.total_value || 0,
          availableBalance: portfolio.available_balance || 0,
          unrealizedPnl: portfolio.total_unrealized_pnl || 0,
          unrealizedPnlPercent: portfolio.total_unrealized_pnl_percent || 0,
          currentPrice: marketData.price || 0,
          priceChange24h: marketData.change_24h_percent || 0,
          systemStatus: systemStatus.system_state || 'Unknown'
        });

      } catch (err) {
        console.error('Error loading dashboard data:', err);
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [api]);

  // Update stats from real-time data
  useEffect(() => {
    if (latestPrice) {
      setStats(prev => ({
        ...prev,
        currentPrice: latestPrice.price,
        priceChange24h: latestPrice.change || prev.priceChange24h
      }));
    }
  }, [latestPrice]);

  useEffect(() => {
    if (latestPortfolio) {
      setStats(prev => ({
        ...prev,
        totalValue: latestPortfolio.total_value,
        availableBalance: latestPortfolio.available_balance,
        unrealizedPnl: latestPortfolio.unrealized_pnl
      }));
    }
  }, [latestPortfolio]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="text-red-800">{error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('dashboard.title')}</h1>
        <p className="text-gray-600">{t('dashboard.subtitle')}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Portfolio Value */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Total Portfolio Value</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(stats.totalValue)}
              </p>
            </div>
            <div className="text-3xl">💼</div>
          </div>
        </div>

        {/* Available Balance */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Available Balance</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(stats.availableBalance)}
              </p>
            </div>
            <div className="text-3xl">💰</div>
          </div>
        </div>

        {/* Unrealized P&L */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Unrealized P&L</p>
              <p className={`text-2xl font-bold ${
                stats.unrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(stats.unrealizedPnl)}
              </p>
              <p className={`text-sm ${
                stats.unrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPercent(stats.unrealizedPnlPercent)}
              </p>
            </div>
            <div className="text-3xl">
              {stats.unrealizedPnl >= 0 ? '📈' : '📉'}
            </div>
          </div>
        </div>

        {/* Bitcoin Price */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Bitcoin Price</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(stats.currentPrice)}
              </p>
              <p className={`text-sm ${
                stats.priceChange24h >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPercent(stats.priceChange24h)} 24h
              </p>
            </div>
            <div className="text-3xl">₿</div>
          </div>
        </div>
      </div>

      {/* Price Chart */}
      <PriceChart symbol="BTCUSDT" height={300} />

      {/* System Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
        <div className="flex items-center space-x-4">
          <div className={`w-4 h-4 rounded-full ${
            stats.systemStatus === 'running' ? 'bg-green-500' : 
            stats.systemStatus === 'starting' ? 'bg-yellow-500' : 'bg-red-500'
          }`}></div>
          <span className="text-gray-900 font-medium">
            System: {stats.systemStatus}
          </span>
          <div className={`w-4 h-4 rounded-full ${
            connectionState === 'connected' ? 'bg-green-500' : 
            connectionState === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
          }`}></div>
          <span className="text-gray-900 font-medium">
            WebSocket: {connectionState}
          </span>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent System Alerts</h2>
        {systemAlerts.length === 0 ? (
          <p className="text-gray-500">No recent alerts</p>
        ) : (
          <div className="space-y-3">
            {systemAlerts.slice(0, 5).map((alert, index) => (
              <div
                key={index}
                className={`p-3 rounded-md border-l-4 ${
                  alert.level === 'error' ? 'bg-red-50 border-red-400' :
                  alert.level === 'warning' ? 'bg-yellow-50 border-yellow-400' :
                  'bg-blue-50 border-blue-400'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium text-gray-900">{alert.title}</p>
                    <p className="text-sm text-gray-600">{alert.message}</p>
                    {alert.component && (
                      <p className="text-xs text-gray-500">Component: {alert.component}</p>
                    )}
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;