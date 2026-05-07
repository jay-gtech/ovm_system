import { Loader2 } from 'lucide-react'
import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface LoaderProps {
  className?: string
  size?: number
  label?: string
  fullPage?: boolean
}

export function Loader({ className, size = 32, label, fullPage }: LoaderProps) {
  const content = (
    <div className={cn("flex flex-col items-center justify-center gap-3", className)}>
      <Loader2 size={size} className="animate-spin text-brand-600" />
      {label && <p className="text-sm font-medium text-slate-500">{label}</p>}
    </div>
  )

  if (fullPage) {
    return (
      <div className="fixed inset-0 z-[200] flex items-center justify-center bg-white/80 backdrop-blur-sm dark:bg-slate-950/80">
        {content}
      </div>
    )
  }

  return content
}
