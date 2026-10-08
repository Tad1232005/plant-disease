import { apiClient } from './client.js'

export const adminAuditApi = {
  list: async (params) => (await apiClient.get('/admin/audit-events', { params })).data,
}
