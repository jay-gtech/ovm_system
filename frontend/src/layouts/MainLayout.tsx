import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { cn } from '../utils/cn'

export function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />
      <Header
        onMenuClick={() => setMobileOpen(!mobileOpen)}
        sidebarCollapsed={collapsed}
      />
      <main className={cn(
        'pt-16 min-h-screen transition-all duration-300',
        collapsed ? 'lg:pl-20' : 'lg:pl-64'
      )}>
        <div className="mx-auto max-w-7xl p-4 sm:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
