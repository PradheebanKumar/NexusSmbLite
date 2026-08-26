import { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [owner, setOwner] = useState(() => {
    const stored = localStorage.getItem('owner')
    return stored ? JSON.parse(stored) : null
  })
  const [loading, setLoading] = useState(false)

  const login = async (phone, password) => {
    const res = await api.post('/owners/login', { phone, password })
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('owner', JSON.stringify(res.data.owner))
    setOwner(res.data.owner)
    return res.data.owner
  }

  const register = async (data) => {
    const res = await api.post('/owners/register', data)
    localStorage.setItem('token', res.data.access_token)
    localStorage.setItem('owner', JSON.stringify(res.data.owner))
    setOwner(res.data.owner)
    return res.data.owner
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('owner')
    setOwner(null)
  }

  return (
    <AuthContext.Provider value={{ owner, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
