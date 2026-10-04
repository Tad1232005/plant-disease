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

export async function explainPrediction(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post('/predict/explain', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return response.data
}
