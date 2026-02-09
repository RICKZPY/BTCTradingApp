import { useAppStore, type TabType } from '../store/useAppStore'
import clsx from 'clsx'

const tabs: { id: TabType; label: string; icon: string }[] = [
  { id: 'strategies', label: '策略管理', icon: '📊' },
  { id: 'backtest', label: '回测分析', icon: '📈' },
  { id: 'options-chain', label: '期权链', icon: '🔗' },
  { id: 'volatility', label: '波动率', icon: '📉' },
  { id: 'settings', label: '设置', icon: '⚙️' },
]

const TabNavigation = () => {
  const { activeTab, setActiveTab } = useAppStore()

  return (
    <nav className="flex space-x-1 -mb-px">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={clsx(
            'px-6 py-3 text-sm font-medium rounded-t-lg transition-all duration-200',
            'hover:bg-bg-card',
            activeTab === tab.id
              ? 'bg-bg-primary text-accent-blue border-b-2 border-accent-blue'
              : 'text-text-secondary'
          )}
        >
          <span className="mr-2">{tab.icon}</span>
          {tab.label}
        </button>
      ))}
    </nav>
  )
}

export default TabNavigation
