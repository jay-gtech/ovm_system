import { useQuery } from '@tanstack/react-query'
import { monitoringApi } from '../../../api/monitoring'
import { Card } from '../../../components/ui/Card'
import { Table, Th, Td } from '../../../components/ui/Table'
import { StatusBadge } from '../../../components/ui/StatusBadge'
import { formatINR } from '../../../utils/format'
import { Loader } from '../../../components/feedback/Loader'

export function PendingPaymentsTable() {
  const { data: payments, isLoading, isError } = useQuery({
    queryKey: ['monitoring', 'pending-payments'],
    queryFn: () => monitoringApi.getPendingPayments()
  })

  if (isLoading) return <Card className="p-6 flex justify-center"><Loader /></Card>
  if (isError) return <Card className="p-6 text-red-500">Failed to load pending payments.</Card>

  return (
    <Card className="overflow-hidden">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <h3 className="text-lg font-semibold">Pending Payments</h3>
      </div>
      <Table>
        <thead>
          <tr>
            <Th>Reference</Th>
            <Th>Invoice #</Th>
            <Th>Vendor</Th>
            <Th>Amount</Th>
            <Th>Aging</Th>
            <Th>Status</Th>
          </tr>
        </thead>
        <tbody>
          {payments?.length === 0 ? (
            <tr>
              <Td colSpan={6} className="text-center py-4 text-slate-500">No pending payments</Td>
            </tr>
          ) : (
            payments?.map((payment) => (
              <tr key={payment.id}>
                <Td className="font-medium">{payment.payment_reference}</Td>
                <Td>{payment.invoice.invoice_number}</Td>
                <Td>{payment.vendor.legal_name || payment.vendor.vendor_code}</Td>
                <Td className="font-semibold">{formatINR(payment.amount)}</Td>
                <Td>{payment.aging_days}d</Td>
                <Td><StatusBadge status={payment.status} /></Td>
              </tr>
            ))
          )}
        </tbody>
      </Table>
    </Card>
  )
}
