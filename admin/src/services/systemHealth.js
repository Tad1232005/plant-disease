import axios from 'axios'
import { API_ORIGIN, apiClient } from './client.js'

/**
 * Số bảng nghiệp vụ trong SQLAlchemy metadata (backend/app/models + alembic).
 * DB PostgreSQL còn có bảng alembic_version do Alembic tạo, không tính vào con số hiển thị.
 */
export const DB_TABLE_COUNT = 11

// Health endpoint không cần auth nên dùng client riêng, timeout ngắn để UI phản hồi nhanh.
const originClient = axios.create({ baseURL: API_ORIGIN, timeout: 8000 })

async function probe(request) {
  try {
    await request
    return true
  } catch {
    return false
  }
}

export const systemHealthApi = {
  /** GET /health/live — tiến trình API còn sống. */
  live: () => probe(originClient.get('/health/live')),
  /** GET /health/ready — DB kết nối được và alembic_version đúng revision hiện tại. */
  ready: () => probe(originClient.get('/health/ready')),
  /** GET /predict/capabilities — policy inference đọc được (public, không cần token). */
  capabilities: () => probe(apiClient.get('/predict/capabilities', { timeout: 8000 })),
  /** GET /admin/model-versions?is_active=true — các version đang chạy Production. */
  activeModelVersions: async () =>
    (await apiClient.get('/admin/model-versions', { params: { is_active: true }, timeout: 8000 })).data,
}
