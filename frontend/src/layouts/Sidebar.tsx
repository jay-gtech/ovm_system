import { NavLink } from 'react-router-dom'
import { ChevronLeft, ChevronRight, LogOut } from 'lucide-react'
import { cn } from '../utils/cn'
import { appRoutes } from '../routes/appRoutes'
import { useAuthStore } from '../store/authStore'
import { authApi } from '../api/auth'

interface SidebarProps {
  collapsed: boolean
  setCollapsed: (v: boolean) => void
  mobileOpen: boolean
  setMobileOpen: (v: boolean) => void
}

export function Sidebar({ collapsed, setCollapsed, mobileOpen, setMobileOpen }: SidebarProps) {
  const { user, logout } = useAuthStore()
  const initials = user?.full_name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2) ?? 'U'
  const roleLabel = user?.is_superuser ? 'Superuser' : 'Member'

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } finally {
      logout()
    }
  }

  return (
    <>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 bg-slate-900/50 backdrop-blur-sm lg:hidden" onClick={() => setMobileOpen(false)} />
      )}

      <aside className={cn(
        'fixed inset-y-0 left-0 z-50 flex flex-col bg-slate-900 transition-all duration-300',
        collapsed ? 'w-20' : 'w-64',
        mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      )}>
        {/* Logo */}
        <div className={cn(
          'flex h-16 items-center border-b border-slate-800 shrink-0',
          collapsed ? 'justify-center px-4' : 'justify-between px-5'
        )}>
          {!collapsed && (
            <div>
              <span className="text-lg font-bold text-white tracking-tight">OVM</span>
              <span className="ml-1 text-lg font-bold text-brand-400">System</span>
            </div>
          )}
          {collapsed && <span className="text-xl font-black text-brand-400">O</span>}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex h-7 w-7 items-center justify-center rounded-md text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
          >
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
          {appRoutes.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) => cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all group relative',
                isActive
                  ? 'bg-brand-600 text-white'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white',
                collapsed && 'justify-center px-2'
              )}
              title={collapsed ? item.label : ''}
            >
              <item.icon size={18} className="shrink-0" />
              {!collapsed && <span className="flex-1">{item.label}</span>}
              {!collapsed && item.badge && (
                <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-brand-500/30 px-1.5 text-[10px] font-bold text-brand-300">
                  {item.badge}
                </span>
              )}
              {collapsed && item.badge && (
                <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-brand-400" />
              )}
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="border-t border-slate-800 p-3 shrink-0">
          <div className={cn('flex items-center gap-3', collapsed && 'flex-col gap-2')}>
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white text-xs font-bold">
              {initials}
            </div>
            {!collapsed && (
              <>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs font-semibold text-white">{user?.full_name}</p>
                  <p className="truncate text-[10px] text-slate-400">{roleLabel}</p>
                </div>
                <button onClick={() => void handleLogout()} className="text-slate-500 hover:text-red-400 transition-colors" title="Logout">
                  <LogOut size={15} />
                </button>
              </>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}
