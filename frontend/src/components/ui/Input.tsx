import type { InputHTMLAttributes } from 'react'
import { cn } from '../../utils/cn'
export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn('h-9 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-100', className)} {...props} />
}
