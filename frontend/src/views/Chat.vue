<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import Icon from '@/components/base/Icon.vue'
import TypingIndicator from '@/components/base/TypingIndicator.vue'
import { useChatStore } from '@/stores/chat'
import { formatTime } from '@/utils/format'
import Prism from 'prismjs'
import 'prismjs/components/prism-python'
import 'prismjs/components/prism-javascript'
import 'prismjs/components/prism-typescript'
import 'prismjs/components/prism-java'
import 'prismjs/components/prism-bash'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-yaml'

const chatStore = useChatStore()
const inputText = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const messagesContainer = ref<HTMLElement | null>(null)
const copiedCode = ref<string | null>(null)

const quickPrompts = [
  '用户登录接口怎么调用？',
  '生成查询用户的 Python 代码',
  '这个接口需要什么参数？',
]

const showQuickPrompts = computed(() =>
  inputText.value === '' && chatStore.messages.length === 0
)

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 140) + 'px'
}

function scrollToBottom() {
  nextTick(() => {
    messagesContainer.value?.scrollTo({
      top: messagesContainer.value.scrollHeight,
      behavior: 'smooth',
    })
  })
}

watch(() => chatStore.messages.length, scrollToBottom)

async function send() {
  const text = inputText.value.trim()
  if (!text || chatStore.isStreaming) return
  inputText.value = ''
  if (textareaRef.value) textareaRef.value.style.height = 'auto'
  await chatStore.sendMessage(text)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function setPrompt(text: string) {
  inputText.value = text
  send()
}

function copyCode(content: string) {
  navigator.clipboard.writeText(content).then(() => {
    copiedCode.value = content
    setTimeout(() => copiedCode.value = null, 1000)
  })
}

function highlightCode(content: string, lang?: string) {
  const language = lang || 'text'
  const safeContent = content.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  if (Prism.languages[language]) {
    return Prism.highlight(content, Prism.languages[language], language)
  }
  return safeContent
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  // Simple markdown: bold, italic, links, inline code
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code style="background:rgba(0,0,0,0.06);padding:2px 4px;border-radius:4px;font-family:var(--font-mono);font-size:12px;">$1</code>')
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank" style="color:var(--text-link);text-decoration:none;">$1</a>')
    .replace(/\n/g, '<br>')
}

function clearChat() {
  if (chatStore.currentSessionId) {
    chatStore.deleteSession(chatStore.currentSessionId)
  }
}

onMounted(() => {
  chatStore.loadSessions()
  if (!chatStore.currentSessionId) {
    chatStore.createSession()
  }
})
</script>

<template>
  <div class="chat-view">
    <div class="chat-header">
      <span class="chat-title">{{ chatStore.currentSession?.title || '新对话' }}</span>
      <div class="chat-actions">
        <button class="icon-btn" @click="clearChat" title="清除会话">
          <Icon name="trash-2" :size="18" />
        </button>
      </div>
    </div>

    <div ref="messagesContainer" class="messages-area">
      <div class="messages-inner">
        <div
          v-for="(msg, index) in chatStore.messages"
          :key="index"
          class="message-group"
          :class="msg.role"
        >
          <!-- User message -->
          <template v-if="msg.role === 'user'">
            <div class="user-bubble-wrapper">
              <div class="bubble user-bubble">
                <div class="bubble-content">{{ msg.content }}</div>
              </div>
              <div class="msg-time" style="text-align:right;">
                {{ formatTime(msg.timestamp) }}
              </div>
            </div>
          </template>

          <!-- Assistant message -->
          <template v-else>
            <div class="assistant-row">
              <div class="assistant-avatar">
                <Icon name="terminal" :size="16" />
              </div>
              <div class="assistant-content">
                <div class="bubble assistant-bubble">
                  <div
                    v-if="msg.type === 'text' && msg.content"
                    class="bubble-content"
                    v-html="renderMarkdown(msg.content)"
                  />
                  <TypingIndicator
                    v-if="chatStore.isStreaming && index === chatStore.messages.length - 1 && msg.role === 'assistant' && !msg.content"
                  />
                </div>

                <!-- Code block -->
                <div v-if="msg.type === 'code' && msg.content" class="code-block">
                  <div class="code-header">
                    <span class="code-lang">{{ msg.lang || 'text' }}</span>
                    <button class="icon-btn" @click="copyCode(msg.content)">
                      <Icon
                        :name="copiedCode === msg.content ? 'check' : 'copy'"
                        :size="16"
                      />
                    </button>
                  </div>
                  <pre class="code-pre"><code class="language-code" v-html="highlightCode(msg.content, msg.lang)"></code></pre>
                </div>

                <div class="msg-time">{{ formatTime(msg.timestamp) }}</div>
              </div>
            </div>
          </template>
        </div>


        <!-- Error -->
        <div v-if="chatStore.error" class="error-banner">
          <Icon name="alert-circle" :size="16" />
          <span>{{ chatStore.error }}</span>
        </div>

        <!-- Empty state -->
        <div v-if="chatStore.messages.length === 0 && !chatStore.isStreaming" class="chat-empty">
          <div class="empty-avatar">
            <Icon name="terminal" :size="32" />
          </div>
          <h3 class="empty-title">有什么可以帮你的？</h3>
          <p class="empty-desc">上传 API 文档后，可以询问接口用法或生成调用代码</p>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-container">
        <div v-if="showQuickPrompts" class="quick-prompts">
          <button
            v-for="prompt in quickPrompts"
            :key="prompt"
            class="prompt-pill"
            @click="setPrompt(prompt)"
          >
            {{ prompt }}
          </button>
        </div>
        <div class="input-box-wrapper">
          <textarea
            ref="textareaRef"
            v-model="inputText"
            class="chat-input"
            placeholder="询问 API 文档或生成调用代码..."
            rows="1"
            @input="autoResize"
            @keydown="handleKeydown"
          />
          <button
            class="send-btn"
            :disabled="!inputText.trim() || chatStore.isStreaming"
            @click="send"
          >
            <Icon name="send" :size="18" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  height: 48px;
  position: sticky;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: rgba(245, 245, 247, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--divider);
  z-index: 10;
}

.chat-title {
  font-size: 15px;
  font-weight: 500;
  letter-spacing: -0.37px;
}

.chat-actions {
  display: flex;
  gap: 4px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s, color 0.15s;
}

.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 0 20px;
}

.messages-inner {
  max-width: 800px;
  margin: 0 auto;
  padding: 40px 0 120px;
}

.message-group {
  margin-bottom: 24px;
}

.user-bubble-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.bubble {
  max-width: 85%;
  padding: 12px 16px;
  word-break: break-word;
}

.user-bubble {
  background: var(--accent);
  color: #fff;
  border-radius: 16px 16px 4px 16px;
  font-size: 15px;
  line-height: 1.5;
}

.assistant-row {
  display: flex;
  gap: 12px;
}

.assistant-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--dark-surface-1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 4px;
}

.assistant-content {
  flex: 1;
  min-width: 0;
}

.assistant-bubble {
  background: var(--bg-card);
  color: var(--text-primary);
  border-radius: 16px 16px 16px 4px;
  box-shadow: var(--shadow-subtle);
  font-size: 15px;
  line-height: 1.6;
}

.bubble-content :deep(a:hover) {
  text-decoration: underline !important;
}

.msg-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  padding: 0 4px;
}

.code-block {
  margin-top: 12px;
  background: var(--dark-surface-1);
  border-radius: 12px;
  overflow: hidden;
}

.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  height: 40px;
  background: var(--dark-surface-2);
}

.code-lang {
  font-size: 12px;
  font-weight: 500;
  color: var(--accent-dark-bg);
  text-transform: lowercase;
}

.code-header .icon-btn {
  color: rgba(255, 255, 255, 0.6);
}

.code-header .icon-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.code-pre {
  padding: 16px 20px;
  overflow-x: auto;
  margin: 0;
}

.code-pre code {
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
  color: #f5f5f7;
}

.error-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 59, 48, 0.06);
  border-left: 3px solid var(--color-error);
  border-radius: 8px;
  color: var(--color-error);
  font-size: 15px;
  max-width: 800px;
  margin: 0 auto;
}

.input-area {
  position: fixed;
  bottom: 0;
  left: 260px;
  right: 0;
  padding: 12px 20px 20px;
  background: rgba(245, 245, 247, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-top: 1px solid var(--divider);
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.quick-prompts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.prompt-pill {
  padding: 6px 14px;
  border-radius: var(--radius-pill);
  background: rgba(0, 0, 0, 0.04);
  border: none;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}

.prompt-pill:hover {
  background: rgba(0, 0, 0, 0.08);
  color: var(--text-primary);
}

.input-box-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 8px 8px 8px 16px;
  box-shadow: var(--shadow-subtle);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-box-wrapper:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12);
}

.chat-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 15px;
  line-height: 1.5;
  color: var(--text-primary);
  resize: none;
  min-height: 24px;
  max-height: 140px;
  font-family: var(--font-body);
}

.chat-input::placeholder {
  color: var(--text-secondary);
}

.send-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: var(--accent);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background 0.15s, transform 0.15s;
}

.send-btn:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: scale(1.05);
}

.send-btn:disabled {
  background: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.24);
  cursor: not-allowed;
}

@media (max-width: 1024px) {
  .input-area { left: 0; }
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  text-align: center;
}

.empty-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--dark-surface-1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 21px;
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.37px;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: var(--text-secondary);
  max-width: 400px;
  line-height: 1.5;
}

@media (max-width: 640px) {
  .messages-inner { padding: 20px 0 120px; }
  .bubble { max-width: 90%; }
  .chat-header { padding: 0 12px; }
  .input-area { padding: 8px 12px 16px; }
}
</style>
