export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'code'
  lang?: string
  timestamp?: string
}

export interface Session {
  id: string
  title: string
  preview: string
  updatedAt: string
}

export interface ApiEndpoint {
  id?: string
  path: string
  method: string
  summary: string
  tags: string[]
  score?: number
  content?: string
}

export interface UploadTask {
  taskId: string
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
  filename: string
  createdAt: string
  updatedAt: string
  result?: { total_endpoints: number; total_chunks: number; doc_id: string }
  error?: string
}

export interface SSEMessageEvent {
  type: 'text' | 'code'
  content: string
  lang?: string
}

export interface SSEDoneEvent {
  finish_reason: string
}

export interface SSEErrorEvent {
  code: number
  message: string
}
