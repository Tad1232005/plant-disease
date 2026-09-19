import { Eye, History } from 'lucide-react'
import DataTable from '../../components/common/DataTable.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { scanHistory } from '../../data/demoData.js'

export default function HistoryPage() {
  const columns = [
    { key: 'date', label: 'Thời gian', sortable: true },
    { key: 'farm', label: 'Khu vực', sortable: true, render: (value) => <span className="font-semibold text-slate-800">{value}</span> },
    { key: 'result', label: 'Kết quả', sortable: true },
    { key: 'confidence', label: 'Độ tin cậy', sortable: true, render: (value) => <span className="font-extrabold text-leaf-700">{value}%</span> },
    { key: 'severity', label: 'Mức độ', render: (value) => <StatusBadge value={value} /> },
  ]
  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow="Theo dõi theo thời gian" title="Lịch sử chẩn đoán" description="Xem lại các lần quét, kết quả dự đoán và mức độ tin cậy của mô hình." />
      <DataTable columns={columns} data={scanHistory} searchPlaceholder="Tìm theo khu vực hoặc kết quả..." actions={() => <button className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700" aria-label="Xem chi tiết"><Eye size={17} /></button>} emptyTitle="Chưa có lần chẩn đoán nào" emptyDescription="Hãy tải ảnh lá cây đầu tiên để bắt đầu lưu lịch sử." />
      <div className="mt-5 flex items-start gap-3 rounded-2xl border border-sky-100 bg-sky-50 p-4 text-sm text-sky-800"><History className="mt-0.5 shrink-0" size={19} /><p className="leading-6">Ở Tuần 2, bảng này dùng dữ liệu mẫu để hoàn thiện UI. Khi API lịch sử được bổ sung, chỉ cần thay nguồn <code className="rounded bg-white/70 px-1.5 py-0.5 text-xs">scanHistory</code> bằng response từ backend.</p></div>
    </div>
  )
}
