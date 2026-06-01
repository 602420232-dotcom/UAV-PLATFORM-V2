import api from './index'

export async function login(username, password) {
  // Note: api baseURL is already '/api', so use '/v1/auth/login' (not '/api/v1/...')
  const res = await api.post('/v1/auth/login', { username, password })
  // 用户信息存储在 localStorage 中（非敏感信息）
  if (res.data && res.data.user) {
    localStorage.setItem('user', JSON.stringify(res.data.user))
  } else if (res.user) {
    localStorage.setItem('user', JSON.stringify(res.user))
  }
  return res
}

export async function logout() {
  await api.post('/v1/auth/logout')
  localStorage.removeItem('user')
}

export function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('user'))
  } catch {
    return null
  }
}

export async function isLoggedIn() {
  try {
    // Try to make an authenticated request to check
    await api.get('/api/user/profile')
    return true
  } catch {
    // If request fails, check if we have user info in localStorage as fallback
    return !!getCurrentUser()
  }
}
