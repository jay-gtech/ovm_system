import { cn } from '../../utils/cn'
import type { OrderStatus, InvoiceStatus, VendorStatus, MatchStatus, AlertSeverity } from '../../types'

type AnyStatus = OrderStatus | InvoiceStatus | VendorStatus | MatchStatus | AlertSeverity | string

const statusConfig: Record<string, { label: string; className: string }> = {
  // Order statuses
  DRAFT:              { label: 'Draft',              className: 'bg-slate-100 text-slate-600 border-slate-200' },
  PENDING_APPROVAL:   { label: 'Pending Approval',   className: 'bg-amber-50 text-amber-700 border-amber-200' },
  APPROVED:           { label: 'Approved',           className: 'bg-blue-50 text-blue-700 border-blue-200' },
  ACKNOWLEDGED:       { label: 'Acknowledged',       className: 'bg-indigo-50 text-indigo-700 border-indigo-200' },
  IN_TRANSIT:         { label: 'In Transit',         className: 'bg-purple-50 text-purple-700 border-purple-200' },
  PARTIALLY_RECEIVED: { label: 'Partial Receipt',    className: 'bg-orange-50 text-orange-700 border-orange-200' },
  FULLY_RECEIVED:     { label: 'Fully Received',     className: 'bg-teal-50 text-teal-700 border-teal-200' },
  DELIVERED:          { label: 'Delivered',          className: 'bg-green-50 text-green-700 border-green-200' },
  INVOICED:           { label: 'Invoiced',           className: 'bg-cyan-50 text-cyan-700 border-cyan-200' },
  PAID:               { label: 'Paid',               className: 'bg-green-100 text-green-800 border-green-300' },
  CLOSED:             { label: 'Closed',             className: 'bg-slate-200 text-slate-600 border-slate-300' },
  DISPUTED:           { label: 'Disputed',           className: 'bg-red-50 text-red-700 border-red-200' },
  // Invoice statuses
  ISSUED:             { label: 'Issued',             className: 'bg-blue-50 text-blue-700 border-blue-200' },
  SENT:               { label: 'Sent',               className: 'bg-blue-50 text-blue-700 border-blue-200' },
  OVERDUE:            { label: 'Overdue',            className: 'bg-red-50 text-red-700 border-red-200' },
  PARTIALLY_PAID:     { label: 'Partially Paid',     className: 'bg-orange-50 text-orange-700 border-orange-200' },
  CANCELLED:          { label: 'Cancelled',          className: 'bg-slate-200 text-slate-600 border-slate-300' },
  // Match statuses
  MATCHED:            { label: 'Matched',            className: 'bg-green-50 text-green-700 border-green-200' },
  PARTIAL_MATCH:      { label: 'Partial Match',      className: 'bg-amber-50 text-amber-700 border-amber-200' },
  MISMATCH:           { label: 'Mismatch',           className: 'bg-red-50 text-red-700 border-red-200' },
  PENDING:            { label: 'Pending',            className: 'bg-slate-50 text-slate-600 border-slate-200' },
  // Vendor statuses
  ACTIVE:             { label: 'Active',             className: 'bg-green-50 text-green-700 border-green-200' },
  PENDING_KYC:        { label: 'Pending KYC',        className: 'bg-amber-50 text-amber-700 border-amber-200' },
  SUSPENDED:          { label: 'Suspended',          className: 'bg-red-50 text-red-700 border-red-200' },
  INACTIVE:           { label: 'Inactive',           className: 'bg-slate-100 text-slate-500 border-slate-200' },
  // Alert severities
  CRITICAL:           { label: 'Critical',           className: 'bg-red-50 text-red-700 border-red-200' },
  HIGH:               { label: 'High',               className: 'bg-orange-50 text-orange-700 border-orange-200' },
  MEDIUM:             { label: 'Medium',             className: 'bg-amber-50 text-amber-700 border-amber-200' },
  LOW:                { label: 'Low',                className: 'bg-blue-50 text-blue-700 border-blue-200' },
  // Payment
  RECEIVED:           { label: 'Received',           className: 'bg-green-100 text-green-800 border-green-300' },
  FAILED:             { label: 'Failed',             className: 'bg-red-100 text-red-800 border-red-300' },
  UNMATCHED:          { label: 'Unmatched',          className: 'bg-red-50 text-red-700 border-red-200' },
}

interface StatusBadgeProps {
  status: AnyStatus
  size?: 'sm' | 'md'
}

export function StatusBadge({ status, size = 'sm' }: StatusBadgeProps) {
  const config = statusConfig[status] ?? { label: status, className: 'bg-slate-100 text-slate-600 border-slate-200' }
  return (
    <span className={cn(
      'inline-flex items-center rounded-full border font-medium',
      size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm',
      config.className
    )}>
      {config.label}
    </span>
  )
}
