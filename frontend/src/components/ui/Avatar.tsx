import { type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  initials?: string
  size?: 'sm' | 'md' | 'lg'
}

export function Avatar({ className, initials = 'U', size = 'md', ...props }: AvatarProps) {
  const sizes = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-12 w-12 text-base',
  }

  return (
    <div
      className={cn(
        'flex items-center justify-center rounded-full bg-surface border border-border text-text font-medium',
        sizes[size],
        className
      )}
      {...props}
    >
      {initials.slice(0, 2).toUpperCase()}
    </div>
  )
}