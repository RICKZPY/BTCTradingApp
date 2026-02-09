import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface DeribitConfig {
  api_key: string;
  api_secret: string;
  test_mode: boolean;
}

export interface TradingConfig {
  risk_free_rate: number;
  default_initial_capital: number;
  commission_rate: number;
}

export interface SystemInfo {
  version: string;
  environment: string;
  api_status: string;
  database_type: string;
  database_status: string;
  deribit_mode: string;
  deribit_status: string;
}

export const settingsApi = {
  // Get Deribit configuration
  getDeribitConfig: async () => {
    const response = await axios.get(`${API_BASE_URL}/api/settings/deribit`);
    return response.data;
  },

  // Update Deribit configuration
  updateDeribitConfig: async (config: DeribitConfig) => {
    const response = await axios.post(`${API_BASE_URL}/api/settings/deribit`, config);
    return response.data;
  },

  // Get trading configuration
  getTradingConfig: async () => {
    const response = await axios.get(`${API_BASE_URL}/api/settings/trading`);
    return response.data;
  },

  // Update trading configuration
  updateTradingConfig: async (config: TradingConfig) => {
    const response = await axios.post(`${API_BASE_URL}/api/settings/trading`, config);
    return response.data;
  },

  // Get system information
  getSystemInfo: async (): Promise<SystemInfo> => {
    const response = await axios.get(`${API_BASE_URL}/api/settings/system-info`);
    return response.data;
  },
};
