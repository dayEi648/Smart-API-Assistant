import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UploadTask } from '@/types'
import { uploadDocument, getTaskStatus } from '@/services/api'

export const useDocumentStore = defineStore('document', () => {
  const tasks = ref<UploadTask[]>([])
  const uploading = ref(false)

  async function upload(file: File) {
    uploading.value = true
    try {
      const res = await uploadDocument(file)
      if (res.code === 0) {
        const task: UploadTask = {
          taskId: res.data.task_id,
          status: res.data.status,
          filename: file.name,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }
        tasks.value.unshift(task)
        pollTask(task.taskId)
        return true
      }
      return false
    } finally {
      uploading.value = false
    }
  }

  async function pollTask(taskId: string) {
    const interval = setInterval(async () => {
      try {
        const res = await getTaskStatus(taskId)
        if (res.code === 0) {
          const task = tasks.value.find(t => t.taskId === taskId)
          if (task) {
            task.status = res.data.status
            task.updatedAt = res.data.updated_at
            task.result = res.data.result
            task.error = res.data.error
            if (task.status === 'COMPLETED' || task.status === 'FAILED') {
              clearInterval(interval)
            }
          }
        }
      } catch {
        clearInterval(interval)
      }
    }, 2000)
  }

  function removeTask(taskId: string) {
    tasks.value = tasks.value.filter(t => t.taskId !== taskId)
  }

  return {
    tasks,
    uploading,
    upload,
    removeTask,
  }
})
