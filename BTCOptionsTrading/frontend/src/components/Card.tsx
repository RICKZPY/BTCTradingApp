import { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  title?: string
  subtitle?: string
  action?: ReactNode
  hover?: boolean
  onClick?: () => void
}

const Card = ({
  children,
  className = '',
  title,
  subtitle,
  action,
  hover = false,
  onClick
}: CardProps) => {
  return (
    <div
      className={`
        bg-bg-card 
        rounded-lg 
        p-6 
        border border-text-disabled
        ${hover ? 'hover:border-accent-blue hover:shadow-lg transition-all duration-200' : ''}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
      onClick={onClick}
    >
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          <div>
            {title && (
              <h3 className="text-lg font-semibold text-text-primary">{title}</h3>
            )}
            {subtitle && (
              <p className="text-sm text-text-secondary mt-1">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  )
}

export default Card
