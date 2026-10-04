import { AlertTriangle, CircleHelp } from 'lucide-react'
import { useLanguage } from '../../contexts/LanguageContext.jsx'
import Modal from './Modal.jsx'

const tones = {
  // Hành động phá huỷ (xóa, từ chối) — mặc định giữ nguyên hành vi cũ.
  danger: {
    box: 'bg-rose-50 text-rose-800 dark:bg-rose-950/40 dark:text-rose-200',
    button: 'bg-rose-600 hover:bg-rose-700',
    icon: AlertTriangle,
  },
  // Hành động quan trọng nhưng không phá huỷ (kích hoạt, duyệt).
  primary: {
    box: 'bg-leaf-50 text-leaf-800 dark:bg-leaf-900/40 dark:text-leaf-200',
    button: 'bg-leaf-600 hover:bg-leaf-700',
    icon: CircleHelp,
  },
}

/**
 * Hộp thoại xác nhận dùng chung.
 *
 * Mặc định giữ đúng hành vi cũ (xác nhận xóa, tone đỏ) để các trang đang dùng
 * không phải sửa. Truyền `tone="primary"` cho hành động không phá huỷ.
 */
export default function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = 'Xác nhận xóa',
  message,
  confirmLabel = 'common.delete_data',
  tone = 'danger',
  loading = false,
}) {
  const { t } = useLanguage()
  const style = tones[tone] || tones.danger
  const Icon = style.icon

  return (
    <Modal open={open} onClose={onClose} title={t(title)} size="sm">
      <div className={`flex gap-4 rounded-2xl p-4 text-sm ${style.box}`}>
        <Icon className="mt-0.5 shrink-0" size={20} />
        <p className="leading-6">{t(message)}</p>
      </div>
      <div className="mt-6 flex justify-end gap-3">
        <button className="btn-secondary" onClick={onClose} disabled={loading}>{t('common.cancel')}</button>
        <button
          className={`inline-flex items-center rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50 ${style.button}`}
          onClick={onConfirm}
          disabled={loading}
        >
          {loading ? t('common.saving') : t(confirmLabel)}
        </button>
      </div>
    </Modal>
  )
}
