/**
 * WebSocket连接状态指示器
 */

import { useWebSocket } from '../hooks/useWebSocket'

const WebSocketIndicator = () => {
  const { isConnected, error } = useWebSocket({
    autoConnect: true
  })

  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center space-x-1">
        <div
          className={`w-2 h-2 rounded-full ${
            isConnected
              ? 'bg-accent-green animate-pulse'
              : error
              ? 'bg-accent-red'
              : 'bg-accent-yellow animate-pulse'
          }`}
        />
        <span className="text-xs text-text-secondary">
          {isConnected ? '实时' : error ? '断开' : '连接中...'}
        </span>
      </div>
    </div>
  )
}

export default WebSocketIndicator
