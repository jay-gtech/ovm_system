import { useState } from 'react'
import { Plus, CheckCircle, AlertTriangle, Package } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { Card, CardContent } from '../../components/ui/Card'
import { mockGRNs } from '../../utils/mockData'
import { formatDate } from '../../utils/format'

export default function GRNPage() {
  const [showForm, setShowForm] = useState(false)
  const partial = mockGRNs.filter(g=>g.isPartial)

  return (
    <div className="space-y-5">
      <PageHeader title="Goods Receipt Notes" subtitle={`${mockGRNs.length} GRNs · ${partial.length} partial receipts`}
        actions={<Button className="gap-2" onClick={()=>setShowForm(true)}><Plus size={16}/> Create GRN</Button>} />

      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label:'Total GRNs', value: mockGRNs.length, icon: Package, color:'border-brand-100 bg-brand-50 text-brand-700' },
          { label:'Fully Received', value: mockGRNs.filter(g=>!g.isPartial).length, icon: CheckCircle, color:'border-green-100 bg-green-50 text-green-700' },
          { label:'Partial Receipt', value: partial.length, icon: AlertTriangle, color:'border-amber-100 bg-amber-50 text-amber-700' },
        ].map(s => (
          <div key={s.label} className={`flex items-center gap-4 rounded-xl border px-5 py-4 ${s.color}`}>
            <s.icon size={22} className="shrink-0 opacity-80" />
            <div>
              <p className="text-xs font-medium opacity-70">{s.label}</p>
              <p className="text-2xl font-bold">{s.value}</p>
            </div>
          </div>
        ))}
      </div>

      {showForm && (
        <Card>
          <div className="border-b border-slate-100 px-5 py-4 flex items-center justify-between">
            <p className="font-semibold text-slate-800">Create Goods Receipt Note</p>
            <button onClick={()=>setShowForm(false)} className="text-slate-400 hover:text-slate-600">✕</button>
          </div>
          <CardContent className="p-5 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Purchase Order</label>
                <select className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none focus:border-brand-400">
                  <option>PO-2025-0283 — Global Electronics Supply</option>
                  <option>PO-2025-0284 — Rajan Textiles Pvt Ltd</option>
                  <option>PO-2025-0278 — Mehta Industrial Goods</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-500 mb-1">Receipt Date</label>
                <input type="date" className="h-9 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm outline-none focus:border-brand-400" />
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-400">Item Description</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-400">Ordered Qty</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-400">Received Qty</th>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-400">Condition</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-slate-50">
                    <td className="px-4 py-3 text-slate-700">Industrial Circuit Boards</td>
                    <td className="px-4 py-3 text-slate-600">200</td>
                    <td className="px-4 py-3"><input type="number" placeholder="0" className="h-8 w-20 rounded border border-slate-200 px-2 text-sm outline-none focus:border-brand-400" /></td>
                    <td className="px-4 py-3">
                      <select className="h-8 rounded border border-slate-200 px-2 text-xs outline-none focus:border-brand-400">
                        <option>Good</option><option>Damaged</option><option>Rejected</option>
                      </select>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-500 mb-1">Notes / Remarks</label>
              <textarea rows={2} placeholder="Add any notes about the delivery..." className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm outline-none focus:border-brand-400 resize-none" />
            </div>
            <div className="flex gap-2">
              <Button size="sm">Submit GRN</Button>
              <Button size="sm" variant="outline" onClick={()=>setShowForm(false)}>Cancel</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <div className="border-b border-slate-100 px-4 py-3">
          <p className="font-semibold text-slate-800 text-sm">Recent GRNs</p>
        </div>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                {['GRN ID','Order #','Vendor','Items Expected','Items Received','Type','Date','Created By'].map(h=>
                  <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">{h}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {mockGRNs.map(g => (
                <tr key={g.id} className={`hover:bg-slate-50/60 ${g.isPartial?'bg-amber-50/30':''}`}>
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-brand-600">GRN-{g.id.padStart(4,'0')}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-500">{g.orderNumber}</td>
                  <td className="px-4 py-3 text-slate-700 font-medium whitespace-nowrap">{g.vendorName}</td>
                  <td className="px-4 py-3 text-slate-600 tabular-nums">{g.itemsExpected}</td>
                  <td className="px-4 py-3 tabular-nums">
                    <span className={g.itemsReceived < g.itemsExpected ? 'text-amber-600 font-semibold' : 'text-green-600 font-semibold'}>
                      {g.itemsReceived}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-semibold border ${g.isPartial ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-green-50 text-green-700 border-green-200'}`}>
                      {g.isPartial ? 'Partial' : 'Full'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500">{formatDate(g.createdAt)}</td>
                  <td className="px-4 py-3 text-slate-600 text-xs">{g.createdBy}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
