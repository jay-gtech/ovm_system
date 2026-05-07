import { Menu, Search, ChevronDown } from 'lucide-react'
import { cn } from '../utils/cn'
import { AlertBell } from '../components/ui/AlertBell'
import { useAuthStore } from '../store/authStore'

interface HeaderProps {
  onMenuClick: () => void
  sidebarCollapsed: boolean
}

export function Header({ onMenuClick, sidebarCollapsed }: HeaderProps) {
  const { user } = useAuthStore()
  const initials = user?.full_name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2) ?? 'U'
  const roleLabel = user?.is_superuser ? 'Superuser' : 'Member'

  return (
    <header className={cn(
      'fixed top-0 right-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-6 transition-all duration-300',
      sidebarCollapsed ? 'lg:left-20' : 'lg:left-64',
      'left-0'
    )}>
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 lg:hidden"
        >
          <Menu size={18} />
        </button>
        <div className="hidden sm:flex items-center gap-2 h-9 px-3 rounded-lg bg-slate-100 text-slate-400 w-56 cursor-text">
          <Search size={14} />
          <span className="text-sm">Search anything...</span>
        </div>
      </div>

      <div className="flex items-center gap-1">
        <AlertBell />
        <div className="mx-2 h-6 w-px bg-slate-200" />
        <button className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-100 transition-colors">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-brand-700 text-xs font-bold">
            {initials}
          </div>
          <div className="hidden text-left md:block">
            <p className="text-sm font-semibold text-slate-900 leading-none">{user?.full_name ?? 'User'}</p>
            <p className="text-[10px] text-slate-400 mt-0.5">{roleLabel}</p>
          </div>
          <ChevronDown size={14} className="text-slate-400 hidden md:block" />
        </button>
      </div>
    </header>
  )
}
