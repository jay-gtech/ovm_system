import { useState } from 'react'
import { Search, Download, Eye, AlertCircle } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Card, CardContent } from '../../components/ui/Card'
import { mockInvoices, mockAgingData } from '../../utils/mockData'
import { formatINR, formatDate } from '../../utils/format'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function InvoicesPage() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('ALL')
  const filtered = mockInvoices.filter(inv => {
    const ms = inv.invoiceNumber.toLowerCase().includes(search.toLowerCase()) ||
      inv.vendorName.toLowerCase().includes(search.toLowerCase()) ||
      inv.orderNumber.toLowerCase().includes(search.toLowerCase())
    return ms && (filterStatus === 'ALL' || inv.status === filterStatus)
  })
  const overdueTotal = mockInvoices.filter(i => i.isOverdue).reduce((a, i) => a + i.totalAmount, 0)
  const pendingTotal = mockInvoices.filter(i => i.status !== 'PAID').reduce((a, i) => a + i.totalAmount, 0)

  return (
    <div className="space-y-5">
      <PageHeader title="Invoices" subtitle={`${mockInvoices.length} invoices · ${mockInvoices.filter(i=>i.isOverdue).length} overdue`}
        actions={<Button variant="outline" className="gap-2"><Download size={15}/> Export</Button>} />

      {mockInvoices.some(i => i.isOverdue) && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
          <AlertCircle size={16} className="text-red-500 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-red-700">{mockInvoices.filter(i=>i.isOverdue).length} overdue invoices totalling {formatINR(overdueTotal)}</p>
            <p className="text-xs text-red-500 mt-0.5">Immediate follow-up required.</p>
          </div>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 grid gap-3 grid-cols-2 sm:grid-cols-4">
          {[
            { label: 'Outstanding', value: formatINR(pendingTotal), sub: `${mockInvoices.filter(i=>i.status!=='PAID').length} invoices`, c: 'border-brand-100 bg-brand-50 text-brand-700' },
            { label: 'Overdue', value: formatINR(overdueTotal), sub: `${mockInvoices.filter(i=>i.isOverdue).length} invoices`, c: 'border-red-100 bg-red-50 text-red-700' },
            { label: 'Matched', value: `${mockInvoices.filter(i=>i.matchStatus==='MATCHED').length}`, sub: '3-way match OK', c: 'border-green-100 bg-green-50 text-green-700' },
            { label: 'Mismatch', value: `${mockInvoices.filter(i=>i.matchStatus==='MISMATCH').length}`, sub: 'Needs review', c: 'border-orange-100 bg-orange-50 text-orange-700' },
          ].map(s => (
            <div key={s.label} className={`rounded-xl border px-4 py-3 ${s.c}`}>
              <p className="text-xs font-medium opacity-70">{s.label}</p>
              <p className="text-xl font-bold mt-0.5">{s.value}</p>
              <p className="text-[11px] mt-0.5 opacity-60">{s.sub}</p>
            </div>
          ))}
        </div>
        <Card>
          <div className="px-4 pt-3 pb-1"><p className="text-sm font-semibold text-slate-700">Aging Buckets</p></div>
          <ResponsiveContainer width="100%" height={110}>
            <BarChart data={mockAgingData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <XAxis dataKey="bucket" tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tickFormatter={v => `${(v/100000).toFixed(0)}L`} tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v: any) => [formatINR(Number(v)), 'Amount']} />
              <Bar dataKey="amount" radius={[3,3,0,0]}>{mockAgingData.map((e,i) => <Cell key={i} fill={e.color}/>)}</Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card>
        <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative max-w-xs flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input type="text" placeholder="Search invoices..." value={search} onChange={e=>setSearch(e.target.value)}
              className="h-9 w-full rounded-lg border border-slate-200 bg-slate-50 pl-8 pr-3 text-sm outline-none focus:border-brand-400" />
          </div>
          <select value={filterStatus} onChange={e=>setFilterStatus(e.target.value)}
            className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none focus:border-brand-400">
            {['ALL','DRAFT','SENT','PARTIALLY_PAID','PAID','OVERDUE','DISPUTED'].map(s =>
              <option key={s} value={s}>{s==='ALL'?'All Statuses':s.replace(/_/g,' ')}</option>)}
          </select>
        </div>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  {['Invoice #','Order #','Vendor','Amount (incl. GST)','Due Date','Aging','Match','Status',''].map(h=>
                    <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">{h}</th>)}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filtered.length===0 && <tr><td colSpan={9} className="px-4 py-16 text-center text-sm text-slate-400">No invoices found.</td></tr>}
                {filtered.map(inv => (
                  <tr key={inv.id} className={`hover:bg-slate-50/60 ${inv.isOverdue?'bg-red-50/30':''}`}>
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-brand-600">{inv.invoiceNumber}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-500">{inv.orderNumber}</td>
                    <td className="px-4 py-3 text-slate-700 font-medium whitespace-nowrap">{inv.vendorName}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900 tabular-nums whitespace-nowrap">{formatINR(inv.totalAmount)}</td>
                    <td className={`px-4 py-3 text-xs whitespace-nowrap ${inv.isOverdue?'text-red-600 font-semibold':'text-slate-500'}`}>
                      {formatDate(inv.dueDate)}{inv.isOverdue&&<span className="ml-1 text-[10px]">({inv.agingDays}d)</span>}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs font-semibold ${inv.agingDays>60?'text-red-600':inv.agingDays>30?'text-amber-600':'text-green-600'}`}>
                        {inv.agingDays===0?'—':`${inv.agingDays}d`}
                      </span>
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={inv.matchStatus}/></td>
                    <td className="px-4 py-3"><StatusBadge status={inv.status}/></td>
                    <td className="px-4 py-3">
                      <button className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-500 hover:border-brand-300 hover:text-brand-600 transition-colors">
                        <Eye size={11}/> View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="border-t border-slate-100 px-4 py-3"><p className="text-xs text-slate-400">Showing {filtered.length} of {mockInvoices.length}</p></div>
        </CardContent>
      </Card>
    </div>
  )
}
