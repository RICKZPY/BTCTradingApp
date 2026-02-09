import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface VolumeData {
  date: string
  volume: number
  trades?: number
}

interface VolumeBarChartProps {
  data: VolumeData[]
  height?: number
}

const VolumeBarChart = ({ data, height = 300 }: VolumeBarChartProps) => {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#474D57" />
        <XAxis
          dataKey="date"
          stroke="#848E9C"
          tick={{ fill: '#848E9C' }}
        />
        <YAxis
          stroke="#848E9C"
          tick={{ fill: '#848E9C' }}
          tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: '#1E2329',
            border: '1px solid #474D57',
            borderRadius: '8px'
          }}
          labelStyle={{ color: '#EAECEF' }}
          itemStyle={{ color: '#EAECEF' }}
          formatter={(value: number) => value.toLocaleString()}
        />
        <Bar
          dataKey="volume"
          fill="#3861FB"
          name="交易量"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default VolumeBarChart
