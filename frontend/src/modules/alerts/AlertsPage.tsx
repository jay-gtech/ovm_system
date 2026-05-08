import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bell, CheckCheck, ShieldAlert, AlertTriangle, Info,
  ChevronLeft, ChevronRight,
} from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Card, CardContent } from '../../components/ui/Card'
import { Loader } from '../../components/feedback/Loader'
import { useAlerts, useAcknowledgeAlert, useResolveAlert, useBulkAcknowledgeAlerts } from './hooks/useAlerts'
import { timeAgo } from '../../utils/format'
import type { AlertSeverity, AlertStatus, AlertType, BackendAlert } from '../../types'

const PAGE_SIZE = 50

// ---------------------------------------------------------------------------
// Severity helpers
// ---------------------------------------------------------------------------
const SEVERITY_BORDER: Record<AlertSeverity, string> = {
  CRITICAL: 'border-l-red-500',
  HIGH: 'border-l-orange-400',
  MEDIUM: 'border-l-amber-400',
  LOW: 'border-l-blue-400',
}

const SEVERITY_ICON: Record<AlertSeverity, React.ReactNode> = {
  CRITICAL: <ShieldAlert size={14} className="text-red-500" />,
  HIGH: <AlertTriangle size={14} className="text-orange-400" />,
  MEDIUM: <AlertTriangle size={14} className="text-amber-400" />,
  LOW: <Info size={14} className="text-blue-400" />,
}

const SEVERITY_STAT: Record<string, string> = {
  ALL: 'border-slate-200 bg-slate-50 text-slate-700',
  CRITICAL: 'border-red-100 bg-red-50 text-red-700',
  HIGH: 'border-orange-100 bg-orange-50 text-orange-700',
  MEDIUM: 'border-amber-100 bg-amber-50 text-amber-700',
  LOW: 'border-blue-100 bg-blue-50 text-blue-700',
}

// ---------------------------------------------------------------------------
// Alert type labels
// ---------------------------------------------------------------------------
const ALERT_TYPE_LABEL: Record<AlertType, string> = {
  OVERDUE_INVOICE: 'Overdue Invoice',
  UNSETTLED_VENDOR_LIABILITY: 'Unsettled Liability',
  WORKFLOW_STALL: 'Workflow Stall',
  HIGH_FINANCIAL_EXPOSURE: 'High Exposure',
}

// ---------------------------------------------------------------------------
// Entity navigation
// ---------------------------------------------------------------------------
const ENTITY_ROUTE: Record<string, string> = {
  invoice: '/invoices',
  payment: '/payments',
  settlement: '/settlements',
}

function entityNavPath(entityType: string, entityId: string): string | null {
  const base = ENTITY_ROUTE[entityType]
  return base ? `${base}/${entityId}` : null
}

// ---------------------------------------------------------------------------
// Status badge (separate from severity)
// ---------------------------------------------------------------------------
function AlertStatusBadge({ status }: { status: AlertStatus }) {
  const cfg: Record<AlertStatus, { label: string; className: string }> = {
    OPEN: { label: 'Open', className: 'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium bg-red-50 text-red-700 border-red-200' },
    ACKNOWLEDGED: { label: 'Acknowledged', className: 'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium bg-indigo-50 text-indigo-700 border-indigo-200' },
    RESOLVED: { label: 'Resolved', className: 'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium bg-green-50 text-green-700 border-green-200' },
  }
  return <span className={cfg[status].className}>{cfg[status].label}</span>
}

// ---------------------------------------------------------------------------
// Single alert row
// ---------------------------------------------------------------------------
function AlertRow({ alert, onAck, onResolve, isActing }: {
  alert: BackendAlert
  onAck: (id: string) => void
  onResolve: (id: string) => void
  isActing: boolean
}) {
  const navigate = useNavigate()
  const navPath = entityNavPath(alert.entity_type, alert.entity_id)
  const severity = alert.severity as AlertSeverity
  const status = alert.status as AlertStatus

  return (
    <div className={`border-l-4 ${SEVERITY_BORDER[severity]} px-5 py-4 hover:bg-slate-50/80 transition-colors`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Badges row */}
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <StatusBadge status={severity} />
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500 uppercase tracking-wide">
              {ALERT_TYPE_LABEL[alert.alert_type] ?? alert.alert_type}
            </span>
            <AlertStatusBadge status={status} />
          </div>

          {/* Title + message */}
          <p className="text-sm font-semibold text-slate-800 leading-snug">{alert.title}</p>
          <p className="mt-0.5 text-sm text-slate-600 leading-relaxed">{alert.message}</p>

          {/* Timestamp + entity type */}
          <div className="mt-1.5 flex items-center gap-3 text-[11px] text-slate-400">
            <span>{timeAgo(alert.triggered_at)}</span>
            <span className="text-slate-300">·</span>
            <span className="capitalize">{alert.entity_type}</span>
            {alert.acknowledged_at && (
              <>
                <span className="text-slate-300">·</span>
                <span>Acknowledged {timeAgo(alert.acknowledged_at)}</span>
              </>
            )}
            {alert.resolved_at && (
              <>
                <span className="text-slate-300">·</span>
                <span>Resolved {timeAgo(alert.resolved_at)}</span>
              </>
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 shrink-0 flex-wrap justify-end">
          {navPath && (
            <button
              onClick={() => navigate(navPath)}
              className="rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-500 hover:border-brand-300 hover:text-brand-600 transition-colors whitespace-nowrap"
            >
              View {alert.entity_type}
            </button>
          )}
          {status === 'OPEN' && (
            <button
              disabled={isActing}
              onClick={() => onAck(alert.id)}
              className="rounded-md border border-indigo-200 px-2.5 py-1 text-xs text-indigo-600 hover:bg-indigo-50 transition-colors disabled:opacity-50 whitespace-nowrap"
            >
              Acknowledge
            </button>
          )}
          {(status === 'OPEN' || status === 'ACKNOWLEDGED') && (
            <button
              disabled={isActing}
              onClick={() => onResolve(alert.id)}
              className="rounded-md border border-green-200 px-2.5 py-1 text-xs text-green-700 hover:bg-green-50 transition-colors disabled:opacity-50 whitespace-nowrap"
            >
              Resolve
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
export default function AlertsPage() {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')
  const [typeFilter, setTypeFilter] = useState<string>('ALL')
  const [page, setPage] = useState(0)

  const filters = {
    skip: page * PAGE_SIZE,
    limit: PAGE_SIZE,
    ...(severityFilter !== 'ALL' ? { severity: severityFilter } : {}),
    ...(statusFilter !== 'ALL' ? { status: statusFilter } : {}),
    ...(typeFilter !== 'ALL' ? { alert_type: typeFilter } : {}),
  }

  const { data, isLoading, isError } = useAlerts(filters)
  const { mutate: ack, isPending: isAcking } = useAcknowledgeAlert()
  const { mutate: resolve, isPending: isResolving } = useResolveAlert()
  const { mutate: bulkAck, isPending: isBulkAcking } = useBulkAcknowledgeAlerts()
  const isActing = isAcking || isResolving || isBulkAcking

  const alerts = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const countBySeverity = (s: string) =>
    s === 'ALL' ? total : alerts.filter(a => a.severity === s).length

  // Open count across the whole filtered result set (not just current page)
  const openCount = statusFilter === 'OPEN'
    ? total
    : alerts.filter(a => a.status === 'OPEN').length

  // Bulk-acknowledge passes current severity+type filters so the server-side
  // scope matches exactly what the user is viewing.  Tenant isolation and
  // pagination-independence are enforced server-side in a single transaction.
  const handleBulkAcknowledge = () => {
    bulkAck({
      ...(severityFilter !== 'ALL' ? { severity: severityFilter } : {}),
      ...(typeFilter !== 'ALL' ? { alert_type: typeFilter } : {}),
    })
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title="Alert Center"
        subtitle={
          statusFilter === 'OPEN'
            ? `${total} open alert${total !== 1 ? 's' : ''}`
            : `${openCount} open on this page`
        }
        actions={
          <Button
            variant="outline"
            className="gap-2"
            onClick={handleBulkAcknowledge}
            disabled={openCount === 0 || isActing}
          >
            <CheckCheck size={15} />
            {isBulkAcking ? 'Acknowledging…' : 'Acknowledge all open'}
          </Button>
        }
      />

      {/* Severity stat cards */}
      <div className="grid gap-3 sm:grid-cols-5">
        {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(s => (
          <button
            key={s}
            onClick={() => { setSeverityFilter(s); setPage(0) }}
            className={`rounded-xl border px-4 py-3 text-left transition-all ${SEVERITY_STAT[s]} ${severityFilter === s ? 'ring-2 ring-brand-400' : ''}`}
          >
            <div className="flex items-center gap-1.5 mb-0.5">
              {s !== 'ALL' && SEVERITY_ICON[s as AlertSeverity]}
              <p className="text-xs font-medium opacity-70">{s === 'ALL' ? 'All Alerts' : s}</p>
            </div>
            <p className="text-2xl font-bold">{countBySeverity(s)}</p>
          </button>
        ))}
      </div>

      {/* Status + Type filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
          {(['ALL', 'OPEN', 'ACKNOWLEDGED', 'RESOLVED'] as const).map(s => (
            <button
              key={s}
              onClick={() => { setStatusFilter(s); setPage(0) }}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                statusFilter === s
                  ? 'bg-brand-500 text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {s === 'ALL' ? 'All Status' : s.charAt(0) + s.slice(1).toLowerCase()}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
          {([
            ['ALL', 'All Types'],
            ['OVERDUE_INVOICE', 'Overdue'],
            ['UNSETTLED_VENDOR_LIABILITY', 'Unsettled'],
            ['WORKFLOW_STALL', 'Stall'],
            ['HIGH_FINANCIAL_EXPOSURE', 'Exposure'],
          ] as const).map(([val, label]) => (
            <button
              key={val}
              onClick={() => { setTypeFilter(val); setPage(0) }}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                typeFilter === val
                  ? 'bg-brand-500 text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Alert feed */}
      <Card>
        <div className="border-b border-slate-100 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell size={15} className="text-slate-400" />
            <p className="text-sm font-semibold text-slate-700">Alert Feed</p>
          </div>
          <p className="text-xs text-slate-400">{total} total</p>
        </div>

        <CardContent className="p-0">
          {isLoading && (
            <div className="flex justify-center py-16">
              <Loader />
            </div>
          )}

          {isError && (
            <div className="px-4 py-12 text-center text-sm text-red-500">
              Failed to load alerts. Check your connection and try again.
            </div>
          )}

          {!isLoading && !isError && (
            <div className="divide-y divide-slate-50">
              {alerts.length === 0 ? (
                <div className="px-4 py-16 text-center text-sm text-slate-400">
                  No alerts match the current filters.
                </div>
              ) : (
                alerts.map(alert => (
                  <AlertRow
                    key={alert.id}
                    alert={alert}
                    onAck={id => ack(id)}
                    onResolve={id => resolve(id)}
                    isActing={isActing}
                  />
                ))
              )}
            </div>
          )}
        </CardContent>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="border-t border-slate-100 px-4 py-3 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Page {page + 1} of {totalPages} · {total} alerts
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
