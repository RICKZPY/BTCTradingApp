/**
 * 前端缓存管理工具
 * 用于缓存期权链数据，避免频繁的API调用
 */

import React from 'react'

interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number // 缓存有效期（毫秒）
}

interface CacheStats {
  hits: number
  misses: number
  size: number
  entries: string[]
}

class CacheManager {
  private cache: Map<string, CacheEntry<any>> = new Map()
  private stats = {
    hits: 0,
    misses: 0,
  }

  /**
   * 生成缓存键
   */
  private generateKey(prefix: string, params: Record<string, any>): string {
    const sortedParams = Object.keys(params)
      .sort()
      .map(key => `${key}=${JSON.stringify(params[key])}`)
      .join('&')
    return `${prefix}:${sortedParams}`
  }

  /**
   * 检查缓存是否过期
   */
  private isExpired(entry: CacheEntry<any>): boolean {
    return Date.now() - entry.timestamp > entry.ttl
  }

  /**
   * 获取缓存数据
   */
  get<T>(prefix: string, params: Record<string, any> = {}, ttl: number = 5 * 60 * 1000): T | null {
    const key = this.generateKey(prefix, params)
    const entry = this.cache.get(key)

    if (!entry) {
      this.stats.misses++
      return null
    }

    if (this.isExpired(entry)) {
      this.cache.delete(key)
      this.stats.misses++
      return null
    }

    this.stats.hits++
    return entry.data as T
  }

  /**
   * 设置缓存数据
   */
  set<T>(prefix: string, data: T, params: Record<string, any> = {}, ttl: number = 5 * 60 * 1000): void {
    const key = this.generateKey(prefix, params)
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    })
  }

  /**
   * 清除特定前缀的缓存
   */
  clear(prefix?: string): void {
    if (!prefix) {
      this.cache.clear()
      return
    }

    const keysToDelete: string[] = []
    this.cache.forEach((_, key) => {
      if (key.startsWith(`${prefix}:`)) {
        keysToDelete.push(key)
      }
    })

    keysToDelete.forEach(key => this.cache.delete(key))
  }

  /**
   * 获取缓存统计信息
   */
  getStats(): CacheStats {
    const entries: string[] = []
    this.cache.forEach((entry, key) => {
      if (!this.isExpired(entry)) {
        entries.push(key)
      }
    })

    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      size: this.cache.size,
      entries,
    }
  }

  /**
   * 重置统计信息
   */
  resetStats(): void {
    this.stats.hits = 0
    this.stats.misses = 0
  }

  /**
   * 获取缓存命中率
   */
  getHitRate(): number {
    const total = this.stats.hits + this.stats.misses
    return total === 0 ? 0 : (this.stats.hits / total) * 100
  }
}

// 导出单例
export const cacheManager = new CacheManager()

/**
 * 缓存装饰器（用于函数）
 */
export function withCache<T>(
  prefix: string,
  ttl: number = 5 * 60 * 1000
) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value

    descriptor.value = async function (...args: any[]) {
      // 生成缓存参数
      const params = args.reduce((acc, arg, index) => {
        acc[`arg${index}`] = arg
        return acc
      }, {})

      // 尝试从缓存获取
      const cached = cacheManager.get(prefix, params, ttl)
      if (cached !== null) {
        console.log(`[Cache Hit] ${prefix}`)
        return cached
      }

      // 调用原始方法
      const result = await originalMethod.apply(this, args)

      // 存入缓存
      cacheManager.set(prefix, result, params, ttl)
      console.log(`[Cache Set] ${prefix}`)

      return result
    }

    return descriptor
  }
}

/**
 * React Hook: 使用缓存的异步数据
 */
export function useCachedData<T>(
  fetchFn: () => Promise<T>,
  cachePrefix: string,
  cacheParams: Record<string, any> = {},
  ttl: number = 5 * 60 * 1000,
  dependencies: any[] = []
) {
  const [data, setData] = React.useState<T | null>(null)
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<Error | null>(null)

  React.useEffect(() => {
    const loadData = async () => {
      // 尝试从缓存获取
      const cached = cacheManager.get<T>(cachePrefix, cacheParams, ttl)
      if (cached !== null) {
        setData(cached)
        return
      }

      // 从API获取
      try {
        setLoading(true)
        setError(null)
        const result = await fetchFn()
        setData(result)
        cacheManager.set(cachePrefix, result, cacheParams, ttl)
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Unknown error'))
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, dependencies)

  return { data, loading, error }
}

export default cacheManager
