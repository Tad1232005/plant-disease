export const roleMeta = {
  user: { label: 'Nông dân' },
  technician: { label: 'Kỹ thuật viên' },
  manager: { label: 'Quản lý trang trại' },
  admin: { label: 'Quản trị viên' },
}

export function getRoleLabel(role) {
  return roleMeta[role]?.label || role
}
