import { get, patch } from './client'
import type { BackendNotification, BackendNotificationList } from '../types'

export interface NotificationFilters {
  skip?: number
  limit?: number
  status?: string
  notification_type?: string
  channel?: string
}

export interface UnreadCountResponse {
  unread_count: number
}

export const notificationApi = {
  listNotifications: (filters: NotificationFilters = {}): Promise<BackendNotificationList> => {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') params.append(k, String(v))
    })
    const qs = params.toString()
    return get<BackendNotificationList>(`/notifications${qs ? `?${qs}` : ''}`)
  },

  getUnreadCount: (): Promise<UnreadCountResponse> =>
    get<UnreadCountResponse>('/notifications/unread-count'),

  markRead: (id: string): Promise<BackendNotification> =>
    patch<BackendNotification>(`/notifications/${id}/read`),
}
