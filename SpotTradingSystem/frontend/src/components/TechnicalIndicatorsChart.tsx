import React, { useEffect, useState } from 'react';
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
import { useWebSocket, SubscriptionType } from '../contexts/WebSocketContext';

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

interface TechnicalIndicatorData {
  timestamp: string;
  rsi: number;
  macd: number;
  macd_signal: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  sma_20: number;
  ema_12: number;
  ema_26: number;
}

interface TechnicalIndicatorsChartProps {
  height?: number;
  maxDataPoints?: number;
  indicators?: string[];
}

const TechnicalIndicatorsChart: React.FC<TechnicalIndicatorsChartProps> = ({
  height = 300,
  maxDataPoints = 100,
  indicators = ['rsi', 'macd', 'bb']
}) => {
  const { latestAnalysis, subscribe, subscriptions } = useWebSocket();
  const [indicatorData, setIndicatorData] = useState<TechnicalIndicatorData[]>([]);
  const [selectedIndicator, setSelectedIndicator] = useState<string>('rsi');

  // Subscribe to analysis updates
  useEffect(() => {
    if (!subscriptions.has(SubscriptionType.ANALYSIS_UPDATES)) {
      subscribe(SubscriptionType.ANALYSIS_UPDATES);
    }
  }, [subscribe, subscriptions]);

  // Update indicator data when new analysis comes in
  useEffect(() => {
    if (latestAnalysis && latestAnalysis.analysis_type === 'SIGNAL_GENERATED') {
      const technicalData = latestAnalysis.result;
      if (technicalData && technicalData.indicators) {
        const newDataPoint: TechnicalIndicatorData = {
          timestamp: latestAnalysis.timestamp,
          rsi: technicalData.indicators.rsi || 50,
          macd: technicalData.indicators.macd || 0,
          macd_signal: technicalData.indicators.macd_signal || 0,
          bb_upper: technicalData.indicators.bb_upper || 0,
          bb_middle: technicalData.indicators.bb_middle || 0,
          bb_lower: technicalData.indicators.bb_lower || 0,
          sma_20: technicalData.indicators.sma_20 || 0,
          ema_12: technicalData.indicators.ema_12 || 0,
          ema_26: technicalData.indicators.ema_26 || 0,
        };

        setIndicatorData(prev => {
          const updated = [...prev, newDataPoint];
          
          // Keep only the last maxDataPoints
          if (updated.length > maxDataPoints) {
            return updated.slice(-maxDataPoints);
          }
          
          return updated;
        });
      }
    }
  }, [latestAnalysis, maxDataPoints]);

  // Generate initial mock data for demonstration
  useEffect(() => {
    if (indicatorData.length === 0) {
      const now = new Date();
      const mockData: TechnicalIndicatorData[] = [];
      
      for (let i = 50; i >= 0; i--) {
        const timestamp = new Date(now.getTime() - i * 300000); // 5 minute intervals
        
        mockData.push({
          timestamp: timestamp.toISOString(),
          rsi: 30 + Math.random() * 40, // RSI between 30-70
          macd: (Math.random() - 0.5) * 200,
          macd_signal: (Math.random() - 0.5) * 180,
          bb_upper: 46000 + Math.random() * 1000,
          bb_middle: 45000 + Math.random() * 500,
          bb_lower: 44000 + Math.random() * 1000,
          sma_20: 45000 + Math.random() * 500,
          ema_12: 45100 + Math.random() * 400,
          ema_26: 44900 + Math.random() * 600,
        });
      }
      
      setIndicatorData(mockData);
    }
  }, []);

  const getChartData = (): ChartData<'line'> => {
    const labels = indicatorData.map(point => new Date(point.timestamp));

    switch (selectedIndicator) {
      case 'rsi':
        return {
          labels,
          datasets: [
            {
              label: 'RSI',
              data: indicatorData.map(point => point.rsi),
              borderColor: 'rgb(147, 51, 234)',
              backgroundColor: 'rgba(147, 51, 234, 0.1)',
              borderWidth: 2,
              fill: false,
              tension: 0.1,
              pointRadius: 0,
            },
            // RSI overbought/oversold lines
            {
              label: 'Overbought (70)',
              data: new Array(indicatorData.length).fill(70),
              borderColor: 'rgba(239, 68, 68, 0.5)',
              borderWidth: 1,
              borderDash: [5, 5],
              fill: false,
              pointRadius: 0,
            },
            {
              label: 'Oversold (30)',
              data: new Array(indicatorData.length).fill(30),
              borderColor: 'rgba(34, 197, 94, 0.5)',
              borderWidth: 1,
              borderDash: [5, 5],
              fill: false,
              pointRadius: 0,
            }
          ]
        };

      case 'macd':
        return {
          labels,
          datasets: [
            {
              label: 'MACD',
              data: indicatorData.map(point => point.macd),
              borderColor: 'rgb(59, 130, 246)',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderWidth: 2,
              fill: false,
              tension: 0.1,
              pointRadius: 0,
            },
            {
              label: 'Signal',
              data: indicatorData.map(point => point.macd_signal),
              borderColor: 'rgb(239, 68, 68)',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderWidth: 2,
              fill: false,
              tension: 0.1,
              pointRadius: 0,
            }
          ]
        };

      case 'bb':
        return {
          labels,
          datasets: [
            {
              label: 'BB Upper',
              data: indicatorData.map(point => point.bb_upper),
              borderColor: 'rgb(239, 68, 68)',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderWidth: 1,
              fill: false,
              tension: 0.1,
              pointRadius: 0,
            },
            {
              label: 'BB Middle (SMA)',
              data: indicatorData.map(point => point.bb_middle),
              borderColor: 'rgb(59, 130, 246)',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderWidth: 2,
              fill: false,
              tension: 0.1,
              pointRadius: 0,
            },
            {
              label: 'BB Lower',
              data: indicatorData.map(point => point.bb_lower),
              borderColor: 'rgb(34, 197, 94)',
              backgroundColor: 'rgba(34, 197, 94, 0.1)',
              borderWidth: 1,
              fill: false,
              tension: 0.1,
              pointRadius: 0,
            }
          ]
        };

      case 'ma':
        return {
          labels,
          datasets: [
            {
              label: 'SMA 20',
              data: indicatorData.map(point => point.sma_20),
              borderColor: 'rgb(59, 130, 246)',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderWidth: 2,
              fill: false,
              tension: 0.1,
              pointRadius: 0,
            },
            {
              label: 'EMA 12',
              data: indicatorData.map(point => point.ema_12),
              borderColor: 'rgb(34, 197, 94)',
              backgroundColor: 'rgba(34, 197, 94, 0.1)',
              borderWidth: 2,
              fill: false,
              tension: 0.1,
              pointRadius: 0,
            },
            {
              label: 'EMA 26',
              data: indicatorData.map(point => point.ema_26),
              borderColor: 'rgb(239, 68, 68)',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              borderWidth: 2,
              fill: false,
              tension: 0.1,
              pointRadius: 0,
            }
          ]
        };

      default:
        return { labels: [], datasets: [] };
    }
  };

  const getChartOptions = (): ChartOptions<'line'> => {
    const baseOptions: ChartOptions<'line'> = {
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
          text: `Technical Indicators - ${selectedIndicator.toUpperCase()}`,
        },
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
            text: getYAxisLabel()
          }
        }
      },
      animation: {
        duration: 0 // Disable animations for real-time updates
      }
    };

    // Special configuration for RSI
    if (selectedIndicator === 'rsi') {
      baseOptions.scales!.y!.min = 0;
      baseOptions.scales!.y!.max = 100;
    }

    return baseOptions;
  };

  const getYAxisLabel = (): string => {
    switch (selectedIndicator) {
      case 'rsi':
        return 'RSI Value';
      case 'macd':
        return 'MACD Value';
      case 'bb':
      case 'ma':
        return 'Price (USD)';
      default:
        return 'Value';
    }
  };

  const indicatorOptions = [
    { value: 'rsi', label: 'RSI (Relative Strength Index)' },
    { value: 'macd', label: 'MACD (Moving Average Convergence Divergence)' },
    { value: 'bb', label: 'Bollinger Bands' },
    { value: 'ma', label: 'Moving Averages' }
  ];

  const getCurrentValue = () => {
    if (indicatorData.length === 0) return null;
    const latest = indicatorData[indicatorData.length - 1];
    
    switch (selectedIndicator) {
      case 'rsi':
        return `RSI: ${latest.rsi.toFixed(2)}`;
      case 'macd':
        return `MACD: ${latest.macd.toFixed(2)}, Signal: ${latest.macd_signal.toFixed(2)}`;
      case 'bb':
        return `Upper: $${latest.bb_upper.toFixed(0)}, Middle: $${latest.bb_middle.toFixed(0)}, Lower: $${latest.bb_lower.toFixed(0)}`;
      case 'ma':
        return `SMA20: $${latest.sma_20.toFixed(0)}, EMA12: $${latest.ema_12.toFixed(0)}, EMA26: $${latest.ema_26.toFixed(0)}`;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Technical Indicators
        </h3>
        <select
          value={selectedIndicator}
          onChange={(e) => setSelectedIndicator(e.target.value)}
          className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {indicatorOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      
      <div style={{ height: `${height}px` }}>
        <Line data={getChartData()} options={getChartOptions()} />
      </div>
      
      {getCurrentValue() && (
        <div className="mt-4 text-sm">
          <span className="text-gray-600">Current Values:</span>
          <span className="ml-2 font-semibold">
            {getCurrentValue()}
          </span>
        </div>
      )}
    </div>
  );
};

export default TechnicalIndicatorsChart;