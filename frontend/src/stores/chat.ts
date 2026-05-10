import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ChatMessage, Session } from '@/types'
import { generateUUID } from '@/utils/uuid'
import { streamChat, getChatHistory, clearSession } from '@/services/api'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string>('')
  const messages = ref<ChatMessage[]>([])
  const isStreaming = ref(false)
  const error = ref('')

  const currentSession = computed(() =>
    sessions.value.find(s => s.id === currentSessionId.value)
  )

  function createSession() {
    const id = generateUUID()
    const session: Session = {
      id,
      title: '新对话',
      preview: '',
      updatedAt: new Date().toISOString(),
    }
    sessions.value.unshift(session)
    currentSessionId.value = id
    messages.value = []
    error.value = ''
    saveSessions()
    return id
  }

  function selectSession(id: string) {
    currentSessionId.value = id
    messages.value = []
    loadHistory(id)
  }

  async function loadHistory(sessionId: string) {
    try {
      const res = await getChatHistory(sessionId)
      if (res.code === 0 && res.data?.messages) {
        messages.value = res.data.messages.map((m: any) => ({
          role: m.role,
          content: m.content,
          type: m.type || 'text',
          timestamp: m.timestamp,
        }))
      }
    } catch (e) {
      console.error('Failed to load history', e)
    }
  }

  async function sendMessage(content: string) {
    if (!currentSessionId.value) {
      createSession()
    }
    const sid = currentSessionId.value

    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    })

    const assistantMsg: ChatMessage = {
      role: 'assistant',
      content: '',
      type: 'text',
      timestamp: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)

    isStreaming.value = true
    error.value = ''

    // Update session preview
    const session = sessions.value.find(s => s.id === sid)
    if (session) {
      session.preview = content
      session.updatedAt = new Date().toISOString()
      if (session.title === '新对话') {
        session.title = content.slice(0, 20)
      }
      saveSessions()
    }

    try {
      for await (const chunk of streamChat(sid, content)) {
        if (chunk.event === 'message') {
          try {
            const data = JSON.parse(chunk.data)
            if (data.type === 'code') {
              assistantMsg.type = 'code'
              assistantMsg.lang = data.lang || 'text'
            }
            assistantMsg.content += data.content || ''
          } catch {
            assistantMsg.content += chunk.data
          }
        } else if (chunk.event === 'error') {
          try {
            const data = JSON.parse(chunk.data)
            error.value = data.message || '请求出错'
          } catch {
            error.value = chunk.data
          }
        } else if (chunk.event === 'done') {
          break
        }
      }
    } catch (e: any) {
      error.value = e.message || '连接失败'
    } finally {
      isStreaming.value = false
    }
  }

  async function deleteSession(id: string) {
    try {
      await clearSession(id)
    } catch {}
    sessions.value = sessions.value.filter(s => s.id !== id)
    if (currentSessionId.value === id) {
      currentSessionId.value = sessions.value[0]?.id || ''
      messages.value = []
      if (currentSessionId.value) {
        await loadHistory(currentSessionId.value)
      }
    }
    saveSessions()
  }

  function saveSessions() {
    localStorage.setItem('sma_sessions', JSON.stringify(sessions.value))
    localStorage.setItem('sma_current_session', currentSessionId.value)
  }

  function loadSessions() {
    const raw = localStorage.getItem('sma_sessions')
    if (raw) {
      try {
        sessions.value = JSON.parse(raw)
        const savedCurrent = localStorage.getItem('sma_current_session')
        if (savedCurrent && sessions.value.some(s => s.id === savedCurrent)) {
          currentSessionId.value = savedCurrent
        } else if (sessions.value.length > 0) {
          currentSessionId.value = sessions.value[0].id
        }
      } catch {}
    }
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isStreaming,
    error,
    currentSession,
    createSession,
    selectSession,
    loadHistory,
    sendMessage,
    deleteSession,
    loadSessions,
  }
})
