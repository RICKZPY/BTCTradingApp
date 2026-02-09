import React from 'react';

interface WelcomeBannerProps {
  onDismiss?: () => void;
}

const WelcomeBanner: React.FC<WelcomeBannerProps> = ({ onDismiss }) => {
  return (
    <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-lg p-6 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-3xl">🚀</span>
            <h2 className="text-xl font-semibold text-gray-100">
              欢迎使用BTC期权交易回测系统
            </h2>
          </div>
          
          <p className="text-gray-300 mb-4">
            这是一个专业的期权交易回测和分析平台。如果您是第一次使用，建议从新手指南开始。
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 新手指南 */}
            <a
              href="https://github.com/RICKZPY/BTCTradingApp/blob/main/BTCOptionsTrading/新手快速入门.md"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-start gap-3 p-4 bg-gray-800/50 hover:bg-gray-800/70 rounded-lg border border-gray-700/50 hover:border-blue-500/50 transition-all group cursor-pointer"
            >
              <span className="text-2xl">📖</span>
              <div>
                <h3 className="font-semibold text-gray-100 group-hover:text-blue-400 transition-colors">
                  新手快速入门
                </h3>
                <p className="text-sm text-gray-400 mt-1">
                  5分钟学会创建策略和运行回测
                </p>
              </div>
            </a>
            
            {/* 完整指南 */}
            <a
              href="https://github.com/RICKZPY/BTCTradingApp/blob/main/BTCOptionsTrading/使用指南.md"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-start gap-3 p-4 bg-gray-800/50 hover:bg-gray-800/70 rounded-lg border border-gray-700/50 hover:border-blue-500/50 transition-all group cursor-pointer"
            >
              <span className="text-2xl">📚</span>
              <div>
                <h3 className="font-semibold text-gray-100 group-hover:text-blue-400 transition-colors">
                  完整使用指南
                </h3>
                <p className="text-sm text-gray-400 mt-1">
                  详细的功能说明和使用方法
                </p>
              </div>
            </a>
            
            {/* API配置 */}
            <a
              href="https://github.com/RICKZPY/BTCTradingApp/blob/main/BTCOptionsTrading/API_CONFIGURATION_GUIDE.md"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-start gap-3 p-4 bg-gray-800/50 hover:bg-gray-800/70 rounded-lg border border-gray-700/50 hover:border-blue-500/50 transition-all group cursor-pointer"
            >
              <span className="text-2xl">⚙️</span>
              <div>
                <h3 className="font-semibold text-gray-100 group-hover:text-blue-400 transition-colors">
                  API配置指南
                </h3>
                <p className="text-sm text-gray-400 mt-1">
                  配置真实数据源和API密钥
                </p>
              </div>
            </a>
          </div>
          
          <div className="mt-4 flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 text-gray-400">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span>系统运行正常</span>
            </div>
            <div className="flex items-center gap-2 text-gray-400">
              <span>🟡</span>
              <span>当前使用测试网数据</span>
            </div>
          </div>
        </div>
        
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="ml-4 text-gray-400 hover:text-gray-200 transition-colors"
            aria-label="关闭欢迎横幅"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default WelcomeBanner;
