'use client'
import { useState } from 'react'
import { Bell, X } from 'lucide-react'
import { cn } from '../../utils/cn'
import { mockAlerts } from '../../utils/mockData'
import { timeAgo } from '../../utils/format'
import { StatusBadge } from './StatusBadge'
import type { AlertSeverity } from '../../types'

export function AlertBell() {
  const [open, setOpen] = useState(false)
  const unread = mockAlerts.filter(a => !a.isRead).length

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
      >
        <Bell size={18} />
        {unread > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white leading-none">
            {unread}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-11 z-50 w-80 rounded-xl border border-slate-200 bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
              <span className="text-sm font-semibold text-slate-900">Alerts</span>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={16} />
              </button>
            </div>
            <div className="max-h-80 overflow-y-auto divide-y divide-slate-50">
              {mockAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={cn('px-4 py-3', !alert.isRead && 'bg-slate-50')}
                >
                  <div className="flex items-start gap-2">
                    <StatusBadge status={alert.severity as AlertSeverity} />
                    <p className="text-xs text-slate-600 leading-relaxed flex-1">{alert.message}</p>
                  </div>
                  <p className="mt-1 text-[10px] text-slate-400">{timeAgo(alert.createdAt)}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
