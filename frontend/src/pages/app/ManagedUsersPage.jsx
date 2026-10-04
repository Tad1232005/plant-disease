import { Link2Off, Plus, UsersRound } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { farmMembersApi, managedUsersApi } from '../../api/managedUsers.js'
import ConfirmDialog from '../../components/common/ConfirmDialog.jsx'
import CrudForm from '../../components/common/CrudForm.jsx'
import DataTable from '../../components/common/DataTable.jsx'
import Modal from '../../components/common/Modal.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatCard from '../../components/common/StatCard.jsx'
import { initialFarms, initialManagedUsers } from '../../data/demoData.js'
import { getRoleLabel } from '../../utils/roles.js'
import { loadCollection, saveCollection } from '../../utils/storage.js'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'

const STORAGE_KEY = 'plantcare_managed_users'

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.users || payload?.data || []
}

function normalizeUser(user, farms, language = 'vi') {
  const farmId = user.farm_id ?? user.farm?.id ?? user.farmId ?? ''
  const farm = farms.find((item) => String(item.id) === String(farmId))
  return {
    ...user,
    id: user.id ?? user.user_id,
    full_name: user.full_name || user.name || user.username,
    farmId,
    farmName: user.farm_name || user.farm?.name || farm?.name || (language === 'vi' ? 'Chưa phân công' : 'Unassigned'),
    status: user.status || 'active',
  }
}

export default function ManagedUsersPage() {
  const { language, t } = usePreferences()
  const copy = language === 'vi' ? {
    success: 'Đã tạo Managed User và gán vào trang trại thành công.', failure: 'Không thể tạo Managed User. Vui lòng kiểm tra API Manager.', removed: 'Đã gỡ Managed User khỏi trang trại.', removeFailure: 'Không thể gỡ thành viên khỏi trang trại.', person: 'Managed User', role: 'Vai trò', farm: 'Trang trại', unassigned: 'Chưa phân công', loading: 'Đang kết nối API quản lý Managed User...', api: 'Đã kết nối API /manager/users.', demo: 'Backend Tuần 4 chưa phản hồi nên trang đang dùng dữ liệu demo localStorage.', search: 'Tìm theo tên, email hoặc trang trại...', remove: 'Gỡ khỏi trang trại', empty: 'Chưa có Managed User', emptyText: 'Nhấn Thêm Managed User để tạo tài khoản và phân công vào trang trại.', removeTitle: 'Gỡ khỏi trang trại', removeQuestion: 'Gỡ', accountKept: 'Tài khoản vẫn được giữ lại.',
  } : {
    success: 'Managed User created and assigned successfully.', failure: 'Unable to create the Managed User. Check the Manager API.', removed: 'Managed User removed from the farm.', removeFailure: 'Unable to remove the member from the farm.', person: 'Managed User', role: 'Role', farm: 'Farm', unassigned: 'Unassigned', loading: 'Connecting to the Managed User API...', api: 'Connected to /manager/users.', demo: 'The Week 4 backend is unavailable, so local demo data is shown.', search: 'Search by name, email, or farm...', remove: 'Remove from farm', empty: 'No Managed Users yet', emptyText: 'Select Add Managed User to create and assign an account.', removeTitle: 'Remove from farm', removeQuestion: 'Remove', accountKept: 'The account will be kept.',
  }
  const [farms] = useState(() => loadCollection('plantcare_farms', initialFarms))
  const [users, setUsers] = useState(() => loadCollection(STORAGE_KEY, initialManagedUsers.filter((item) => item.role === 'user')))
  const [mode, setMode] = useState('loading')
  const [formOpen, setFormOpen] = useState(false)
  const [removing, setRemoving] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    managedUsersApi.list()
      .then((payload) => {
        if (!active) return
        const rows = unwrapList(payload).map((item) => normalizeUser(item, farms, language))
        setUsers(rows)
        setMode('api')
      })
      .catch(() => {
        if (active) setMode('demo')
      })
    return () => { active = false }
  }, [farms, language])

  useEffect(() => {
    if (mode !== 'loading') saveCollection(STORAGE_KEY, users)
  }, [mode, users])

  const fields = useMemo(() => [
    { name: 'full_name', label: t('register.fullName'), placeholder: language === 'vi' ? 'Nguyễn Văn Bình' : 'Alex Nguyen', fullWidth: true },
    { name: 'username', label: t('login.username'), placeholder: 'managed.user', minLength: 3 },
    { name: 'email', label: 'Email', type: 'email', placeholder: 'user@example.com' },
    { name: 'password', label: t('managed.initialPassword'), type: 'password', placeholder: t('register.passwordPlaceholder'), minLength: 6 },
    { name: 'farm_id', label: t('managed.farm'), type: 'select', options: farms.map((farm) => ({ value: String(farm.id), label: farm.name })) },
  ], [farms, language, t])

  async function createManagedUser(values) {
    setSaving(true)
    setMessage('')
    const farm = farms.find((item) => String(item.id) === String(values.farm_id))
    const payload = {
      full_name: values.full_name,
      username: values.username,
      email: values.email,
      password: values.password,
      role: 'user',
    }

    try {
      if (mode === 'api') {
        const created = await managedUsersApi.create(payload)
        const userId = created.id ?? created.user_id
        if (values.farm_id && userId) await farmMembersApi.add(values.farm_id, userId)
        setUsers((items) => [normalizeUser({ ...created, farm_id: values.farm_id }, farms, language), ...items])
      } else {
        setUsers((items) => [{
          ...payload,
          password: undefined,
          id: Date.now(),
          farmId: values.farm_id,
          farmName: farm?.name || copy.unassigned,
          status: 'active',
        }, ...items])
      }
      setFormOpen(false)
      setMessage(copy.success)
    } catch (error) {
      setMessage(error?.response?.data?.detail || copy.failure)
    } finally {
      setSaving(false)
    }
  }

  async function removeFromFarm() {
    if (!removing) return
    setSaving(true)
    setMessage('')
    try {
      if (mode === 'api' && removing.farmId) await farmMembersApi.remove(removing.farmId, removing.id)
      setUsers((items) => items.map((item) => item.id === removing.id ? { ...item, farmId: '', farmName: copy.unassigned } : item))
      setMessage(copy.removed)
      setRemoving(null)
    } catch (error) {
      setMessage(error?.response?.data?.detail || copy.removeFailure)
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { key: 'full_name', label: copy.person, sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800">{value}</p><p className="mt-0.5 text-xs text-slate-400">@{row.username}</p></div> },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'role', label: copy.role, sortable: true, render: (value) => <span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">{language === 'vi' ? getRoleLabel(value) : 'User'}</span> },
    { key: 'farmName', label: copy.farm, sortable: true, render: (value) => <span className={value === copy.unassigned ? 'text-amber-600' : 'font-semibold text-leaf-700'}>{value}</span> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={t('managed.eyebrow')}
        title={t('managed.title')}
        description={t('managed.description')}
        action={<button className="btn-primary" onClick={() => { setMessage(''); setFormOpen(true) }}><Plus size={18} />{t('managed.add')}</button>}
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard icon={UsersRound} label={t('managed.total')} value={String(users.length).padStart(2, '0')} />
        <StatCard icon={UsersRound} label={t('managed.assigned')} value={users.filter((item) => item.farmId).length} tone="blue" />
        <StatCard icon={UsersRound} label={t('managed.unassigned')} value={users.filter((item) => !item.farmId).length} tone="amber" />
      </div>

      <div className={`mb-5 rounded-2xl border p-4 text-sm ${mode === 'api' ? 'border-emerald-100 bg-emerald-50 text-emerald-800' : 'border-amber-100 bg-amber-50 text-amber-800'}`}>
        {mode === 'loading' ? copy.loading : mode === 'api' ? copy.api : copy.demo}
      </div>
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">{message}</p>}

      <DataTable
        columns={columns}
        data={users}
        searchPlaceholder={copy.search}
        actions={(row) => <button disabled={!row.farmId} onClick={() => setRemoving(row)} className="rounded-lg p-2 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-30" aria-label={copy.remove}><Link2Off size={17} /></button>}
        emptyTitle={copy.empty}
        emptyDescription={copy.emptyText}
      />

      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={t('managed.createTitle')} description={t('managed.createText')} size="xl">
        <CrudForm fields={fields} defaultValues={{ farm_id: farms[0]?.id ? String(farms[0].id) : '' }} onSubmit={createManagedUser} onCancel={() => setFormOpen(false)} submitLabel={t('managed.create')} loading={saving} />
      </Modal>
      <ConfirmDialog open={Boolean(removing)} onClose={() => setRemoving(null)} onConfirm={removeFromFarm} title={copy.removeTitle} message={removing ? `${copy.removeQuestion} “${removing.full_name}” — “${removing.farmName}”? ${copy.accountKept}` : ''} />
    </div>
  )
}
