import { apiClient } from './client.js'

export async function predictImage(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post('/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return response.data // { label, confidence, top_k }
}
