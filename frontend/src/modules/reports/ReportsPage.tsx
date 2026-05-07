import { Download, TrendingUp, TrendingDown } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { mockVendors, mockRevenueData } from '../../utils/mockData'
import { formatINR } from '../../utils/format'
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function ReportsPage() {
  const totalRevenue = mockRevenueData.reduce((a,m)=>a+m.revenue,0)
  const totalCost = mockRevenueData.reduce((a,m)=>a+m.cost,0)
  const grossMargin = ((totalRevenue - totalCost) / totalRevenue * 100).toFixed(1)

  return (
    <div className="space-y-5">
      <PageHeader title="Reports & Analytics" subtitle="Business intelligence and financial summaries"
        actions={<Button variant="outline" className="gap-2"><Download size={15}/> Export Report</Button>} />

      {/* KPIs */}
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label:'Total Revenue (6M)', value: formatINR(totalRevenue), trend: '+14%', up: true },
          { label:'Total Cost (6M)', value: formatINR(totalCost), trend: '+9%', up: false },
          { label:'Gross Margin', value: `${grossMargin}%`, trend: '+2.1pp', up: true },
        ].map(k => (
          <div key={k.label} className="rounded-xl border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{k.label}</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{k.value}</p>
            <p className={`flex items-center gap-1 text-xs font-semibold mt-1 ${k.up?'text-green-600':'text-red-500'}`}>
              {k.up ? <TrendingUp size={12}/> : <TrendingDown size={12}/>} {k.trend} vs prior period
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base font-semibold">Monthly Revenue Trend</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={mockRevenueData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="r2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.15} /><stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={v=>`₹${(v/100000).toFixed(0)}L`} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: any) => formatINR(Number(v))} />
                <Area type="monotone" dataKey="revenue" stroke="#2563eb" strokeWidth={2} fill="url(#r2)" name="Revenue" />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base font-semibold">Top Vendors by Value</CardTitle></CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={mockVendors.filter(v=>v.status==='ACTIVE').sort((a,b)=>b.totalValue-a.totalValue).slice(0,5)} margin={{ top: 5, right: 5, left: 0, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#94a3b8' }} axisLine={false} tickLine={false} angle={-20} textAnchor="end" interval={0} />
                <YAxis tickFormatter={v=>`${(v/1000000).toFixed(0)}M`} tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: any) => [formatINR(Number(v)), 'Value']} />
                <Bar dataKey="totalValue" fill="#2563eb" radius={[4,4,0,0]} name="Total Value" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Vendor performance table */}
      <Card>
        <CardHeader className="pb-3 border-b border-slate-100"><CardTitle className="text-base font-semibold">Vendor Performance Summary</CardTitle></CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  {['Vendor','Total Orders','Total Value','On-Time %','Reliability Score','Status'].map(h=>
                    <th key={h} className="px-4 py-3 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider whitespace-nowrap">{h}</th>)}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {mockVendors.sort((a,b)=>b.totalValue-a.totalValue).map(v => (
                  <tr key={v.id} className="hover:bg-slate-50/60">
                    <td className="px-4 py-3 font-semibold text-slate-800">{v.name}</td>
                    <td className="px-4 py-3 text-slate-600 tabular-nums">{v.totalOrders}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900 tabular-nums">{formatINR(v.totalValue)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 rounded-full bg-slate-100 overflow-hidden">
                          <div className={`h-full rounded-full ${v.onTimeDeliveryRate>=90?'bg-green-500':v.onTimeDeliveryRate>=75?'bg-amber-400':'bg-red-400'}`} style={{width:`${v.onTimeDeliveryRate}%`}} />
                        </div>
                        <span className={`text-xs font-semibold ${v.onTimeDeliveryRate>=90?'text-green-600':v.onTimeDeliveryRate>=75?'text-amber-600':'text-red-500'}`}>{v.onTimeDeliveryRate}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <span className="text-amber-400">★</span>
                        <span className="text-sm font-bold text-slate-700">{v.reliabilityScore}</span>
                        <span className="text-xs text-slate-400">/ 5</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold border ${v.status==='ACTIVE'?'bg-green-50 text-green-700 border-green-200':v.status==='SUSPENDED'?'bg-red-50 text-red-700 border-red-200':'bg-amber-50 text-amber-700 border-amber-200'}`}>
                        {v.status.replace(/_/g,' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
