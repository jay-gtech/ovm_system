import { useUnsettledPayments } from '../hooks/useMonitoring'
import { Card } from '../../../components/ui/Card'
import { Table, Th, Td } from '../../../components/ui/Table'
import { formatINR } from '../../../utils/format'
import { Loader } from '../../../components/feedback/Loader'

export function UnsettledPaymentsTable() {
  const { data: unsettled, isLoading, isError } = useUnsettledPayments()

  if (isLoading) return <Card className="p-6 flex justify-center"><Loader /></Card>
  if (isError) return <Card className="p-6 text-red-500">Failed to load unsettled payments.</Card>

  return (
    <Card className="overflow-hidden">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <h3 className="text-lg font-semibold text-red-600 dark:text-red-400">Unsettled Liabilities</h3>
      </div>
      <Table>
        <thead>
          <tr>
            <Th>Payment Ref</Th>
            <Th>Invoice #</Th>
            <Th>Vendor</Th>
            <Th>Payment</Th>
            <Th>Settled</Th>
            <Th>Liability</Th>
          </tr>
        </thead>
        <tbody>
          {unsettled?.length === 0 ? (
            <tr>
              <Td colSpan={6} className="text-center py-4 text-slate-500">No unsettled liabilities</Td>
            </tr>
          ) : (
            unsettled?.map((item) => (
              <tr key={item.id}>
                <Td className="font-medium">{item.payment_reference}</Td>
                <Td>{item.invoice.invoice_number}</Td>
                <Td>{item.vendor.legal_name || item.vendor.vendor_code}</Td>
                <Td>{formatINR(item.amount)}</Td>
                <Td>{formatINR(item.settlement_total)}</Td>
                <Td className="font-bold text-red-600">{formatINR(item.unsettled_amount)}</Td>
              </tr>
            ))
          )}
        </tbody>
      </Table>
    </Card>
  )
}
