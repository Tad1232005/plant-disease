import { apiClient } from './client.js'

// Public GET, các thao tác ghi được backend giới hạn cho admin.
export const diseasesApi = {
  list: async () => (await apiClient.get('/disease-info')).data,
  create: async (payload) => (await apiClient.post('/disease-info', payload)).data,
  update: async (id, payload) => (await apiClient.put(`/disease-info/${id}`, payload)).data,
  remove: async (id) => (await apiClient.delete(`/disease-info/${id}`)).data,
}
