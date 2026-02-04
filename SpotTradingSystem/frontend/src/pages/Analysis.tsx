import React, { useEffect, useState } from 'react';
import { useApi, AnalysisData } from '../contexts/ApiContext';
import { useWebSocket, SubscriptionType } from '../contexts/WebSocketContext';
import { useLanguage } from '../contexts/LanguageContext';
import PriceChart from '../components/PriceChart';
import TechnicalIndicatorsChart from '../components/TechnicalIndicatorsChart';
import SentimentVisualization from '../components/SentimentVisualization';

const AnalysisPage: React.FC = () => {
  const { api } = useApi();
  const { t } = useLanguage();
  const { 
    latestAnalysis,
    subscribe,
    subscriptions 
  } = useWebSocket();
  
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);

  // Subscribe to real-time updates
  useEffect(() => {
    if (!subscriptions.has(SubscriptionType.ANALYSIS_UPDATES)) {
      subscribe(SubscriptionType.ANALYSIS_UPDATES);
    }
  }, [subscribe, subscriptions]);

  // Load initial analysis data
  const loadAnalysis = async () => {
    try {
      setError(null);
      const analysisData = await api.getCurrentAnalysis();
      setAnalysis(analysisData);
    } catch (err) {
      console.error('Error loading analysis:', err);
      setError('Failed to load analysis data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalysis();
  }, [api]);

  // Update analysis from real-time data
  useEffect(() => {
    if (latestAnalysis) {
      setAnalysis(prev => {
        const updated = { ...prev };
        
        switch (latestAnalysis.analysis_type) {
          case 'SENTIMENT_ANALYZED':
            updated.sentiment = latestAnalysis.result;
            break;
          case 'SIGNAL_GENERATED':
            updated.technical = latestAnalysis.result;
            break;
          case 'TRADING_DECISION_MADE':
            updated.decision = latestAnalysis.result;
            break;
        }
        
        return updated;
      });
    }
  }, [latestAnalysis]);

  const handleTriggerAnalysis = async () => {
    try {
      setTriggering(true);
      setError(null);
      
      const response = await api.triggerAnalysis();
      if (response.success) {
        // Reload analysis after a short delay
        setTimeout(() => {
          loadAnalysis();
        }, 2000);
      } else {
        setError(response.message || 'Failed to trigger analysis');
      }
    } catch (err: any) {
      console.error('Error triggering analysis:', err);
      setError(err.response?.data?.message || 'Failed to trigger analysis');
    } finally {
      setTriggering(false);
    }
  };

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.1) return 'text-green-600';
    if (score < -0.1) return 'text-red-600';
    return 'text-yellow-600';
  };

  const getSentimentLabel = (score: number) => {
    if (score > 0.3) return t('analysis.very_bullish');
    if (score > 0.1) return t('analysis.bullish');
    if (score > -0.1) return t('analysis.neutral');
    if (score > -0.3) return t('analysis.bearish');
    return t('analysis.very_bearish');
  };

  const getSignalColor = (signalType: string) => {
    switch (signalType.toLowerCase()) {
      case 'buy':
      case 'strong_buy':
        return 'text-green-600';
      case 'sell':
      case 'strong_sell':
        return 'text-red-600';
      default:
        return 'text-yellow-600';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('analysis.title')}</h1>
          <p className="text-gray-600">{t('analysis.subtitle')}</p>
        </div>
        <button
          onClick={handleTriggerAnalysis}
          disabled={triggering}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {triggering ? t('analysis.analyzing') : t('analysis.trigger_analysis')}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="text-red-800">{error}</div>
        </div>
      )}

      {/* Price Chart */}
      <PriceChart symbol="BTCUSDT" height={400} showVolume={true} />

      {/* Sentiment Analysis Visualization */}
      <SentimentVisualization height={300} />

      {/* Technical Indicators Chart */}
      <TechnicalIndicatorsChart height={350} />

      {!analysis ? (
        <div className="text-center text-gray-600">
          {t('analysis.no_data')}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sentiment Analysis Summary */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('analysis.sentiment_summary')}</h2>
            
            {analysis.sentiment ? (
              <div className="space-y-4">
                {/* Overall Sentiment */}
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getSentimentColor(analysis.sentiment.sentiment_score)}`}>
                    {getSentimentLabel(analysis.sentiment.sentiment_score)}
                  </div>
                  <div className="text-sm text-gray-600">
                    {t('analysis.sentiment_score')}: {analysis.sentiment.sentiment_score.toFixed(3)}
                  </div>
                  <div className="text-sm text-gray-600">
                    {t('analysis.confidence')}: {formatPercent(analysis.sentiment.confidence)}
                  </div>
                </div>

                {/* Key Topics */}
                {analysis.sentiment.key_topics && analysis.sentiment.key_topics.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">{t('analysis.key_topics')}</h3>
                    <div className="flex flex-wrap gap-2">
                      {analysis.sentiment.key_topics.map((topic, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-xs text-gray-500">
                  {t('analysis.last_updated')}: {new Date(analysis.sentiment.timestamp).toLocaleString()}
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500">
                {t('analysis.no_data')}
              </div>
            )}
          </div>

          {/* Technical Analysis Summary */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('analysis.technical_summary')}</h2>
            
            {analysis.technical ? (
              <div className="space-y-4">
                {/* Signal */}
                <div className="text-center">
                  <div className={`text-2xl font-bold ${getSignalColor(analysis.technical.signal_type)}`}>
                    {analysis.technical.signal_type.replace('_', ' ').toUpperCase()}
                  </div>
                  <div className="text-sm text-gray-600">
                    {t('analysis.signal_strength')}: {analysis.technical.strength.toFixed(2)}
                  </div>
                  <div className="text-sm text-gray-600">
                    {t('analysis.confidence')}: {formatPercent(analysis.technical.confidence)}
                  </div>
                </div>

                {/* Technical Indicators Summary */}
                {analysis.technical.indicators && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">{t('analysis.key_indicators')}</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {Object.entries(analysis.technical.indicators).slice(0, 6).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-gray-600 uppercase">
                            {key}
                          </span>
                          <span className="font-medium text-gray-900">
                            {typeof value === 'number' ? value.toFixed(2) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="text-xs text-gray-500">
                  {t('analysis.last_updated')}: {new Date(analysis.technical.timestamp).toLocaleString()}
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500">
                {t('analysis.no_data')}
              </div>
            )}
          </div>

          {/* Trading Decision */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('analysis.trading_decision')}</h2>
            
            {analysis.decision ? (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-sm text-gray-600">{t('analysis.action')}</div>
                    <div className={`text-xl font-bold ${getSignalColor(analysis.decision.action)}`}>
                      {analysis.decision.action.toUpperCase()}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-600">{t('trading.symbol')}</div>
                    <div className="text-xl font-bold text-gray-900">
                      {analysis.decision.symbol}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-600">{t('analysis.quantity')}</div>
                    <div className="text-xl font-bold text-gray-900">
                      {analysis.decision.quantity ? analysis.decision.quantity.toFixed(8) : 'N/A'}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-sm text-gray-600">{t('analysis.confidence')}</div>
                    <div className="text-xl font-bold text-gray-900">
                      {formatPercent(analysis.decision.confidence)}
                    </div>
                  </div>
                </div>

                {/* Reasoning */}
                {analysis.decision.reasoning && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">{t('analysis.reasoning')}</h3>
                    <div className="bg-gray-50 rounded-md p-3">
                      <p className="text-sm text-gray-700">
                        {analysis.decision.reasoning}
                      </p>
                    </div>
                  </div>
                )}

                <div className="text-xs text-gray-500">
                  {t('analysis.last_updated')}: {new Date(analysis.decision.timestamp).toLocaleString()}
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500">
                {t('analysis.no_data')}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalysisPage;