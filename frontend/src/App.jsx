import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/auth/ProtectedRoute.jsx'
import RoleGuard from './components/auth/RoleGuard.jsx'
import AdminLayout from './layouts/AdminLayout.jsx'
import AppLayout from './layouts/AppLayout.jsx'
import FarmsPage from './pages/app/FarmsPage.jsx'
import DashboardPage from './pages/app/DashboardPage.jsx'
import DiseaseLibraryPage from './pages/app/DiseaseLibraryPage.jsx'
import HistoryPage from './pages/app/HistoryPage.jsx'
import ScanPage from './pages/app/ScanPage.jsx'
import AdminDashboardPage from './pages/admin/AdminDashboardPage.jsx'
import DiseaseManagementPage from './pages/admin/DiseaseManagementPage.jsx'
import PlaceholderPage from './pages/admin/PlaceholderPage.jsx'
import UsersPage from './pages/admin/UsersPage.jsx'
import LoginPage from './pages/auth/LoginPage.jsx'
import RegisterPage from './pages/auth/RegisterPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import LandingPage from './pages/public/LandingPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<RoleGuard allowedRoles={['user', 'technician', 'manager']} />}>
          <Route path="/app" element={<AppLayout />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="scan" element={<ScanPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="farms" element={<FarmsPage />} />
            <Route path="diseases" element={<DiseaseLibraryPage />} />
          </Route>
        </Route>

        <Route element={<RoleGuard allowedRoles={['admin']} />}>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminDashboardPage />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="farms" element={<FarmsPage adminMode />} />
            <Route path="diseases" element={<DiseaseManagementPage />} />
            <Route path="models" element={<PlaceholderPage title="Quản lý phiên bản mô hình" description="Khung quản lý model_versions, accuracy và model đang chạy production." />} />
            <Route path="system" element={<PlaceholderPage title="Theo dõi hệ thống" description="Khung thống kê lượt quét, tỷ lệ bệnh và người dùng hoạt động." />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
