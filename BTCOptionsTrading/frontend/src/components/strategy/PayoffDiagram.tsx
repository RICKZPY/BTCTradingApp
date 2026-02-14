interface PayoffDiagramProps {
  strategyType: string
  width?: number
  height?: number
}

const PayoffDiagram = ({ strategyType, width = 120, height = 60 }: PayoffDiagramProps) => {
  // 生成不同策略类型的收益曲线路径
  const getPayoffPath = () => {
    const centerX = width / 2
    const centerY = height / 2
    
    switch (strategyType) {
      case 'single_leg':
        // 单腿看涨期权：向上倾斜的线
        return `M 10,${height - 10} L ${centerX},${centerY} L ${width - 10},10`
      
      case 'straddle':
        // 跨式：V形
        return `M 10,10 L ${centerX},${height - 10} L ${width - 10},10`
      
      case 'strangle':
        // 宽跨式：宽V形
        return `M 10,15 L ${centerX * 0.7},${height - 10} L ${centerX * 1.3},${height - 10} L ${width - 10},15`
      
      case 'iron_condor':
        // 铁鹰：平顶山形
        return `M 10,${height - 10} L ${centerX * 0.6},${centerY - 10} L ${centerX * 1.4},${centerY - 10} L ${width - 10},${height - 10}`
      
      case 'butterfly':
        // 蝶式：尖顶山形
        return `M 10,${height - 10} L ${centerX},10 L ${width - 10},${height - 10}`
      
      default:
        return ''
    }
  }

  return (
    <svg 
      width={width} 
      height={height} 
      viewBox={`0 0 ${width} ${height}`}
      className="opacity-30 group-hover:opacity-60 transition-opacity"
    >
      {/* 坐标轴 */}
      <line 
        x1="0" 
        y1={height / 2} 
        x2={width} 
        y2={height / 2} 
        stroke="currentColor" 
        strokeWidth="0.5" 
        strokeDasharray="2,2"
        className="text-text-disabled"
      />
      
      {/* 收益曲线 */}
      <path
        d={getPayoffPath()}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-accent-blue"
      />
    </svg>
  )
}

export default PayoffDiagram
