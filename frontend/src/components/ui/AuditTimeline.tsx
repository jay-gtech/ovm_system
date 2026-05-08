import type { AuditLog } from '../../types'
import { useAuditTimeline } from '../../hooks/useAuditTimeline'
import { Loader } from '../feedback/Loader'

// ─── Action metadata ──────────────────────────────────────────────────────────

const ACTION_LABELS: Record<string, string> = {
  INVOICE_CREATED:        'Invoice Created',
  INVOICE_UPDATED:        'Field Updated',
  INVOICE_STATUS_CHANGED: 'Status Changed',
  INVOICE_CANCELLED:      'Invoice Cancelled',
  PAYMENT_CREATED:        'Payment Recorded',
  PAYMENT_RECEIVED:       'Payment Received',
  PAYMENT_FAILED:         'Payment Failed',
  PAYMENT_CANCELLED:      'Payment Cancelled',
  PAYMENT_STATUS_CHANGED: 'Payment Status Changed',
  SETTLEMENT_CREATED:     'Settlement Created',
  SETTLEMENT_COMPLETED:   'Settlement Completed',
  SETTLEMENT_CANCELLED:   'Settlement Cancelled',
  SETTLEMENT_STATUS_CHANGED: 'Settlement Status Changed',
  VENDOR_CREATED:         'Vendor Created',
  VENDOR_UPDATED:         'Vendor Updated',
  VENDOR_STATUS_CHANGED:  'Status Changed',
}

function actionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action.replace(/_/g, ' ')
}

type DotVariant = 'green' | 'red' | 'blue' | 'yellow' | 'slate'

function dotVariant(action: string): DotVariant {
  if (action.endsWith('_CREATED'))  return 'green'
  if (action.endsWith('_CANCELLED') || action.endsWith('_FAILED')) return 'red'
  if (action.includes('STATUS') || action.endsWith('_RECEIVED') || action.endsWith('_COMPLETED')) return 'blue'
  if (action.endsWith('_UPDATED'))  return 'yellow'
  return 'slate'
}

const DOT_CLASSES: Record<DotVariant, string> = {
  green:  'bg-emerald-500',
  red:    'bg-red-500',
  blue:   'bg-blue-500',
  yellow: 'bg-amber-400',
  slate:  'bg-slate-400',
}

const BADGE_CLASSES: Record<DotVariant, string> = {
  green:  'bg-emerald-50 text-emerald-700 border border-emerald-200',
  red:    'bg-red-50 text-red-700 border border-red-200',
  blue:   'bg-blue-50 text-blue-700 border border-blue-200',
  yellow: 'bg-amber-50 text-amber-700 border border-amber-200',
  slate:  'bg-slate-100 text-slate-600 border border-slate-200',
}

// ─── Formatting helpers ───────────────────────────────────────────────────────

function formatTs(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: true,
  })
}

function shortId(id?: string): string {
  if (!id) return 'System'
  return id.slice(0, 8).toUpperCase()
}

// ─── Single audit entry ───────────────────────────────────────────────────────

interface AuditEntryProps {
  entry: AuditLog
  isLast: boolean
}

function AuditEntry({ entry, isLast }: AuditEntryProps) {
  const variant = dotVariant(entry.action)

  return (
    <div className="flex gap-3">
      {/* Timeline spine */}
      <div className="flex flex-col items-center">
        <div className={`w-2.5 h-2.5 rounded-full mt-1 shrink-0 ${DOT_CLASSES[variant]}`} />
        {!isLast && <div className="w-px flex-1 bg-slate-200 mt-1" />}
      </div>

      {/* Content */}
      <div className={`pb-5 min-w-0 flex-1 ${isLast ? '' : ''}`}>
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${BADGE_CLASSES[variant]}`}>
            {actionLabel(entry.action)}
          </span>
          {entry.field_name && (
            <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
              {entry.field_name}
            </span>
          )}
        </div>

        {/* Field-level diff */}
        {entry.field_name && (entry.old_value !== undefined || entry.new_value !== undefined) && (
          <div className="flex items-center gap-2 text-xs mt-1 mb-1.5">
            {entry.old_value != null ? (
              <span className="font-mono bg-red-50 text-red-700 px-1.5 py-0.5 rounded line-through max-w-[140px] truncate">
                {entry.old_value}
              </span>
            ) : (
              <span className="text-slate-400 italic text-[10px]">empty</span>
            )}
            <span className="text-slate-400">→</span>
            {entry.new_value != null ? (
              <span className="font-mono bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded max-w-[140px] truncate">
                {entry.new_value}
              </span>
            ) : (
              <span className="text-slate-400 italic text-[10px]">empty</span>
            )}
          </div>
        )}

        {/* Actor + timestamp */}
        <div className="flex items-center gap-2 text-[11px] text-slate-400">
          <span className="font-medium text-slate-500">
            {entry.actor_user_id ? `User ${shortId(entry.actor_user_id)}` : 'System'}
          </span>
          {entry.actor_role && (
            <>
              <span>·</span>
              <span className="uppercase tracking-wide text-[10px]">{entry.actor_role}</span>
            </>
          )}
          <span>·</span>
          <span>{formatTs(entry.created_at)}</span>
        </div>

        {/* Reason (if set) */}
        {entry.reason && (
          <p className="mt-1 text-xs text-slate-500 italic">{entry.reason}</p>
        )}
      </div>
    </div>
  )
}

// ─── Public component ─────────────────────────────────────────────────────────

interface AuditTimelineProps {
  entityType: string
  entityId: string
  limit?: number
}

export function AuditTimeline({ entityType, entityId, limit = 50 }: AuditTimelineProps) {
  const { data, isLoading, error } = useAuditTimeline(entityType, entityId, { limit })

  if (isLoading) return <div className="py-4"><Loader /></div>

  if (error) {
    return (
      <p className="text-xs text-red-500 py-2">Could not load audit trail.</p>
    )
  }

  if (!data?.items.length) {
    return (
      <p className="text-xs text-slate-400 py-2 text-center">No audit records yet.</p>
    )
  }

  return (
    <div className="pt-2">
      {data.items.map((entry, i) => (
        <AuditEntry
          key={entry.id}
          entry={entry}
          isLast={i === data.items.length - 1}
        />
      ))}
      {data.total > data.items.length && (
        <p className="text-[11px] text-slate-400 pt-1 text-center">
          Showing {data.items.length} of {data.total} entries
        </p>
      )}
    </div>
  )
}
