interface SkeletonProps {
  width?: string
  height?: string
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
}

const Skeleton = ({
  width = '100%',
  height = '1rem',
  className = '',
  variant = 'rectangular'
}: SkeletonProps) => {
  const variantStyles = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-lg'
  }

  return (
    <div
      className={`
        bg-bg-secondary animate-pulse
        ${variantStyles[variant]}
        ${className}
      `}
      style={{ width, height }}
    />
  )
}

// Skeleton组合组件
export const SkeletonCard = () => (
  <div className="card space-y-4">
    <Skeleton height="1.5rem" width="60%" />
    <Skeleton height="1rem" width="40%" />
    <Skeleton height="8rem" />
    <div className="flex gap-2">
      <Skeleton height="2rem" width="5rem" />
      <Skeleton height="2rem" width="5rem" />
    </div>
  </div>
)

export const SkeletonTable = ({ rows = 5 }: { rows?: number }) => (
  <div className="space-y-2">
    <Skeleton height="2.5rem" />
    {Array.from({ length: rows }).map((_, i) => (
      <Skeleton key={i} height="3rem" />
    ))}
  </div>
)

export default Skeleton
