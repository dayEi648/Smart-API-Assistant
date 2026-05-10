import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ApiEndpoint } from '@/types'
import { getApiOverview, searchApiDocs, deleteApiEndpoint } from '@/services/api'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const endpoints = ref<ApiEndpoint[]>([])
  const searchResults = ref<ApiEndpoint[]>([])
  const total = ref(0)
  const loading = ref(false)
  const query = ref('')

  async function loadEndpoints(limit = 50, offset = 0) {
    loading.value = true
    try {
      const res = await getApiOverview(limit, offset)
      if (res.code === 0) {
        endpoints.value = res.data.items || []
        total.value = res.data.total || 0
      }
    } finally {
      loading.value = false
    }
  }

  async function search(q: string) {
    if (!q.trim()) return
    query.value = q
    loading.value = true
    try {
      const res = await searchApiDocs(q)
      if (res.code === 0) {
        searchResults.value = (res.data.results || []).map((r: any) => ({
          id: r.id,
          path: r.path,
          method: r.method,
          summary: r.summary,
          tags: r.tags || [],
          score: r.score,
          content: r.content,
        }))
      }
    } finally {
      loading.value = false
    }
  }

  function clearSearch() {
    searchResults.value = []
    query.value = ''
  }

  async function removeEndpoint(apiId: string) {
    if (!apiId) return
    const res = await deleteApiEndpoint(apiId)
    if (res.code === 0) {
      endpoints.value = endpoints.value.filter(e => e.id !== apiId)
      searchResults.value = searchResults.value.filter(e => e.id !== apiId)
      total.value = Math.max(0, total.value - 1)
    }
    return res
  }

  return {
    endpoints,
    searchResults,
    total,
    loading,
    query,
    loadEndpoints,
    search,
    clearSearch,
    removeEndpoint,
  }
})
