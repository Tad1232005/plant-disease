import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { en } from '../i18n/en.js'
import { vi } from '../i18n/vi.js'
import { autoTranslate, getCachedTranslation } from '../services/translator.js'

const STORAGE_KEY = 'plantcare_admin_lang'
const dictionaries = { vi, en }

const LanguageContext = createContext(null)

function getInitialLanguage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved === 'vi' || saved === 'en') return saved
  } catch {
    /* ignore */
  }
  return 'vi'
}

export function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(getInitialLanguage)
  const [, setCacheRevision] = useState(0) // Trigger re-render khi có bản dịch tự động mới về

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, language)
    } catch {
      /* ignore */
    }
    if (typeof document !== 'undefined') {
      document.documentElement.lang = language
    }
  }, [language])

  const toggleLanguage = useCallback(() => {
    setLanguage((cur) => (cur === 'vi' ? 'en' : 'vi'))
  }, [])

  /**
   * Hàm t(path, params, options)
   * 1. Tìm trong từ điển vi/en hiện tại
   * 2. Nếu không tìm thấy:
   *    - Nếu đang ở tiếng Việt: trả về chính path/text
   *    - Nếu đang ở tiếng Anh: kiểm tra cache xem đã dịch tự động chưa;
   *      nếu chưa, ngầm gửi request dịch tự động và lưu cache, khi có kết quả sẽ kích hoạt cập nhật UI!
   */
  const t = useCallback(
    (path, params = {}) => {
      if (!path) return ''
      const dict = dictionaries[language] || vi
      const keys = typeof path === 'string' ? path.split('.') : []
      let val = dict

      // Tra cứu theo key (ví dụ: 'nav.dashboard')
      if (keys.length > 1) {
        for (const k of keys) {
          if (val && typeof val === 'object' && k in val) {
            val = val[k]
          } else {
            val = null
            break
          }
        }
      } else {
        val = dict?.[path] ?? null
      }

      // Nếu tìm thấy chuỗi trong từ điển
      if (typeof val === 'string') {
        return val.replace(/\{(\w+)\}/g, (_, key) => (params[key] !== undefined ? params[key] : `{${key}}`))
      }

      // Nếu không có trong từ điển tiếng Anh:
      if (language === 'en') {
        // Kiểm tra xem đã có bản dịch tự động trong cache chưa
        const cached = getCachedTranslation(path, 'en')
        if (cached) {
          return cached.replace(/\{(\w+)\}/g, (_, key) => (params[key] !== undefined ? params[key] : `{${key}}`))
        }

        // Nếu chuỗi là một thông báo/nội dung có dấu cách hoặc tiếng Việt (không phải key kỹ thuật dạng a.b)
        // Kích hoạt dịch tự động không đồng bộ, khi hoàn tất sẽ cập nhật state để giao diện tự hiển thị tiếng Anh
        if (typeof path === 'string' && (path.includes(' ') || /[à-ỹÀ-Ỹ]/.test(path))) {
          autoTranslate(path, 'en').then((translated) => {
            // Chỉ re-render khi thực sự có bản dịch mới (tránh lặp vô hạn khi offline)
            if (translated !== path) setCacheRevision((r) => r + 1)
          })
        }
      }

      // Fallback về từ điển tiếng Việt hoặc chính path
      let fallback = vi
      if (keys.length > 1) {
        for (const k of keys) {
          if (fallback && typeof fallback === 'object' && k in fallback) {
            fallback = fallback[k]
          } else {
            fallback = path
            break
          }
        }
      } else {
        fallback = vi?.[path] ?? path
      }

      const finalVal = typeof fallback === 'string' ? fallback : path
      return finalVal.replace(/\{(\w+)\}/g, (_, key) => (params[key] !== undefined ? params[key] : `{${key}}`))
    },
    [language],
  )

  /**
   * Hàm hỗ trợ dịch trực tiếp cho các thông báo / toast / alert không đồng bộ
   * Ví dụ: const msg = await translateMessage("Đã lưu thành công")
   */
  const translateMessage = useCallback(
    async (text) => {
      if (!text) return ''
      if (language === 'vi') return text
      return await autoTranslate(text, 'en')
    },
    [language],
  )

  const value = useMemo(
    () => ({
      language,
      isEn: language === 'en',
      isVi: language === 'vi',
      setLanguage,
      toggleLanguage,
      t,
      translateMessage,
      autoTranslate,
    }),
    [language, toggleLanguage, t, translateMessage],
  )

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) throw new Error('useLanguage phải được dùng bên trong LanguageProvider')
  return context
}

