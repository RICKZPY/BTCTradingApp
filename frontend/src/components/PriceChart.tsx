import React, { useEffect, useRef, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  ChartOptions,
  ChartData
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import { useApi } from '../contexts/ApiContext';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface PriceDataPoint {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface PriceChartProps {
  symbol?: string;
  height?: number;
  maxDataPoints?: number;
  showVolume?: boolean;
}

const PriceChart: React.FC<PriceChartProps> = ({
  symbol = 'BTCUSDT',
  height = 400,
  maxDataPoints = 100,
  showVolume = false
}) => {
  const { api } = useApi();
  const [priceData, setPriceData] = useState<PriceDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<ChartJS<'line'>>(null);

  // Load real kline data from API
  useEffect(() => {
    const loadKlineData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Get 24 hours of 1-hour klines for the chart
        const response = await api.getKlineData(symbol, '1h', 24);
        
        if (response.success && response.data.klines) {
          setPriceData(response.data.klines);
        } else {
          throw new Error('Failed to load kline data');
        }
      } catch (err) {
        console.error('Error loading kline data:', err);
        setError('Failed to load price data');
      } finally {
        setLoading(false);
      }
    };

    loadKlineData();
    
    // Refresh data every 30 seconds
    const interval = setInterval(loadKlineData, 30000);
    
    return () => clearInterval(interval);
  }, [api, symbol]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600">Loading price chart...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">{error}</div>
        </div>
      </div>
    );
  }

  const chartData: ChartData<'line'> = {
    labels: priceData.map(point => new Date(point.timestamp)),
    datasets: [
      {
        label: `${symbol} Price`,
        data: priceData.map(point => point.close),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.1,
        pointRadius: 0,
        pointHoverRadius: 4,
      },
      ...(showVolume ? [{
        label: 'Volume',
        data: priceData.map(point => point.volume || 0),
        borderColor: 'rgba(156, 163, 175, 0.5)',
        backgroundColor: 'rgba(156, 163, 175, 0.1)',
        borderWidth: 1,
        fill: false,
        yAxisID: 'volume',
        pointRadius: 0,
      }] : [])
    ]
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: 'index',
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${symbol} Real-time Price Chart`,
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            if (context.datasetIndex === 0) {
              return `Price: $${context.parsed.y.toLocaleString()}`;
            } else {
              return `Volume: ${context.parsed.y.toLocaleString()}`;
            }
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time',
        time: {
          displayFormats: {
            minute: 'HH:mm',
            hour: 'HH:mm'
          }
        },
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: {
          display: true,
          text: 'Price (USD)'
        },
        ticks: {
          callback: function(value) {
            return '$' + Number(value).toLocaleString();
          }
        }
      },
      ...(showVolume ? {
        volume: {
          type: 'linear' as const,
          display: true,
          position: 'right' as const,
          title: {
            display: true,
            text: 'Volume'
          },
          grid: {
            drawOnChartArea: false,
          },
          ticks: {
            callback: function(value: any) {
              return Number(value).toLocaleString();
            }
          }
        }
      } : {})
    },
    animation: {
      duration: 0 // Disable animations for real-time updates
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          {symbol} Price Chart
        </h3>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-blue-500 rounded-full mr-1"></div>
            <span>Price</span>
          </div>
          {showVolume && (
            <div className="flex items-center">
              <div className="w-3 h-3 bg-gray-400 rounded-full mr-1"></div>
              <span>Volume</span>
            </div>
          )}
          <span className="text-xs">
            {priceData.length} data points
          </span>
        </div>
      </div>
      
      <div style={{ height: `${height}px` }}>
        <Line ref={chartRef} data={chartData} options={options} />
      </div>
      
      {priceData.length > 0 && (
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600">Current Price:</span>
            <span className="ml-2 font-semibold">
              ${priceData[priceData.length - 1]?.close.toLocaleString()}
            </span>
          </div>
          <div>
            <span className="text-gray-600">24h High:</span>
            <span className="ml-2 font-semibold text-green-600">
              ${Math.max(...priceData.map(p => p.high)).toLocaleString()}
            </span>
          </div>
          <div>
            <span className="text-gray-600">24h Low:</span>
            <span className="ml-2 font-semibold text-red-600">
              ${Math.min(...priceData.map(p => p.low)).toLocaleString()}
            </span>
          </div>
          <div>
            <span className="text-gray-600">Volume:</span>
            <span className="ml-2 font-semibold">
              {priceData[priceData.length - 1]?.volume.toLocaleString()}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default PriceChart;