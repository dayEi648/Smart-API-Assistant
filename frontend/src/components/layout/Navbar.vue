<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Icon from '@/components/base/Icon.vue'
import { useChatStore } from '@/stores/chat'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()

const emit = defineEmits<{
  (e: 'toggle-sidebar'): void
}>()

const navItems = [
  { path: '/', label: '聊天', icon: 'message-square' },
  { path: '/knowledge', label: '知识库', icon: 'database' },
  { path: '/documents', label: '文档', icon: 'file-text' },
]

const currentPath = computed(() => route.path)
const isChatPage = computed(() => route.path === '/' || route.path === '')

function newChat() {
  chatStore.createSession()
  router.push('/')
}

function goTo(path: string) {
  router.push(path)
}
</script>

<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <div class="nav-left">
        <button
          v-if="isChatPage"
          class="icon-btn menu-toggle"
          @click="emit('toggle-sidebar')"
          title="切换侧边栏"
        >
          <Icon name="menu" :size="18" />
        </button>
        <div class="nav-brand" @click="goTo('/')">
          <svg class="logo" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
          </svg>
          <span>Smart API Assistant</span>
        </div>
      </div>
      <div class="nav-links">
        <button
          v-for="item in navItems"
          :key="item.path"
          class="nav-link"
          :class="{ active: currentPath === item.path }"
          @click="goTo(item.path)"
        >
          {{ item.label }}
        </button>
      </div>
      <div class="nav-actions">
        <button class="nav-btn-upload" @click="goTo('/documents')">
          上传文档
        </button>
        <button class="icon-btn" @click="newChat" title="新建对话">
          <Icon name="plus" :size="18" />
        </button>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 48px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  z-index: var(--z-navbar);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.navbar-inner {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.menu-toggle {
  display: none;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
}

.logo {
  width: 16px;
  height: 16px;
  color: var(--accent);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 24px;
}

.nav-link {
  color: rgba(255, 255, 255, 0.8);
  font-size: 12px;
  font-weight: 400;
  text-decoration: none;
  cursor: pointer;
  padding: 4px 0;
  position: relative;
  transition: color 0.2s;
  background: none;
  border: none;
}

.nav-link:hover {
  color: #fff;
}

.nav-link.active {
  color: #fff;
}

.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: #fff;
  border-radius: 1px;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-btn-upload {
  height: 28px;
  padding: 0 12px;
  border-radius: 6px;
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 12px;
  font-weight: 400;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s;
}

.nav-btn-upload:hover {
  background: var(--accent-hover);
  transform: scale(1.02);
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.icon-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

@media (max-width: 1024px) {
  .menu-toggle { display: flex; }
}

@media (max-width: 640px) {
  .nav-links { display: none; }
}
</style>
