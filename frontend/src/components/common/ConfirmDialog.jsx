import { AlertTriangle } from 'lucide-react'
import Modal from './Modal.jsx'

export default function ConfirmDialog({ open, onClose, onConfirm, title = 'Xác nhận xóa', message }) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <div className="flex gap-4 rounded-2xl bg-rose-50 p-4 text-sm text-rose-800">
        <AlertTriangle className="mt-0.5 shrink-0" size={20} />
        <p className="leading-6">{message}</p>
      </div>
      <div className="mt-6 flex justify-end gap-3">
        <button className="btn-secondary" onClick={onClose}>Hủy</button>
        <button className="inline-flex items-center rounded-xl bg-rose-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-rose-700" onClick={onConfirm}>
          Xóa dữ liệu
        </button>
      </div>
    </Modal>
  )
}
