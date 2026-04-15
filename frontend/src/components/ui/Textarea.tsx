import { forwardRef, type TextareaHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <div className="w-full">
        <textarea
          ref={ref}
          className={cn(
            'flex min-h-[80px] w-full rounded-md border bg-bg px-3 py-2 text-sm text-text placeholder:text-text-muted',
            'border-border transition-colors duration-fast',
            'focus:outline-none focus:ring-2 focus:ring-offset-0 focus:ring-primary focus:border-primary',
            'hover:border-border-hover',
            'disabled:cursor-not-allowed disabled:opacity-50',
            'resize-y',
            error ? 'border-error' : '',
            className
          )}
          {...props}
        />
        {error && <p className="mt-1 text-xs text-error">{error}</p>}
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'