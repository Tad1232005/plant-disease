import { apiClient } from './client.js'

export const modelVersionsApi = {
  list: async () => (await apiClient.get('/model-versions')).data,
  create: async (payload) => (await apiClient.post('/model-versions', payload)).data,
  update: async (id, payload) => {
    try {
      return (await apiClient.put(`/model-versions/${id}`, payload)).data
    } catch (error) {
      if (![404, 405].includes(error?.response?.status)) throw error
      return (await apiClient.put('/model-versions', { id, ...payload })).data
    }
  },
}
