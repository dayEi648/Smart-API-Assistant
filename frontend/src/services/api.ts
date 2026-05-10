import type { ChatMessage, ApiEndpoint, UploadTask } from '@/types'

const BASE = ''

export async function uploadDocument(file: File) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/v1/documents/upload`, {
    method: 'POST',
    body: form,
  })
  return res.json()
}

export async function getTaskStatus(taskId: string) {
  const res = await fetch(`${BASE}/api/v1/documents/tasks/${taskId}`)
  return res.json()
}

export async function getChatHistory(sessionId: string, limit = 20) {
  const res = await fetch(`${BASE}/api/v1/chat/sessions/${sessionId}/history?limit=${limit}`)
  return res.json()
}

export async function clearSession(sessionId: string) {
  const res = await fetch(`${BASE}/api/v1/chat/sessions/${sessionId}`, { method: 'DELETE' })
  return res.json()
}

export async function getApiOverview(limit = 50, offset = 0) {
  const res = await fetch(`${BASE}/api/v1/knowledge/apis?limit=${limit}&offset=${offset}`)
  return res.json()
}

export async function searchApiDocs(q: string, topK = 5) {
  const res = await fetch(`${BASE}/api/v1/knowledge/search?q=${encodeURIComponent(q)}&top_k=${topK}`)
  return res.json()
}

export async function deleteApiEndpoint(apiId: string) {
  const res = await fetch(`${BASE}/api/v1/knowledge/apis/${encodeURIComponent(apiId)}`, {
    method: 'DELETE',
  })
  return res.json()
}

export function createChatStream(sessionId: string, message: string) {
  return new EventSource(`${BASE}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Accept': 'text/event-stream',
      'Content-Type': 'application/json',
    } as any,
    body: JSON.stringify({ session_id: sessionId, message }),
  } as any)
}

// Manual fetch with SSE-like streaming for browsers that don't support POST EventSource
export async function* streamChat(sessionId: string, message: string) {
  const response = await fetch(`${BASE}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Accept': 'text/event-stream',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId, message }),
  })

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      const match = line.match(/^event: (\w+)\ndata: (.+)$/m)
      if (match) {
        yield { event: match[1], data: match[2] }
      }
    }
  }
}
