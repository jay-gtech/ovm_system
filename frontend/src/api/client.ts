import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig } from 'axios'
import { setupInterceptors } from './interceptors'

const client: AxiosInstance = axios.create({
  baseURL: import.meta.env['VITE_API_BASE_URL'] || 'http://localhost:4000',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' },
})

setupInterceptors(client)
export default client

export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const res = await client.get<T>(url, config)
  return res.data
}
export async function post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
  const res = await client.post<T>(url, data, config)
  return res.data
}
export async function put<T>(url: string, data?: unknown): Promise<T> {
  const res = await client.put<T>(url, data)
  return res.data
}
export async function del<T>(url: string): Promise<T> {
  const res = await client.delete<T>(url)
  return res.data
}
