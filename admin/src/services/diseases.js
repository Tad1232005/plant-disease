import { apiClient } from './client.js'

export const adminDiseasesApi = {
  list: async () => (await apiClient.get('/disease-info')).data,
  get: async (labelKey) => (await apiClient.get(`/disease-info/${labelKey}`)).data,
  create: async (payload) => (await apiClient.post('/disease-info', payload)).data,
  update: async (labelKey, payload) => (await apiClient.put(`/disease-info/${labelKey}`, payload)).data,
  remove: async (labelKey) => (await apiClient.delete(`/disease-info/${labelKey}`)).data,
}
