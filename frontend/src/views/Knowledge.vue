<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import Icon from '@/components/base/Icon.vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import type { ApiEndpoint } from '@/types'

const router = useRouter()
const store = useKnowledgeStore()
const searchInput = ref('')

const methodColors: Record<string, { bg: string; text: string }> = {
  GET: { bg: 'rgba(52,199,89,0.12)', text: '#34c759' },
  POST: { bg: 'rgba(0,113,227,0.12)', text: '#0071e3' },
  PUT: { bg: 'rgba(255,149,0,0.12)', text: '#ff9500' },
  DELETE: { bg: 'rgba(255,59,48,0.12)', text: '#ff3b30' },
  PATCH: { bg: 'rgba(175,82,222,0.12)', text: '#af52de' },
}

const displayItems = computed(() =>
  store.query ? store.searchResults : store.endpoints
)

const isSearching = computed(() => !!store.query)

function doSearch() {
  if (!searchInput.value.trim()) {
    store.clearSearch()
    return
  }
  store.search(searchInput.value)
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') doSearch()
}

function getMethodStyle(method: string) {
  return methodColors[method.toUpperCase()] || { bg: 'rgba(0,0,0,0.06)', text: 'var(--text-secondary)' }
}

function confirmDelete(item: ApiEndpoint) {
  if (!item.id) return
  if (confirm(`确定要删除接口 ${item.method} ${item.path} 吗？`)) {
    store.removeEndpoint(item.id)
  }
}

onMounted(() => {
  store.loadEndpoints()
})
</script>

<template>
  <div class="knowledge-view">
    <div class="knowledge-header">
      <h1 class="page-title">知识库</h1>
      <span v-if="!isSearching" class="endpoint-count">{{ store.total }} 个端点</span>
    </div>

    <div class="search-section">
      <div class="search-box">
        <Icon name="search" :size="20" />
        <input
          v-model="searchInput"
          class="search-input"
          placeholder="搜索 API 端点..."
          @keydown="handleKeydown"
        />
        <button class="search-btn" @click="doSearch">
          <Icon v-if="store.loading" name="loader" :size="16" />
          <span v-else>搜索</span>
        </button>
      </div>
      <p v-if="isSearching" class="search-result-hint">
        找到 {{ store.searchResults.length }} 个与 "{{ store.query }}" 相关的结果
        <button class="clear-search" @click="store.clearSearch(); searchInput = ''">清除</button>
      </p>
    </div>

    <div v-if="store.loading && displayItems.length === 0" class="skeleton-grid">
      <div v-for="i in 6" :key="i" class="skeleton-card" />
    </div>

    <div v-else-if="displayItems.length === 0" class="empty-state">
      <Icon name="upload-cloud" :size="64" />
      <h3>知识库为空</h3>
      <p>上传 API 文档以开始浏览和检索</p>
      <button class="primary-btn" @click="router.push('/documents')">
        上传文档
      </button>
    </div>

    <div v-else class="api-grid">
      <div
        v-for="item in displayItems"
        :key="item.path + item.method"
        class="api-card"
      >
        <div class="api-card-header">
          <span
            class="method-badge"
            :style="{ background: getMethodStyle(item.method).bg, color: getMethodStyle(item.method).text }"
          >
            {{ item.method }}
          </span>
          <span class="api-path">{{ item.path }}</span>
          <span v-if="item.score !== undefined" class="similarity-score">
            {{ (item.score * 100).toFixed(0) }}%
          </span>
          <button
            v-if="item.id"
            class="delete-btn"
            title="删除此接口"
            @click.stop="confirmDelete(item)"
          >
            <Icon name="trash-2" :size="14" />
          </button>
        </div>
        <div class="divider" />
        <p class="api-summary">{{ item.summary || '无描述' }}</p>
        <div v-if="item.content" class="api-content-preview">
          {{ item.content }}
        </div>
        <div class="api-tags">
          <span v-for="tag in item.tags" :key="tag" class="api-tag">
            {{ tag }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.knowledge-view {
  padding: 0 20px 40px;
}

.knowledge-header {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 0 16px;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.14;
  letter-spacing: 0.2px;
  color: var(--text-primary);
}

.endpoint-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.search-section {
  max-width: 800px;
  margin: 0 auto 24px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 11px;
  padding: 0 12px 0 16px;
  height: 44px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.search-box:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.12);
}

.search-box > svg {
  color: rgba(0, 0, 0, 0.48);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-size: 15px;
  color: var(--text-primary);
  font-family: var(--font-body);
}

.search-input::placeholder {
  color: var(--text-secondary);
}

.search-btn {
  height: 32px;
  padding: 0 14px;
  border-radius: 8px;
  border: none;
  background: var(--accent);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: background 0.15s;
}

.search-btn:hover {
  background: var(--accent-hover);
}

.search-result-hint {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
}

.clear-search {
  background: none;
  border: none;
  color: var(--text-link);
  font-size: 13px;
  cursor: pointer;
  margin-left: 4px;
}

.clear-search:hover {
  text-decoration: underline;
}

.skeleton-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.skeleton-card {
  height: 160px;
  border-radius: 12px;
  background: linear-gradient(90deg, rgba(0,0,0,0.04) 25%, rgba(0,0,0,0.08) 50%, rgba(0,0,0,0.04) 75%);
  background-size: 200% 100%;
  animation: skeleton 1.5s ease infinite;
}

@keyframes skeleton {
  0% { background-position: 200% 0; }
  100% { background-position: 0 0; }
}

.empty-state {
  max-width: 1200px;
  margin: 80px auto 0;
  text-align: center;
  color: rgba(0, 0, 0, 0.12);
}

.empty-state h3 {
  font-size: 17px;
  font-weight: 500;
  color: var(--text-primary);
  margin-top: 16px;
}

.empty-state p {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
  margin-bottom: 20px;
}

.primary-btn {
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

.api-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.api-card {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 20px;
  box-shadow: var(--shadow-subtle);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  cursor: default;
}

.api-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card);
}

.api-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.method-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  white-space: nowrap;
}

.api-path {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  word-break: break-all;
}

.similarity-score {
  margin-left: auto;
  font-size: 12px;
  font-weight: 500;
  color: var(--accent);
}

.delete-btn {
  margin-left: 8px;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.15s, background 0.15s, color 0.15s;
}

.api-card:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: rgba(255, 59, 48, 0.1);
  color: var(--color-error);
}

.divider {
  height: 1px;
  background: var(--divider);
  margin: 12px 0;
}

.api-summary {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.api-content-preview {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 8px;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  opacity: 0.7;
}

.api-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.api-tag {
  font-size: 12px;
  color: var(--text-secondary);
  background: var(--bg-primary);
  padding: 4px 10px;
  border-radius: var(--radius-pill);
}

@media (max-width: 1024px) {
  .api-grid { grid-template-columns: repeat(2, 1fr); }
  .skeleton-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .api-grid { grid-template-columns: 1fr; }
  .skeleton-grid { grid-template-columns: 1fr; }
  .knowledge-header { flex-direction: column; gap: 4px; }
}
</style>
