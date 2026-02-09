/**
 * 实时价格显示组件
 * 使用WebSocket接收实时BTC价格更新
 */

import { useEffect, useState } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'

interface RealTimePriceDisplayProps {
  symbol?: string
  className?: string
}

const RealTimePriceDisplay = ({ 
  symbol = 'BTC',
  className = ''
}: RealTimePriceDisplayProps) => {
  const [price, setPrice] = useState<number | null>(null)
  const [priceChange, setPriceChange] = useState<'up' | 'down' | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string>('')
  
  const { isConnected, subscribe, unsubscribe, lastMessage } = useWebSocket({
    autoConnect: true
  })

  useEffect(() => {
    // 订阅市场数据
    subscribe('market_data')
    
    return () => {
      unsubscribe('market_data')
    }
  }, [subscribe, unsubscribe])

  useEffect(() => {
    if (lastMessage?.type === 'market_data') {
      const newPrice = lastMessage.data?.price
      
      if (typeof newPrice === 'number') {
        // 检测价格变化方向
        if (price !== null) {
          setPriceChange(newPrice > price ? 'up' : newPrice < price ? 'down' : null)
          
          // 2秒后清除变化指示
          setTimeout(() => setPriceChange(null), 2000)
        }
        
        setPrice(newPrice)
        setLastUpdate(new Date().toLocaleTimeString('zh-CN'))
      }
    }
  }, [lastMessage, price])

  if (!isConnected) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="w-2 h-2 rounded-full bg-accent-yellow animate-pulse" />
        <span className="text-text-secondary text-sm">连接中...</span>
      </div>
    )
  }

  if (price === null) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
        <span className="text-text-secondary text-sm">等待数据...</span>
      </div>
    )
  }

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* 连接状态指示器 */}
      <div className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
      
      {/* 价格显示 */}
      <div className="flex items-center space-x-2">
        <span className="text-text-secondary text-sm">{symbol}:</span>
        <span 
          className={`text-xl font-bold font-mono transition-colors duration-300 ${
            priceChange === 'up' 
              ? 'text-accent-green' 
              : priceChange === 'down' 
              ? 'text-accent-red' 
              : 'text-text-primary'
          }`}
        >
          ${price.toLocaleString('en-US', { 
            minimumFractionDigits: 2,
            maximumFractionDigits: 2 
          })}
        </span>
        
        {/* 价格变化箭头 */}
        {priceChange && (
          <span className={`text-sm ${
            priceChange === 'up' ? 'text-accent-green' : 'text-accent-red'
          }`}>
            {priceChange === 'up' ? '↑' : '↓'}
          </span>
        )}
      </div>
      
      {/* 最后更新时间 */}
      <span className="text-xs text-text-disabled">
        {lastUpdate}
      </span>
    </div>
  )
}

export default RealTimePriceDisplay
