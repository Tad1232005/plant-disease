import { apiClient } from './client.js'

export const managedUsersApi = {
  list: async () => (await apiClient.get('/manager/users')).data,
  create: async (payload) => (await apiClient.post('/manager/users', payload)).data,
  changeStatus: async (userId, payload) => (await apiClient.patch(`/manager/users/${userId}/status`, payload)).data,
  resetPassword: async (userId, newPassword) => (await apiClient.post(`/manager/users/${userId}/reset-password`, { new_password: newPassword })).data,
}

export const farmMembersApi = {
  list: async (farmId) => (await apiClient.get(`/farms/${farmId}/members`)).data,
  add: async (farmId, userId) => (await apiClient.post(`/farms/${farmId}/members`, { user_id: userId })).data,
  remove: async (farmId, userId) => (await apiClient.delete(`/farms/${farmId}/members/${userId}`)).data,
}
