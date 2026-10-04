import { apiClient } from './client.js'

export const adminStatsApi = {
  overview: async () => (await apiClient.get('/stats/admin/overview')).data,
  /** GET /admin/scans — lượt quét toàn hệ thống, nhận window ?from=&to= (ISO có múi giờ) + limit/offset. */
  scans: async (params) => (await apiClient.get('/admin/scans', { params })).data,
}
