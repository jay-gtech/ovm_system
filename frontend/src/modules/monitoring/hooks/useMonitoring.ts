import { useQuery } from '@tanstack/react-query'
import { monitoringApi } from '../../../api/monitoring'

export const monitoringKeys = {
  all: ['monitoring'] as const,
  outstandingInvoices: () => [...monitoringKeys.all, 'outstanding-invoices'] as const,
  pendingPayments: () => [...monitoringKeys.all, 'pending-payments'] as const,
  unsettledPayments: () => [...monitoringKeys.all, 'unsettled-payments'] as const,
  pendingSettlements: () => [...monitoringKeys.all, 'pending-settlements'] as const,
  financialSummary: () => [...monitoringKeys.all, 'financial-summary'] as const,
}

export function useOutstandingInvoices() {
  return useQuery({
    queryKey: monitoringKeys.outstandingInvoices(),
    queryFn: monitoringApi.getOutstandingInvoices,
    staleTime: 60_000,
  })
}

export function usePendingPayments() {
  return useQuery({
    queryKey: monitoringKeys.pendingPayments(),
    queryFn: monitoringApi.getPendingPayments,
    staleTime: 60_000,
  })
}

export function useUnsettledPayments() {
  return useQuery({
    queryKey: monitoringKeys.unsettledPayments(),
    queryFn: monitoringApi.getUnsettledPayments,
    staleTime: 60_000,
  })
}

export function usePendingSettlements() {
  return useQuery({
    queryKey: monitoringKeys.pendingSettlements(),
    queryFn: monitoringApi.getPendingSettlements,
    staleTime: 60_000,
  })
}

export function useFinancialSummary() {
  return useQuery({
    queryKey: monitoringKeys.financialSummary(),
    queryFn: monitoringApi.getFinancialSummary,
    staleTime: 60_000,
  })
}
