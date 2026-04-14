import React, { forwardRef, type ButtonHTMLAttributes, type ReactElement, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive' | 'outline'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  asChild?: boolean
  children: ReactNode
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', loading, disabled, children, asChild, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none'
    
    const variants = {
      primary: 'bg-primary text-white hover:bg-primary-hover focus:ring-primary',
      secondary: 'bg-surface text-text border border-border hover:bg-surface/80 focus:ring-border',
      ghost: 'hover:bg-surface focus:ring-border',
      destructive: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-600',
      outline: 'border border-border bg-transparent hover:bg-surface focus:ring-border',
    }
    
    const sizes = {
      sm: 'h-8 px-3 text-sm rounded',
      md: 'h-10 px-4 text-sm rounded-md',
      lg: 'h-12 px-6 text-base rounded-md',
    }

    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children as ReactElement<{ className?: string; ref?: React.Ref<unknown> }>, {
        className: cn(baseStyles, variants[variant], sizes[size], className, (children.props as { className?: string }).className),
      })
    }

    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        disabled={disabled || loading}
        {...props}
      >
        {loading && (
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'