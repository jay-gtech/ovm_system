import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { paymentsApi, type PaymentListParams, type CreatePaymentPayload } from '../api/payments'
import type { PaymentStatus } from '../types'

export const paymentKeys = {
  all: ['payments'] as const,
  lists: () => [...paymentKeys.all, 'list'] as const,
  list: (params: PaymentListParams) => [...paymentKeys.lists(), params] as const,
  details: () => [...paymentKeys.all, 'detail'] as const,
  detail: (id: string) => [...paymentKeys.details(), id] as const,
}

export function usePayments(params?: PaymentListParams) {
  return useQuery({
    queryKey: paymentKeys.list(params || {}),
    queryFn: () => paymentsApi.list(params),
  })
}

export function usePayment(id: string) {
  return useQuery({
    queryKey: paymentKeys.detail(id),
    queryFn: () => paymentsApi.get(id),
    enabled: !!id,
  })
}

export function useCreatePayment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreatePaymentPayload) => paymentsApi.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: paymentKeys.lists() })
      queryClient.invalidateQueries({ queryKey: ['invoices', 'detail', variables.invoice_id] })
    },
  })
}

export function useUpdatePaymentStatus() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: PaymentStatus }) => 
      paymentsApi.updateStatus(id, status),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: paymentKeys.all })
      queryClient.invalidateQueries({ queryKey: ['invoices', 'detail', data.invoice_id] })
    },
  })
}
