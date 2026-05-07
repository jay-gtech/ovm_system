import { CheckCircle2, AlertCircle, Zap } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Card, CardContent } from '../../components/ui/Card'
import { Button } from '../../components/ui/Button'
import { mockPayments, mockInvoices } from '../../utils/mockData'
import { formatINR, formatDate } from '../../utils/format'

const suggestions = [
  { paymentId: '3', ref: 'TXN-97011', amount: 280000, invoiceId: '1', invoiceNumber: 'INV-2025-0142', invoiceAmount: 100300, confidence: 72, reason: 'Amount fuzzy match + same vendor' },
  { paymentId: '4', ref: 'TXN-96544', amount: 450000, invoiceId: '6', invoiceNumber: 'INV-2025-0137', invoiceAmount: 660800, confidence: 54, reason: 'Vendor description semantic match' },
]

export default function ReconcilePage() {
  const unmatched = mockPayments.filter(p => p.status === 'UNMATCHED')
  const unmatchedTotal = unmatched.reduce((a, p) => a + p.amount, 0)

  return (
    <div className="space-y-5">
      <PageHeader title="Payment Reconciliation" subtitle="Match unidentified payments to their invoices using AI suggestions" />

      <div className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3">
        <AlertCircle size={16} className="text-amber-500 mt-0.5 shrink-0" />
        <div>
          <p className="text-sm font-semibold text-amber-800">{unmatched.length} unmatched payments — {formatINR(unmatchedTotal)} in suspense</p>
          <p className="text-xs text-amber-600 mt-0.5">Review AI suggestions below and confirm matches manually.</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: 'In Suspense', value: unmatched.length, color: 'border-amber-100 bg-amber-50 text-amber-700' },
          { label: 'Suspense Value', value: formatINR(unmatchedTotal), color: 'border-red-100 bg-red-50 text-red-700' },
          { label: 'AI Suggestions Ready', value: suggestions.length, color: 'border-purple-100 bg-purple-50 text-purple-700' },
        ].map(s => (
          <div key={s.label} className={`rounded-xl border px-5 py-4 ${s.color}`}>
            <p className="text-xs font-medium opacity-70">{s.label}</p>
            <p className="text-2xl font-bold mt-0.5">{s.value}</p>
          </div>
        ))}
      </div>

      <div className="space-y-4">
        {unmatched.map(payment => {
          const suggestion = suggestions.find(s => s.paymentId === payment.id)
          return (
            <Card key={payment.id}>
              <div className="border-b border-slate-100 bg-slate-50 px-5 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-sm font-bold text-brand-600">{payment.paymentReference}</span>
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">UNMATCHED</span>
                </div>
                <p className="text-lg font-bold text-slate-900">{formatINR(payment.amount)}</p>
              </div>
              <CardContent className="p-5">
                <div className="grid gap-4 lg:grid-cols-2">
                  {/* Payment details */}
                  <div className="space-y-2">
                    <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Payment Details</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div><p className="text-xs text-slate-400">Date</p><p className="font-medium text-slate-700">{formatDate(payment.paymentDate)}</p></div>
                      <div><p className="text-xs text-slate-400">Method</p><p className="font-medium text-slate-700">{payment.method}</p></div>
                      <div><p className="text-xs text-slate-400">Amount</p><p className="font-bold text-slate-900">{formatINR(payment.amount)}</p></div>
                    </div>
                  </div>

                  {/* AI Suggestion */}
                  {suggestion ? (
                    <div className="rounded-xl border border-purple-200 bg-purple-50 p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Zap size={14} className="text-purple-600" />
                        <p className="text-xs font-semibold text-purple-700">AI Suggestion</p>
                        <div className="ml-auto flex items-center gap-1">
                          <div className="h-1.5 w-20 rounded-full bg-purple-200 overflow-hidden">
                            <div className="h-full rounded-full bg-purple-500" style={{ width: `${suggestion.confidence}%` }} />
                          </div>
                          <span className="text-xs font-bold text-purple-700">{suggestion.confidence}%</span>
                        </div>
                      </div>
                      <p className="text-sm font-semibold text-slate-800">{suggestion.invoiceNumber}</p>
                      <p className="text-xs text-slate-500 mt-0.5">Invoice amount: {formatINR(suggestion.invoiceAmount)}</p>
                      <p className="text-xs text-slate-400 mt-1 italic">"{suggestion.reason}"</p>
                      <div className="mt-3 flex gap-2">
                        <Button size="sm" className="gap-1"><CheckCircle2 size={13}/> Confirm Match</Button>
                        <Button size="sm" variant="outline">Reject</Button>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-xl border border-dashed border-slate-200 p-4 flex items-center justify-center">
                      <div className="text-center">
                        <p className="text-sm text-slate-400">No AI suggestion available</p>
                        <Button size="sm" variant="outline" className="mt-2">Match Manually</Button>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
