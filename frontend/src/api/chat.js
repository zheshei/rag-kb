// 问答流式接口：fetch + SSE 解析（可携带 Authorization 头）
export async function askStream(question, topK, conversationId, onEvent) {
  const token = localStorage.getItem('access_token')
  const resp = await fetch(`${import.meta.env.VITE_API_BASE || '/api/v1'}/chat/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify({ question, top_k: topK, conversation_id: conversationId || null })
  })

  if (!resp.ok) {
    let msg = `请求失败（${resp.status}）`
    try {
      const j = await resp.json()
      if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail)
    } catch (e) { /* 保留默认消息 */ }
    throw new Error(msg)
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buf = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })
    let idx
    while ((idx = buf.indexOf('\n\n')) >= 0) {
      const frame = buf.slice(0, idx)
      buf = buf.slice(idx + 2)
      let event = 'message'
      let data = ''
      for (const line of frame.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) data += line.slice(5).trim()
      }
      if (data) {
        try { onEvent(event, JSON.parse(data)) } catch (e) { /* 忽略无法解析的帧 */ }
      }
    }
  }
}
