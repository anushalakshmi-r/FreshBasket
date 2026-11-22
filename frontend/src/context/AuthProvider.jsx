import { AuthContext } from './authContext'
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  fetchWithAccessToken,
  getCsrfToken,
  hasRefreshCookie,
  loginCustomer,
  logoutCustomer,
  readAuthResponse,
  refreshCustomerSession,
  registerCustomer,
} from '../services/auth'

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState('')
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [authError, setAuthError] = useState('')
  const refreshInFlight = useRef(null)
  const accessTokenRef = useRef('')

  const acceptSession = useCallback((session) => {
    accessTokenRef.current = session.access
    setAccessToken(session.access)
    setUser(session.user)
    setAuthError('')
  }, [])

  const refreshSession = useCallback(() => {
    if (!refreshInFlight.current) {
      refreshInFlight.current = refreshCustomerSession()
        .then((session) => {
          acceptSession(session)
          return session.access
        })
        .finally(() => {
          refreshInFlight.current = null
        })
    }
    return refreshInFlight.current
  }, [acceptSession])

  useEffect(() => {
    let active = true

    async function restoreSession() {
      try {
        await getCsrfToken()
        if (hasRefreshCookie()) await refreshSession()
      } catch (error) {
        if (active && error.status !== 401) setAuthError(error.message)
      } finally {
        if (active) setIsLoading(false)
      }
    }

    restoreSession()
    return () => {
      active = false
    }
  }, [refreshSession])

  const login = useCallback(async (credentials) => {
    const session = await loginCustomer(credentials)
    acceptSession(session)
    return session.user
  }, [acceptSession])

  const register = useCallback(async (details) => {
    const session = await registerCustomer(details)
    acceptSession(session)
    return session.user
  }, [acceptSession])

  const logout = useCallback(async () => {
    try {
      await logoutCustomer()
    } finally {
      accessTokenRef.current = ''
      setAccessToken('')
      setUser(null)
      setAuthError('')
    }
  }, [])

  const authenticatedFetch = useCallback(async (path, options = {}) => {
    const currentToken = accessTokenRef.current
    const response = await fetchWithAccessToken(path, currentToken, options)
    if (response.status !== 401 || !currentToken) return response

    let refreshedAccessToken
    try {
      refreshedAccessToken = await refreshSession()
    } catch {
      accessTokenRef.current = ''
      setAccessToken('')
      setUser(null)
      return response
    }

    return fetchWithAccessToken(path, refreshedAccessToken, options)
  }, [refreshSession])

  const updateProfile = useCallback(async (profile) => {
    const response = await authenticatedFetch('/api/accounts/profile/', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    })
    const updatedProfile = await readAuthResponse(response)
    setUser(updatedProfile)
    return updatedProfile
  }, [authenticatedFetch])

  const value = {
    user,
    isLoading,
    authError,
    isAuthenticated: Boolean(user && accessToken),
    login,
    register,
    logout,
    authenticatedFetch,
    updateProfile,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
