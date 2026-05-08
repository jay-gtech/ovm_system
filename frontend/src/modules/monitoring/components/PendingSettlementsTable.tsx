import { usePendingSettlements } from '../hooks/useMonitoring'
import { Card } from '../../../components/ui/Card'
import { Table, Th, Td } from '../../../components/ui/Table'
import { StatusBadge } from '../../../components/ui/StatusBadge'
import { formatINR } from '../../../utils/format'
import { Loader } from '../../../components/feedback/Loader'

export function PendingSettlementsTable() {
  const { data: settlements, isLoading, isError } = usePendingSettlements()

  if (isLoading) return <Card className="p-6 flex justify-center"><Loader /></Card>
  if (isError) return <Card className="p-6 text-red-500">Failed to load pending settlements.</Card>

  return (
    <Card className="overflow-hidden">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <h3 className="text-lg font-semibold">Pending Settlements</h3>
      </div>
      <Table>
        <thead>
          <tr>
            <Th>Reference</Th>
            <Th>Vendor</Th>
            <Th>Invoice #</Th>
            <Th>Amount</Th>
            <Th>Aging</Th>
            <Th>Status</Th>
          </tr>
        </thead>
        <tbody>
          {settlements?.length === 0 ? (
            <tr>
              <Td colSpan={6} className="text-center py-4 text-slate-500">No pending settlements</Td>
            </tr>
          ) : (
            settlements?.map((item) => (
              <tr key={item.id}>
                <Td className="font-medium">{item.settlement_reference}</Td>
                <Td>{item.vendor.legal_name || item.vendor.vendor_code}</Td>
                <Td>{item.invoice.invoice_number}</Td>
                <Td className="font-semibold">{formatINR(item.amount)}</Td>
                <Td>{item.aging_days}d</Td>
                <Td><StatusBadge status={item.status} /></Td>
              </tr>
            ))
          )}
        </tbody>
      </Table>
    </Card>
  )
}
