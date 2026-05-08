import { useQuery } from '@tanstack/react-query'
import { monitoringApi } from '../../../api/monitoring'
import { Card } from '../../../components/ui/Card'
import { Table, Th, Td } from '../../../components/ui/Table'
import { StatusBadge } from '../../../components/ui/StatusBadge'
import { formatINR } from '../../../utils/format'
import { Loader } from '../../../components/feedback/Loader'

export function OutstandingInvoicesTable() {
  const { data: invoices, isLoading, isError } = useQuery({
    queryKey: ['monitoring', 'outstanding-invoices'],
    queryFn: () => monitoringApi.getOutstandingInvoices()
  })

  if (isLoading) return <Card className="p-6 flex justify-center"><Loader /></Card>
  if (isError) return <Card className="p-6 text-red-500">Failed to load outstanding invoices.</Card>

  return (
    <Card className="overflow-hidden">
      <div className="p-4 border-b border-slate-200 dark:border-slate-800">
        <h3 className="text-lg font-semibold">Outstanding Invoices</h3>
      </div>
      <Table>
        <thead>
          <tr>
            <Th>Invoice #</Th>
            <Th>Vendor</Th>
            <Th>Amount</Th>
            <Th>Outstanding</Th>
            <Th>Aging</Th>
            <Th>Status</Th>
          </tr>
        </thead>
        <tbody>
          {invoices?.length === 0 ? (
            <tr>
              <Td colSpan={6} className="text-center py-4 text-slate-500">No outstanding invoices</Td>
            </tr>
          ) : (
            invoices?.map((inv) => (
              <tr key={inv.id}>
                <Td className="font-medium">{inv.invoice_number}</Td>
                <Td>{inv.vendor.legal_name || inv.vendor.vendor_code}</Td>
                <Td>{formatINR(inv.total_amount)}</Td>
                <Td className="font-semibold text-amber-600">{formatINR(inv.outstanding_amount)}</Td>
                <Td>
                  <span className={inv.is_overdue ? "text-red-600 font-medium" : ""}>
                    {inv.aging_days}d {inv.is_overdue && '(Overdue)'}
                  </span>
                </Td>
                <Td><StatusBadge status={inv.status} /></Td>
              </tr>
            ))
          )}
        </tbody>
      </Table>
    </Card>
  )
}
