import { apiClient } from './client.js'

/**
 * Model Version API — backend chỉ cho role admin (require_role("admin")).
 * - GET  /admin/model-versions?model_type=&is_active= : danh sách metadata.
 * - POST /admin/model-versions                        : đăng ký bundle từ manifest.json trên server.
 * - POST /admin/model-versions/{id}/activate          : validate + warm-up + đưa lên Production.
 * Không có endpoint PUT/PATCH: metadata lấy từ manifest, không sửa tay qua API.
 */
export const modelVersionsApi = {
  list: async (params) => (await apiClient.get('/admin/model-versions', { params })).data,
  register: async (payload) => (await apiClient.post('/admin/model-versions', payload)).data,
  activate: async (id) => (await apiClient.post(`/admin/model-versions/${id}/activate`)).data,
}

