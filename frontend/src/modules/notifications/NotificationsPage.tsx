import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, CheckCheck, ChevronLeft, ChevronRight } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { Card, CardContent } from '../../components/ui/Card'
import { Loader } from '../../components/feedback/Loader'
import { useNotifications, useMarkNotificationRead } from './hooks/useNotifications'
import { timeAgo } from '../../utils/format'
import type { BackendNotification, NotificationType } from '../../types'

const PAGE_SIZE = 50

// ---------------------------------------------------------------------------
// Notification type display config
// ---------------------------------------------------------------------------
const TYPE_CONFIG: Record<NotificationType, { label: string; color: string }> = {
  ALERT_ESCALATED:     { label: 'Escalation',     color: 'bg-orange-100 text-orange-700 border-orange-200' },
  SLA_BREACHED:        { label: 'SLA Breach',      color: 'bg-red-100 text-red-700 border-red-200' },
  CRITICAL_EXPOSURE:   { label: 'Critical',        color: 'bg-red-50 text-red-700 border-red-200' },
  UNRESOLVED_HIGH_RISK:{ label: 'High Risk',       color: 'bg-amber-100 text-amber-700 border-amber-200' },
}

const ENTITY_ROUTE: Record<string, string> = {
  alert: '/alerts',
  invoice: '/invoices',
  payment: '/payments',
}

// ---------------------------------------------------------------------------
// Single notification row
// ---------------------------------------------------------------------------
function NotificationRow({
  notif,
  onRead,
  isActing,
}: {
  notif: BackendNotification
  onRead: (id: string) => void
  isActing: boolean
}) {
  const navigate = useNavigate()
  const cfg = TYPE_CONFIG[notif.notification_type] ?? {
    label: notif.notification_type,
    color: 'bg-slate-100 text-slate-600 border-slate-200',
  }
  const isUnread = notif.status !== 'READ'
  const navBase = notif.related_entity_type ? ENTITY_ROUTE[notif.related_entity_type] : null
  const navPath = navBase && notif.related_entity_id ? `${navBase}/${notif.related_entity_id}` : null

  const handleClick = () => {
    if (isUnread) onRead(notif.id)
    if (navPath) navigate(navPath)
  }

  return (
    <div
      className={`px-5 py-4 hover:bg-slate-50 transition-colors cursor-pointer ${isUnread ? 'bg-slate-50/70' : ''}`}
      onClick={handleClick}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cfg.color}`}>
              {cfg.label}
            </span>
            {notif.channel === 'EMAIL' && (
              <span className="text-[10px] text-slate-400 border border-slate-200 rounded-full px-2 py-0.5">
                Email
              </span>
            )}
            {isUnread && (
              <span className="h-1.5 w-1.5 rounded-full bg-brand-500 shrink-0" />
            )}
          </div>
          <p className="text-sm font-medium text-slate-800 leading-snug">{notif.title}</p>
          <p className="mt-0.5 text-sm text-slate-500 leading-relaxed line-clamp-2">{notif.message}</p>
          <p className="mt-1 text-[11px] text-slate-400">{timeAgo(notif.created_at)}</p>
        </div>

        <div className="flex gap-2 shrink-0">
          {isUnread && (
            <button
              disabled={isActing}
              onClick={e => { e.stopPropagation(); onRead(notif.id) }}
              className="rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-500 hover:bg-slate-100 disabled:opacity-50 transition-colors whitespace-nowrap"
            >
              Mark read
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function NotificationsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [typeFilter, setTypeFilter] = useState<string>('ALL')
  const [page, setPage] = useState(0)

  const filters = {
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    ...(statusFilter !== 'ALL' ? { status: statusFilter } : {}),
    ...(typeFilter !== 'ALL' ? { notification_type: typeFilter } : {}),
  }

  const { data, isLoading, isError } = useNotifications(filters)
  const { mutate: markRead, isPending: isMarking } = useMarkNotificationRead()

  const notifications = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)
  const unreadCount = notifications.filter(n => n.status !== 'READ').length

  const markAllRead = () => {
    notifications.filter(n => n.status !== 'READ').forEach(n => markRead(n.id))
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Notification Center"
        subtitle={`${unreadCount} unread on this page`}
        actions={
          <Button
            variant="outline"
            className="gap-2"
            onClick={markAllRead}
            disabled={unreadCount === 0 || isMarking}
          >
            <CheckCheck size={15} /> Mark all read
          </Button>
        }
      />

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
          {(['ALL', 'SENT', 'PENDING', 'READ', 'FAILED'] as const).map(s => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(0) }}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                statusFilter === s ? 'bg-brand-500 text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {s === 'ALL' ? 'All' : s.charAt(0) + s.slice(1).toLowerCase()}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
          {([
            ['ALL', 'All Types'],
            ['ALERT_ESCALATED', 'Escalation'],
            ['SLA_BREACHED', 'SLA Breach'],
            ['CRITICAL_EXPOSURE', 'Critical'],
            ['UNRESOLVED_HIGH_RISK', 'High Risk'],
          ] as const).map(([val, label]) => (
            <button
              key={val}
              onClick={() => { setTypeFilter(val); setPage(0) }}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                typeFilter === val ? 'bg-brand-500 text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <Card>
        <div className="border-b border-slate-100 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell size={15} className="text-slate-400" />
            <p className="text-sm font-semibold text-slate-700">Notifications</p>
          </div>
          <p className="text-xs text-slate-400">{total} total</p>
        </div>

        <CardContent className="p-0">
          {isLoading && (
            <div className="flex justify-center py-16"><Loader /></div>
          )}
          {isError && (
            <div className="px-4 py-12 text-center text-sm text-red-500">
              Failed to load notifications.
            </div>
          )}
          {!isLoading && !isError && (
            <div className="divide-y divide-slate-50">
              {notifications.length === 0 ? (
                <div className="px-4 py-16 text-center text-sm text-slate-400">
                  No notifications match the current filters.
                </div>
              ) : (
                notifications.map(n => (
                  <NotificationRow
                    key={n.id}
                    notif={n}
                    onRead={id => markRead(id)}
                    isActing={isMarking}
                  />
                ))
              )}
            </div>
          )}
        </CardContent>

        {totalPages > 1 && (
          <div className="border-t border-slate-100 px-4 py-3 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Page {page + 1} of {totalPages} · {total} notifications
            </p>
            <div className="flex gap-2">
              <button
                disabled={page === 0}
                onClick={() => setPage(p => p - 1)}
                className="rounded-md border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft size={14} />
              </button>
              <button
                disabled={page >= totalPages - 1}
                onClick={() => setPage(p => p + 1)}
                className="rounded-md border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50 disabled:opacity-40 transition-colors"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </Card>
    </div>
  )
}
