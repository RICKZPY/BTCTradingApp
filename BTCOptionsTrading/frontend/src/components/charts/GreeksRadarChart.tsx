import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'

interface GreeksData {
  delta: number
  gamma: number
  theta: number
  vega: number
  rho: number
}

interface GreeksRadarChartProps {
  greeks: GreeksData
  height?: number
}

const GreeksRadarChart = ({ greeks, height = 400 }: GreeksRadarChartProps) => {
  // 标准化希腊字母值到0-100范围
  const normalizeValue = (value: number, max: number) => {
    return Math.abs(value) / max * 100
  }

  const data = [
    {
      greek: 'Delta',
      value: normalizeValue(greeks.delta, 1),
      fullMark: 100
    },
    {
      greek: 'Gamma',
      value: normalizeValue(greeks.gamma, 0.1),
      fullMark: 100
    },
    {
      greek: 'Theta',
      value: normalizeValue(greeks.theta, 100),
      fullMark: 100
    },
    {
      greek: 'Vega',
      value: normalizeValue(greeks.vega, 100),
      fullMark: 100
    },
    {
      greek: 'Rho',
      value: normalizeValue(greeks.rho, 100),
      fullMark: 100
    }
  ]

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data}>
        <PolarGrid stroke="#474D57" />
        <PolarAngleAxis
          dataKey="greek"
          tick={{ fill: '#848E9C' }}
        />
        <PolarRadiusAxis
          angle={90}
          domain={[0, 100]}
          tick={{ fill: '#848E9C' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1E2329',
            border: '1px solid #474D57',
            borderRadius: '8px'
          }}
          labelStyle={{ color: '#EAECEF' }}
          itemStyle={{ color: '#EAECEF' }}
        />
        <Radar
          name="希腊字母"
          dataKey="value"
          stroke="#3861FB"
          fill="#3861FB"
          fillOpacity={0.6}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}

export default GreeksRadarChart
