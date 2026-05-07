import { formatINR, formatDate } from '../../../utils/format'
import { StatusBadge } from '../../../components/ui/StatusBadge'
import { Check, X, Ban, Clock } from 'lucide-react'
import type { Payment, PaymentStatus } from '../../../types'
import { useUpdatePaymentStatus } from '../../../hooks/usePayments'

interface PaymentTableProps {
  payments: Payment[]
  isLoading?: boolean
}

export function PaymentTable({ payments, isLoading }: PaymentTableProps) {
  const updateStatus = useUpdatePaymentStatus()

  const handleStatusUpdate = (id: string, status: PaymentStatus) => {
    if (confirm(`Are you sure you want to update payment status to ${status}?`)) {
      updateStatus.mutate({ id, status })
    }
  }

  if (isLoading) return <div className="py-8 text-center text-slate-400">Loading payments...</div>
  if (payments.length === 0) return <div className="py-8 text-center text-slate-400 font-medium">No payment history found.</div>

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 bg-slate-50">
            {['Reference', 'Amount', 'Method', 'Date', 'Status', 'Actions'].map(h => (
              <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-50">
          {payments.map((p) => (
            <tr key={p.id} className="hover:bg-slate-50/60 transition-colors">
              <td className="px-4 py-3 font-mono text-xs font-semibold text-brand-600">
                {p.payment_reference}
              </td>
              <td className="px-4 py-3 font-semibold text-slate-900 tabular-nums">
                {formatINR(p.amount)}
              </td>
              <td className="px-4 py-3">
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-500 uppercase">
                  {p.payment_method.replace('_', ' ')}
                </span>
              </td>
              <td className="px-4 py-3 text-xs text-slate-500 whitespace-nowrap">
                {formatDate(p.payment_date)}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={p.status} />
              </td>
              <td className="px-4 py-3">
                {p.status === 'PENDING' && (
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => handleStatusUpdate(p.id, 'RECEIVED')}
                      className="p-1 text-green-600 hover:bg-green-50 rounded"
                      title="Mark as Received"
                    >
                      <Check size={14} />
                    </button>
                    <button
                      onClick={() => handleStatusUpdate(p.id, 'FAILED')}
                      className="p-1 text-red-600 hover:bg-red-50 rounded"
                      title="Mark as Failed"
                    >
                      <X size={14} />
                    </button>
                    <button
                      onClick={() => handleStatusUpdate(p.id, 'CANCELLED')}
                      className="p-1 text-slate-400 hover:bg-slate-50 rounded"
                      title="Cancel Payment"
                    >
                      <Ban size={14} />
                    </button>
                  </div>
                )}
                {p.status !== 'PENDING' && (
                  <span className="text-[10px] text-slate-300 italic">Finalized</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
