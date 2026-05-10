<script setup lang="ts">
import { ref } from 'vue'
import Icon from '@/components/base/Icon.vue'
import { useDocumentStore } from '@/stores/document'

const store = useDocumentStore()
const dragover = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

function handleDrop(e: DragEvent) {
  e.preventDefault()
  dragover.value = false
  const files = e.dataTransfer?.files
  if (files?.length) upload(files[0])
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (target.files?.length) upload(target.files[0])
}

async function upload(file: File) {
  const ok = await store.upload(file)
  if (ok) {
    ;(window as any).$toast?.('上传成功，正在解析...', 'success')
  } else {
    ;(window as any).$toast?.('上传失败', 'error')
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'PENDING': return 'clock'
    case 'PROCESSING': return 'loader'
    case 'COMPLETED': return 'check'
    case 'FAILED': return 'alert-circle'
    default: return 'clock'
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'PENDING': return 'var(--color-warning)'
    case 'PROCESSING': return 'var(--accent)'
    case 'COMPLETED': return 'var(--color-success)'
    case 'FAILED': return 'var(--color-error)'
    default: return 'var(--text-secondary)'
  }
}
</script>

<template>
  <div class="documents-view">
    <div class="documents-header">
      <h1 class="page-title">文档管理</h1>
      <button class="primary-btn" @click="fileInput?.click()">
        <Icon name="upload-cloud" :size="16" />
        上传文档
      </button>
      <input
        ref="fileInput"
        type="file"
        accept=".json,.yaml,.yml"
        style="display: none"
        @change="handleFileSelect"
      />
    </div>

    <div class="dropzone-wrapper">
      <div
        class="dropzone"
        :class="{ dragover }"
        @dragover.prevent="dragover = true"
        @dragleave.prevent="dragover = false"
        @drop="handleDrop"
        @click="fileInput?.click()"
      >
        <Icon name="upload-cloud" :size="48" />
        <p class="dropzone-title">拖拽文件到此处，或点击上传</p>
        <p class="dropzone-hint">支持 .json、.yaml、.yml，最大 10MB</p>
      </div>
    </div>

    <div v-if="store.tasks.length > 0" class="task-list">
      <h2 class="section-title">上传记录</h2>
      <div
        v-for="task in store.tasks"
        :key="task.taskId"
        class="task-item"
      >
        <div class="task-icon">
          <Icon name="file-text" :size="24" />
        </div>
        <div class="task-info">
          <div class="task-name">{{ task.filename }}</div>
          <div class="task-meta">
            <span class="task-status" :style="{ color: getStatusColor(task.status) }">
              <Icon :name="getStatusIcon(task.status)" :size="12" />
              {{ task.status === 'PENDING' ? '等待中' : task.status === 'PROCESSING' ? '解析中...' : task.status === 'COMPLETED' ? '已完成' : '失败' }}
            </span>
            <span v-if="task.result" class="task-result">
              {{ task.result.total_endpoints }} 个端点，{{ task.result.total_chunks }} 个片段
            </span>
            <span v-if="task.error" class="task-error">{{ task.error }}</span>
          </div>
        </div>
        <button class="icon-btn" @click="store.removeTask(task.taskId)">
          <Icon name="trash-2" :size="16" />
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.documents-view {
  padding: 0 20px 40px;
  max-width: 800px;
  margin: 0 auto;
}

.documents-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 0 16px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.14;
  letter-spacing: 0.2px;
}

.primary-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s, transform 0.15s;
}

.primary-btn:hover {
  background: var(--accent-hover);
  transform: scale(1.02);
}

.dropzone-wrapper {
  margin-bottom: 32px;
}

.dropzone {
  height: 200px;
  background: var(--bg-primary);
  border: 2px dashed var(--border-medium);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.dropzone:hover,
.dropzone.dragover {
  border-color: var(--accent);
  background: rgba(0, 113, 227, 0.04);
}

.dropzone-title {
  font-size: 15px;
  color: var(--text-primary);
}

.dropzone-hint {
  font-size: 13px;
  color: var(--text-secondary);
}

.section-title {
  font-size: 17px;
  font-weight: 600;
  margin-bottom: 12px;
  letter-spacing: -0.37px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-card);
  border-radius: 8px;
  padding: 16px 20px;
  transition: box-shadow 0.2s;
}

.task-item:hover {
  box-shadow: var(--shadow-subtle);
}

.task-icon {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.task-info {
  flex: 1;
  min-width: 0;
}

.task-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
  font-size: 12px;
}

.task-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 500;
}

.task-result {
  color: var(--text-secondary);
}

.task-error {
  color: var(--color-error);
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
  flex-shrink: 0;
}

.icon-btn:hover {
  background: rgba(255, 59, 48, 0.1);
  color: var(--color-error);
}

@media (max-width: 640px) {
  .documents-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>
