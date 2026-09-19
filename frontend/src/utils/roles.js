export const roleMeta = {
  user: { label: 'Nông dân', shortLabel: 'Nông dân', home: '/app/dashboard' },
  technician: { label: 'Kỹ thuật viên', shortLabel: 'Kỹ thuật viên', home: '/app/dashboard' },
  manager: { label: 'Quản lý trang trại', shortLabel: 'Quản lý', home: '/app/dashboard' },
  admin: { label: 'Quản trị viên', shortLabel: 'Admin', home: '/admin' },
}

export function getRoleLabel(role) {
  return roleMeta[role]?.label || role
}

export function getHomeForRole(role) {
  return roleMeta[role]?.home || '/app/dashboard'
}
