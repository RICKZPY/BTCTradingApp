interface RiskGaugeProps {
  value: number
  max: number
  label: string
  unit?: string
  thresholds?: {
    low: number
    medium: number
    high: number
  }
}

const RiskGauge = ({
  value,
  max,
  label,
  unit = '',
  thresholds = { low: 0.3, medium: 0.6, high: 0.9 }
}: RiskGaugeProps) => {
  const percentage = Math.min((value / max) * 100, 100)
  
  const getColor = () => {
    const ratio = value / max
    if (ratio < thresholds.low) return '#0ECB81' // 绿色 - 低风险
    if (ratio < thresholds.medium) return '#F0B90B' // 黄色 - 中风险
    if (ratio < thresholds.high) return '#FF9500' // 橙色 - 高风险
    return '#F6465D' // 红色 - 极高风险
  }

  const color = getColor()

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-48 h-48">
        {/* 背景圆环 */}
        <svg className="w-full h-full transform -rotate-90">
          <circle
            cx="96"
            cy="96"
            r="80"
            stroke="#474D57"
            strokeWidth="12"
            fill="none"
          />
          {/* 进度圆环 */}
          <circle
            cx="96"
            cy="96"
            r="80"
            stroke={color}
            strokeWidth="12"
            fill="none"
            strokeDasharray={`${percentage * 5.03} 503`}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        {/* 中心文字 */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold text-text-primary">
            {value.toFixed(2)}
          </span>
          {unit && (
            <span className="text-sm text-text-secondary mt-1">{unit}</span>
          )}
        </div>
      </div>
      <p className="mt-4 text-sm font-medium text-text-secondary">{label}</p>
      <div className="mt-2 flex items-center gap-2 text-xs">
        <span className="text-text-disabled">最大值:</span>
        <span className="text-text-primary font-medium">{max.toFixed(2)}</span>
      </div>
    </div>
  )
}

export default RiskGauge
