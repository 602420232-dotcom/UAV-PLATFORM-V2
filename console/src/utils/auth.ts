const TOKEN_KEY = 'uav_platform_token'
const USER_INFO_KEY = 'uav_platform_user_info'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export interface StoredUserInfo {
  id: number
  username: string
  role: string
  tenantId?: number
  tenantName?: string
}

export function getUserInfo(): StoredUserInfo | null {
  const raw = localStorage.getItem(USER_INFO_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as StoredUserInfo
  } catch {
    return null
  }
}

export function setUserInfo(info: StoredUserInfo): void {
  localStorage.setItem(USER_INFO_KEY, JSON.stringify(info))
}

export function removeUserInfo(): void {
  localStorage.removeItem(USER_INFO_KEY)
}
