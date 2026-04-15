import { type HTMLAttributes, type ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  elevation?: 0 | 1 | 2 | 3
  children: ReactNode
}

const elevationClasses = {
  0: 'shadow-elevation0',
  1: 'shadow-elevation-1',
  1.5: 'shadow-elevation-1b',
  2: 'shadow-elevation-2',
  3: 'shadow-elevation-3',
}

export function Card({ className, elevation = 1, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        'rounded-lg border border-border bg-surface transition-shadow duration-normal',
        elevationClasses[elevation],
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ className, children, ...props }: CardProps) {
  return (
    <div className={cn('px-6 py-4 border-b border-border', className)} {...props}>
      {children}
    </div>
  )
}

export function CardContent({ className, children, ...props }: CardProps) {
  return (
    <div className={cn('px-6 py-4', className)} {...props}>
      {children}
    </div>
  )
}

export function CardFooter({ className, children, ...props }: CardProps) {
  return (
    <div className={cn('px-6 py-4 border-t border-border', className)} {...props}>
      {children}
    </div>
  )
}