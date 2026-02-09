import { ReactNode } from 'react'

interface BadgeProps {
  children: ReactNode
  variant?: 'default' | 'success' | 'danger' | 'warning' | 'info'
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const Badge = ({
  children,
  variant = 'default',
  size = 'md',
  className = ''
}: BadgeProps) => {
  const variantStyles = {
    default: 'bg-bg-secondary text-text-primary',
    success: 'bg-accent-green bg-opacity-20 text-accent-green',
    danger: 'bg-accent-red bg-opacity-20 text-accent-red',
    warning: 'bg-accent-yellow bg-opacity-20 text-accent-yellow',
    info: 'bg-accent-blue bg-opacity-20 text-accent-blue'
  }

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base'
  }

  return (
    <span
      className={`
        inline-flex items-center justify-center
        rounded-full font-medium
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
    >
      {children}
    </span>
  )
}

export default Badge
