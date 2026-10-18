// 认证相关接口
const BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export async function login(username, password) {
  const resp = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || `登录失败（${resp.status}）`)
  return data
}

export async function register(username, password) {
  const resp = await fetch(`${BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || `注册失败（${resp.status}）`)
  return data
}

export async function getMe(token) {
  const resp = await fetch(`${BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` }
  })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '获取用户信息失败')
  return data
}

export async function changePassword(token, oldPassword, newPassword) {
  const resp = await fetch(`${BASE}/auth/change-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
  })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '修改密码失败')
  return data
}
