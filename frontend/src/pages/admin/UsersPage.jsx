import { LockKeyhole, UserCog } from 'lucide-react'
import DataTable from '../../components/common/DataTable.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { demoUsers } from '../../data/demoData.js'
import { getRoleLabel } from '../../utils/roles.js'

export default function UsersPage() {
  const rows = Object.values(demoUsers).map(({ password: _, ...user }, index) => ({ ...user, status: index === 3 ? 'active' : 'active' }))
  const columns = [
    { key: 'full_name', label: 'Người dùng', sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800">{value}</p><p className="mt-0.5 text-xs text-slate-400">@{row.username}</p></div> },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'role', label: 'Vai trò', sortable: true, render: (value) => <span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">{getRoleLabel(value)}</span> },
    { key: 'status', label: 'Trạng thái', render: (value) => <StatusBadge value={value} /> },
  ]
  return <div className="mx-auto max-w-7xl"><PageHeader eyebrow="Khung chờ Tuần 6" title="Quản lý người dùng" description="Bảng dữ liệu đã sẵn sàng để nối API danh sách, khóa/mở tài khoản và đổi role." /><DataTable columns={columns} data={rows} searchPlaceholder="Tìm tên, email hoặc vai trò..." actions={() => <button className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700" aria-label="Quản lý quyền"><UserCog size={17} /></button>} /><div className="mt-5 flex gap-3 rounded-2xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-800"><LockKeyhole className="mt-0.5 shrink-0" size={18} /><p>Tuần 2 chỉ dựng khung trang này. Các nút thay đổi tài khoản sẽ nối API quản trị ở Tuần 6.</p></div></div>
}
