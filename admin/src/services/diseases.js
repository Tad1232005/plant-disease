import { apiClient } from './client.js'

/**
 * Nội dung bệnh — public được đọc, chỉ Admin được thêm/sửa/xóa.
 * - GET    /disease-info            : danh sách public, có limit/offset
 * - GET    /disease-info/{label}    : chi tiết 1 bệnh
 * - POST   /disease-info            : thêm bệnh mới (admin)
 * - PUT    /disease-info/{label}    : cập nhật bệnh (admin)
 * - DELETE /disease-info/{label}    : xóa mềm bệnh (admin)
 */
export const diseasesApi = {
  list: async (params) => (await apiClient.get('/disease-info', { params })).data,
  get: async (labelKey) => (await apiClient.get(`/disease-info/${labelKey}`)).data,
  create: async (payload) => (await apiClient.post('/disease-info', payload)).data,
  update: async (labelKey, payload) => (await apiClient.put(`/disease-info/${labelKey}`, payload)).data,
  remove: async (labelKey) => (await apiClient.delete(`/disease-info/${labelKey}`)).data,
}
