import { apiClient } from './client.js'

export const adminStatsApi = {
  overview: async () => (await apiClient.get('/stats/admin/overview')).data,
}
