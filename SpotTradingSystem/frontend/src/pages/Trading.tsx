import React, { useEffect, useState } from 'react';
import { useApi, TradingOrder } from '../contexts/ApiContext';
import { useWebSocket, SubscriptionType } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';

interface OrderFormData {
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT';
  quantity: string;
  price: string;
}

const TradingPage: React.FC = () => {
  const { api } = useApi();
  const { t } = useLanguage();
  const { 
    latestOrder, 
    latestPrice,
    subscribe,
    subscriptions 
  } = useWebSocket();
  
  const [orders, setOrders] = useState<TradingOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [autoTradingStatus, setAutoTradingStatus] = useState<any>(null);
  
  const [orderForm, setOrderForm] = useState<OrderFormData>({
    symbol: 'BTCUSDT',
    side: 'BUY',
    type: 'MARKET',
    quantity: '',
    price: ''
  });

  // Subscribe to real-time updates
  useEffect(() => {
    if (!subscriptions.has(SubscriptionType.ORDER_UPDATES)) {
      subscribe(SubscriptionType.ORDER_UPDATES);
    }
    if (!subscriptions.has(SubscriptionType.PRICE_DATA)) {
      subscribe(SubscriptionType.PRICE_DATA);
    }
  }, [subscribe, subscriptions]);

  // Load order history
  const loadOrders = async () => {
    try {
      setError(null);
      const response = await api.getOrderHistory({ limit: 50 });
      setOrders(response.data?.orders || []);
    } catch (err) {
      console.error('Error loading orders:', err);
      setError('Failed to load order history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
    loadAutoTradingStatus();
  }, [api]);

  // Load auto trading status
  const loadAutoTradingStatus = async () => {
    try {
      const response = await api.getAutoTradingStatus();
      if (response.success) {
        setAutoTradingStatus(response.data);
      }
    } catch (err) {
      console.error('Error loading auto trading status:', err);
    }
  };

  // Update orders from real-time data
  useEffect(() => {
    if (latestOrder) {
      setOrders(prev => {
        const existingIndex = prev.findIndex(order => order.order_id === latestOrder.order_id);
        if (existingIndex >= 0) {
          // Update existing order
          const updated = [...prev];
          updated[existingIndex] = {
            ...updated[existingIndex],
            status: latestOrder.status,
            filled_quantity: latestOrder.quantity,
            updated_at: latestOrder.timestamp
          };
          return updated;
        } else {
          // Add new order
          const newOrder: TradingOrder = {
            order_id: latestOrder.order_id,
            symbol: latestOrder.symbol,
            side: latestOrder.side as 'BUY' | 'SELL',
            type: 'MARKET', // Default, could be enhanced
            quantity: latestOrder.quantity,
            price: latestOrder.price,
            status: latestOrder.status,
            filled_quantity: latestOrder.quantity,
            created_at: latestOrder.timestamp,
            updated_at: latestOrder.timestamp
          };
          return [newOrder, ...prev];
        }
      });
    }
  }, [latestOrder]);

  // Update current price in form
  useEffect(() => {
    if (latestPrice && latestPrice.symbol === orderForm.symbol && orderForm.type === 'LIMIT') {
      setOrderForm(prev => ({
        ...prev,
        price: latestPrice.price.toString()
      }));
    }
  }, [latestPrice, orderForm.symbol, orderForm.type]);

  const handleFormChange = (field: keyof OrderFormData, value: string) => {
    setOrderForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmitOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!orderForm.quantity || parseFloat(orderForm.quantity) <= 0) {
      setError(t('trading.valid_quantity'));
      return;
    }
    
    if (orderForm.type === 'LIMIT' && (!orderForm.price || parseFloat(orderForm.price) <= 0)) {
      setError(t('trading.valid_price'));
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const orderData = {
        symbol: orderForm.symbol,
        side: orderForm.side,
        type: orderForm.type,
        quantity: parseFloat(orderForm.quantity),
        ...(orderForm.type === 'LIMIT' && { price: parseFloat(orderForm.price) })
      };

      const response = await api.placeOrder(orderData);
      
      if (response.success) {
        // Reset form
        setOrderForm(prev => ({
          ...prev,
          quantity: '',
          price: prev.type === 'LIMIT' ? prev.price : ''
        }));
        
        // Reload orders
        loadOrders();
      } else {
        setError(response.message || t('common.error'));
      }
    } catch (err: any) {
      console.error('Error placing order:', err);
      setError(err.response?.data?.message || t('common.error'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      const response = await api.cancelOrder(orderId);
      if (response.success) {
        loadOrders();
      } else {
        setError(response.message || 'Failed to cancel order');
      }
    } catch (err: any) {
      console.error('Error canceling order:', err);
      setError(err.response?.data?.message || 'Failed to cancel order');
    }
  };

  const toggleAutoTrading = async () => {
    try {
      const newStatus = !autoTradingStatus?.enabled;
      const response = await api.toggleAutoTrading(newStatus);
      
      if (response.success) {
        setAutoTradingStatus((prev: any) => ({
          ...prev,
          enabled: newStatus
        }));
      }
    } catch (err) {
      console.error('Error toggling auto trading:', err);
      setError('Failed to toggle auto trading');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatQuantity = (value: number) => {
    return value.toFixed(8);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'filled':
        return 'bg-green-100 text-green-800';
      case 'pending':
      case 'new':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      case 'failed':
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('trading.title')}</h1>
        <p className="text-gray-600">{t('trading.subtitle')}</p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {/* Auto Trading Status */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">{t('trading.auto_trading')}</h2>
          <button
            onClick={toggleAutoTrading}
            className={`px-4 py-2 rounded-md text-white font-medium ${
              autoTradingStatus?.enabled 
                ? 'bg-red-600 hover:bg-red-700' 
                : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {autoTradingStatus?.enabled ? t('trading.disable_auto') : t('trading.enable_auto')}
          </button>
        </div>
        
        {autoTradingStatus && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="text-sm text-gray-600">{t('trading.status')}:</span>
              <div className={`font-semibold ${
                autoTradingStatus.enabled ? 'text-green-600' : 'text-red-600'
              }`}>
                {autoTradingStatus.enabled ? 'ENABLED' : 'DISABLED'}
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">{t('trading.strategy')}:</span>
              <div className="font-semibold text-gray-900">{autoTradingStatus.strategy}</div>
            </div>
            <div>
              <span className="text-sm text-gray-600">{t('trading.last_signal')}:</span>
              <div className="font-semibold text-gray-900">{autoTradingStatus.last_signal}</div>
            </div>
            <div>
              <span className="text-sm text-gray-600">{t('trading.todays_trades')}:</span>
              <div className="font-semibold text-gray-900">{autoTradingStatus.total_trades_today}</div>
            </div>
          </div>
        )}
        
        {autoTradingStatus?.note && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <p className="text-sm text-yellow-800">{autoTradingStatus.note}</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Order Form */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('trading.place_order')}</h2>
            
            <form onSubmit={handleSubmitOrder} className="space-y-4">
              {/* Symbol */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('trading.symbol')}
                </label>
                <select
                  value={orderForm.symbol}
                  onChange={(e) => handleFormChange('symbol', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="BTCUSDT">BTC/USDT</option>
                </select>
              </div>

              {/* Side */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('trading.side')}
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
                    {t('trading.buy')}
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
                    {t('trading.sell')}
                  </button>
                </div>
              </div>

              {/* Order Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('trading.order_type')}
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
                    {t('trading.market')}
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
                    {t('trading.limit')}
                  </button>
                </div>
              </div>

              {/* Quantity */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('trading.quantity')} (BTC)
                </label>
                <input
                  type="number"
                  step="0.00000001"
                  min="0"
                  value={orderForm.quantity}
                  onChange={(e) => handleFormChange('quantity', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00000000"
                  required
                />
              </div>

              {/* Price (for limit orders) */}
              {orderForm.type === 'LIMIT' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('trading.price')} (USDT)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={orderForm.price}
                    onChange={(e) => handleFormChange('price', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="0.00"
                    required
                  />
                </div>
              )}

              {/* Current Price Display */}
              {latestPrice && latestPrice.symbol === orderForm.symbol && (
                <div className="text-sm text-gray-600">
                  {t('trading.current_price')}: {formatCurrency(latestPrice.price)}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={submitting}
                className={`w-full px-4 py-2 rounded-md text-white font-medium ${
                  orderForm.side === 'BUY'
                    ? 'bg-green-600 hover:bg-green-700'
                    : 'bg-red-600 hover:bg-red-700'
                } disabled:opacity-50`}
              >
                {submitting ? t('trading.placing_order') : `${t(`trading.${orderForm.side.toLowerCase()}`)} ${orderForm.symbol}`}
              </button>
            </form>
          </div>
        </div>

        {/* Order History */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">{t('trading.order_history')}</h2>
            </div>
            
            {loading ? (
              <div className="p-6 text-center text-gray-600">
                {t('trading.loading_orders')}
              </div>
            ) : orders.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                {t('trading.no_orders')}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('trading.order_id')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('trading.symbol')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('trading.side')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('trading.order_type')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('trading.quantity')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('trading.price')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('trading.status')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('trading.created')}
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {t('trading.actions')}
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {orders.map((order) => (
                      <tr key={order.order_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                          {order.order_id.slice(-8)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {order.symbol}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            order.side === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {order.side}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {order.type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatQuantity(order.quantity)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {order.price ? formatCurrency(order.price) : 'Market'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(order.status)}`}>
                            {order.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(order.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {(order.status === 'NEW' || order.status === 'PENDING') && (
                            <button
                              onClick={() => handleCancelOrder(order.order_id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              {t('trading.cancel')}
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingPage;