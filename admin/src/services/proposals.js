import { apiClient } from './client.js'

export const adminProposalsApi = {
  list: async () => (await apiClient.get('/admin/disease-proposals')).data,
  update: async (id, payload) => {
    try {
      return (await apiClient.put(`/admin/disease-proposals/${id}`, payload)).data
    } catch (error) {
      if (![404, 405].includes(error?.response?.status)) throw error
      return (await apiClient.put('/admin/disease-proposals', { id, ...payload })).data
    }
  },
}
