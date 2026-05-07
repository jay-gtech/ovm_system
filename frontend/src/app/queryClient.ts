import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query'

/**
 * Global Query Client Configuration
 * Manages caching, retries, and global error handling for all data fetching.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
  },
  queryCache: new QueryCache({
    onError: (error) => {
      // Global error handling for queries
      console.error('Query Error:', error.message)
      // You could trigger a global toast notification here
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      // Global error handling for mutations
      console.error('Mutation Error:', error.message)
      // You could trigger a global toast notification here
    },
  }),
})
