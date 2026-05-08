import { PageHeader } from '../../components/ui/PageHeader'
import { MonitoringSummaryCard } from './components/MonitoringSummaryCard'
import { OutstandingInvoicesTable } from './components/OutstandingInvoicesTable'
import { PendingPaymentsTable } from './components/PendingPaymentsTable'
import { UnsettledPaymentsTable } from './components/UnsettledPaymentsTable'
import { PendingSettlementsTable } from './components/PendingSettlementsTable'

export default function MonitoringPage() {
  return (
    <div className="space-y-6">
      <PageHeader 
        title="Operational Monitoring" 
        subtitle="Workflow risk visibility and unresolved liability tracking."
      />

      <MonitoringSummaryCard />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <OutstandingInvoicesTable />
        <PendingPaymentsTable />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <UnsettledPaymentsTable />
        <PendingSettlementsTable />
      </div>
    </div>
  )
}
