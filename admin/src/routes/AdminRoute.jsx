import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext.jsx'

export default function AdminRoute() {
  const { user, isAuthenticated, initializing } = useAuth()
  const location = useLocation()

  if (initializing) {
    return (
      <div className="grid min-h-screen place-items-center bg-leaf-50">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-leaf-200 border-t-leaf-600" />
          <p className="mt-4 text-sm font-medium text-leaf-800">Đang khởi tạo trang quản trị...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated || user?.role !== 'admin') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}
