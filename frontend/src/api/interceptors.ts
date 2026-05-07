import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

export function setupInterceptors(client: AxiosInstance) {
  client.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      const token = localStorage.getItem('ovm_token')
      if (token) config.headers.Authorization = `Bearer ${token}`
      return config
    },
    (error) => Promise.reject(error)
  )
  client.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('ovm_token')
        window.location.href = '/login'
      }
      return Promise.reject(error)
    }
  )
}
