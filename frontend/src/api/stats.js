import { apiClient } from './client.js'

export const statsApi = {
  farm: async (farmId) => (await apiClient.get(`/stats/farm/${farmId}`)).data,
}
