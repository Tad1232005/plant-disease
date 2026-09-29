import { apiClient } from './client.js'

export const adminUsersApi = {
  list: async (params) => (await apiClient.get('/admin/users', { params })).data,
}

export const authApi = {
  async login(payload) {
    const { data } = await apiClient.post('/auth/login', payload)
    return data
  },
  async me() {
    const { data } = await apiClient.get('/auth/me')
    return data
  },
}
