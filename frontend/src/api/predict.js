import axios from 'axios'

// Đổi URL này khi deploy backend lên server thật
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function predictImage(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await axios.post(`${API_BASE_URL}/api/predict`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })

  return response.data // { label, confidence }
}
