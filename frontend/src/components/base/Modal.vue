<script setup lang="ts">
import Icon from './Icon.vue'

defineProps<{
  show: boolean
  title?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()
</script>

<template>
  <teleport to="body">
    <transition name="modal">
      <div v-if="show" class="modal-overlay" @click.self="emit('close')">
        <div class="modal-panel">
          <div class="modal-header">
            <h3 v-if="title" class="modal-title">{{ title }}</h3>
            <button class="icon-btn" @click="emit('close')">
              <Icon name="x" :size="16" />
            </button>
          </div>
          <div class="modal-body">
            <slot />
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: 20px;
}

.modal-panel {
  background: var(--bg-card);
  border-radius: var(--radius-xl);
  max-width: 480px;
  width: 100%;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 0;
}

.modal-title {
  font-size: 17px;
  font-weight: 600;
  letter-spacing: -0.37px;
}

.modal-body {
  padding: 20px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}

.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.modal-enter-active { transition: opacity 0.2s ease-out; }
.modal-leave-active { transition: opacity 0.15s ease-in; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-active .modal-panel { transition: transform 0.2s ease-out; }
.modal-leave-active .modal-panel { transition: transform 0.15s ease-in; }
.modal-enter-from .modal-panel { transform: scale(0.96); }
.modal-leave-to .modal-panel { transform: scale(0.96); }
</style>
