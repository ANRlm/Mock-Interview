import * as React from 'react'

import { cn } from '@/lib/utils'

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number
}

export function Progress({ value, className, ...props }: ProgressProps) {
  const width = Math.max(0, Math.min(100, value))

  return (
    <div className={cn('relative h-2 w-full overflow-hidden rounded-full bg-slate-800', className)} {...props}>
      <div
        className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-500"
        style={{ width: `${width}%` }}
      />
    </div>
  )
}
