// 知识库相关接口
const BASE = import.meta.env.VITE_API_BASE || '/api/v1'

function headers() {
  return { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
}

export async function getStats() {
  const resp = await fetch(`${BASE}/kb/stats`, { headers: headers() })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '获取统计失败')
  return data
}

export async function listDocuments(page = 1, pageSize = 20) {
  const resp = await fetch(`${BASE}/kb/documents?page=${page}&page_size=${pageSize}`, { headers: headers() })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '获取文档列表失败')
  return data
}

export async function uploadDocument(file) {
  const form = new FormData()
  form.append('file', file)
  const resp = await fetch(`${BASE}/kb/documents/upload`, {
    method: 'POST',
    headers: headers(),
    body: form
  })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '上传失败')
  return data
}

export async function deleteDocument(id) {
  const resp = await fetch(`${BASE}/kb/documents/${id}`, { method: 'DELETE', headers: headers() })
  const data = await resp.json()
  if (!resp.ok) throw new Error(data.detail || '删除失败')
  return data
}
