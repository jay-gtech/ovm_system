'use client'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, X, ExternalLink } from 'lucide-react'
import { cn } from '../../utils/cn'
import { timeAgo } from '../../utils/format'
import {
  useNotifications,
  useUnreadNotificationCount,
  useMarkNotificationRead,
} from '../../modules/notifications/hooks/useNotifications'
import type { NotificationType } from '../../types'

const TYPE_DOT: Record<NotificationType, string> = {
  ALERT_ESCALATED:      'bg-orange-400',
  SLA_BREACHED:         'bg-red-500',
  CRITICAL_EXPOSURE:    'bg-red-500',
  UNRESOLVED_HIGH_RISK: 'bg-amber-400',
}

const ENTITY_ROUTE: Record<string, string> = {
  alert: '/alerts',
  invoice: '/invoices',
  payment: '/payments',
}

export function AlertBell() {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  // Lightweight poll for the badge count — refetches every 60 s.
  const { data: countData } = useUnreadNotificationCount()
  const unread = countData?.unread_count ?? 0

  // Dropdown shows latest 10 notifications (newest-first).
  const { data: listData } = useNotifications({ limit: 10, skip: 0 })
  const notifications = listData?.items ?? []

  const { mutate: markRead } = useMarkNotificationRead()

  const handleItemClick = (id: string, entityType?: string | null, entityId?: string | null) => {
    markRead(id)
    setOpen(false)
    const base = entityType ? ENTITY_ROUTE[entityType] : null
    if (base && entityId) navigate(`${base}/${entityId}`)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="relative flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
        aria-label="Notifications"
      >
        <Bell size={18} />
        {unread > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white leading-none">
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-11 z-50 w-84 rounded-xl border border-slate-200 bg-white shadow-xl overflow-hidden"
               style={{ width: '22rem' }}>

            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
              <div className="flex items-center gap-2">
                <Bell size={14} className="text-slate-400" />
                <span className="text-sm font-semibold text-slate-900">Notifications</span>
                {unread > 0 && (
                  <span className="rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-bold text-red-600">
                    {unread} unread
                  </span>
                )}
              </div>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => { setOpen(false); navigate('/notifications') }}
                  className="text-slate-400 hover:text-brand-600 transition-colors p-1"
                  title="View all"
                >
                  <ExternalLink size={14} />
                </button>
                <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600 p-1">
                  <X size={14} />
                </button>
              </div>
            </div>

            {/* List */}
            <div className="max-h-80 overflow-y-auto divide-y divide-slate-50">
              {notifications.length === 0 ? (
                <div className="px-4 py-8 text-center text-sm text-slate-400">
                  No notifications yet.
                </div>
              ) : (
                notifications.map(n => {
                  const isUnread = n.status !== 'READ'
                  const dotColor = TYPE_DOT[n.notification_type] ?? 'bg-slate-300'
                  return (
                    <button
                      key={n.id}
                      className={cn(
                        'w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors',
                        isUnread && 'bg-slate-50/80'
                      )}
                      onClick={() => handleItemClick(n.id, n.related_entity_type, n.related_entity_id)}
                    >
                      <div className="flex items-start gap-2">
                        <span className={`mt-1.5 h-2 w-2 rounded-full shrink-0 ${dotColor}`} />
                        <div className="min-w-0 flex-1">
                          <p className={cn(
                            'text-xs leading-snug line-clamp-2',
                            isUnread ? 'font-semibold text-slate-800' : 'text-slate-600'
                          )}>
                            {n.title}
                          </p>
                          <p className="mt-0.5 text-[10px] text-slate-400 truncate">{n.message}</p>
                          <p className="mt-0.5 text-[10px] text-slate-400">{timeAgo(n.created_at)}</p>
                        </div>
                      </div>
                    </button>
                  )
                })
              )}
            </div>

            {/* Footer */}
            <div className="border-t border-slate-100 px-4 py-2.5">
              <button
                onClick={() => { setOpen(false); navigate('/notifications') }}
                className="w-full text-center text-xs text-brand-600 hover:text-brand-700 font-medium transition-colors"
              >
                View all notifications →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
