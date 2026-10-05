import { History, Search, Shield, ShieldAlert, ShieldCheck, User } from 'lucide-react'
import { useState } from 'react'
import DataTable from '../components/common/DataTable.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'

const initialAuditLogs = [
  {
    id: 1,
    timestamp: '2026-10-04 22:30:15',
    actor: 'admin',
    action: 'model.activated',
    resource_type: 'model_version',
    resource_id: '1',
    details: 'Kích hoạt phiên bản MobileNetV2 Primary',
    status: 'success',
  },
  {
    id: 2,
    timestamp: '2026-10-04 21:15:00',
    actor: 'admin',
    action: 'proposal.approved',
    resource_type: 'disease_proposal',
    resource_id: '4',
    details: 'Duyệt đề xuất bệnh gỉ sắt ngô, chuyển vào disease_info',
    status: 'success',
  },
  {
    id: 3,
    timestamp: '2026-10-04 19:42:10',
    actor: 'manager_minh',
    action: 'farm.member_added',
    resource_type: 'farm',
    resource_id: '2',
    details: 'Gán người dùng ID 15 vào nông trại Ruộng A1',
    status: 'success',
  },
  {
    id: 4,
    timestamp: '2026-10-04 18:20:44',
    actor: 'farmer_nam',
    action: 'user.password_changed',
    resource_type: 'user',
    resource_id: '12',
    details: 'Đổi mật khẩu người dùng thành công',
    status: 'success',
  },
  {
    id: 5,
    timestamp: '2026-10-04 16:05:32',
    actor: 'technician_ha',
    action: 'proposal.submitted',
    resource_type: 'disease_proposal',
    resource_id: '5',
    details: 'Gửi đề xuất bổ sung bệnh thán thư ớt',
    status: 'pending',
  },
  {
    id: 6,
    timestamp: '2026-10-04 14:12:00',
    actor: 'admin',
    action: 'user.provisioned',
    resource_type: 'user',
    resource_id: '16',
    details: 'Khởi tạo tài khoản Kỹ thuật viên mới: technician_tuan',
    status: 'success',
  },
]

export default function AuditLogsPage() {
  const { language } = useLanguage()
  const isVi = language === 'vi'

  const [logs] = useState(initialAuditLogs)

  const columns = [
    {
      key: 'timestamp',
      label: isVi ? 'Thời gian' : 'Timestamp',
      sortable: true,
      render: (val) => <span className="font-mono text-xs text-slate-500">{val}</span>,
    },
    {
      key: 'actor',
      label: isVi ? 'Người thực hiện' : 'Actor',
      sortable: true,
      render: (val) => (
        <span className="inline-flex items-center gap-1.5 font-bold text-slate-700 dark:text-slate-200">
          <User size={14} className="text-leaf-600" /> @{val}
        </span>
      ),
    },
    {
      key: 'action',
      label: isVi ? 'Hành động' : 'Action',
      sortable: true,
      render: (val) => (
        <span className="rounded-lg bg-slate-100 dark:bg-slate-800 px-2.5 py-1 font-mono text-xs font-bold text-slate-800 dark:text-slate-200">
          {val}
        </span>
      ),
    },
    {
      key: 'resource_type',
      label: isVi ? 'Tài nguyên' : 'Resource',
      render: (val, row) => (
        <span className="text-xs text-slate-500">
          {val} #{row.resource_id}
        </span>
      ),
    },
    {
      key: 'details',
      label: isVi ? 'Chi tiết sự kiện' : 'Event Details',
      render: (val) => <span className="text-xs text-slate-600 dark:text-slate-300">{val}</span>,
    },
    {
      key: 'status',
      label: isVi ? 'Trạng thái' : 'Status',
      render: (val) => <StatusBadge value={val === 'success' ? 'active' : 'pending'} />,
    },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={isVi ? 'Bảo mật & Giám sát' : 'Security & Auditing'}
        title={isVi ? 'Nhật ký kiểm toán (Audit Logs)' : 'System Audit Logs'}
        description={
          isVi
            ? 'Theo dõi toàn bộ hoạt động nhạy cảm trong hệ thống: kích hoạt model, phê duyệt bệnh cây, thay đổi phân quyền.'
            : 'Track all sensitive activities in the system: model activation, proposal approvals, and permission changes.'
        }
      />

      <div className="mt-6">
        <DataTable
          columns={columns}
          data={logs}
          searchPlaceholder={isVi ? 'Tìm theo hành động hoặc người thực hiện...' : 'Search by action or actor...'}
        />
      </div>
    </div>
  )
}
