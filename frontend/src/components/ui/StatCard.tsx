import { type LucideIcon } from 'lucide-react'
import { cn } from '../../utils/cn'

interface StatCardProps {
  title: string
  value: string
  sub?: string
  icon: LucideIcon
  color?: 'blue' | 'green' | 'amber' | 'red' | 'purple' | 'teal'
  trend?: { value: string; up: boolean }
}

const colorMap = {
  blue:   { bg: 'bg-blue-50',   icon: 'bg-blue-100 text-blue-600',   border: 'border-blue-100' },
  green:  { bg: 'bg-green-50',  icon: 'bg-green-100 text-green-600', border: 'border-green-100' },
  amber:  { bg: 'bg-amber-50',  icon: 'bg-amber-100 text-amber-600', border: 'border-amber-100' },
  red:    { bg: 'bg-red-50',    icon: 'bg-red-100 text-red-600',     border: 'border-red-100' },
  purple: { bg: 'bg-purple-50', icon: 'bg-purple-100 text-purple-600', border: 'border-purple-100' },
  teal:   { bg: 'bg-teal-50',   icon: 'bg-teal-100 text-teal-600',   border: 'border-teal-100' },
}

export function StatCard({ title, value, sub, icon: Icon, color = 'blue', trend }: StatCardProps) {
  const c = colorMap[color]
  return (
    <div className={cn('rounded-xl border bg-white p-5 shadow-sm flex items-start gap-4', c.border)}>
      <div className={cn('flex h-11 w-11 shrink-0 items-center justify-center rounded-lg', c.icon)}>
        <Icon size={20} />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wider text-slate-500">{title}</p>
        <p className="mt-1 text-2xl font-bold text-slate-900">{value}</p>
        {trend && (
          <p className={cn('mt-1 text-xs font-medium', trend.up ? 'text-green-600' : 'text-red-500')}>
            {trend.up ? '↑' : '↓'} {trend.value}
          </p>
        )}
        {sub && !trend && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
      </div>
    </div>
  )
}
