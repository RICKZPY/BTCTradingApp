import React, { useState, useEffect } from 'react';
import { useApi } from '../contexts/ApiContext';
import { useLanguage } from '../contexts/LanguageContext';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js';
import 'chartjs-adapter-date-fns';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface BacktestConfig {
  symbol: string;
  days: number;
  initial_capital: number;
  strategy_name: string;
  strategy_id?: string;
  strategy_type: 'built-in' | 'custom';
  strategy_config: {
    risk_parameters: {
      max_position_size: number;
      stop_loss_percentage: number;
      take_profit_percentage: number;
      max_daily_trades: number;
      risk_per_trade: number;
    };
  };
}

interface Strategy {
  info: {
    id: string;
    name: string;
    description: string;
    author: string;
    version: string;
    created_at: string;
    updated_at: string;
    tags: string[];
  };
  code: string;
  parameters: Record<string, any>;
}

interface BacktestResult {
  backtest_id: string;
  strategy_name: string;
  performance_metrics: any;
  total_trades: number;
  trade_summary: any[];
  equity_curve: Array<{ timestamp: string; value: number }>;
  drawdown_curve: Array<{ timestamp: string; drawdown: number }>;
}

const BacktestingPage: React.FC = () => {
  const { api } = useApi();
  const { t } = useLanguage();
  const [config, setConfig] = useState<BacktestConfig>({
    symbol: 'BTCUSDT',
    days: 30,
    initial_capital: 10000,
    strategy_name: 'Simple Moving Average Strategy',
    strategy_type: 'built-in',
    strategy_config: {
      risk_parameters: {
        max_position_size: 0.1,
        stop_loss_percentage: 0.05,
        take_profit_percentage: 0.15,
        max_daily_trades: 5,
        risk_per_trade: 0.02
      }
    }
  });

  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoTradingStatus, setAutoTradingStatus] = useState<any>(null);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loadingStrategies, setLoadingStrategies] = useState(true);

  // Built-in strategies
  const builtInStrategies = [
    { id: 'sma', name: t('backtest.builtin_strategies') + ' - SMA', description: 'Classic SMA crossover strategy' },
    { id: 'rsi', name: t('backtest.builtin_strategies') + ' - RSI', description: 'RSI-based momentum strategy' },
    { id: 'sentiment', name: t('backtest.builtin_strategies') + ' - Sentiment', description: 'Market sentiment based strategy' }
  ];

  // Load strategies and auto trading status
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load custom strategies
        const strategiesResponse = await api.request('/api/v1/strategies');
        if (strategiesResponse.success && strategiesResponse.data) {
          setStrategies(Array.isArray(strategiesResponse.data) ? strategiesResponse.data : []);
        } else {
          console.warn('Failed to load strategies for backtesting:', strategiesResponse);
          setStrategies([]);
        }

        // Load auto trading status
        const autoTradingResponse = await api.getAutoTradingStatus();
        if (autoTradingResponse.success) {
          setAutoTradingStatus(autoTradingResponse.data);
        }
      } catch (err: any) {
        console.error('Error loading data:', err);
        setStrategies([]);
      } finally {
        setLoadingStrategies(false);
      }
    };

    loadData();
  }, [api]);

  const handleConfigChange = (field: string, value: any) => {
    if (field.includes('.')) {
      const [parent, child, grandchild] = field.split('.');
      setConfig(prev => {
        const newConfig = { ...prev };
        if (grandchild) {
          // Handle nested object updates
          (newConfig as any)[parent] = {
            ...(newConfig as any)[parent],
            [child]: {
              ...((newConfig as any)[parent] as any)[child],
              [grandchild]: value
            }
          };
        } else {
          // Handle single level nested updates
          (newConfig as any)[parent] = {
            ...(newConfig as any)[parent],
            [child]: value
          };
        }
        return newConfig;
      });
    } else {
      setConfig(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleStrategyChange = (strategyValue: string) => {
    if (strategyValue.startsWith('built-in:')) {
      const strategyId = strategyValue.replace('built-in:', '');
      const builtInStrategy = builtInStrategies.find(s => s.id === strategyId);
      if (builtInStrategy) {
        setConfig(prev => ({
          ...prev,
          strategy_type: 'built-in',
          strategy_name: builtInStrategy.name,
          strategy_id: strategyId
        }));
      }
    } else if (strategyValue.startsWith('custom:')) {
      const strategyId = strategyValue.replace('custom:', '');
      const customStrategy = strategies.find(s => s.info.id === strategyId);
      if (customStrategy) {
        setConfig(prev => ({
          ...prev,
          strategy_type: 'custom',
          strategy_name: customStrategy.info.name,
          strategy_id: strategyId
        }));
      }
    }
  };

  const runBacktest = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Prepare backtest configuration
      const backtestConfig = {
        ...config,
        strategy_type: config.strategy_type,
        strategy_id: config.strategy_id
      };
      
      const response = await api.runBacktest(backtestConfig);
      
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message || t('common.error'));
      }
    } catch (err: any) {
      console.error('Error running backtest:', err);
      setError(err.response?.data?.detail || 'Failed to run backtest');
    } finally {
      setLoading(false);
    }
  };

  const toggleAutoTrading = async () => {
    try {
      const newStatus = !autoTradingStatus?.enabled;
      const response = await api.toggleAutoTrading(newStatus);
      
      if (response.success) {
        setAutoTradingStatus((prev: any) => ({
          ...prev,
          enabled: newStatus
        }));
      }
    } catch (err) {
      console.error('Error toggling auto trading:', err);
    }
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
    return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
  };

  // Chart data for equity curve
  const equityChartData = result ? {
    labels: result.equity_curve.map(point => new Date(point.timestamp)),
    datasets: [
      {
        label: 'Portfolio Value',
        data: result.equity_curve.map(point => point.value),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1,
      }
    ]
  } : null;

  // Chart data for drawdown curve
  const drawdownChartData = result ? {
    labels: result.drawdown_curve.map(point => new Date(point.timestamp)),
    datasets: [
      {
        label: 'Drawdown',
        data: result.drawdown_curve.map(point => -point.drawdown * 100),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1,
      }
    ]
  } : null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          displayFormats: {
            day: 'MMM dd',
            hour: 'HH:mm'
          }
        }
      },
      y: {
        beginAtZero: false,
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('backtest.title')}</h1>
        <p className="text-gray-600">{t('backtest.subtitle')}</p>
      </div>

      {/* Auto Trading Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">{t('backtest.auto_trading')}</h2>
          <button
            onClick={toggleAutoTrading}
            className={`px-4 py-2 rounded-md text-white font-medium ${
              autoTradingStatus?.enabled 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {autoTradingStatus?.enabled ? t('backtest.disable_auto') : t('backtest.enable_auto')}
          </button>
        </div>
        
        {autoTradingStatus && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="text-sm text-gray-600">{t('backtest.status')}:</span>
              <div className={`font-semibold ${
                autoTradingStatus.enabled ? 'text-green-600' : 'text-red-600'
              }`}>
                {autoTradingStatus.enabled ? 'ENABLED' : 'DISABLED'}
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">{t('backtest.strategy')}:</span>
              <div className="font-semibold text-gray-900">{autoTradingStatus.strategy}</div>
            </div>
            <div>
              <span className="text-sm text-gray-600">{t('backtest.last_signal')}:</span>
              <div className="font-semibold text-gray-900">{autoTradingStatus.last_signal}</div>
            </div>
            <div>
              <span className="text-sm text-gray-600">{t('backtest.todays_pnl')}:</span>
              <div className={`font-semibold ${
                autoTradingStatus.pnl_today >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatCurrency(autoTradingStatus.pnl_today)}
              </div>
            </div>
          </div>
        )}
        
        {autoTradingStatus?.note && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800">{autoTradingStatus.note}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Backtest Configuration */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('backtest.config')}</h2>
            
            <div className="space-y-4">
              {/* Symbol */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('backtest.symbol')}
                </label>
                <select
                  value={config.symbol}
                  onChange={(e) => handleConfigChange('symbol', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="BTCUSDT">BTC/USDT</option>
                </select>
              </div>

              {/* Days */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('backtest.period')}
                </label>
                <select
                  value={config.days}
                  onChange={(e) => handleConfigChange('days', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={7}>7 Days</option>
                  <option value={14}>14 Days</option>
                  <option value={30}>30 Days</option>
                  <option value={60}>60 Days</option>
                  <option value={90}>90 Days</option>
                </select>
              </div>

              {/* Initial Capital */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('backtest.initial_capital')}
                </label>
                <input
                  type="number"
                  value={config.initial_capital}
                  onChange={(e) => handleConfigChange('initial_capital', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  min="1000"
                  step="1000"
                />
              </div>

              {/* Strategy Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('backtest.strategy')}
                </label>
                {loadingStrategies ? (
                  <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500">
                    {t('backtest.strategy_loading')}
                  </div>
                ) : (
                  <select
                    value={config.strategy_type === 'built-in' ? `built-in:${config.strategy_id || 'sma'}` : `custom:${config.strategy_id || ''}`}
                    onChange={(e) => handleStrategyChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <optgroup label={t('backtest.builtin_strategies')}>
                      {builtInStrategies.map((strategy) => (
                        <option key={strategy.id} value={`built-in:${strategy.id}`}>
                          {strategy.name}
                        </option>
                      ))}
                    </optgroup>
                    {strategies.length > 0 && (
                      <optgroup label={t('backtest.custom_strategies')}>
                        {strategies.map((strategy) => (
                          <option key={strategy.info.id} value={`custom:${strategy.info.id}`}>
                            {strategy.info.name} (by {strategy.info.author})
                          </option>
                        ))}
                      </optgroup>
                    )}
                  </select>
                )}
                
                {/* Strategy Description */}
                <div className="mt-2 text-sm text-gray-600">
                  {config.strategy_type === 'built-in' ? (
                    builtInStrategies.find(s => s.id === config.strategy_id)?.description || 'Built-in trading strategy'
                  ) : (
                    strategies.find(s => s.info.id === config.strategy_id)?.info.description || 'Custom trading strategy'
                  )}
                </div>
              </div>

              {/* Risk Parameters */}
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">{t('backtest.risk_params')}</h3>
                
                <div className="space-y-2">
                  <div>
                    <label className="block text-xs text-gray-600">{t('backtest.max_position')}</label>
                    <input
                      type="number"
                      value={config.strategy_config.risk_parameters.max_position_size * 100}
                      onChange={(e) => handleConfigChange('strategy_config.risk_parameters.max_position_size', parseFloat(e.target.value) / 100)}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      min="1"
                      max="100"
                      step="1"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-xs text-gray-600">{t('backtest.stop_loss')}</label>
                    <input
                      type="number"
                      value={config.strategy_config.risk_parameters.stop_loss_percentage * 100}
                      onChange={(e) => handleConfigChange('strategy_config.risk_parameters.stop_loss_percentage', parseFloat(e.target.value) / 100)}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      min="1"
                      max="20"
                      step="0.5"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-xs text-gray-600">{t('backtest.take_profit')}</label>
                    <input
                      type="number"
                      value={config.strategy_config.risk_parameters.take_profit_percentage * 100}
                      onChange={(e) => handleConfigChange('strategy_config.risk_parameters.take_profit_percentage', parseFloat(e.target.value) / 100)}
                      className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                      min="5"
                      max="50"
                      step="1"
                    />
                  </div>
                </div>
              </div>

              {/* Run Backtest Button */}
              <button
                onClick={runBacktest}
                disabled={loading}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? t('backtest.running') : t('backtest.run')}
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-2">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
              <div className="text-red-800">{error}</div>
            </div>
          )}

          {loading && (
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-center h-64">
                <div className="text-lg text-gray-600">{t('backtest.running')}</div>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-6">
              {/* Performance Metrics */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('backtest.performance')}</h3>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {formatPercent(result.performance_metrics.total_return)}
                    </div>
                    <div className="text-sm text-gray-600">{t('backtest.total_return')}</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {result.performance_metrics.sharpe_ratio.toFixed(2)}
                    </div>
                    <div className="text-sm text-gray-600">{t('backtest.sharpe_ratio')}</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">
                      {formatPercent(result.performance_metrics.max_drawdown)}
                    </div>
                    <div className="text-sm text-gray-600">{t('backtest.max_drawdown')}</div>
                  </div>
                  
                  <div className="text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {formatPercent(result.performance_metrics.win_rate)}
                    </div>
                    <div className="text-sm text-gray-600">{t('backtest.win_rate')}</div>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">{t('backtest.total_trades')}:</span>
                    <span className="ml-2 font-semibold">{result.total_trades}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">{t('backtest.final_capital')}:</span>
                    <span className="ml-2 font-semibold">{formatCurrency(result.performance_metrics.final_capital)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">{t('backtest.profit_factor')}:</span>
                    <span className="ml-2 font-semibold">{result.performance_metrics.profit_factor.toFixed(2)}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">{t('backtest.volatility')}:</span>
                    <span className="ml-2 font-semibold">{formatPercent(result.performance_metrics.volatility)}</span>
                  </div>
                </div>
              </div>

              {/* Equity Curve */}
              {equityChartData && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('backtest.equity_curve')}</h3>
                  <div style={{ height: '300px' }}>
                    <Line data={equityChartData} options={chartOptions} />
                  </div>
                </div>
              )}

              {/* Drawdown Curve */}
              {drawdownChartData && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('backtest.drawdown_curve')}</h3>
                  <div style={{ height: '300px' }}>
                    <Line data={drawdownChartData} options={chartOptions} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BacktestingPage;