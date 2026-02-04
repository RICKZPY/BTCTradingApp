import React, { useState, useEffect } from 'react';
import { useApi } from '../contexts/ApiContext';
import { useWebSocket, SubscriptionType } from '../contexts/WebSocketContext';

interface ManualTradingPanelProps {
  onOrderPlaced?: (order: any) => void;
}

const ManualTradingPanel: React.FC<ManualTradingPanelProps> = ({ onOrderPlaced }) => {
  const { api } = useApi();
  const { latestPrice, subscribe, subscriptions } = useWebSocket();
  
  const [orderForm, setOrderForm] = useState({
    symbol: 'BTCUSDT',
    side: 'BUY' as 'BUY' | 'SELL',
    type: 'MARKET' as 'MARKET' | 'LIMIT',
    quantity: '',
    price: '',
    stopLoss: '',
    takeProfit: ''
  });
  
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [estimatedCost, setEstimatedCost] = useState<number>(0);

  // Subscribe to price updates
  useEffect(() => {
    if (!subscriptions.has(SubscriptionType.PRICE_DATA)) {
      subscribe(SubscriptionType.PRICE_DATA);
    }
  }, [subscribe, subscriptions]);

  // Update current price
  useEffect(() => {
    if (latestPrice && latestPrice.symbol === orderForm.symbol) {
      setCurrentPrice(latestPrice.price);
      if (orderForm.type === 'LIMIT' && !orderForm.price) {
        setOrderForm(prev => ({ ...prev, price: latestPrice.price.toString() }));
      }
    }
  }, [latestPrice, orderForm.symbol, orderForm.type]);

  // Calculate estimated cost
  useEffect(() => {
    const quantity = parseFloat(orderForm.quantity) || 0;
    const price = orderForm.type === 'MARKET' ? currentPrice : parseFloat(orderForm.price) || 0;
    setEstimatedCost(quantity * price);
  }, [orderForm.quantity, orderForm.price, orderForm.type, currentPrice]);

  const handleFormChange = (field: string, value: string) => {
    setOrderForm(prev => ({ ...prev, [field]: value }));
    setError(null);
    setSuccess(null);
  };

  const handleQuickQuantity = (percentage: number) => {
    // This would normally calculate based on available balance
    // For demo purposes, we'll use a mock calculation
    const mockBalance = 10000; // $10,000 USD
    const price = orderForm.type === 'MARKET' ? currentPrice : parseFloat(orderForm.price) || currentPrice;
    const quantity = (mockBalance * percentage / 100) / price;
    setOrderForm(prev => ({ ...prev, quantity: quantity.toFixed(8) }));
  };

  const validateOrder = (): string | null => {
    if (!orderForm.quantity || parseFloat(orderForm.quantity) <= 0) {
      return '请输入有效的数量';
    }
    
    if (orderForm.type === 'LIMIT' && (!orderForm.price || parseFloat(orderForm.price) <= 0)) {
      return '限价单需要输入有效的价格';
    }
    
    if (estimatedCost <= 0) {
      return '订单金额必须大于0';
    }
    
    return null;
  };

  const handleSubmitOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validationError = validateOrder();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setSuccess(null);

      const orderData = {
        symbol: orderForm.symbol,
        side: orderForm.side,
        type: orderForm.type,
        quantity: parseFloat(orderForm.quantity),
        ...(orderForm.type === 'LIMIT' && { price: parseFloat(orderForm.price) })
      };

      const response = await api.placeOrder(orderData);
      
      if (response.success) {
        setSuccess(`${orderForm.side} 订单已成功提交`);
        
        // Reset form
        setOrderForm(prev => ({
          ...prev,
          quantity: '',
          price: prev.type === 'LIMIT' ? prev.price : '',
          stopLoss: '',
          takeProfit: ''
        }));
        
        if (onOrderPlaced) {
          onOrderPlaced(response.data);
        }
      } else {
        setError(response.message || '订单提交失败');
      }
    } catch (err: any) {
      console.error('Error placing order:', err);
      setError(err.response?.data?.message || '订单提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">手动交易控制面板</h3>
        <div className="text-sm text-gray-600">
          当前价格: {formatCurrency(currentPrice)}
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
          <div className="text-red-800 text-sm">{error}</div>
        </div>
      )}
      
      {success && (
        <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-3">
          <div className="text-green-800 text-sm">{success}</div>
        </div>
      )}

      <form onSubmit={handleSubmitOrder} className="space-y-4">
        {/* Symbol and Side */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              交易对
            </label>
            <select
              value={orderForm.symbol}
              onChange={(e) => handleFormChange('symbol', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="BTCUSDT">BTC/USDT</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              交易方向
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => handleFormChange('side', 'BUY')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  orderForm.side === 'BUY'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                买入
              </button>
              <button
                type="button"
                onClick={() => handleFormChange('side', 'SELL')}
                className={`px-3 py-2 rounded-md text-sm font-medium ${
                  orderForm.side === 'SELL'
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                卖出
              </button>
            </div>
          </div>
        </div>

        {/* Order Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            订单类型
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleFormChange('type', 'MARKET')}
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                orderForm.type === 'MARKET'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              市价单
            </button>
            <button
              type="button"
              onClick={() => handleFormChange('type', 'LIMIT')}
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                orderForm.type === 'LIMIT'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              限价单
            </button>
          </div>
        </div>

        {/* Quantity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            数量 (BTC)
          </label>
          <input
            type="number"
            step="0.00000001"
            min="0"
            value={orderForm.quantity}
            onChange={(e) => handleFormChange('quantity', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="0.00000000"
          />
          
          {/* Quick quantity buttons */}
          <div className="mt-2 flex space-x-2">
            {[25, 50, 75, 100].map(percentage => (
              <button
                key={percentage}
                type="button"
                onClick={() => handleQuickQuantity(percentage)}
                className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                {percentage}%
              </button>
            ))}
          </div>
        </div>

        {/* Price (for limit orders) */}
        {orderForm.type === 'LIMIT' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              价格 (USDT)
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={orderForm.price}
              onChange={(e) => handleFormChange('price', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="0.00"
            />
          </div>
        )}

        {/* Advanced Options */}
        <div className="border-t pt-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">高级选项</h4>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                止损价格 (USDT)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={orderForm.stopLoss}
                onChange={(e) => handleFormChange('stopLoss', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="可选"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                止盈价格 (USDT)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={orderForm.takeProfit}
                onChange={(e) => handleFormChange('takeProfit', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="可选"
              />
            </div>
          </div>
        </div>

        {/* Order Summary */}
        <div className="bg-gray-50 rounded-md p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">订单摘要</h4>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">交易对:</span>
              <span className="font-medium">{orderForm.symbol}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">方向:</span>
              <span className={`font-medium ${
                orderForm.side === 'BUY' ? 'text-green-600' : 'text-red-600'
              }`}>
                {orderForm.side === 'BUY' ? '买入' : '卖出'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">类型:</span>
              <span className="font-medium">
                {orderForm.type === 'MARKET' ? '市价单' : '限价单'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">数量:</span>
              <span className="font-medium">{orderForm.quantity || '0'} BTC</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">预估成本:</span>
              <span className="font-medium">{formatCurrency(estimatedCost)}</span>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={submitting || !orderForm.quantity}
          className={`w-full px-4 py-3 rounded-md text-white font-medium ${
            orderForm.side === 'BUY'
              ? 'bg-green-600 hover:bg-green-700'
              : 'bg-red-600 hover:bg-red-700'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {submitting ? '提交中...' : `${orderForm.side === 'BUY' ? '买入' : '卖出'} ${orderForm.symbol}`}
        </button>
      </form>
    </div>
  );
};

export default ManualTradingPanel;