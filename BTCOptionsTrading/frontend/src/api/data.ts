import apiClient from './client'
import type { GreeksRequest, GreeksResponse } from './types'
import { cacheManager } from '../utils/cache'

// 缓存配置
const CACHE_CONFIG = {
  optionsChain: {
    ttl: 5 * 60 * 1000, // 5分钟
    prefix: 'options_chain',
  },
  atmOptions: {
    ttl: 5 * 60 * 1000, // 5分钟
    prefix: 'atm_options',
  },
  strikeRange: {
    ttl: 5 * 60 * 1000, // 5分钟
    prefix: 'strike_range',
  },
  underlyingPrice: {
    ttl: 1 * 60 * 1000, // 1分钟
    prefix: 'underlying_price',
  },
  volatilitySurface: {
    ttl: 10 * 60 * 1000, // 10分钟
    prefix: 'volatility_surface',
  },
}

export const dataApi = {
  // 计算希腊字母
  calculateGreeks: async (data: GreeksRequest): Promise<GreeksResponse> => {
    const response = await apiClient.post('/api/data/calculate-greeks', data)
    return response.data
  },

  // 获取标的资产价格（带缓存）
  getUnderlyingPrice: async (symbol = 'BTC'): Promise<{ symbol: string; price: number; timestamp: string }> => {
    // 尝试从缓存获取
    const cached = cacheManager.get(
      CACHE_CONFIG.underlyingPrice.prefix,
      { symbol },
      CACHE_CONFIG.underlyingPrice.ttl
    )
    if (cached) {
      console.log(`[Cache Hit] Underlying price for ${symbol}`)
      return cached
    }

    // 从API获取
    const response = await apiClient.get(`/api/data/underlying-price/${symbol}`)
    const data = response.data

    // 存入缓存
    cacheManager.set(
      CACHE_CONFIG.underlyingPrice.prefix,
      data,
      { symbol },
      CACHE_CONFIG.underlyingPrice.ttl
    )

    return data
  },

  // 获取期权链（完整数据，带缓存）
  getOptionsChain: async (currency = 'BTC'): Promise<any[]> => {
    // 尝试从缓存获取
    const cached = cacheManager.get(
      CACHE_CONFIG.optionsChain.prefix,
      { currency },
      CACHE_CONFIG.optionsChain.ttl
    )
    if (cached) {
      console.log(`[Cache Hit] Options chain for ${currency}`)
      return cached
    }

    // 从API获取
    const response = await apiClient.get('/api/data/options-chain', {
      params: { currency },
    })
    const data = response.data

    // 存入缓存
    cacheManager.set(
      CACHE_CONFIG.optionsChain.prefix,
      data,
      { currency },
      CACHE_CONFIG.optionsChain.ttl
    )

    return data
  },

  // 获取ATM期权数据（轻量级，推荐用于策略创建）
  getATMOptions: async (
    currency = 'BTC',
    expiryDate?: string,
    numStrikes: number = 5
  ): Promise<any> => {
    // 尝试从缓存获取
    const cached = cacheManager.get(
      CACHE_CONFIG.atmOptions.prefix,
      { currency, expiryDate, numStrikes },
      CACHE_CONFIG.atmOptions.ttl
    )
    if (cached) {
      console.log(`[Cache Hit] ATM options for ${currency}`)
      return cached
    }

    // 从API获取
    const params: any = { currency, num_strikes: numStrikes }
    if (expiryDate) {
      params.expiry_date = expiryDate
    }

    const response = await apiClient.get('/api/options/atm', { params })
    const data = response.data

    // 存入缓存
    cacheManager.set(
      CACHE_CONFIG.atmOptions.prefix,
      data,
      { currency, expiryDate, numStrikes },
      CACHE_CONFIG.atmOptions.ttl
    )

    return data
  },

  // 获取执行价范围内的期权数据
  getStrikeRangeOptions: async (
    currency = 'BTC',
    expiryDate?: string,
    minStrike?: number,
    maxStrike?: number,
    numStrikes: number = 10
  ): Promise<any> => {
    // 尝试从缓存获取
    const cached = cacheManager.get(
      CACHE_CONFIG.strikeRange.prefix,
      { currency, expiryDate, minStrike, maxStrike, numStrikes },
      CACHE_CONFIG.strikeRange.ttl
    )
    if (cached) {
      console.log(`[Cache Hit] Strike range options for ${currency}`)
      return cached
    }

    // 从API获取
    const params: any = { currency, num_strikes: numStrikes }
    if (expiryDate) {
      params.expiry_date = expiryDate
    }
    if (minStrike !== undefined) {
      params.min_strike = minStrike
    }
    if (maxStrike !== undefined) {
      params.max_strike = maxStrike
    }

    const response = await apiClient.get('/api/options/strike-range', { params })
    const data = response.data

    // 存入缓存
    cacheManager.set(
      CACHE_CONFIG.strikeRange.prefix,
      data,
      { currency, expiryDate, minStrike, maxStrike, numStrikes },
      CACHE_CONFIG.strikeRange.ttl
    )

    return data
  },

  // 获取缓存中的执行价列表（不调用API）
  getCachedStrikes: async (currency = 'BTC', expiryDate?: string): Promise<any> => {
    const params: any = { currency }
    if (expiryDate) {
      params.expiry_date = expiryDate
    }

    const response = await apiClient.get('/api/options/cached-strikes', { params })
    return response.data
  },

  // 获取波动率曲面（带缓存）
  getVolatilitySurface: async (currency = 'BTC'): Promise<any> => {
    // 尝试从缓存获取
    const cached = cacheManager.get(
      CACHE_CONFIG.volatilitySurface.prefix,
      { currency },
      CACHE_CONFIG.volatilitySurface.ttl
    )
    if (cached) {
      console.log(`[Cache Hit] Volatility surface for ${currency}`)
      return cached
    }

    // 从API获取
    const response = await apiClient.get(`/api/data/volatility-surface/${currency}`)
    const data = response.data

    // 存入缓存
    cacheManager.set(
      CACHE_CONFIG.volatilitySurface.prefix,
      data,
      { currency },
      CACHE_CONFIG.volatilitySurface.ttl
    )

    return data
  },

  // 清除缓存
  clearCache: (type?: 'all' | 'optionsChain' | 'atmOptions' | 'strikeRange' | 'underlyingPrice' | 'volatilitySurface'): void => {
    if (!type || type === 'all') {
      cacheManager.clear()
      console.log('[Cache] Cleared all cache')
    } else if (type === 'optionsChain') {
      cacheManager.clear(CACHE_CONFIG.optionsChain.prefix)
      console.log('[Cache] Cleared options chain cache')
    } else if (type === 'atmOptions') {
      cacheManager.clear(CACHE_CONFIG.atmOptions.prefix)
      console.log('[Cache] Cleared ATM options cache')
    } else if (type === 'strikeRange') {
      cacheManager.clear(CACHE_CONFIG.strikeRange.prefix)
      console.log('[Cache] Cleared strike range cache')
    } else if (type === 'underlyingPrice') {
      cacheManager.clear(CACHE_CONFIG.underlyingPrice.prefix)
      console.log('[Cache] Cleared underlying price cache')
    } else if (type === 'volatilitySurface') {
      cacheManager.clear(CACHE_CONFIG.volatilitySurface.prefix)
      console.log('[Cache] Cleared volatility surface cache')
    }
  },

  // 获取缓存统计信息
  getCacheStats: () => {
    return cacheManager.getStats()
  },

  // 获取缓存命中率
  getCacheHitRate: () => {
    return cacheManager.getHitRate()
  },
}
