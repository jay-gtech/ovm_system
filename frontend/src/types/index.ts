export type OrderStatus =
  | 'DRAFT'
  | 'PENDING_APPROVAL'
  | 'APPROVED'
  | 'ACKNOWLEDGED'
  | 'IN_TRANSIT'
  | 'PARTIALLY_RECEIVED'
  | 'FULLY_RECEIVED'
  | 'DELIVERED'
  | 'INVOICED'
  | 'PAID'
  | 'CLOSED'
  | 'DISPUTED'

export type InvoiceStatus = 'DRAFT' | 'ISSUED' | 'PAID' | 'CANCELLED' | 'OVERDUE' | 'DISPUTED'
export type PaymentStatus = 'PENDING' | 'RECEIVED' | 'FAILED' | 'CANCELLED'
export type PaymentMethod = 'CASH' | 'BANK_TRANSFER' | 'CREDIT_CARD' | 'CHECK' | 'OTHER'
export type MatchStatus = 'MATCHED' | 'PARTIAL_MATCH' | 'MISMATCH' | 'PENDING'
export type VendorStatus = 'ACTIVE' | 'PENDING_KYC' | 'SUSPENDED' | 'INACTIVE'
export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
export type UserRole = 'admin' | 'manager' | 'procurement' | 'accounts' | 'operations' | 'vendor'

export interface Vendor {
  id: string
  name: string
  vendor_code?: string
  legal_name?: string
  gstin: string
  pan: string
  email: string
  phone: string
  city: string
  status: VendorStatus
  reliabilityScore: number
  totalOrders: number
  totalValue: number
  onTimeDeliveryRate: number
  createdAt: string
}

export interface Order {
  id: string
  orderNumber: string
  vendor: { id: string; name: string }
  description: string
  quantity: number
  unitPrice: number
  totalAmount: number
  status: OrderStatus
  expectedDelivery: string
  createdBy: string
  createdAt: string
  updatedAt: string
}

export interface Invoice {
  id: string
  invoiceNumber: string
  orderId: string
  orderNumber: string
  vendorName: string
  amount: string
  taxAmount: string
  totalAmount: string
  paidAmount: string
  outstandingAmount: string
  dueDate: string
  status: InvoiceStatus
  matchStatus: MatchStatus
  isOverdue: boolean
  agingDays: number
  createdAt: string
}

export interface Payment {
  id: string
  payment_reference: string
  invoice_id: string
  amount: string
  payment_method: PaymentMethod
  payment_date: string
  status: PaymentStatus
  notes?: string
  created_at: string
}

export interface Alert {
  id: string
  severity: AlertSeverity
  message: string
  module: string
  orderId?: string
  createdAt: string
  isRead: boolean
}

export interface GRN {
  id: string
  orderId: string
  orderNumber: string
  vendorName: string
  itemsExpected: number
  itemsReceived: number
  isPartial: boolean
  createdAt: string
  createdBy: string
}

export interface DashboardStats {
  totalOrders: number
  pendingApprovals: number
  totalRevenue: number
  activeVendors: number
  overdueInvoices: number
  pendingGRNs: number
  criticalAlerts: number
  matchedInvoices: number
}

export interface AgingBucket {
  bucket: string
  amount: number
  count: number
  color: string
}
