import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  ChartOptions,
  ChartData
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import { useWebSocket, SubscriptionType } from '../contexts/WebSocketContext';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface SentimentData {
  timestamp: string;
  sentiment_score: number;
  confidence: number;
  key_topics: string[];
  impact_assessment: Record<string, number>;
}

interface SentimentVisualizationProps {
  height?: number;
  maxDataPoints?: number;
}

const SentimentVisualization: React.FC<SentimentVisualizationProps> = ({
  height = 300,
  maxDataPoints = 50
}) => {
  const { latestAnalysis, subscribe, subscriptions } = useWebSocket();
  const [sentimentHistory, setSentimentHistory] = useState<SentimentData[]>([]);
  const [currentSentiment, setCurrentSentiment] = useState<SentimentData | null>(null);

  // Subscribe to analysis updates
  useEffect(() => {
    if (!subscriptions.has(SubscriptionType.ANALYSIS_UPDATES)) {
      subscribe(SubscriptionType.ANALYSIS_UPDATES);
    }
  }, [subscribe, subscriptions]);

  // Update sentiment data when new analysis comes in
  useEffect(() => {
    if (latestAnalysis && latestAnalysis.analysis_type === 'SENTIMENT_ANALYZED') {
      const sentimentData = latestAnalysis.result;
      if (sentimentData) {
        const newDataPoint: SentimentData = {
          timestamp: latestAnalysis.timestamp,
          sentiment_score: sentimentData.sentiment_score || 0,
          confidence: sentimentData.confidence || 0,
          key_topics: sentimentData.key_topics || [],
          impact_assessment: sentimentData.impact_assessment || {},
        };

        setCurrentSentiment(newDataPoint);
        
        setSentimentHistory(prev => {
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
    if (sentimentHistory.length === 0) {
      const now = new Date();
      const mockData: SentimentData[] = [];
      const topics = ['regulation', 'adoption', 'market_volatility', 'institutional_investment', 'technology'];
      
      for (let i = 20; i >= 0; i--) {
        const timestamp = new Date(now.getTime() - i * 3600000); // 1 hour intervals
        const sentimentScore = (Math.random() - 0.5) * 1.5; // -0.75 to 0.75
        
        const dataPoint: SentimentData = {
          timestamp: timestamp.toISOString(),
          sentiment_score: sentimentScore,
          confidence: 0.6 + Math.random() * 0.3,
          key_topics: topics.slice(0, 2 + Math.floor(Math.random() * 3)),
          impact_assessment: {
            short_term: (Math.random() - 0.5) * 0.5,
            medium_term: (Math.random() - 0.5) * 0.3,
            long_term: (Math.random() - 0.5) * 0.2,
          }
        };
        
        mockData.push(dataPoint);
      }
      
      setSentimentHistory(mockData);
      setCurrentSentiment(mockData[mockData.length - 1]);
    }
  }, []);

  const getSentimentLabel = (score: number): string => {
    if (score > 0.3) return 'Very Bullish';
    if (score > 0.1) return 'Bullish';
    if (score > -0.1) return 'Neutral';
    if (score > -0.3) return 'Bearish';
    return 'Very Bearish';
  };

  const getSentimentColor = (score: number): string => {
    if (score > 0.3) return '#10b981'; // green-500
    if (score > 0.1) return '#34d399'; // green-400
    if (score > -0.1) return '#fbbf24'; // yellow-400
    if (score > -0.3) return '#f87171'; // red-400
    return '#ef4444'; // red-500
  };

  // Sentiment history chart data
  const sentimentChartData: ChartData<'bar'> = {
    labels: sentimentHistory.map(point => 
      new Date(point.timestamp).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit'
      })
    ),
    datasets: [
      {
        label: 'Sentiment Score',
        data: sentimentHistory.map(point => point.sentiment_score),
        backgroundColor: sentimentHistory.map(point => getSentimentColor(point.sentiment_score)),
        borderColor: sentimentHistory.map(point => getSentimentColor(point.sentiment_score)),
        borderWidth: 1,
      }
    ]
  };

  const sentimentChartOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      title: {
        display: true,
        text: 'Sentiment Score History',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const score = context.parsed.y;
            return `Sentiment: ${score.toFixed(3)} (${getSentimentLabel(score)})`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Time'
        }
      },
      y: {
        min: -1,
        max: 1,
        title: {
          display: true,
          text: 'Sentiment Score'
        },
        ticks: {
          callback: function(value) {
            return Number(value).toFixed(1);
          }
        }
      }
    }
  };

  // Impact assessment doughnut chart
  const impactChartData: ChartData<'doughnut'> = currentSentiment ? {
    labels: Object.keys(currentSentiment.impact_assessment).map(key => 
      key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())
    ),
    datasets: [
      {
        data: Object.values(currentSentiment.impact_assessment).map(Math.abs),
        backgroundColor: [
          '#3b82f6', // blue-500
          '#10b981', // green-500
          '#f59e0b', // yellow-500
          '#ef4444', // red-500
          '#8b5cf6', // purple-500
        ],
        borderColor: [
          '#1d4ed8', // blue-700
          '#047857', // green-700
          '#d97706', // yellow-600
          '#dc2626', // red-600
          '#7c3aed', // purple-600
        ],
        borderWidth: 2,
      }
    ]
  } : { labels: [], datasets: [] };

  const impactChartOptions: ChartOptions<'doughnut'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
      title: {
        display: true,
        text: 'Impact Assessment',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const value = currentSentiment?.impact_assessment[
              Object.keys(currentSentiment.impact_assessment)[context.dataIndex]
            ];
            return `${context.label}: ${value?.toFixed(3)}`;
          }
        }
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Current Sentiment Overview */}
      {currentSentiment && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Current Market Sentiment
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Sentiment Score */}
            <div className="text-center">
              <div 
                className="text-4xl font-bold mb-2"
                style={{ color: getSentimentColor(currentSentiment.sentiment_score) }}
              >
                {getSentimentLabel(currentSentiment.sentiment_score)}
              </div>
              <div className="text-sm text-gray-600">
                Score: {currentSentiment.sentiment_score.toFixed(3)}
              </div>
              <div className="text-sm text-gray-600">
                Confidence: {(currentSentiment.confidence * 100).toFixed(1)}%
              </div>
            </div>

            {/* Sentiment Meter */}
            <div className="flex flex-col justify-center">
              <div className="relative">
                <div className="w-full bg-gray-200 rounded-full h-6">
                  <div 
                    className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-6 rounded-full"
                    style={{ width: '100%' }}
                  ></div>
                  <div 
                    className="absolute top-0 w-2 h-6 bg-black rounded"
                    style={{ 
                      left: `${((currentSentiment.sentiment_score + 1) / 2) * 100}%`,
                      transform: 'translateX(-50%)'
                    }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Very Bearish</span>
                  <span>Neutral</span>
                  <span>Very Bullish</span>
                </div>
              </div>
            </div>

            {/* Key Topics */}
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Key Topics</h4>
              <div className="flex flex-wrap gap-2">
                {currentSentiment.key_topics.map((topic, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                  >
                    {topic.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sentiment History Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <div style={{ height: `${height}px` }}>
            <Bar data={sentimentChartData} options={sentimentChartOptions} />
          </div>
        </div>

        {/* Impact Assessment Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <div style={{ height: `${height}px` }}>
            {currentSentiment && Object.keys(currentSentiment.impact_assessment).length > 0 ? (
              <Doughnut data={impactChartData} options={impactChartOptions} />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No impact assessment data available
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Detailed Impact Assessment */}
      {currentSentiment && Object.keys(currentSentiment.impact_assessment).length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h4 className="text-lg font-semibold text-gray-900 mb-4">
            Detailed Impact Assessment
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.entries(currentSentiment.impact_assessment).map(([key, value]) => (
              <div key={key} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">
                  {key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </div>
                <div className={`text-2xl font-bold ${
                  value > 0 ? 'text-green-600' : value < 0 ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {value > 0 ? '+' : ''}{value.toFixed(3)}
                </div>
                <div className="text-xs text-gray-500">
                  {value > 0.1 ? 'Positive Impact' : 
                   value < -0.1 ? 'Negative Impact' : 'Neutral Impact'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SentimentVisualization;