import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { authApi } from '../api/auth.js'
import { getApiError } from '../api/client.js'
import { demoUsers } from '../data/demoData.js'

const TOKEN_KEY = 'plantcare_access_token'
const USER_KEY = 'plantcare_user'
const DEMO_TOKEN = 'plantcare_demo_session'

const AuthContext = createContext(null)

function getSavedUser() {
  try {
    const value = localStorage.getItem(USER_KEY)
    return value ? JSON.parse(value) : null
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getSavedUser)
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
      .then((profile) => saveSession(profile, token))
      .catch((error) => {
        if (error?.response?.status === 401) logout()
      })
      .finally(() => setInitializing(false))
  }, [])

  async function login(credentials) {
    const demoUser = Object.values(demoUsers).find(
      (item) => item.username === credentials.username && item.password === credentials.password,
    )

    if (demoUser) {
      const { password: _, ...safeUser } = demoUser
      saveSession(safeUser, DEMO_TOKEN)
      return safeUser
    }

    try {
      const tokenData = await authApi.login(credentials)
      localStorage.setItem(TOKEN_KEY, tokenData.access_token)
      const profile = await authApi.me()
      saveSession(profile, tokenData.access_token)
      return profile
    } catch (error) {
      throw new Error(getApiError(error, 'Tên đăng nhập hoặc mật khẩu không đúng.'))
    }
  }

  async function register(payload) {
    try {
      await authApi.register(payload)
      return login({ username: payload.username, password: payload.password })
    } catch (error) {
      throw new Error(getApiError(error, 'Không thể tạo tài khoản.'))
    }
  }

  const value = useMemo(() => ({
    user,
    initializing,
    isAuthenticated: Boolean(user),
    login,
    register,
    logout,
  }), [user, initializing])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth phải được dùng bên trong AuthProvider')
  return context
}
