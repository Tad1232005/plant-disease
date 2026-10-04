import { apiClient } from './client.js'

export const proposalsApi = {
  mine: async () => (await apiClient.get('/disease-proposals/mine')).data,
  create: async (payload) => (await apiClient.post('/disease-proposals', payload)).data,
}
