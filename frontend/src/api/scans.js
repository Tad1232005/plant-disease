import { apiClient } from './client.js'

export const scansApi = {
  history: async () => (await apiClient.get('/scans/history')).data,
  getById: async (id) => (await apiClient.get(`/scans/${id}`)).data,
}
