import { create } from 'zustand'

export type TabType = 'strategies' | 'backtest' | 'options-chain' | 'volatility' | 'historical-data' | 'settings'

interface AppState {
  // 当前激活的Tab
  activeTab: TabType
  setActiveTab: (tab: TabType) => void

  // 侧边栏状态
  sidebarCollapsed: boolean
  toggleSidebar: () => void

  // 加载状态
  isLoading: boolean
  setIsLoading: (loading: boolean) => void

  // 错误信息
  error: string | null
  setError: (error: string | null) => void

  // 成功消息
  successMessage: string | null
  setSuccessMessage: (message: string | null) => void

  // Toast helper
  showToast: (message: string, type: 'success' | 'error') => void
}

export const useAppStore = create<AppState>((set) => ({
  activeTab: 'strategies',
  setActiveTab: (tab) => set({ activeTab: tab }),

  sidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),

  error: null,
  setError: (error) => set({ error }),

  successMessage: null,
  setSuccessMessage: (message) => set({ successMessage: message }),

  showToast: (message, type) => {
    if (type === 'error') {
      set({ error: message, successMessage: null })
    } else {
      set({ successMessage: message, error: null })
    }
  },
}))
