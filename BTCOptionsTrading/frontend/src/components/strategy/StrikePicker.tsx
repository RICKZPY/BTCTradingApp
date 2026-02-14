import { useState, useEffect } from 'react'

interface OptionData {
  strike: number
  callPrice: number
  putPrice: number
  callIV: number
  putIV: number
}

interface StrikePickerProps {
  value: number | null
  onChange: (strike: number) => void
  underlyingPrice: number
  optionsData: OptionData[]
  label?: string
  disabled?: boolean
  className?: string
}

const StrikePicker = ({
  value,
  onChange,
  underlyingPrice,
  optionsData,
  label = '执行价',
  disabled = false,
  className = ''
}: StrikePickerProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  // 过滤和排序执行价
  const filteredStrikes = optionsData
    .filter(option => 
      searchTerm === '' || 
      option.strike.toString().includes(searchTerm)
    )
    .sort((a, b) => a.strike - b.strike)

  // 找到最接近的ATM执行价
  const atmStrike = optionsData.reduce((closest, option) => {
    const currentDiff = Math.abs(option.strike - underlyingPrice)
    const closestDiff = Math.abs(closest - underlyingPrice)
    return currentDiff < closestDiff ? option.strike : closest
  }, optionsData[0]?.strike || 0)

  // 格式化价格
  const formatPrice = (price: number) => {
    return price > 0 ? `$${price.toFixed(2)}` : '-'
  }

  // 格式化IV
  const formatIV = (iv: number) => {
    return iv > 0 ? `${(iv * 100).toFixed(1)}%` : '-'
  }

  // 处理选择
  const handleSelect = (strike: number) => {
    onChange(strike)
    setIsOpen(false)
    setSearchTerm('')
  }

  // 点击外部关闭下拉菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('.strike-picker-container')) {
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

  return (
    <div className={`strike-picker-container relative ${className}`}>
      {label && (
        <label className="block text-sm font-medium text-text-secondary mb-2">
          {label}
        </label>
      )}
      
      {/* 选择器按钮 */}
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full px-4 py-2 text-left bg-bg-secondary border border-text-disabled 
          rounded-lg focus:outline-none focus:ring-2 focus:ring-accent-blue
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-accent-blue cursor-pointer'}
          transition-colors
        `}
      >
        <div className="flex items-center justify-between">
          <span className={value ? 'text-text-primary' : 'text-text-secondary'}>
            {value ? (
              <span className="font-mono">
                ${value.toLocaleString()}
                {value === atmStrike && (
                  <span className="ml-2 text-xs text-accent-blue">(ATM)</span>
                )}
              </span>
            ) : (
              '选择执行价'
            )}
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
          {/* 搜索框 */}
          <div className="p-3 border-b border-text-disabled">
            <input
              type="text"
              placeholder="搜索执行价..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 bg-bg-primary border border-text-disabled rounded text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue"
              autoFocus
            />
          </div>

          {/* 标的价格提示 */}
          <div className="px-3 py-2 bg-bg-primary border-b border-text-disabled">
            <span className="text-xs text-text-secondary">
              当前标的价格: 
              <span className="ml-2 font-mono text-text-primary font-medium">
                ${underlyingPrice.toLocaleString()}
              </span>
            </span>
          </div>

          {/* 执行价列表 */}
          <div className="overflow-y-auto max-h-80">
            {filteredStrikes.length === 0 ? (
              <div className="px-4 py-8 text-center text-text-secondary">
                没有找到匹配的执行价
              </div>
            ) : (
              filteredStrikes.map((option) => {
                const isATM = option.strike === atmStrike
                const isSelected = option.strike === value
                
                return (
                  <button
                    key={option.strike}
                    type="button"
                    onClick={() => handleSelect(option.strike)}
                    className={`
                      w-full px-4 py-3 text-left hover:bg-bg-primary transition-colors
                      border-b border-text-disabled last:border-b-0
                      ${isSelected ? 'bg-accent-blue bg-opacity-10' : ''}
                      ${isATM ? 'bg-accent-blue bg-opacity-5' : ''}
                    `}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className={`font-mono font-bold ${
                        isATM ? 'text-accent-blue' : 'text-text-primary'
                      }`}>
                        ${option.strike.toLocaleString()}
                      </span>
                      {isATM && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-accent-blue text-white rounded">
                          ATM
                        </span>
                      )}
                      {isSelected && !isATM && (
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
                    
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      {/* Call数据 */}
                      <div>
                        <div className="text-text-secondary mb-1">看涨 (Call)</div>
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-text-secondary">价格:</span>
                            <span className="font-mono text-accent-green">
                              {formatPrice(option.callPrice)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-text-secondary">IV:</span>
                            <span className="font-mono text-text-primary">
                              {formatIV(option.callIV)}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      {/* Put数据 */}
                      <div>
                        <div className="text-text-secondary mb-1">看跌 (Put)</div>
                        <div className="space-y-1">
                          <div className="flex justify-between">
                            <span className="text-text-secondary">价格:</span>
                            <span className="font-mono text-accent-red">
                              {formatPrice(option.putPrice)}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-text-secondary">IV:</span>
                            <span className="font-mono text-text-primary">
                              {formatIV(option.putIV)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default StrikePicker
