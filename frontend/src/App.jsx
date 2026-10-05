import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/auth/ProtectedRoute.jsx'
import RoleGuard from './components/auth/RoleGuard.jsx'
import AppLayout from './layouts/AppLayout.jsx'
import FarmsPage from './pages/app/FarmsPage.jsx'
import DashboardPage from './pages/app/DashboardPage.jsx'
import DiseaseLibraryPage from './pages/app/DiseaseLibraryPage.jsx'
import DiseaseProposalsPage from './pages/app/DiseaseProposalsPage.jsx'
import FarmDashboardPage from './pages/app/FarmDashboardPage.jsx'
import HistoryPage from './pages/app/HistoryPage.jsx'
import ManagedUsersPage from './pages/app/ManagedUsersPage.jsx'
import ScanPage from './pages/app/ScanPage.jsx'
import ProfilePage from './pages/app/ProfilePage.jsx'
import ScanDetailPage from './pages/app/ScanDetailPage.jsx'
import LoginPage from './pages/auth/LoginPage.jsx'
import RegisterPage from './pages/auth/RegisterPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import LandingPage from './pages/public/LandingPage.jsx'
import GuestScanPage from './pages/public/GuestScanPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/guest/scan" element={<GuestScanPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<RoleGuard allowedRoles={['user', 'technician', 'manager']} />}>
          <Route path="/app" element={<AppLayout />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="scan" element={<ScanPage />} />
            <Route path="scans/:id" element={<ScanDetailPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="diseases" element={<DiseaseLibraryPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route element={<RoleGuard allowedRoles={['manager']} />}>
              <Route path="farms" element={<FarmsPage />} />
              <Route path="managed-users" element={<ManagedUsersPage />} />
              <Route path="farm-dashboard" element={<FarmDashboardPage />} />
            </Route>
            <Route element={<RoleGuard allowedRoles={['technician']} />}>
              <Route path="proposals" element={<DiseaseProposalsPage />} />
            </Route>
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
