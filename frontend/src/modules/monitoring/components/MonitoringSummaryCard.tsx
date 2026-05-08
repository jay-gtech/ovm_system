import { useFinancialSummary } from '../hooks/useMonitoring'
import { Card } from '../../../components/ui/Card'
import { formatINR } from '../../../utils/format'
import { AlertCircle, FileText, CreditCard, Clock } from 'lucide-react'

export function MonitoringSummaryCard() {
  const { data: summary, isLoading, isError } = useFinancialSummary()

  if (isLoading) {
    return <Card className="p-6 h-32 flex items-center justify-center">Loading summary...</Card>
  }

  if (isError || !summary) {
    return <Card className="p-6 h-32 flex items-center justify-center text-red-500">Failed to load summary</Card>
  }

  const items = [
    { label: 'Outstanding Invoices', value: summary.total_outstanding_invoices, icon: FileText, color: 'text-amber-500', bg: 'bg-amber-100 dark:bg-amber-900/30' },
    { label: 'Pending Payments', value: summary.total_pending_payments, icon: Clock, color: 'text-blue-500', bg: 'bg-blue-100 dark:bg-blue-900/30' },
    { label: 'Unsettled Liabilities', value: summary.total_unsettled_liabilities, icon: AlertCircle, color: 'text-red-500', bg: 'bg-red-100 dark:bg-red-900/30' },
    { label: 'Pending Settlements', value: summary.total_pending_settlements, icon: CreditCard, color: 'text-purple-500', bg: 'bg-purple-100 dark:bg-purple-900/30' }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {items.map((item, i) => (
        <Card key={i} className="p-5 flex items-center gap-4">
          <div className={`p-3 rounded-full ${item.bg} ${item.color}`}>
            <item.icon size={24} />
          </div>
          <div>
            <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">{item.label}</p>
            <p className="text-2xl font-bold">{formatINR(item.value)}</p>
          </div>
        </Card>
      ))}
    </div>
  )
}
