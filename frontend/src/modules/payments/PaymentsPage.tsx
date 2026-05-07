import { useState } from 'react'
import { Plus, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Card, CardContent } from '../../components/ui/Card'
import { mockPayments } from '../../utils/mockData'
import { formatINR, formatDate } from '../../utils/format'

export default function PaymentsPage() {
  const [showForm, setShowForm] = useState(false)
  const matched = mockPayments.filter(p=>p.status==='MATCHED')
  const unmatched = mockPayments.filter(p=>p.status==='UNMATCHED')
  const totalIn = mockPayments.reduce((a,p)=>a+p.amount,0)

  return (
    <div className="space-y-5">
      <PageHeader title="Payments" subtitle="Record and track all incoming payments"
        actions={<Button className="gap-2" onClick={()=>setShowForm(true)}><Plus size={16}/> Record Payment</Button>} />

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label:'Total Received', value: formatINR(totalIn), icon: CheckCircle2, color:'text-green-600 bg-green-50 border-green-100' },
          { label:'Matched', value: `${matched.length} payments`, icon: CheckCircle2, color:'text-brand-600 bg-brand-50 border-brand-100' },
          { label:'Unmatched', value: `${unmatched.length} payments`, icon: XCircle, color:'text-red-600 bg-red-50 border-red-100' },
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

      {showForm && (
        <Card>
          <div className="border-b border-slate-100 px-5 py-4 flex items-center justify-between">
            <p className="font-semibold text-slate-800">Record New Payment</p>
            <button onClick={()=>setShowForm(false)} className="text-slate-400 hover:text-slate-600 text-sm">✕</button>
          </div>
          <CardContent className="p-5">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label:'Payment Reference', placeholder:'TXN-XXXXX', type:'text' },
                { label:'Amount (₹)', placeholder:'0.00', type:'number' },
                { label:'Payment Date', placeholder:'', type:'date' },
                { label:'Payment Method', placeholder:'', type:'select' },
              ].map(f => (
                <div key={f.label}>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">{f.label}</label>
                  {f.type === 'select' ? (
                    <select className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-brand-400">
                      <option>NEFT</option><option>RTGS</option><option>IMPS</option><option>Cheque</option>
                    </select>
                  ) : (
                    <input type={f.type} placeholder={f.placeholder}
                      className="h-9 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-brand-400" />
                  )}
                </div>
              ))}
            </div>
            <div className="mt-4 flex gap-2">
              <Button size="sm">Save Payment</Button>
              <Button size="sm" variant="outline" onClick={()=>setShowForm(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <div className="border-b border-slate-100 px-4 py-3">
          <p className="font-semibold text-slate-800 text-sm">Payment History</p>
        </div>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                {['Reference','Invoice #','Amount','Date','Method','Status'].map(h=>
                  <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">{h}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {mockPayments.map(p => (
                <tr key={p.id} className="hover:bg-slate-50/60">
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-brand-600">{p.paymentReference}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">{p.invoiceNumber || <span className="text-slate-300 italic">unmatched</span>}</td>
                  <td className="px-4 py-3 font-semibold text-slate-900 tabular-nums">{formatINR(p.amount)}</td>
                  <td className="px-4 py-3 text-xs text-slate-500">{formatDate(p.paymentDate)}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">{p.method}</span>
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={p.status}/></td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
