import { type ButtonHTMLAttributes, type ReactNode } from 'react'
import { cn } from '../../utils/cn'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'outline' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  children: ReactNode
}

const variants = {
  primary: 'bg-brand-600 text-white hover:bg-brand-700 border-transparent shadow-sm',
  outline: 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50 hover:border-slate-300',
  ghost:   'bg-transparent text-slate-600 border-transparent hover:bg-slate-100',
  danger:  'bg-red-600 text-white hover:bg-red-700 border-transparent shadow-sm',
}
const sizes = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-9 px-4 text-sm',
  lg: 'h-11 px-6 text-base',
}

export function Button({ variant = 'primary', size = 'md', children, className, disabled, ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-lg border font-medium transition-all focus:outline-none focus:ring-2 focus:ring-brand-400 focus:ring-offset-1',
        variants[variant],
        sizes[size],
        disabled && 'opacity-50 cursor-not-allowed pointer-events-none',
        className
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}
