import api from './index'

export async function login(username, password) {
  // Note: api baseURL is already '/api', so use '/v1/auth/login' (not '/api/v1/...')
  const res = await api.post('/v1/auth/login', { username, password })
  const token = res.token || (res.data && res.data.token)
  if (token) {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(res.user || (res.data && res.data.user)))
  }
  return res
}

export function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export function getToken() {
  return localStorage.getItem('token')
}

export function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem('user'))
  } catch {
    return null
  }
}

export function isLoggedIn() {
  return !!getToken()
}
