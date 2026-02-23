import { useState, useEffect } from 'react'
import { dataApi } from '../api/data'
import apiClient from '../api/client'

interface CacheStats {
  hits: number
  misses: number
  size: number
  entries: string[]
}

interface BackendCacheStats {
  total_entries: number
  valid_entries: number
  expired_entries: number
  ttl_seconds: number
}

const CacheManager = () => {
  const [frontendStats, setFrontendStats] = useState<CacheStats | null>(null)
  const [backendStats, setBackendStats] = useState<BackendCacheStats | null>(null)
  const [hitRate, setHitRate] = useState(0)
  const [isLoading, setIsLoading] = useState(false)

  // 刷新统计信息
  const refreshStats = async () => {
    try {
      setIsLoading(true)

      // 获取前端缓存统计
      const fStats = dataApi.getCacheStats()
      setFrontendStats(fStats)

      // 获取后端缓存统计
      const response = await apiClient.get('/api/data/cache/stats')
      setBackendStats(response.data.cache_stats)

      // 获取命中率
      const rate = dataApi.getCacheHitRate()
      setHitRate(rate)
    } catch (error) {
      console.error('Failed to refresh cache stats:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 清除前端缓存
  const clearFrontendCache = () => {
    if (confirm('确定要清除前端缓存吗？')) {
      dataApi.clearCache('all')
      refreshStats()
    }
  }

  // 清除后端缓存
  const clearBackendCache = async () => {
    if (confirm('确定要清除后端缓存吗？')) {
      try {
        await apiClient.delete('/api/data/cache/clear')
        refreshStats()
      } catch (error) {
        console.error('Failed to clear backend cache:', error)
      }
    }
  }

  // 清理过期缓存
  const cleanupExpiredCache = async () => {
    try {
      const response = await apiClient.post('/api/data/cache/cleanup')
      alert(response.data.message)
      refreshStats()
    } catch (error) {
      console.error('Failed to cleanup cache:', error)
    }
  }

  // 初始化时加载统计
  useEffect(() => {
    refreshStats()
    // 每30秒自动刷新一次
    const interval = setInterval(refreshStats, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="bg-bg-secondary rounded-lg p-4 border border-border-primary">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">缓存管理</h3>
        <button
          onClick={refreshStats}
          disabled={isLoading}
          className="px-3 py-1 bg-primary text-white rounded hover:bg-primary-dark disabled:opacity-50"
        >
          {isLoading ? '刷新中...' : '刷新'}
        </button>
      </div>

      {/* 前端缓存统计 */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-text-secondary mb-2">前端缓存</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="bg-bg-primary p-2 rounded">
            <div className="text-text-secondary">缓存命中</div>
            <div className="text-lg font-bold text-success">{frontendStats?.hits || 0}</div>
          </div>
          <div className="bg-bg-primary p-2 rounded">
            <div className="text-text-secondary">缓存未命中</div>
            <div className="text-lg font-bold text-warning">{frontendStats?.misses || 0}</div>
          </div>
          <div className="bg-bg-primary p-2 rounded">
            <div className="text-text-secondary">命中率</div>
            <div className="text-lg font-bold text-info">{hitRate.toFixed(1)}%</div>
          </div>
          <div className="bg-bg-primary p-2 rounded">
            <div className="text-text-secondary">缓存条目</div>
            <div className="text-lg font-bold text-primary">{frontendStats?.size || 0}</div>
          </div>
        </div>
      </div>

      {/* 后端缓存统计 */}
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-text-secondary mb-2">后端缓存</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="bg-bg-primary p-2 rounded">
            <div className="text-text-secondary">有效条目</div>
            <div className="text-lg font-bold text-success">{backendStats?.valid_entries || 0}</div>
          </div>
          <div className="bg-bg-primary p-2 rounded">
            <div className="text-text-secondary">过期条目</div>
            <div className="text-lg font-bold text-warning">{backendStats?.expired_entries || 0}</div>
          </div>
          <div className="bg-bg-primary p-2 rounded">
            <div className="text-text-secondary">总条目</div>
            <div className="text-lg font-bold text-primary">{backendStats?.total_entries || 0}</div>
          </div>
          <div className="bg-bg-primary p-2 rounded">
            <div className="text-text-secondary">TTL</div>
            <div className="text-lg font-bold text-info">{backendStats?.ttl_seconds || 0}s</div>
          </div>
        </div>
      </div>

      {/* 缓存条目列表 */}
      {frontendStats && frontendStats.entries.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-text-secondary mb-2">缓存条目</h4>
          <div className="bg-bg-primary rounded p-2 max-h-32 overflow-y-auto">
            <ul className="text-xs text-text-secondary space-y-1">
              {frontendStats.entries.map((entry, index) => (
                <li key={index} className="truncate">
                  • {entry}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* 操作按钮 */}
      <div className="flex gap-2">
        <button
          onClick={clearFrontendCache}
          className="flex-1 px-3 py-2 bg-warning text-white rounded text-sm hover:bg-warning-dark"
        >
          清除前端缓存
        </button>
        <button
          onClick={clearBackendCache}
          className="flex-1 px-3 py-2 bg-warning text-white rounded text-sm hover:bg-warning-dark"
        >
          清除后端缓存
        </button>
        <button
          onClick={cleanupExpiredCache}
          className="flex-1 px-3 py-2 bg-info text-white rounded text-sm hover:bg-info-dark"
        >
          清理过期
        </button>
      </div>

      {/* 缓存说明 */}
      <div className="mt-4 p-2 bg-bg-primary rounded text-xs text-text-secondary">
        <p className="mb-1">
          <strong>缓存策略：</strong>
        </p>
        <ul className="list-disc list-inside space-y-1">
          <li>期权链数据：5分钟缓存</li>
          <li>标的价格：1分钟缓存</li>
          <li>波动率曲面：10分钟缓存</li>
          <li>自动清理过期条目</li>
        </ul>
      </div>
    </div>
  )
}

export default CacheManager
