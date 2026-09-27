import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'

export default function AdminRoute() {
  const { user, isAuthenticated, initializing } = useAuth()
  const location = useLocation()
  const { t } = useLanguage()

  if (initializing) {
    return (
      <div className="grid min-h-screen place-items-center bg-leaf-50">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-leaf-200 border-t-leaf-600" />
          <p className="mt-4 text-sm font-medium text-leaf-800">{t('common.init_loading')}</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated || user?.role !== 'admin') {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  return <Outlet />
}
