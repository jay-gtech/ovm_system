import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from '../layouts/MainLayout'
import { ProtectedRoute } from './ProtectedRoute'

const Login      = lazy(() => import('../modules/auth/LoginPage'))
const Dashboard  = lazy(() => import('../modules/dashboard/DashboardPage'))
const Orders     = lazy(() => import('../modules/orders/OrdersPage'))
const Vendors    = lazy(() => import('../modules/vendors/VendorsPage'))
const Products   = lazy(() => import('../modules/products/ProductsPage'))
const Invoices   = lazy(() => import('../modules/invoices/InvoicesPage'))
const InvoiceDetail = lazy(() => import('../modules/invoices/InvoiceDetailPage'))
const Payments   = lazy(() => import('../modules/payments/PaymentsPage'))
const GRN        = lazy(() => import('../modules/grn/GRNPage'))
const Reconcile  = lazy(() => import('../modules/reconcile/ReconcilePage'))
const Alerts             = lazy(() => import('../modules/alerts/AlertsPage'))
const Notifications      = lazy(() => import('../modules/notifications/NotificationsPage'))
const RiskIntelligence   = lazy(() => import('../modules/risk/RiskIntelligencePage'))
const Monitoring         = lazy(() => import('../modules/monitoring/MonitoringPage'))
const Reports    = lazy(() => import('../modules/reports/ReportsPage'))
const Settings   = lazy(() => import('../modules/settings/SettingsPage'))

function PageLoader() {
  return (
    <div className="flex h-64 items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-brand-600 border-t-transparent" />
    </div>
  )
}

export function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/login"
        element={<Suspense fallback={<PageLoader />}><Login /></Suspense>}
      />
      <Route
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/"          element={<Suspense fallback={<PageLoader/>}><Dashboard/></Suspense>} />
        <Route path="/orders"    element={<Suspense fallback={<PageLoader/>}><Orders/></Suspense>} />
        <Route path="/vendors"   element={<Suspense fallback={<PageLoader/>}><Vendors/></Suspense>} />
        <Route path="/products"  element={<Suspense fallback={<PageLoader/>}><Products/></Suspense>} />
        <Route path="/invoices"  element={<Suspense fallback={<PageLoader/>}><Invoices/></Suspense>} />
        <Route path="/invoices/:id" element={<Suspense fallback={<PageLoader/>}><InvoiceDetail/></Suspense>} />
        <Route path="/payments"  element={<Suspense fallback={<PageLoader/>}><Payments/></Suspense>} />
        <Route path="/grn"       element={<Suspense fallback={<PageLoader/>}><GRN/></Suspense>} />
        <Route path="/reconcile" element={<Suspense fallback={<PageLoader/>}><Reconcile/></Suspense>} />
        <Route path="/alerts"         element={<Suspense fallback={<PageLoader/>}><Alerts/></Suspense>} />
        <Route path="/notifications"     element={<Suspense fallback={<PageLoader/>}><Notifications/></Suspense>} />
        <Route path="/risk-intelligence" element={<Suspense fallback={<PageLoader/>}><RiskIntelligence/></Suspense>} />
        <Route path="/monitoring"        element={<Suspense fallback={<PageLoader/>}><Monitoring/></Suspense>} />
        <Route path="/reports"   element={<Suspense fallback={<PageLoader/>}><Reports/></Suspense>} />
        <Route path="/settings"  element={<Suspense fallback={<PageLoader/>}><Settings/></Suspense>} />
        <Route path="*"          element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
