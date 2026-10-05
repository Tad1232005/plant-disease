import { apiClient } from './client.js'

export const adminProposalsApi = {
  list: async () => (await apiClient.get('/admin/disease-proposals')).data,
  approve: async (id) => (await apiClient.put(`/admin/disease-proposals/${id}/approve`)).data,
  reject: async (id, reviewNote = 'Từ chối bởi Admin') =>
    (await apiClient.put(`/admin/disease-proposals/${id}/reject`, { review_note: reviewNote || 'Từ chối bởi Admin' })).data,
  update: async (id, payload) => {
    if (payload.status === 'approved') {
      return (await apiClient.put(`/admin/disease-proposals/${id}/approve`)).data
    }
    const note = payload.admin_note || payload.review_note || 'Từ chối bởi Admin'
    return (await apiClient.put(`/admin/disease-proposals/${id}/reject`, { review_note: note })).data
  },
}
