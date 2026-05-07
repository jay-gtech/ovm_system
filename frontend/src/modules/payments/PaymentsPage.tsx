import { useState } from 'react'
import { Plus, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Card, CardContent } from '../../components/ui/Card'
import { formatINR, formatDate } from '../../utils/format'
import { usePayments } from '../../hooks/usePayments'
import { PaymentTable } from './components/PaymentTable'
import { Loader } from '../../components/feedback/Loader'

export default function PaymentsPage() {
  const { data: paymentsData, isLoading } = usePayments()
  const payments = paymentsData?.items || []
  
  const received = payments.filter(p=>p.status==='RECEIVED')
  const pending = payments.filter(p=>p.status==='PENDING')
  const totalIn = received.reduce((a,p)=>a+p.amount,0)

  if (isLoading) return <Loader />

  return (
    <div className="space-y-5">
      <PageHeader title="Payments" subtitle="Record and track all incoming payments" />

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label:'Total Received', value: formatINR(totalIn), icon: CheckCircle2, color:'text-green-600 bg-green-50 border-green-100' },
          { label:'Received Count', value: `${received.length} payments`, icon: CheckCircle2, color:'text-brand-600 bg-brand-50 border-brand-100' },
          { label:'Pending', value: `${pending.length} payments`, icon: Clock, color:'text-amber-600 bg-amber-50 border-amber-100' },
        ].map(s => (
          <div key={s.label} className={`flex items-center gap-4 rounded-xl border px-5 py-4 ${s.color}`}>
            <s.icon size={24} className="shrink-0 opacity-80" />
            <div>
              <p className="text-xs font-medium opacity-70">{s.label}</p>
              <p className="text-xl font-bold mt-0.5">{s.value}</p>
            </div>
          </div>
        ))}
      </div>

      <Card>
        <div className="border-b border-slate-100 px-4 py-3">
          <p className="font-semibold text-slate-800 text-sm">Payment History</p>
        </div>
        <CardContent className="p-0">
          <PaymentTable payments={payments} isLoading={isLoading} />
        </CardContent>
      </Card>
    </div>
  )
}
