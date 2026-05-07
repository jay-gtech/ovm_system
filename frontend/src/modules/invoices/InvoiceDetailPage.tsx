import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Plus, Calendar, FileText, User, Hash } from 'lucide-react'
import { PageHeader } from '../../components/ui/PageHeader'
import { Button } from '../../components/ui/Button'
import { Card, CardContent } from '../../components/ui/Card'
import { StatusBadge } from '../../components/ui/StatusBadge'
import { formatINR, formatDate } from '../../utils/format'
import { useInvoice } from '../../hooks/useInvoices'
import { usePayments } from '../../hooks/usePayments'
import { PaymentTable } from '../payments/components/PaymentTable'
import { PaymentForm } from '../payments/components/PaymentForm'
import { PaymentSummaryCard } from '../payments/components/PaymentSummaryCard'
import { Loader } from '../../components/feedback/Loader'
import { ErrorState } from '../../components/feedback/ErrorState'

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [showPaymentForm, setShowPaymentForm] = useState(false)

  const { data: invoice, isLoading: isLoadingInvoice, error: invoiceError } = useInvoice(id!)
  const { data: paymentsData, isLoading: isLoadingPayments } = usePayments({ invoiceId: id })

  if (isLoadingInvoice) return <Loader />
  if (invoiceError || !invoice) return <ErrorState message="Could not load invoice details." />

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-4">
        <button 
          onClick={() => navigate('/invoices')}
          className="p-2 hover:bg-slate-100 rounded-full transition-colors"
        >
          <ArrowLeft size={20} className="text-slate-500" />
        </button>
        <PageHeader 
          title={`Invoice ${invoice.invoiceNumber}`} 
          subtitle={`Issued on ${formatDate(invoice.createdAt)}`}
          actions={
            <div className="flex gap-2">
              <StatusBadge status={invoice.status} size="md" />
            </div>
          }
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <div className="border-b border-slate-100 px-5 py-4">
              <h3 className="text-sm font-bold text-slate-700 flex items-center gap-2">
                <FileText size={16} className="text-slate-400" />
                Invoice Information
              </h3>
            </div>
            <CardContent className="p-6">
              <div className="grid gap-6 sm:grid-cols-2">
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <User size={16} className="text-slate-400 mt-1" />
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Vendor</p>
                      <p className="font-semibold text-slate-900">{invoice.vendorName}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Hash size={16} className="text-slate-400 mt-1" />
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Order Number</p>
                      <p className="font-mono text-sm text-slate-600">{invoice.orderNumber}</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <Calendar size={16} className="text-slate-400 mt-1" />
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Due Date</p>
                      <p className={`font-semibold ${invoice.isOverdue ? 'text-red-600' : 'text-slate-900'}`}>
                        {formatDate(invoice.dueDate)}
                        {invoice.isOverdue && <span className="ml-2 text-xs">(Overdue)</span>}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <FileText size={16} className="text-slate-400 mt-1" />
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Match Status</p>
                      <StatusBadge status={invoice.matchStatus} />
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <div className="border-b border-slate-100 px-5 py-4 flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-700 flex items-center gap-2">
                <Calendar size={16} className="text-slate-400" />
                Payment History
              </h3>
              {!showPaymentForm && invoice.status !== 'PAID' && (
                <Button 
                  size="sm" 
                  className="gap-2 h-8" 
                  onClick={() => setShowPaymentForm(true)}
                >
                  <Plus size={14} /> Record Payment
                </Button>
              )}
            </div>
            <CardContent className={showPaymentForm ? 'p-6' : 'p-0'}>
              {showPaymentForm ? (
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-5">
                  <h4 className="text-sm font-bold text-slate-800 mb-4">Record New Payment</h4>
                  <PaymentForm 
                    invoiceId={invoice.id} 
                    onSuccess={() => setShowPaymentForm(false)}
                    onCancel={() => setShowPaymentForm(false)}
                  />
                </div>
              ) : (
                <PaymentTable 
                  payments={paymentsData?.items || []} 
                  isLoading={isLoadingPayments} 
                />
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <PaymentSummaryCard 
            totalAmount={invoice.totalAmount}
            paidAmount={invoice.paidAmount}
            outstandingAmount={invoice.outstandingAmount}
          />
          
          <Card className="bg-brand-900 text-white border-none">
            <CardContent className="p-6 space-y-4">
              <h4 className="font-bold text-brand-100 text-xs uppercase tracking-widest">Quick Actions</h4>
              <div className="grid gap-2">
                <Button variant="outline" className="w-full justify-start border-brand-700 hover:bg-brand-800 text-white">
                  Download PDF
                </Button>
                <Button variant="outline" className="w-full justify-start border-brand-700 hover:bg-brand-800 text-white">
                  Email Vendor
                </Button>
                <Button variant="outline" className="w-full justify-start border-brand-700 hover:bg-brand-800 text-white">
                  Dispute Invoice
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
