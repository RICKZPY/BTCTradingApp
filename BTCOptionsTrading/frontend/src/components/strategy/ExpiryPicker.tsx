import { useState, useEffect } from 'react'

interface ExpiryPickerProps {
  value: string
  onChange: (date: string) => void
  availableDates: string[]
  label?: string
  disabled?: boolean
  className?: string
}

const ExpiryPicker = ({
  value,
  onChange,
  availableDates,
  label = '到期日',
  disabled = false,
  className = ''
}: ExpiryPickerProps) => {
  const [isOpen, setIsOpen] = useState(false)

  // 格式化日期显示
  const formatDate = (dateStr: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    
    // 计算距离今天的天数
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const targetDate = new Date(dateStr)
    targetDate.setHours(0, 0, 0, 0)
    const diffTime = targetDate.getTime() - today.getTime()
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
    
    return {
      full: `${year}-${month}-${day}`,
      display: `${year}年${month}月${day}日`,
      daysUntil: diffDays
    }
  }

  // 获取选中日期的显示文本
  const getSelectedText = () => {
    if (!value) return '选择到期日期'
    const formatted = formatDate(value)
    if (typeof formatted === 'string') return '选择到期日期'
    return `${formatted.display} (${formatted.daysUntil}天后)`
  }

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('.expiry-picker-container')) {
        setIsOpen(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // 按日期分组（按月份）
  const groupedDates = availableDates.reduce((groups, dateStr) => {
    const date = new Date(dateStr)
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
    if (!groups[monthKey]) {
      groups[monthKey] = []
    }
    groups[monthKey].push(dateStr)
    return groups
  }, {} as Record<string, string[]>)

  return (
    <div className={`expiry-picker-container relative ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-text-secondary mb-2">
          {label} *
        </label>
      )}
      
      {/* 选择器按钮 */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled || availableDates.length === 0}
        className={`
          w-full px-4 py-2 text-left bg-bg-secondary border border-text-disabled 
          rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-blue
          ${disabled || availableDates.length === 0 ? 'opacity-50 cursor-not-allowed' : 'hover:border-accent-blue cursor-pointer'}
          transition-colors
        `}
      >
        <div className="flex items-center justify-between">
          <span className={value ? 'text-text-primary' : 'text-text-secondary'}>
            {availableDates.length === 0 ? '加载到期日期中...' : getSelectedText()}
          </span>
          <svg
            className={`w-5 h-5 text-text-secondary transition-transform ${
              isOpen ? 'transform rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </button>

      {/* 下拉菜单 */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-bg-secondary border border-text-disabled rounded-lg shadow-lg max-h-96 overflow-hidden">
          {/* 提示信息 */}
          <div className="px-4 py-3 bg-bg-primary border-b border-text-disabled">
            <p className="text-xs text-text-secondary">
              共有 {availableDates.length} 个可用到期日期
            </p>
          </div>

          {/* 日期列表 */}
          <div className="overflow-y-auto max-h-80">
            {Object.entries(groupedDates).map(([monthKey, dates]) => {
              const [year, month] = monthKey.split('-')
              return (
                <div key={monthKey}>
                  {/* 月份标题 */}
                  <div className="sticky top-0 px-4 py-2 bg-bg-primary border-b border-text-disabled">
                    <span className="text-xs font-medium text-accent-blue">
                      {year}年{month}月
                    </span>
                  </div>
                  
                  {/* 该月的日期 */}
                  {dates.map((dateStr) => {
                    const formatted = formatDate(dateStr)
                    if (typeof formatted === 'string') return null
                    
                    const isSelected = dateStr === value
                    const isNearExpiry = formatted.daysUntil <= 7
                    
                    return (
                      <button
                        key={dateStr}
                        type="button"
                        onClick={() => {
                          onChange(dateStr)
                          setIsOpen(false)
                        }}
                        className={`
                          w-full px-4 py-3 text-left hover:bg-bg-primary transition-colors
                          border-b border-text-disabled last:border-b-0
                          ${isSelected ? 'bg-accent-blue bg-opacity-10' : ''}
                        `}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-text-primary font-medium">
                                {formatted.display}
                              </span>
                              {isNearExpiry && (
                                <span className="px-2 py-0.5 text-xs font-medium bg-accent-red bg-opacity-20 text-accent-red rounded">
                                  即将到期
                                </span>
                              )}
                            </div>
                            <div className="text-xs text-text-secondary mt-1">
                              {formatted.daysUntil > 0 ? (
                                `${formatted.daysUntil} 天后到期`
                              ) : formatted.daysUntil === 0 ? (
                                '今天到期'
                              ) : (
                                `已过期 ${Math.abs(formatted.daysUntil)} 天`
                              )}
                            </div>
                          </div>
                          {isSelected && (
                            <span className="text-accent-blue">
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                  fillRule="evenodd"
                                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                  clipRule="evenodd"
                                />
                              </svg>
                            </span>
                          )}
                        </div>
                      </button>
                    )
                  })}
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

export default ExpiryPicker
