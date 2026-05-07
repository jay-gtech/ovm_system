import { useState } from 'react'
import { Button } from '../../../components/ui/Button'
import { useCreatePayment } from '../../../hooks/usePayments'
import type { PaymentMethod } from '../../../types'

interface PaymentFormProps {
  invoiceId: string
  onSuccess: () => void
  onCancel: () => void
}

export function PaymentForm({ invoiceId, onSuccess, onCancel }: PaymentFormProps) {
  const createPayment = useCreatePayment()
  const [formData, setFormData] = useState({
    payment_reference: '',
    amount: '',
    payment_method: 'BANK_TRANSFER' as PaymentMethod,
    payment_date: new Date().toISOString().split('T')[0],
    notes: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createPayment.mutate({
      invoice_id: invoiceId,
      payment_reference: formData.payment_reference,
      amount: parseFloat(formData.amount),
      payment_method: formData.payment_method,
      payment_date: new Date(formData.payment_date).toISOString(),
      notes: formData.notes
    }, {
      onSuccess: () => {
        onSuccess()
      }
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1">Payment Reference</label>
          <input
            required
            type="text"
            placeholder="TXN-XXXXX"
            value={formData.payment_reference}
            onChange={e => setFormData({ ...formData, payment_reference: e.target.value })}
            className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none focus:border-brand-400"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1">Amount (₹)</label>
          <input
            required
            type="number"
            step="0.01"
            placeholder="0.00"
            value={formData.amount}
            onChange={e => setFormData({ ...formData, amount: e.target.value })}
            className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none focus:border-brand-400"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1">Payment Date</label>
          <input
            required
            type="date"
            value={formData.payment_date}
            onChange={e => setFormData({ ...formData, payment_date: e.target.value })}
            className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm outline-none focus:border-brand-400"
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-slate-500 mb-1">Payment Method</label>
          <select
            value={formData.payment_method}
            onChange={e => setFormData({ ...formData, payment_method: e.target.value as PaymentMethod })}
            className="h-9 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-brand-400"
          >
            <option value="BANK_TRANSFER">Bank Transfer</option>
            <option value="CREDIT_CARD">Credit Card</option>
            <option value="CHECK">Check</option>
            <option value="CASH">Cash</option>
            <option value="OTHER">Other</option>
          </select>
        </div>
      </div>
      <div>
        <label className="block text-xs font-semibold text-slate-500 mb-1">Notes (Optional)</label>
        <textarea
          value={formData.notes}
          onChange={e => setFormData({ ...formData, notes: e.target.value })}
          rows={2}
          className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-400"
        />
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" size="sm" onClick={onCancel} disabled={createPayment.isPending}>
          Cancel
        </Button>
        <Button type="submit" size="sm" disabled={createPayment.isPending}>
          {createPayment.isPending ? 'Recording...' : 'Record Payment'}
        </Button>
      </div>
    </form>
  )
}
