import {
  ShoppingCart, Users, TrendingUp, AlertTriangle,
  FileText, Package, CheckCircle, Clock, Plus
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from 'recharts'
import { StatCard } from '../../components/ui/StatCard'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/Card'
import { mockStats, mockOrders, mockAlerts, mockRevenueData, mockAgingData } from '../../utils/mockData'
import { formatINR, formatDate, timeAgo } from '../../utils/format'
import { useNavigate } from 'react-router-dom'

export default function Dashboard() {
  const navigate = useNavigate()

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle="Real-time overview of orders, vendors, and finances."
        actions={
          <Button className="gap-2" onClick={() => navigate('/orders')}>
            <Plus size={16} /> New Order
          </Button>
        }
      />

      {/* Row 1 stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Orders" value={String(mockStats.totalOrders)} icon={ShoppingCart} color="blue" trend={{ value: '+18 this week', up: true }} />
        <StatCard title="Total Revenue" value={formatINR(mockStats.totalRevenue)} icon={TrendingUp} color="green" trend={{ value: '+12.4% vs last month', up: true }} />
        <StatCard title="Active Vendors" value={String(mockStats.activeVendors)} icon={Users} color="purple" sub="3 pending KYC" />
        <StatCard title="Critical Alerts" value={String(mockStats.criticalAlerts)} icon={AlertTriangle} color="red" sub="Needs immediate action" />
      </div>

      {/* Row 2 stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Pending Approvals" value={String(mockStats.pendingApprovals)} icon={Clock} color="amber" sub="Awaiting manager review" />
        <StatCard title="Overdue Invoices" value={String(mockStats.overdueInvoices)} icon={FileText} color="red" sub="Past due date" />
        <StatCard title="Pending GRNs" value={String(mockStats.pendingGRNs)} icon={Package} color="teal" sub="Goods to be received" />
        <StatCard title="Match Rate" value={`${mockStats.matchedInvoices}%`} icon={CheckCircle} color="green" trend={{ value: '+2% vs last week', up: true }} />
      </div>

      {/* Charts row */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Revenue vs Cost — Last 6 Months</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={mockRevenueData} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.12} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="cost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.12} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={(v) => `₹${(v/100000).toFixed(0)}L`} tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: any) => formatINR(Number(v))} />
                <Area type="monotone" dataKey="revenue" stroke="#2563eb" strokeWidth={2} fill="url(#rev)" name="Revenue" />
                <Area type="monotone" dataKey="cost" stroke="#f59e0b" strokeWidth={2} fill="url(#cost)" name="Cost" />
              </AreaChart>
            </ResponsiveContainer>
            <div className="mt-2 flex gap-6 justify-end">
              <span className="flex items-center gap-1.5 text-xs text-slate-500"><span className="h-2 w-4 rounded bg-brand-500 inline-block" /> Revenue</span>
              <span className="flex items-center gap-1.5 text-xs text-slate-500"><span className="h-2 w-4 rounded bg-amber-400 inline-block" /> Cost</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Invoice Aging</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={190}>
              <BarChart data={mockAgingData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="bucket" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={(v) => `₹${(v/100000).toFixed(0)}L`} tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip formatter={(v: any) => [formatINR(Number(v)), 'Amount']} />
                <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
                  {mockAgingData.map((entry, i) => <Cell key={i} fill={entry.color} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="mt-1 space-y-1">
              {mockAgingData.map((b) => (
                <div key={b.bucket} className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-slate-500">
                    <span className="h-2 w-2 rounded-full inline-block" style={{ backgroundColor: b.color }} />
                    {b.bucket}
                  </span>
                  <span className="font-semibold text-slate-700">{formatINR(b.amount)}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent orders + alerts */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex-row items-center justify-between pb-3 border-b border-slate-100">
            <CardTitle className="text-base font-semibold">Recent Orders</CardTitle>
            <button onClick={() => navigate('/orders')} className="text-xs font-medium text-brand-600 hover:underline">View all →</button>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  {['Order #','Vendor','Amount','Status','Date'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left text-[11px] font-semibold text-slate-400 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {mockOrders.slice(0,5).map((order) => (
                  <tr key={order.id} className="hover:bg-slate-50/60 cursor-pointer" onClick={() => navigate('/orders')}>
                    <td className="px-4 py-3 font-mono text-xs font-semibold text-brand-600">{order.orderNumber}</td>
                    <td className="px-4 py-3 text-slate-700 font-medium max-w-[130px] truncate">{order.vendor.name}</td>
                    <td className="px-4 py-3 font-semibold text-slate-900 tabular-nums">{formatINR(order.totalAmount)}</td>
                    <td className="px-4 py-3"><StatusBadge status={order.status} /></td>
                    <td className="px-4 py-3 text-slate-400 text-xs">{formatDate(order.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between pb-3 border-b border-slate-100">
            <CardTitle className="text-base font-semibold">Live Alerts</CardTitle>
            <button onClick={() => navigate('/alerts')} className="text-xs font-medium text-brand-600 hover:underline">View all →</button>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-slate-50">
              {mockAlerts.slice(0,4).map((alert) => {
                const left = { CRITICAL:'border-l-red-500', HIGH:'border-l-orange-400', MEDIUM:'border-l-amber-400', LOW:'border-l-blue-400' }[alert.severity] ?? 'border-l-slate-300'
                return (
                  <div key={alert.id} className={`px-4 py-3 border-l-4 ${left} ${!alert.isRead ? 'bg-slate-50/60' : ''}`}>
                    <div className="flex items-center gap-1.5 mb-1">
                      <StatusBadge status={alert.severity} />
                      {!alert.isRead && <span className="h-1.5 w-1.5 rounded-full bg-brand-500 shrink-0" />}
                    </div>
                    <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">{alert.message}</p>
                    <p className="mt-1 text-[10px] text-slate-400">{timeAgo(alert.createdAt)}</p>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
