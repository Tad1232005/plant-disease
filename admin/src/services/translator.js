// Dịch vụ tự động dịch (Auto-Translate) với bộ nhớ đệm (localStorage)
// Kết hợp giữa dịch vụ trực tuyến và bộ đệm offline để tối ưu tốc độ và không cần phụ thuộc hoàn toàn vào file cứng.

const TRANSLATE_CACHE_KEY = 'plantcare_i18n_autocache'

// Đọc cache từ localStorage
function getCache() {
  try {
    const raw = localStorage.getItem(TRANSLATE_CACHE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

// Lưu cache vào localStorage
function saveCache(cache) {
  try {
    localStorage.setItem(TRANSLATE_CACHE_KEY, JSON.stringify(cache))
  } catch {
    /* ignore storage quota limits */
  }
}

const memoryCache = getCache()

// Theo dõi các request đang bay (in-flight) để tránh gọi API trùng lặp
const pending = new Map()

// Các chuỗi đã dịch thất bại trong phiên hiện tại — không thử lại để tránh lặp vô hạn khi offline
const failed = new Set()

/**
 * Tự động dịch một chuỗi văn bản (message / notification) sang ngôn ngữ mục tiêu (mặc định 'en').
 * Nếu đã có trong cache thì trả về ngay lập tức (0ms).
 * Nếu chưa có, gọi API dịch (Google Translate GTX) và tự động ghi vào cache cho các lần sau.
 *
 * @param {string} text - Văn bản cần dịch (ví dụ: "Đã lưu thành công")
 * @param {string} targetLang - 'en' hoặc 'vi'
 * @returns {Promise<string>}
 */
export function autoTranslate(text, targetLang = 'en') {
  if (!text || typeof text !== 'string') return Promise.resolve(text)

  const trimmed = text.trim()
  if (!trimmed) return Promise.resolve(text)

  const cacheKey = `${targetLang}:${trimmed}`
  if (memoryCache[cacheKey]) {
    return Promise.resolve(memoryCache[cacheKey])
  }

  // Đã thử và thất bại trong phiên này → trả về gốc, không gọi lại
  if (failed.has(cacheKey)) {
    return Promise.resolve(trimmed)
  }

  // Nếu request cho chuỗi này đang chạy, dùng lại promise cũ
  if (pending.has(cacheKey)) {
    return pending.get(cacheKey)
  }

  const promise = (async () => {
    try {
      const sourceLang = targetLang === 'en' ? 'vi' : 'en'
      const url = new URL('https://translate.googleapis.com/translate_a/single')
      url.searchParams.set('client', 'gtx')
      url.searchParams.set('sl', sourceLang)
      url.searchParams.set('tl', targetLang)
      url.searchParams.set('dt', 't')
      url.searchParams.set('q', trimmed)

      const res = await fetch(url.toString())
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      // Cấu trúc response GTX: [[["Bản dịch", "Gốc", null, null, 1]], ...]
      const translatedText = data?.[0]?.map?.((part) => part[0])?.join('') || ''

      if (translatedText) {
        memoryCache[cacheKey] = translatedText
        saveCache(memoryCache)
        return translatedText
      }
    } catch {
      // Nếu mất mạng hoặc API lỗi, fallback về chính văn bản gốc an toàn
    } finally {
      pending.delete(cacheKey)
    }

    failed.add(cacheKey)
    return trimmed
  })()

  pending.set(cacheKey, promise)
  return promise
}

/**
 * Lấy đồng bộ từ cache (nếu đã từng được dịch trước đó)
 */
export function getCachedTranslation(text, targetLang = 'en') {
  if (!text || typeof text !== 'string') return text
  const trimmed = text.trim()
  const cacheKey = `${targetLang}:${trimmed}`
  return memoryCache[cacheKey] || null
}
