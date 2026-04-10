import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

import { cn } from '@/lib/utils'

const badgeVariants = cva('inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium transition-colors', {
  variants: {
    variant: {
      default: 'border-blue-500/40 bg-blue-500/10 text-blue-300',
      secondary: 'border-slate-700 bg-slate-800 text-slate-300',
      success: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
      warning: 'border-amber-500/40 bg-amber-500/10 text-amber-300',
    },
  },
  defaultVariants: {
    variant: 'default',
  },
})

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge }
