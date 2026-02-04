import React, { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react';

// WebSocket Message Types
export enum MessageType {
  // Client to server
  SUBSCRIBE = 'subscribe',
  UNSUBSCRIBE = 'unsubscribe',
  PING = 'ping',
  
  // Server to client
  PRICE_UPDATE = 'price_update',
  ORDER_UPDATE = 'order_update',
  PORTFOLIO_UPDATE = 'portfolio_update',
  SYSTEM_ALERT = 'system_alert',
  ANALYSIS_UPDATE = 'analysis_update',
  PONG = 'pong',
  ERROR = 'error',
  SUBSCRIBED = 'subscribed',
  UNSUBSCRIBED = 'unsubscribed'
}

export enum SubscriptionType {
  PRICE_DATA = 'price_data',
  ORDER_UPDATES = 'order_updates',
  PORTFOLIO_UPDATES = 'portfolio_updates',
  SYSTEM_ALERTS = 'system_alerts',
  ANALYSIS_UPDATES = 'analysis_updates',
  ALL = 'all'
}

export interface WebSocketMessage {
  type: MessageType;
  data?: any;
  subscription?: string;
  timestamp: string;
}

export interface PriceUpdate {
  symbol: string;
  price: number;
  volume: number;
  change?: number;
  timestamp: string;
}

export interface OrderUpdate {
  order_id: string;
  symbol: string;
  side: string;
  quantity: number;
  price?: number;
  status: string;
  event_type: string;
  timestamp: string;
}

export interface PortfolioUpdate {
  total_value: number;
  available_balance: number;
  positions: any[];
  unrealized_pnl: number;
  timestamp: string;
}

export interface SystemAlert {
  level: 'error' | 'warning' | 'info';
  title: string;
  message: string;
  component?: string;
  event_type: string;
  timestamp: string;
}

export interface AnalysisUpdate {
  analysis_type: string;
  result: any;
  timestamp: string;
}

// Connection states
export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error'
}

// WebSocket Context Type
interface WebSocketContextType {
  // Connection state
  connectionState: ConnectionState;
  connectionId: string | null;
  
  // Real-time data
  latestPrice: PriceUpdate | null;
  latestOrder: OrderUpdate | null;
  latestPortfolio: PortfolioUpdate | null;
  systemAlerts: SystemAlert[];
  latestAnalysis: AnalysisUpdate | null;
  
  // Connection management
  connect: () => void;
  disconnect: () => void;
  
  // Subscription management
  subscribe: (subscriptionType: SubscriptionType) => void;
  unsubscribe: (subscriptionType: SubscriptionType) => void;
  subscriptions: Set<SubscriptionType>;
  
  // Message sending
  sendMessage: (message: WebSocketMessage) => void;
  ping: () => void;
  
  // Statistics
  messageCount: number;
  lastMessageTime: Date | null;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

// Provider Props
interface WebSocketProviderProps {
  children: ReactNode;
  url?: string;
  autoConnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({
  children,
  url = 'ws://localhost:8000/api/v1/ws/stream',
  autoConnect = true,
  reconnectInterval = 5000,
  maxReconnectAttempts = 10
}) => {
  // Connection state
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.DISCONNECTED);
  const [connectionId, setConnectionId] = useState<string | null>(null);
  
  // Real-time data state
  const [latestPrice, setLatestPrice] = useState<PriceUpdate | null>(null);
  const [latestOrder, setLatestOrder] = useState<OrderUpdate | null>(null);
  const [latestPortfolio, setLatestPortfolio] = useState<PortfolioUpdate | null>(null);
  const [systemAlerts, setSystemAlerts] = useState<SystemAlert[]>([]);
  const [latestAnalysis, setLatestAnalysis] = useState<AnalysisUpdate | null>(null);
  
  // Subscription management
  const [subscriptions, setSubscriptions] = useState<Set<SubscriptionType>>(new Set());
  
  // Statistics
  const [messageCount, setMessageCount] = useState(0);
  const [lastMessageTime, setLastMessageTime] = useState<Date | null>(null);
  
  // WebSocket and reconnection management
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isManualDisconnectRef = useRef(false);

  // Message handlers
  const handleMessage = (event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      setMessageCount(prev => prev + 1);
      setLastMessageTime(new Date());
      
      switch (message.type) {
        case MessageType.SUBSCRIBED:
          if (message.data?.connection_id) {
            setConnectionId(message.data.connection_id);
          }
          console.log('WebSocket subscribed:', message.data);
          break;
          
        case MessageType.PRICE_UPDATE:
          setLatestPrice(message.data as PriceUpdate);
          break;
          
        case MessageType.ORDER_UPDATE:
          setLatestOrder(message.data as OrderUpdate);
          break;
          
        case MessageType.PORTFOLIO_UPDATE:
          setLatestPortfolio(message.data as PortfolioUpdate);
          break;
          
        case MessageType.SYSTEM_ALERT:
          const alert = message.data as SystemAlert;
          setSystemAlerts(prev => {
            const newAlerts = [alert, ...prev];
            // Keep only last 50 alerts
            return newAlerts.slice(0, 50);
          });
          break;
          
        case MessageType.ANALYSIS_UPDATE:
          setLatestAnalysis(message.data as AnalysisUpdate);
          break;
          
        case MessageType.PONG:
          console.log('WebSocket pong received');
          break;
          
        case MessageType.ERROR:
          console.error('WebSocket error message:', message.data);
          break;
          
        default:
          console.log('Unknown WebSocket message type:', message.type);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  // Connection management
  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }
    
    isManualDisconnectRef.current = false;
    setConnectionState(ConnectionState.CONNECTING);
    
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionState(ConnectionState.CONNECTED);
        reconnectAttemptsRef.current = 0;
        
        // Clear any pending reconnection
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };
      
      ws.onmessage = handleMessage;
      
      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        setConnectionState(ConnectionState.DISCONNECTED);
        setConnectionId(null);
        
        // Attempt reconnection if not manually disconnected
        if (!isManualDisconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`Attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionState(ConnectionState.ERROR);
      };
      
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      setConnectionState(ConnectionState.ERROR);
    }
  };

  const disconnect = () => {
    isManualDisconnectRef.current = true;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setConnectionState(ConnectionState.DISCONNECTED);
    setConnectionId(null);
  };

  // Message sending
  const sendMessage = (message: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  };

  const ping = () => {
    sendMessage({
      type: MessageType.PING,
      timestamp: new Date().toISOString()
    });
  };

  // Subscription management
  const subscribe = (subscriptionType: SubscriptionType) => {
    sendMessage({
      type: MessageType.SUBSCRIBE,
      data: { subscription: subscriptionType },
      timestamp: new Date().toISOString()
    });
    
    setSubscriptions(prev => new Set([...prev, subscriptionType]));
  };

  const unsubscribe = (subscriptionType: SubscriptionType) => {
    sendMessage({
      type: MessageType.UNSUBSCRIBE,
      data: { subscription: subscriptionType },
      timestamp: new Date().toISOString()
    });
    
    setSubscriptions(prev => {
      const newSet = new Set(prev);
      newSet.delete(subscriptionType);
      return newSet;
    });
  };

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, []);

  // Ping interval to keep connection alive
  useEffect(() => {
    if (connectionState === ConnectionState.CONNECTED) {
      const pingInterval = setInterval(() => {
        ping();
      }, 30000); // Ping every 30 seconds
      
      return () => clearInterval(pingInterval);
    }
  }, [connectionState]);

  const contextValue: WebSocketContextType = {
    // Connection state
    connectionState,
    connectionId,
    
    // Real-time data
    latestPrice,
    latestOrder,
    latestPortfolio,
    systemAlerts,
    latestAnalysis,
    
    // Connection management
    connect,
    disconnect,
    
    // Subscription management
    subscribe,
    unsubscribe,
    subscriptions,
    
    // Message sending
    sendMessage,
    ping,
    
    // Statistics
    messageCount,
    lastMessageTime
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};

// Hook
export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};