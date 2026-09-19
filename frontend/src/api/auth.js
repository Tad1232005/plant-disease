import { apiClient } from './client.js'

export const authApi = {
  async register(payload) {
    const { data } = await apiClient.post('/auth/register', payload)
    return data
  },
  async login(payload) {
    const { data } = await apiClient.post('/auth/login', payload)
    return data
  },
  async me() {
    const { data } = await apiClient.get('/auth/me')
    return data
  },
}
