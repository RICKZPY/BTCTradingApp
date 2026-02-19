import { useState, useEffect } from 'react'
import { useAppStore } from '../store/useAppStore'
import TabNavigation from './TabNavigation'
import WelcomeBanner from './WelcomeBanner'
import StrategiesTab from './tabs/StrategiesTab'
import BacktestTab from './tabs/BacktestTab'
import OptionsChainTab from './tabs/OptionsChainTab'
import VolatilityTab from './tabs/VolatilityTab'
import HistoricalDataTab from './tabs/HistoricalDataTab'
import SettingsTab from './tabs/SettingsTab'
import Toast from './Toast'

const Layout = () => {
  const { activeTab } = useAppStore()
  const [showWelcome, setShowWelcome] = useState(true)

  // 检查是否是首次访问
  useEffect(() => {
    const hasVisited = localStorage.getItem('hasVisited')
    if (hasVisited) {
      setShowWelcome(false)
    }
  }, [])

  const handleDismissWelcome = () => {
    setShowWelcome(false)
    localStorage.setItem('hasVisited', 'true')
  }

  const renderTab = () => {
    switch (activeTab) {
      case 'strategies':
        return <StrategiesTab />
      case 'backtest':
        return <BacktestTab />
      case 'options-chain':
        return <OptionsChainTab />
      case 'volatility':
        return <VolatilityTab />
      case 'historical-data':
        return <HistoricalDataTab />
      case 'settings':
        return <SettingsTab />
      default:
        return <StrategiesTab />
    }
  }

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* 顶部导航栏 */}
      <header className="bg-bg-secondary border-b border-text-disabled">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-accent-blue rounded flex items-center justify-center">
                <span className="text-white font-bold text-lg">₿</span>
              </div>
              <h1 className="text-xl font-bold text-text-primary">
                BTC期权交易回测系统
              </h1>
            </div>

            {/* 右侧工具栏 */}
            <div className="flex items-center space-x-4">
              <button className="text-text-secondary hover:text-text-primary transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </button>
              <div className="w-8 h-8 bg-accent-blue rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">U</span>
              </div>
            </div>
          </div>

          {/* Tab导航 */}
          <TabNavigation />
        </div>
      </header>

      {/* 主内容区域 */}
      <main className="flex-1 container mx-auto px-4 py-6">
        {/* 欢迎横幅 - 仅首次访问显示 */}
        {showWelcome && <WelcomeBanner onDismiss={handleDismissWelcome} />}
        
        {renderTab()}
      </main>

      {/* Toast通知 */}
      <Toast />
    </div>
  )
}

export default Layout
