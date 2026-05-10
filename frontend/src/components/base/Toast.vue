<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Icon from './Icon.vue'

interface ToastItem {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
}

const toasts = ref<ToastItem[]>([])
let idCounter = 0

function show(message: string, type: ToastItem['type'] = 'info') {
  const id = ++idCounter
  toasts.value.push({ id, message, type })
  setTimeout(() => remove(id), 3000)
}

function remove(id: number) {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

onMounted(() => {
  ;(window as any).$toast = show
})

defineExpose({ show })
</script>

<template>
  <teleport to="body">
    <div class="toast-container">
      <transition-group name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-item"
          :class="toast.type"
        >
          <Icon
            :name="toast.type === 'success' ? 'check' : toast.type === 'error' ? 'alert-circle' : 'info'"
            :size="16"
          />
          <span>{{ toast.message }}</span>
        </div>
      </transition-group>
    </div>
  </teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--z-toast);
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  color: #fff;
  font-size: 14px;
  white-space: nowrap;
}

.toast-item.success { color: var(--color-success); }
.toast-item.error { color: var(--color-error); }

.toast-enter-active { transition: all 0.3s ease-out; }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
