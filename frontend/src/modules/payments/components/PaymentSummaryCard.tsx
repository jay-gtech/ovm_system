import { formatINR } from '../../../utils/format'
import { Card, CardContent } from '../../../components/ui/Card'
import { CreditCard, CheckCircle2, AlertCircle } from 'lucide-react'

interface PaymentSummaryCardProps {
  totalAmount: number
  paidAmount: number
  outstandingAmount: number
}

export function PaymentSummaryCard({ totalAmount, paidAmount, outstandingAmount }: PaymentSummaryCardProps) {
  const percentPaid = (paidAmount / totalAmount) * 100

  return (
    <Card className="overflow-hidden border-slate-200 shadow-sm">
      <div className="bg-slate-50 border-b border-slate-100 px-4 py-3">
        <h3 className="text-sm font-bold text-slate-700 flex items-center gap-2">
          <CreditCard size={16} className="text-brand-600" />
          Financial Summary
        </h3>
      </div>
      <CardContent className="p-5">
        <div className="space-y-4">
          <div className="flex items-end justify-between">
            <div>
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Total Invoice</p>
              <p className="text-2xl font-bold text-slate-900">{formatINR(totalAmount)}</p>
            </div>
            <div className="text-right">
              <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Status</p>
              <p className={`text-xs font-bold ${outstandingAmount === 0 ? 'text-green-600' : 'text-amber-600'}`}>
                {outstandingAmount === 0 ? 'FULLY PAID' : 'PENDING BALANCE'}
              </p>
            </div>
          </div>

          <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ${outstandingAmount === 0 ? 'bg-green-500' : 'bg-brand-500'}`}
              style={{ width: `${Math.min(percentPaid, 100)}%` }}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-lg bg-green-50 border border-green-100 p-3">
              <div className="flex items-center gap-2 text-green-700 mb-1">
                <CheckCircle2 size={14} />
                <span className="text-[10px] font-bold uppercase tracking-wider">Paid</span>
              </div>
              <p className="text-lg font-bold text-green-700">{formatINR(paidAmount)}</p>
            </div>
            <div className="rounded-lg bg-amber-50 border border-amber-100 p-3">
              <div className="flex items-center gap-2 text-amber-700 mb-1">
                <AlertCircle size={14} />
                <span className="text-[10px] font-bold uppercase tracking-wider">Outstanding</span>
              </div>
              <p className="text-lg font-bold text-amber-700">{formatINR(outstandingAmount)}</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
