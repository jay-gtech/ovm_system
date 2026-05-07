import type { SelectHTMLAttributes } from 'react'
import { cn } from '../../utils/cn'
export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn('h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-brand-400', className)} {...props} />
}
