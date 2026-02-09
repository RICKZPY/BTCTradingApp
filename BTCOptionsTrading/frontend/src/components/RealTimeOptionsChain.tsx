/**
 * 实时期权链组件
 * 使用WebSocket接收实时期权链更新
 */

import { useEffect, useState } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import LoadingSpinner from './LoadingSpinner'

interface OptionData {
  instrument_name: string
  strike: number
  mark_price: number
  implied_volatility: number
  delta: number
  gamma?: number
  theta?: number
  vega?: number
}

interface RealTimeOptionsChainProps {
  currency?: string
  maxOptions?: number
}

const RealTimeOptionsChain = ({ 
  currency = 'BTC',
  maxOptions = 10
}: RealTimeOptionsChainProps) => {
  const [options, setOptions] = useState<OptionData[]>([])
  const [lastUpdate, setLastUpdate] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  
  const { isConnected, subscribe, unsubscribe, lastMessage } = useWebSocket({
    autoConnect: true
  })

  useEffect(() => {
    // 订阅期权链数据
    subscribe('options_chain')
    
    return () => {
      unsubscribe('options_chain')
    }
  }, [subscribe, unsubscribe])

  useEffect(() => {
    if (lastMessage?.type === 'options_chain') {
      const optionsData = lastMessage.data?.options
      
      if (Array.isArray(optionsData)) {
        setOptions(optionsData.slice(0, maxOptions))
        setLastUpdate(new Date().toLocaleTimeString('zh-CN'))
        setIsLoading(false)
      }
    }
  }, [lastMessage, maxOptions])

  if (!isConnected) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <div className="w-3 h-3 rounded-full bg-accent-yellow animate-pulse mx-auto mb-2" />
            <p className="text-text-secondary">WebSocket连接中...</p>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-8">
          <div className="text-center">
            <LoadingSpinner />
            <p className="text-text-secondary mt-2">等待期权链数据...</p>
          </div>
        </div>
      </div>
    )
  }

  if (options.length === 0) {
    return (
      <div className="card">
        <div className="text-center py-8 text-text-secondary">
          暂无期权数据
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-text-primary">
          实时期权链 - {currency}
        </h3>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
          <span className="text-xs text-text-secondary">
            最后更新: {lastUpdate}
          </span>
        </div>
      </div>

      {/* 期权表格 */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-text-disabled">
              <th className="text-left py-2 px-3 text-text-secondary text-xs font-medium">
                合约
              </th>
              <th className="text-right py-2 px-3 text-text-secondary text-xs font-medium">
                执行价
              </th>
              <th className="text-right py-2 px-3 text-text-secondary text-xs font-medium">
                标记价格
              </th>
              <th className="text-right py-2 px-3 text-text-secondary text-xs font-medium">
                隐含波动率
              </th>
              <th className="text-right py-2 px-3 text-text-secondary text-xs font-medium">
                Delta
              </th>
            </tr>
          </thead>
          <tbody>
            {options.map((option, index) => (
              <tr 
                key={option.instrument_name || index}
                className="border-b border-text-disabled hover:bg-bg-secondary transition-colors"
              >
                <td className="py-2 px-3 text-text-primary text-sm font-mono">
                  {option.instrument_name}
                </td>
                <td className="py-2 px-3 text-right text-text-primary text-sm font-mono">
                  ${option.strike?.toLocaleString()}
                </td>
                <td className="py-2 px-3 text-right text-accent-blue text-sm font-mono">
                  ${option.mark_price?.toFixed(2)}
                </td>
                <td className="py-2 px-3 text-right text-text-primary text-sm font-mono">
                  {(option.implied_volatility * 100)?.toFixed(1)}%
                </td>
                <td className="py-2 px-3 text-right text-text-primary text-sm font-mono">
                  {option.delta?.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* 说明 */}
      <div className="mt-4 text-xs text-text-disabled">
        <p>💡 数据每10秒自动更新</p>
        <p>💡 显示前{maxOptions}个期权合约</p>
      </div>
    </div>
  )
}

export default RealTimeOptionsChain
