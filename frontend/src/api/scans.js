import { apiClient } from './client.js'

export const scansApi = {
  history: async () => (await apiClient.get('/scans/history')).data,
  getById: async (id) => (await apiClient.get(`/scans/${id}`)).data,
  getImage: async (id) => {
    const res = await apiClient.get(`/scans/${id}/image`, { responseType: 'blob' })
    return URL.createObjectURL(res.data)
  },
}
