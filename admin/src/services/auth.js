import { apiClient } from './client.js'

export const adminUsersApi = {
  list: async (params) => (await apiClient.get('/admin/users', { params })).data,
  create: async (payload) => (await apiClient.post('/admin/users', payload)).data,
  changeStatus: async (userId, payload) => (await apiClient.patch(`/admin/users/${userId}/status`, payload)).data,
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
  async changePassword(payload) {
    const { data } = await apiClient.post('/auth/change-password', payload)
    return data
  },
}
