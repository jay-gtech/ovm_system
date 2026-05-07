import { useState } from 'react'
import { Plus, Search, Filter, Eye } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Card, CardContent } from '../../components/ui/Card'
import { mockOrders } from '../../utils/mockData'
import { formatINR, formatDate } from '../../utils/format'
import type { OrderStatus } from '../../types'

const ALL_STATUSES: OrderStatus[] = [
  'DRAFT','PENDING_APPROVAL','APPROVED','ACKNOWLEDGED',
  'IN_TRANSIT','PARTIALLY_RECEIVED','FULLY_RECEIVED',
  'DELIVERED','INVOICED','PAID','CLOSED','DISPUTED',
]

export default function OrdersPage() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState<string>('ALL')

  const filtered = mockOrders.filter(o => {
    const matchSearch = o.orderNumber.toLowerCase().includes(search.toLowerCase()) ||
      o.vendor.name.toLowerCase().includes(search.toLowerCase()) ||
      o.description.toLowerCase().includes(search.toLowerCase())
    const matchStatus = filterStatus === 'ALL' || o.status === filterStatus
    return matchSearch && matchStatus
  })

  return (
    <div className="space-y-5">
      <PageHeader
        title="Purchase Orders"
        subtitle={`${mockOrders.length} total orders`}
        actions={
          <Button className="gap-2">
            <Plus size={16} /> Create PO
          </Button>
        }
      />

      {/* Summary pills */}
      <div className="flex flex-wrap gap-2">
        {[
          { label: 'All', value: 'ALL', count: mockOrders.length },
          { label: 'Pending Approval', value: 'PENDING_APPROVAL', count: mockOrders.filter(o=>o.status==='PENDING_APPROVAL').length },
          { label: 'In Transit', value: 'IN_TRANSIT', count: mockOrders.filter(o=>o.status==='IN_TRANSIT').length },
          { label: 'Disputed', value: 'DISPUTED', count: mockOrders.filter(o=>o.status==='DISPUTED').length },
        ].map(pill => (
          <button
            key={pill.value}
            onClick={() => setFilterStatus(pill.value)}
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              filterStatus === pill.value
                ? 'bg-brand-600 border-brand-600 text-white'
                : 'bg-white border-slate-200 text-slate-600 hover:border-brand-300 hover:text-brand-700'
            }`}
          >
            {pill.label}
            <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-bold ${filterStatus===pill.value ? 'bg-brand-700 text-white' : 'bg-slate-100 text-slate-500'}`}>
              {pill.count}
            </span>
          </button>
        ))}
      </div>

      <Card>
        {/* Toolbar */}
        <div className="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1 max-w-xs">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search orders..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="h-9 w-full rounded-lg border border-slate-200 bg-slate-50 pl-8 pr-3 text-sm text-slate-900 placeholder-slate-400 outline-none focus:border-brand-400 focus:ring-1 focus:ring-brand-100"
            />
          </div>
          <div className="flex items-center gap-2">
            <select
              value={filterStatus}
              onChange={e => setFilterStatus(e.target.value)}
              className="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-brand-400"
            >
              <option value="ALL">All Statuses</option>
              {ALL_STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g,' ')}</option>)}
            </select>
            <Button variant="outline" size="sm" className="gap-1.5">
              <Filter size={13} /> Filter
            </Button>
          </div>
        </div>

        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  {['Order #','Description','Vendor','Amount','Delivery Date','Status',''].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {filtered.length === 0 && (
                  <tr><td colSpan={7} className="px-4 py-16 text-center text-sm text-slate-400">No orders found matching your filters.</td></tr>
                )}
                {filtered.map(order => (
                  <tr key={order.id} className="hover:bg-slate-50/60">
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs font-semibold text-brand-600">{order.orderNumber}</span>
                    </td>
                    <td className="px-4 py-3 max-w-[200px]">
                      <p className="text-slate-800 font-medium truncate">{order.description}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">Qty: {order.quantity} × {formatINR(order.unitPrice)}</p>
                    </td>
                    <td className="px-4 py-3 text-slate-600 font-medium whitespace-nowrap">{order.vendor.name}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900 tabular-nums whitespace-nowrap">{formatINR(order.totalAmount)}</td>
                    <td className="px-4 py-3 text-slate-500 text-xs whitespace-nowrap">{formatDate(order.expectedDelivery)}</td>
                    <td className="px-4 py-3"><StatusBadge status={order.status} /></td>
                    <td className="px-4 py-3">
                      <button className="flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs text-slate-500 hover:border-brand-300 hover:text-brand-600 transition-colors">
                        <Eye size={12} /> View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {/* Footer */}
          <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
            <p className="text-xs text-slate-400">Showing {filtered.length} of {mockOrders.length} orders</p>
            <div className="flex gap-1">
              <button className="rounded border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-50 disabled:opacity-40" disabled>Previous</button>
              <button className="rounded border border-slate-200 bg-brand-600 px-3 py-1 text-xs text-white">1</button>
              <button className="rounded border border-slate-200 px-3 py-1 text-xs text-slate-500 hover:bg-slate-50">Next</button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
