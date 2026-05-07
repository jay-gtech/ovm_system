import { type ReactNode } from 'react'
import { cn } from '../../utils/cn'

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn('rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden', className)}>
      {children}
    </div>
  )
}

export function CardHeader({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('flex flex-col gap-1 px-5 pt-5 pb-3', className)}>{children}</div>
}

export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return <h3 className={cn('font-semibold text-slate-800', className)}>{children}</h3>
}

export function CardContent({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn('px-5 pb-5', className)}>{children}</div>
}
