import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { getHomeForRole } from '../../utils/roles.js'

export default function RoleGuard({ allowedRoles }) {
  const { user } = useAuth()
  if (!user || !allowedRoles.includes(user.role)) return <Navigate to={getHomeForRole(user?.role)} replace />
  return <Outlet />
}
