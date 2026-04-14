import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <div className="w-full">
        <input
          ref={ref}
          className={cn(
            'flex h-10 w-full rounded-md border bg-bg px-3 py-2 text-sm text-text placeholder:text-text-muted',
            'focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-primary',
            'disabled:cursor-not-allowed disabled:opacity-50',
            error ? 'border-red-500' : 'border-border',
            className
          )}
          {...props}
        />
        {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'