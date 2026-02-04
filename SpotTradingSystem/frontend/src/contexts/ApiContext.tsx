import React, { createContext, useContext, ReactNode } from 'react';
import axios, { AxiosInstance, AxiosResponse } from 'axios';

// API Types
export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
  timestamp: string;
}

export interface SystemStatus {
  system_state: string;
  start_time?: string;
  uptime_seconds?: number;
  components: {
    total: number;
    healthy: number;
    unhealthy: number;
    details: Record<string, any>;
  };
}

export interface Portfolio {
  total_value: number;
  available_balance: number;
  positions: Position[];
  total_unrealized_pnl: number;
  total_unrealized_pnl_percent: number;
  timestamp: string;
}

export interface Position {
  symbol: string;
  quantity: number;
  average_price: number;
  current_price?: number;
  current_value?: number;
  unrealized_pnl?: number;
  unrealized_pnl_percent?: number;
  side: string;
  timestamp: string;
}

export interface TradingOrder {
  order_id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT';
  quantity: number;
  price?: number;
  status: string;
  filled_quantity: number;
  average_price?: number;
  created_at: string;
  updated_at?: string;
}

export interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  change_24h?: number;
  change_24h_percent?: number;
  high_24h?: number;
  low_24h?: number;
  timestamp: string;
}

export interface AnalysisData {
  sentiment?: {
    sentiment_score: number;
    confidence: number;
    key_topics: string[];
    impact_assessment: Record<string, number>;
    timestamp: string;
  };
  technical?: {
    signal_type: string;
    strength: number;
    confidence: number;
    indicators: Record<string, any>;
    timestamp: string;
  };
  decision?: {
    action: string;
    symbol: string;
    quantity?: number;
    confidence: number;
    reasoning: string;
    timestamp: string;
  };
}

// API Client Class
class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = '/api/v1') {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Generic request method
  async request(url: string, options?: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: string;
    params?: Record<string, any>;
  }) {
    const { method = 'GET', body, params } = options || {};
    
    const config: any = {
      method: method.toLowerCase(),
      url,
      params
    };
    
    if (body && (method === 'POST' || method === 'PUT')) {
      config.data = body;
      config.headers = {
        'Content-Type': 'application/json'
      };
    }
    
    const response = await this.client.request(config);
    return response.data;
  }

  // System endpoints
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await this.client.get<ApiResponse<SystemStatus>>('/system/status');
    return response.data.data || response.data as any;
  }

  async controlSystem(action: string) {
    const response = await this.client.post('/system/control', { action });
    return response.data;
  }

  // Trading endpoints
  async getPortfolio(): Promise<Portfolio> {
    const response = await this.client.get<ApiResponse<{ portfolio: Portfolio }>>('/trading/portfolio');
    return response.data.data?.portfolio || response.data as any;
  }

  async getOrderHistory(params?: { symbol?: string; limit?: number; offset?: number }) {
    const response = await this.client.get('/trading/orders', { params });
    return response.data;
  }

  async placeOrder(order: {
    symbol: string;
    side: 'BUY' | 'SELL';
    type: 'MARKET' | 'LIMIT';
    quantity: number;
    price?: number;
  }) {
    const response = await this.client.post('/trading/orders', order);
    return response.data;
  }

  async cancelOrder(orderId: string) {
    const response = await this.client.delete(`/trading/orders/${orderId}`);
    return response.data;
  }

  async getMarketData(symbol: string): Promise<MarketData> {
    const response = await this.client.get<ApiResponse<{ data: MarketData }>>(`/trading/market-data/${symbol}`);
    return response.data.data?.data || response.data as any;
  }

  async getKlineData(symbol: string, interval: string = '1h', limit: number = 24) {
    const response = await this.client.get(`/trading/market-data/${symbol}/klines`, {
      params: { interval, limit }
    });
    return response.data;
  }

  async getPriceHistory(symbol: string, days: number = 7) {
    const response = await this.client.get(`/trading/price-history/${symbol}`, {
      params: { days }
    });
    return response.data;
  }

  // Backtesting endpoints
  async runBacktest(config: {
    symbol?: string;
    days?: number;
    initial_capital?: number;
    strategy_config?: any;
    strategy_name?: string;
  }) {
    const response = await this.client.post('/backtesting/run', config);
    return response.data;
  }

  async getBacktestStatus() {
    const response = await this.client.get('/backtesting/status');
    return response.data;
  }

  // Auto trading endpoints
  async getAutoTradingStatus() {
    const response = await this.client.get('/trading/auto-trading/status');
    return response.data;
  }

  async toggleAutoTrading(enabled: boolean) {
    const response = await this.client.post('/trading/auto-trading/toggle', { enabled });
    return response.data;
  }

  // Monitoring endpoints
  async getSystemHealth() {
    const response = await this.client.get('/system/monitoring/health');
    return response.data;
  }

  async getSystemAlerts() {
    const response = await this.client.get('/system/monitoring/alerts');
    return response.data;
  }

  async getSystemMetrics() {
    const response = await this.client.get('/system/monitoring/metrics');
    return response.data;
  }

  // Analysis endpoints
  async getCurrentAnalysis(): Promise<AnalysisData> {
    const response = await this.client.get<ApiResponse<AnalysisData>>('/analysis/current');
    return response.data.data || response.data as any;
  }

  async getSentimentAnalysis() {
    const response = await this.client.get('/analysis/sentiment');
    return response.data;
  }

  async getTechnicalAnalysis() {
    const response = await this.client.get('/analysis/technical');
    return response.data;
  }

  async triggerAnalysis() {
    const response = await this.client.post('/analysis/trigger', {});
    return response.data;
  }

  // Health endpoints
  async getHealthCheck() {
    const response = await this.client.get('/health/');
    return response.data;
  }

  async getSimpleHealth() {
    const response = await this.client.get('/health/simple');
    return response.data;
  }

  // Strategy management endpoints
  async getStrategies() {
    const response = await this.client.get('/strategies');
    return response.data;
  }

  async getStrategyTemplates() {
    const response = await this.client.get('/strategies/templates');
    return response.data;
  }

  async getStrategy(strategyId: string) {
    const response = await this.client.get(`/strategies/${strategyId}`);
    return response.data;
  }

  async createStrategy(strategy: {
    name: string;
    description: string;
    code: string;
    parameters: Record<string, any>;
    author?: string;
    tags?: string[];
  }) {
    const response = await this.client.post('/strategies', strategy);
    return response.data;
  }

  async updateStrategy(strategyId: string, updates: {
    name?: string;
    description?: string;
    code?: string;
    parameters?: Record<string, any>;
    tags?: string[];
  }) {
    const response = await this.client.put(`/strategies/${strategyId}`, updates);
    return response.data;
  }

  async deleteStrategy(strategyId: string) {
    const response = await this.client.delete(`/strategies/${strategyId}`);
    return response.data;
  }

  async testStrategy(strategyId: string) {
    const response = await this.client.post(`/strategies/${strategyId}/test`);
    return response.data;
  }

  async validateStrategyCode(code: string) {
    const response = await this.client.post('/strategies/validate', { code });
    return response.data;
  }
}

// Context
interface ApiContextType {
  api: ApiClient;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

// Provider
interface ApiProviderProps {
  children: ReactNode;
}

export const ApiProvider: React.FC<ApiProviderProps> = ({ children }) => {
  const api = new ApiClient();

  return (
    <ApiContext.Provider value={{ api }}>
      {children}
    </ApiContext.Provider>
  );
};

// Hook
export const useApi = (): ApiContextType => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};