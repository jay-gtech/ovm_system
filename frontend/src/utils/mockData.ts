import type { Order, Vendor, Invoice, Payment, Alert, GRN, DashboardStats, AgingBucket } from '../types'

export const mockStats: DashboardStats = {
  totalOrders: 284,
  pendingApprovals: 12,
  totalRevenue: 48750000,
  activeVendors: 47,
  overdueInvoices: 8,
  pendingGRNs: 6,
  criticalAlerts: 3,
  matchedInvoices: 94,
}

export const mockVendors: Vendor[] = [
  { id: '1', name: 'Rajan Textiles Pvt Ltd', gstin: '27AABCR1234A1Z5', pan: 'AABCR1234A', email: 'rajan@rajantex.com', phone: '+91 98765 43210', city: 'Mumbai', status: 'ACTIVE', reliabilityScore: 4.8, totalOrders: 142, totalValue: 18500000, onTimeDeliveryRate: 96, createdAt: '2023-03-15' },
  { id: '2', name: 'Global Electronics Supply', gstin: '29AADCG5678B1Z3', pan: 'AADCG5678B', email: 'ops@globalelec.in', phone: '+91 87654 32109', city: 'Bengaluru', status: 'ACTIVE', reliabilityScore: 4.2, totalOrders: 89, totalValue: 12300000, onTimeDeliveryRate: 88, createdAt: '2023-06-22' },
  { id: '3', name: 'Shree Packaging Co.', gstin: '24AAFCS9012C1Z1', pan: 'AAFCS9012C', email: 'contact@shreepack.com', phone: '+91 76543 21098', city: 'Ahmedabad', status: 'PENDING_KYC', reliabilityScore: 3.5, totalOrders: 23, totalValue: 2800000, onTimeDeliveryRate: 75, createdAt: '2024-01-10' },
  { id: '4', name: 'Mehta Industrial Goods', gstin: '06AABHM3456D1Z9', pan: 'AABHM3456D', email: 'mehta@mihg.co.in', phone: '+91 65432 10987', city: 'Gurugram', status: 'ACTIVE', reliabilityScore: 4.6, totalOrders: 67, totalValue: 9200000, onTimeDeliveryRate: 92, createdAt: '2023-09-05' },
  { id: '5', name: 'Southern Raw Materials', gstin: '33AAECS7890E1Z7', pan: 'AAECS7890E', email: 'info@southernrm.com', phone: '+91 54321 09876', city: 'Chennai', status: 'SUSPENDED', reliabilityScore: 2.1, totalOrders: 12, totalValue: 1500000, onTimeDeliveryRate: 58, createdAt: '2024-02-20' },
  { id: '6', name: 'Patel Logistics & Supply', gstin: '24AAKCP2345F1Z6', pan: 'AAKCP2345F', email: 'ops@patellogi.com', phone: '+91 43210 98765', city: 'Surat', status: 'ACTIVE', reliabilityScore: 4.4, totalOrders: 98, totalValue: 11700000, onTimeDeliveryRate: 91, createdAt: '2023-07-18' },
]

export const mockOrders: Order[] = [
  { id: '1', orderNumber: 'PO-2025-0284', vendor: { id: '1', name: 'Rajan Textiles Pvt Ltd' }, description: 'Cotton Fabric Roll - Grade A (500m)', quantity: 500, unitPrice: 1200, totalAmount: 600000, status: 'PENDING_APPROVAL', expectedDelivery: '2025-06-15', createdBy: 'Priya Sharma', createdAt: '2025-05-28', updatedAt: '2025-05-28' },
  { id: '2', orderNumber: 'PO-2025-0283', vendor: { id: '2', name: 'Global Electronics Supply' }, description: 'Industrial Circuit Boards (200 units)', quantity: 200, unitPrice: 8500, totalAmount: 1700000, status: 'IN_TRANSIT', expectedDelivery: '2025-06-10', createdBy: 'Rahul Verma', createdAt: '2025-05-25', updatedAt: '2025-05-27' },
  { id: '3', orderNumber: 'PO-2025-0282', vendor: { id: '4', name: 'Mehta Industrial Goods' }, description: 'Steel Pipes 4-inch (100 units)', quantity: 100, unitPrice: 3200, totalAmount: 320000, status: 'FULLY_RECEIVED', expectedDelivery: '2025-06-05', createdBy: 'Anita Nair', createdAt: '2025-05-22', updatedAt: '2025-06-02' },
  { id: '4', orderNumber: 'PO-2025-0281', vendor: { id: '6', name: 'Patel Logistics & Supply' }, description: 'Corrugated Boxes 24x18x12 (1000 units)', quantity: 1000, unitPrice: 85, totalAmount: 85000, status: 'INVOICED', expectedDelivery: '2025-06-01', createdBy: 'Kiran Patel', createdAt: '2025-05-20', updatedAt: '2025-06-01' },
  { id: '5', orderNumber: 'PO-2025-0280', vendor: { id: '1', name: 'Rajan Textiles Pvt Ltd' }, description: 'Polyester Blend (300m)', quantity: 300, unitPrice: 950, totalAmount: 285000, status: 'PAID', expectedDelivery: '2025-05-28', createdBy: 'Priya Sharma', createdAt: '2025-05-15', updatedAt: '2025-05-30' },
  { id: '6', orderNumber: 'PO-2025-0279', vendor: { id: '2', name: 'Global Electronics Supply' }, description: 'LED Display Panels (50 units)', quantity: 50, unitPrice: 15000, totalAmount: 750000, status: 'DISPUTED', expectedDelivery: '2025-05-25', createdBy: 'Rahul Verma', createdAt: '2025-05-10', updatedAt: '2025-05-29' },
  { id: '7', orderNumber: 'PO-2025-0278', vendor: { id: '4', name: 'Mehta Industrial Goods' }, description: 'Aluminium Sheets 3mm (200 units)', quantity: 200, unitPrice: 2800, totalAmount: 560000, status: 'APPROVED', expectedDelivery: '2025-06-20', createdBy: 'Anita Nair', createdAt: '2025-05-26', updatedAt: '2025-05-26' },
  { id: '8', orderNumber: 'PO-2025-0277', vendor: { id: '6', name: 'Patel Logistics & Supply' }, description: 'Bubble Wrap Roll 50m (20 rolls)', quantity: 20, unitPrice: 450, totalAmount: 9000, status: 'CLOSED', expectedDelivery: '2025-05-20', createdBy: 'Kiran Patel', createdAt: '2025-05-05', updatedAt: '2025-05-22' },
]

export const mockInvoices: Invoice[] = [
  { id: '1', invoiceNumber: 'INV-2025-0142', orderId: '4', orderNumber: 'PO-2025-0281', vendorName: 'Patel Logistics & Supply', amount: 85000, taxAmount: 15300, totalAmount: 100300, dueDate: '2025-06-15', status: 'SENT', matchStatus: 'MATCHED', isOverdue: false, agingDays: 5, createdAt: '2025-06-01' },
  { id: '2', invoiceNumber: 'INV-2025-0141', orderId: '3', orderNumber: 'PO-2025-0282', vendorName: 'Mehta Industrial Goods', amount: 320000, taxAmount: 57600, totalAmount: 377600, dueDate: '2025-05-25', status: 'OVERDUE', matchStatus: 'MATCHED', isOverdue: true, agingDays: 12, createdAt: '2025-05-25' },
  { id: '3', invoiceNumber: 'INV-2025-0140', orderId: '2', orderNumber: 'PO-2025-0283', vendorName: 'Global Electronics Supply', amount: 1700000, taxAmount: 306000, totalAmount: 2006000, dueDate: '2025-06-20', status: 'DRAFT', matchStatus: 'PENDING', isOverdue: false, agingDays: 0, createdAt: '2025-06-02' },
  { id: '4', invoiceNumber: 'INV-2025-0139', orderId: '5', orderNumber: 'PO-2025-0280', vendorName: 'Rajan Textiles Pvt Ltd', amount: 285000, taxAmount: 51300, totalAmount: 336300, dueDate: '2025-05-30', status: 'PAID', matchStatus: 'MATCHED', isOverdue: false, agingDays: 0, createdAt: '2025-05-20' },
  { id: '5', invoiceNumber: 'INV-2025-0138', orderId: '6', orderNumber: 'PO-2025-0279', vendorName: 'Global Electronics Supply', amount: 750000, taxAmount: 135000, totalAmount: 885000, dueDate: '2025-05-28', status: 'DISPUTED', matchStatus: 'MISMATCH', isOverdue: true, agingDays: 9, createdAt: '2025-05-18' },
  { id: '6', invoiceNumber: 'INV-2025-0137', orderId: '7', orderNumber: 'PO-2025-0278', vendorName: 'Mehta Industrial Goods', amount: 560000, taxAmount: 100800, totalAmount: 660800, dueDate: '2025-06-25', status: 'SENT', matchStatus: 'PARTIAL_MATCH', isOverdue: false, agingDays: 2, createdAt: '2025-06-03' },
]

export const mockPayments: Payment[] = [
  { id: '1', paymentReference: 'TXN-98432', invoiceId: '4', invoiceNumber: 'INV-2025-0139', amount: 336300, paymentDate: '2025-05-30', method: 'NEFT', status: 'MATCHED' },
  { id: '2', paymentReference: 'TXN-97821', invoiceId: '1', invoiceNumber: 'INV-2025-0142', amount: 100300, paymentDate: '2025-06-05', method: 'RTGS', status: 'MATCHED' },
  { id: '3', paymentReference: 'TXN-97011', invoiceId: '', invoiceNumber: '', amount: 280000, paymentDate: '2025-06-01', method: 'NEFT', status: 'UNMATCHED' },
  { id: '4', paymentReference: 'TXN-96544', invoiceId: '', invoiceNumber: '', amount: 450000, paymentDate: '2025-05-29', method: 'IMPS', status: 'UNMATCHED' },
]

export const mockAlerts: Alert[] = [
  { id: '1', severity: 'CRITICAL', message: 'Invoice INV-2025-0141 overdue by 12 days — ₹3,77,600 at risk', module: 'Invoices', orderId: '3', createdAt: '2025-06-06T09:00:00Z', isRead: false },
  { id: '2', severity: 'CRITICAL', message: 'Three-way match FAILED on INV-2025-0138 — vendor invoice ₹8.85L vs PO ₹7.5L', module: 'Invoices', orderId: '6', createdAt: '2025-06-06T08:30:00Z', isRead: false },
  { id: '3', severity: 'CRITICAL', message: 'PO-2025-0283 vendor not acknowledged — 48hr timer expires in 2 hours', module: 'Orders', orderId: '2', createdAt: '2025-06-06T08:00:00Z', isRead: false },
  { id: '4', severity: 'HIGH', message: '₹2,80,000 payment TXN-97011 unmatched in suspense — needs reconciliation', module: 'Payments', createdAt: '2025-06-05T14:00:00Z', isRead: false },
  { id: '5', severity: 'HIGH', message: 'PO-2025-0282 GRN completed — customer delivery not created after 2 hours', module: 'Operations', orderId: '3', createdAt: '2025-06-05T11:00:00Z', isRead: true },
  { id: '6', severity: 'MEDIUM', message: 'Vendor "Southern Raw Materials" reliability score dropped to 2.1 — review recommended', module: 'Vendors', createdAt: '2025-06-04T16:00:00Z', isRead: true },
]

export const mockGRNs: GRN[] = [
  { id: '1', orderId: '2', orderNumber: 'PO-2025-0283', vendorName: 'Global Electronics Supply', itemsExpected: 200, itemsReceived: 200, isPartial: false, createdAt: '2025-06-02', createdBy: 'Rajesh Kumar' },
  { id: '2', orderId: '3', orderNumber: 'PO-2025-0282', vendorName: 'Mehta Industrial Goods', itemsExpected: 100, itemsReceived: 85, isPartial: true, createdAt: '2025-06-01', createdBy: 'Suresh Pillai' },
  { id: '3', orderId: '4', orderNumber: 'PO-2025-0281', vendorName: 'Patel Logistics & Supply', itemsExpected: 1000, itemsReceived: 1000, isPartial: false, createdAt: '2025-05-31', createdBy: 'Rajesh Kumar' },
]

export const mockAgingData: AgingBucket[] = [
  { bucket: '0–30 days', amount: 1504300, count: 8, color: '#22c55e' },
  { bucket: '31–60 days', amount: 2890000, count: 12, color: '#f59e0b' },
  { bucket: '61–90 days', amount: 1240000, count: 5, color: '#f97316' },
  { bucket: '90+ days', amount: 885000, count: 3, color: '#ef4444' },
]

export const mockRevenueData = [
  { month: 'Jan', revenue: 3200000, cost: 2400000 },
  { month: 'Feb', revenue: 4100000, cost: 3100000 },
  { month: 'Mar', revenue: 3800000, cost: 2900000 },
  { month: 'Apr', revenue: 5200000, cost: 3800000 },
  { month: 'May', revenue: 4750000, cost: 3500000 },
  { month: 'Jun', revenue: 6100000, cost: 4400000 },
]
