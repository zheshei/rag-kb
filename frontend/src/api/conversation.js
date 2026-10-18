// 会话管理接口（M4）
const BASE = import.meta.env.VITE_API_BASE || '/api/v1'

function headers() {
  return { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
}

export async function listConversations(page = 1, pageSize = 100) {
  const resp = await fetch(`${BASE}/conversations?page=${page}&page_size=${pageSize}`, { headers: headers() })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '获取会话列表失败')
  return data
}

export async function createConversation(title) {
  const resp = await fetch(`${BASE}/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers() },
    body: JSON.stringify({ title })
  })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '创建会话失败')
  return data
}

export async function renameConversation(id, title) {
  const resp = await fetch(`${BASE}/conversations/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...headers() },
    body: JSON.stringify({ title })
  })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '重命名失败')
  return data
}

export async function deleteConversation(id) {
  const resp = await fetch(`${BASE}/conversations/${id}`, { method: 'DELETE', headers: headers() })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '删除会话失败')
  return data
}

export async function getMessages(convId) {
  const resp = await fetch(`${BASE}/conversations/${convId}/messages`, { headers: headers() })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '获取历史消息失败')
  return data
}
