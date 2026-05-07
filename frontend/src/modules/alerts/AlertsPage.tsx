import { useState } from 'react'
import { Bell, CheckCheck } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Card, CardContent } from '../../components/ui/Card'
import { mockAlerts } from '../../utils/mockData'
import { timeAgo } from '../../utils/format'
import type { AlertSeverity } from '../../types'

export default function AlertsPage() {
  const [filter, setFilter] = useState('ALL')
  const filtered = mockAlerts.filter(a => filter === 'ALL' || a.severity === filter)

  const borderColor = (s: string) => ({
    CRITICAL: 'border-l-red-500', HIGH: 'border-l-orange-400', MEDIUM: 'border-l-amber-400', LOW: 'border-l-blue-400'
  }[s] ?? 'border-l-slate-300')

  return (
    <div className="space-y-5">
      <PageHeader title="Alerts" subtitle={`${mockAlerts.filter(a=>!a.isRead).length} unread alerts`}
        actions={<Button variant="outline" className="gap-2"><CheckCheck size={15}/> Mark all read</Button>} />

      <div className="grid gap-3 sm:grid-cols-4">
        {(['ALL','CRITICAL','HIGH','MEDIUM'] as const).map(s => {
          const count = s === 'ALL' ? mockAlerts.length : mockAlerts.filter(a=>a.severity===s).length
          const colors = { ALL:'border-slate-200 bg-slate-50 text-slate-700', CRITICAL:'border-red-100 bg-red-50 text-red-700', HIGH:'border-orange-100 bg-orange-50 text-orange-700', MEDIUM:'border-amber-100 bg-amber-50 text-amber-700' }
          return (
            <button key={s} onClick={()=>setFilter(s)}
              className={`rounded-xl border px-4 py-3 text-left transition-all ${colors[s]} ${filter===s?'ring-2 ring-brand-400':''}`}>
              <p className="text-xs font-medium opacity-70">{s === 'ALL' ? 'All Alerts' : s}</p>
              <p className="text-2xl font-bold mt-0.5">{count}</p>
            </button>
          )
        })}
      </div>

      <Card>
        <div className="border-b border-slate-100 px-4 py-3 flex items-center gap-2">
          <Bell size={15} className="text-slate-400" />
          <p className="text-sm font-semibold text-slate-700">Alert Feed</p>
        </div>
        <CardContent className="p-0">
          <div className="divide-y divide-slate-50">
            {filtered.length === 0 && (
              <div className="px-4 py-16 text-center text-sm text-slate-400">No alerts for this filter.</div>
            )}
            {filtered.map(alert => (
              <div key={alert.id} className={`border-l-4 ${borderColor(alert.severity)} px-5 py-4 ${!alert.isRead?'bg-slate-50/60':''} hover:bg-slate-50 transition-colors`}>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <StatusBadge status={alert.severity as AlertSeverity} />
                      <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-500">{alert.module}</span>
                      {!alert.isRead && <span className="h-1.5 w-1.5 rounded-full bg-brand-500 shrink-0" />}
                    </div>
                    <p className="text-sm text-slate-700 leading-relaxed">{alert.message}</p>
                    <p className="mt-1 text-[11px] text-slate-400">{timeAgo(alert.createdAt)}</p>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    {alert.orderId && (
                      <button className="rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-500 hover:border-brand-300 hover:text-brand-600 transition-colors whitespace-nowrap">
                        View Order
                      </button>
                    )}
                    <button className="rounded-md border border-slate-200 px-2.5 py-1 text-xs text-slate-500 hover:bg-slate-100 transition-colors">
                      Dismiss
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
