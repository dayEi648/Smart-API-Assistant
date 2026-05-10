<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/base/Icon.vue'
import { useChatStore } from '@/stores/chat'
import { truncate } from '@/utils/format'

const router = useRouter()
const chatStore = useChatStore()

const sortedSessions = computed(() =>
  [...chatStore.sessions].sort((a, b) =>
    new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  )
)

function select(id: string) {
  chatStore.selectSession(id)
}

function remove(id: string, e: Event) {
  e.stopPropagation()
  chatStore.deleteSession(id)
}

function newSession() {
  chatStore.createSession()
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <span class="sidebar-title">会话历史</span>
    </div>
    <button class="new-session-btn" @click="newSession">
      <Icon name="plus" :size="16" />
      <span>新建会话</span>
    </button>
    <div class="session-list">
      <div
        v-for="session in sortedSessions"
        :key="session.id"
        class="session-item"
        :class="{ active: session.id === chatStore.currentSessionId }"
        @click="select(session.id)"
      >
        <div class="session-info">
          <div class="session-title">{{ truncate(session.title, 24) }}</div>
          <div class="session-preview">{{ truncate(session.preview, 30) }}</div>
        </div>
        <button class="session-delete" @click="remove(session.id, $event)">
          <Icon name="trash-2" :size="14" />
        </button>
      </div>
      <div v-if="sortedSessions.length === 0" class="empty-sessions">
        <Icon name="message-square" :size="48" />
        <span>暂无会话</span>
      </div>
    </div>
    <div class="sidebar-footer">
      <div class="footer-divider" />
      <button class="footer-link" @click="router.push('/documents')">
        <Icon name="upload-cloud" :size="14" />
        <span>上传文档</span>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 260px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--divider);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: fixed;
  left: 0;
  top: 48px;
  bottom: 0;
  z-index: var(--z-sidebar);
}

.sidebar-header {
  padding: 16px 20px 8px;
}

.sidebar-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.new-session-btn {
  margin: 0 16px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-medium);
  background: transparent;
  color: var(--text-link);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}

.new-session-btn:hover {
  background: var(--bg-hover);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  margin-bottom: 2px;
  cursor: pointer;
  position: relative;
  transition: background 0.15s;
}

.session-item:hover {
  background: var(--bg-hover);
}

.session-item:hover .session-delete {
  opacity: 1;
}

.session-item.active {
  background: var(--bg-active);
}

.session-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
}

.session-info {
  flex: 1;
  min-width: 0;
  margin-left: 4px;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-preview {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.session-delete {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s, background 0.15s;
}

.session-delete:hover {
  background: rgba(255, 59, 48, 0.1);
  color: var(--color-error);
}

.empty-sessions {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px 20px;
  color: rgba(0, 0, 0, 0.12);
  gap: 8px;
}

.empty-sessions span {
  font-size: 12px;
  color: var(--text-secondary);
}

.sidebar-footer {
  padding: 8px 16px 16px;
}

.footer-divider {
  height: 1px;
  background: var(--divider);
  margin-bottom: 8px;
}

.footer-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border-medium);
  background: transparent;
  color: var(--text-link);
  font-size: 13px;
  cursor: pointer;
  width: 100%;
  transition: background 0.15s;
}

.footer-link:hover {
  background: var(--bg-hover);
}

@media (max-width: 1024px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  .sidebar.open {
    transform: translateX(0);
  }
}
</style>
