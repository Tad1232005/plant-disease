import { apiClient } from './client.js'

export async function predictImage(file, { farmId } = {}) {
  const formData = new FormData()
  formData.append('file', file)
  if (farmId) formData.append('farm_id', farmId)

  const response = await apiClient.post('/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return response.data // { label, confidence, top_k }
}

export async function getScanGradCam(scanId) {
  // Đảm bảo gradcam đã được sinh
  try {
    await apiClient.post(`/scans/${scanId}/gradcam`)
  } catch {
    // Nếu đã tồn tại hoặc tạo tự động thì bỏ qua lỗi
  }

  // Tải ảnh heatmap dưới dạng Blob
  const response = await apiClient.get(`/scans/${scanId}/gradcam`, {
    responseType: 'blob',
  })
  return URL.createObjectURL(response.data)
}

export async function explainPrediction(file, scanId = null) {
  if (scanId) {
    const url = await getScanGradCam(scanId)
    return { gradcam_url: url }
  }
  // Fallback mô phỏng cho guest
  return { demo: true }
}
