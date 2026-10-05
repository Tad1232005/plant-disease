import { apiClient } from './client.js'

/**
 * Quản lý tài khoản — backend chỉ cho role admin (require_role("admin")).
 * - GET   /admin/users                 : danh sách toàn hệ thống, lọc ?role=
 * - GET   /admin/users/{id}            : chi tiết 1 tài khoản
 * - POST  /admin/users                 : tạo technician hoặc manager
 * - PATCH /admin/users/{id}/status     : khóa/mở tài khoản, bắt buộc có reason
 * BE không có endpoint cập nhật thông tin hay xóa tài khoản.
 */
export const adminUsersApi = {
  list: async (params) => (await apiClient.get('/admin/users', { params })).data,
  get: async (id) => (await apiClient.get(`/admin/users/${id}`)).data,
  create: async (payload) => (await apiClient.post('/admin/users', payload)).data,
  setStatus: async (id, payload) => (await apiClient.patch(`/admin/users/${id}/status`, payload)).data,
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
