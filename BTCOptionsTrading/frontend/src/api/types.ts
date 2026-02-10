// API类型定义

export interface Strategy {
  id: string
  name: string
  description?: string
  strategy_type: string
  max_profit?: number
  max_loss?: number
  created_at: string
  legs?: StrategyLeg[]
  // 风险指标
  breakeven_points?: number[]
  greeks?: {
    delta: number
    gamma: number
    theta: number
    vega: number
    rho: number
  }
  initial_cost?: number
  risk_reward_ratio?: number
}

export interface OptionContract {
  instrument_name: string
  underlying: string
  option_type: 'call' | 'put'
  strike_price: number
  expiration_date: string
}

export interface StrategyLeg {
  option_contract: OptionContract
  action: 'buy' | 'sell'
  quantity: number
}

export interface CreateStrategyRequest {
  name: string
  description?: string
  strategy_type: string
  legs: StrategyLeg[]
}

export interface BacktestRequest {
  strategy_id: string
  start_date: string
  end_date: string
  initial_capital: number
  underlying_symbol?: string
}

export interface BacktestResult {
  id: string
  strategy_id: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital: number
  total_return: number
  sharpe_ratio?: number
  max_drawdown?: number
  win_rate?: number
  total_trades: number
  created_at: string
}

export interface Trade {
  timestamp: string
  action: string
  instrument_name: string
  quantity: number
  price: number
  pnl?: number
  portfolio_value?: number
}

export interface DailyPnL {
  date: string
  portfolio_value: number
  daily_pnl: number
  cumulative_pnl: number
}

export interface GreeksRequest {
  spot_price: number
  strike_price: number
  time_to_expiry: number
  volatility: number
  risk_free_rate?: number
  option_type: 'call' | 'put'
}

export interface GreeksResponse {
  delta: number
  gamma: number
  theta: number
  vega: number
  rho: number
  price: number
}

export interface StrategyTemplate {
  type: string
  name: string
  description: string
}
