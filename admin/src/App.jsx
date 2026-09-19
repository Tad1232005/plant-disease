import { Route, Routes } from 'react-router-dom'
import AdminLayout from './components/AdminLayout.jsx'
import AdminDashboardPage from './pages/AdminDashboardPage.jsx'
import DiseaseManagementPage from './pages/DiseaseManagementPage.jsx'
import DiseaseProposalsPage from './pages/DiseaseProposalsPage.jsx'
import FarmsPage from './pages/FarmsPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import ModelVersionsPage from './pages/ModelVersionsPage.jsx'
import SystemStatsPage from './pages/SystemStatsPage.jsx'
import UsersPage from './pages/UsersPage.jsx'
import AdminRoute from './routes/AdminRoute.jsx'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<AdminRoute />}>
        <Route element={<AdminLayout />}>
          <Route index element={<AdminDashboardPage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="farms" element={<FarmsPage adminMode />} />
          <Route path="diseases" element={<DiseaseManagementPage />} />
          <Route path="proposals" element={<DiseaseProposalsPage />} />
          <Route path="models" element={<ModelVersionsPage />} />
          <Route path="system" element={<SystemStatsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
