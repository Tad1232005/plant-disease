import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { demoUsers } from '../data/demoData.js'
import { authApi } from '../services/auth.js'
import { getApiError } from '../services/client.js'

const TOKEN_KEY = 'plantcare_admin_access_token'
const USER_KEY = 'plantcare_admin_user'
const DEMO_TOKEN = 'plantcare_admin_demo_session'
const AuthContext = createContext(null)

function getSavedAdmin() {
  try {
    const value = localStorage.getItem(USER_KEY)
    const savedUser = value ? JSON.parse(value) : null
    return savedUser?.role === 'admin' ? savedUser : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getSavedAdmin)
  const [initializing, setInitializing] = useState(true)

  function saveSession(nextUser, token) {
    setUser(nextUser)
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
    localStorage.setItem(TOKEN_KEY, token)
  }

  function logout() {
    setUser(null)
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem(TOKEN_KEY)
  }

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token || token === DEMO_TOKEN) {
      setInitializing(false)
      return
    }

    authApi.me()
      .then((profile) => {
        if (profile.role !== 'admin') throw new Error('Tài khoản không có quyền quản trị.')
        saveSession(profile, token)
      })
      .catch(logout)
      .finally(() => setInitializing(false))
  }, [])

  async function login(credentials) {
    const demoAdmin = demoUsers.admin
    if (credentials.username === demoAdmin.username && credentials.password === demoAdmin.password) {
      const { password: _, ...safeAdmin } = demoAdmin
      saveSession(safeAdmin, DEMO_TOKEN)
      return safeAdmin
    }

    try {
      const tokenData = await authApi.login(credentials)
      localStorage.setItem(TOKEN_KEY, tokenData.access_token)
      const profile = await authApi.me()
      if (profile.role !== 'admin') {
        logout()
        throw new Error('Tài khoản này không có quyền truy cập trang quản trị.')
      }
      saveSession(profile, tokenData.access_token)
      return profile
    } catch (error) {
      if (error.message?.includes('quyền truy cập')) throw error
      throw new Error(getApiError(error, 'Tên đăng nhập hoặc mật khẩu không đúng.'))
    }
  }

  const value = useMemo(() => ({
    user,
    initializing,
    isAuthenticated: Boolean(user),
    login,
    logout,
  }), [user, initializing])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth phải được dùng bên trong AuthProvider')
  return context
}
