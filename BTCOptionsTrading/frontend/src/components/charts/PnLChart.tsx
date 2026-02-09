import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'

interface PnLDataPoint {
  date: string
  value: number
  pnl?: number
}

interface PnLChartProps {
  data: PnLDataPoint[]
  height?: number
  showPnL?: boolean
}

const PnLChart = ({ data, height = 400, showPnL = true }: PnLChartProps) => {
  const formatCurrency = (value: number) => {
    return `$${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
        <XAxis
          dataKey="date"
          stroke="#848E9C"
          tick={{ fill: '#848E9C' }}
        />
        <YAxis
          stroke="#848E9C"
          tick={{ fill: '#848E9C' }}
          tickFormatter={formatCurrency}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1E2329',
            border: '1px solid #474D57',
            borderRadius: '8px'
          }}
          labelStyle={{ color: '#EAECEF' }}
          itemStyle={{ color: '#EAECEF' }}
          formatter={(value: number) => formatCurrency(value)}
        />
        <Legend wrapperStyle={{ color: '#EAECEF' }} />
        <ReferenceLine y={0} stroke="#848E9C" strokeDasharray="3 3" />
        <Line
          type="monotone"
          dataKey="value"
          stroke="#3861FB"
          strokeWidth={2}
          name="组合价值"
          dot={false}
        />
        {showPnL && (
          <Line
            type="monotone"
            dataKey="pnl"
            stroke="#0ECB81"
            strokeWidth={2}
            name="累计盈亏"
            dot={false}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}

export default PnLChart
