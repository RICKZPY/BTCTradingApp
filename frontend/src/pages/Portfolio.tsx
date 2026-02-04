import React, { useEffect, useState } from 'react';
import { useApi, Portfolio, Position } from '../contexts/ApiContext';
import { useWebSocket, SubscriptionType } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';

const PortfolioPage: React.FC = () => {
  const { api } = useApi();
  const { t } = useLanguage();
  const { 
    latestPortfolio, 
    latestPrice,
    subscribe,
    subscriptions 
  } = useWebSocket();
  
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Subscribe to real-time updates
  useEffect(() => {
    if (!subscriptions.has(SubscriptionType.PORTFOLIO_UPDATES)) {
      subscribe(SubscriptionType.PORTFOLIO_UPDATES);
    }
    if (!subscriptions.has(SubscriptionType.PRICE_DATA)) {
      subscribe(SubscriptionType.PRICE_DATA);
    }
  }, [subscribe, subscriptions]);

  // Load initial portfolio data
  const loadPortfolio = async () => {
    try {
      setError(null);
      const portfolioData = await api.getPortfolio();
      setPortfolio(portfolioData);
    } catch (err) {
      console.error('Error loading portfolio:', err);
      setError('Failed to load portfolio data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadPortfolio();
  }, [api]);

  // Update portfolio from real-time data
  useEffect(() => {
    if (latestPortfolio) {
      setPortfolio(prev => ({
        ...latestPortfolio,
        positions: latestPortfolio.positions || prev?.positions || [],
        timestamp: latestPortfolio.timestamp,
        total_unrealized_pnl: latestPortfolio.unrealized_pnl || 0,
        total_unrealized_pnl_percent: 0 // Calculate if needed
      }));
    }
  }, [latestPortfolio]);

  // Update position prices from real-time price data
  useEffect(() => {
    if (latestPrice && portfolio) {
      setPortfolio(prev => {
        if (!prev) return prev;
        
        const updatedPositions = prev.positions.map(position => {
          if (position.symbol === latestPrice.symbol) {
            const currentValue = position.quantity * latestPrice.price;
            const unrealizedPnl = currentValue - (position.quantity * position.average_price);
            const unrealizedPnlPercent = ((latestPrice.price - position.average_price) / position.average_price) * 100;
            
            return {
              ...position,
              current_price: latestPrice.price,
              current_value: currentValue,
              unrealized_pnl: unrealizedPnl,
              unrealized_pnl_percent: unrealizedPnlPercent
            };
          }
          return position;
        });
        
        return {
          ...prev,
          positions: updatedPositions
        };
      });
    }
  }, [latestPrice, portfolio]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadPortfolio();
  };

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

  const formatQuantity = (value: number) => {
    return value.toFixed(8);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">Loading portfolio...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">{error}</div>
        </div>
        <button
          onClick={handleRefresh}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="text-center text-gray-600">
        No portfolio data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('portfolio.title')}</h1>
          <p className="text-gray-600">{t('portfolio.subtitle')}</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Total Value</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(portfolio.total_value)}
              </p>
            </div>
            <div className="text-3xl">💼</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Available Balance</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(portfolio.available_balance)}
              </p>
            </div>
            <div className="text-3xl">💰</div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Total P&L</p>
              <p className={`text-2xl font-bold ${
                portfolio.total_unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(portfolio.total_unrealized_pnl)}
              </p>
              <p className={`text-sm ${
                portfolio.total_unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPercent(portfolio.total_unrealized_pnl_percent)}
              </p>
            </div>
            <div className="text-3xl">
              {portfolio.total_unrealized_pnl >= 0 ? '📈' : '📉'}
            </div>
          </div>
        </div>
      </div>

      {/* Positions Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Current Positions</h2>
        </div>
        
        {portfolio.positions.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No positions found
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Symbol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Side
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quantity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Avg Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Current Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    P&L
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    P&L %
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {portfolio.positions.map((position, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {position.symbol}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        position.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {position.side}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatQuantity(position.quantity)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatCurrency(position.average_price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {position.current_price ? formatCurrency(position.current_price) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {position.current_value ? formatCurrency(position.current_value) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {position.unrealized_pnl !== undefined ? (
                        <span className={position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatCurrency(position.unrealized_pnl)}
                        </span>
                      ) : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {position.unrealized_pnl_percent !== undefined ? (
                        <span className={position.unrealized_pnl_percent >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatPercent(position.unrealized_pnl_percent)}
                        </span>
                      ) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Last Updated */}
      <div className="text-sm text-gray-500 text-center">
        Last updated: {new Date(portfolio.timestamp).toLocaleString()}
      </div>
    </div>
  );
};

export default PortfolioPage;