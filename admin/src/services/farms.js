import { apiClient } from './client.js'

export const adminFarmsApi = {
  list: async () => (await apiClient.get('/farms')).data,
  create: async (payload) => (await apiClient.post('/farms', payload)).data,
  update: async (id, payload) => (await apiClient.put(`/farms/${id}`, payload)).data,
  remove: async (id) => (await apiClient.delete(`/farms/${id}`)).data,
}
