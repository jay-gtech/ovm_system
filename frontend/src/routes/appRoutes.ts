import {
  LayoutDashboard, ShoppingCart, Users, Package,
  FileText, CreditCard, BarChart3, Settings, Bell, ClipboardList, Tag, Activity, BellRing,
  BarChart2,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface AppRoute {
  path: string
  label: string
  icon: LucideIcon
  badge?: string
}

export const appRoutes: AppRoute[] = [
  { path: '/',          label: 'Dashboard', icon: LayoutDashboard },
  { path: '/orders',    label: 'Orders',    icon: ShoppingCart,  badge: '12' },
  { path: '/vendors',   label: 'Vendors',   icon: Users },
  { path: '/products',  label: 'Products',  icon: Tag },
  { path: '/grn',       label: 'GRN',       icon: Package,       badge: '3' },
  { path: '/invoices',  label: 'Invoices',  icon: FileText,      badge: '8' },
  { path: '/payments',  label: 'Payments',  icon: CreditCard },
  { path: '/reconcile', label: 'Reconcile', icon: ClipboardList, badge: '2' },
  { path: '/alerts',    label: 'Alerts',    icon: Bell,          badge: '4' },
  { path: '/notifications', label: 'Notifications', icon: BellRing },
  { path: '/risk-intelligence', label: 'Risk Intelligence', icon: BarChart2 },
  { path: '/monitoring',label: 'Monitoring',icon: Activity },
  { path: '/reports',   label: 'Reports',   icon: BarChart3 },
  { path: '/settings',  label: 'Settings',  icon: Settings },
]
