<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './Navbar.vue'
import Sidebar from './Sidebar.vue'

const route = useRoute()
const showSidebar = ref(true)
const sidebarOpen = ref(false)

watch(() => route.path, () => {
  showSidebar.value = route.path === '/' || route.path === ''
  sidebarOpen.value = false
}, { immediate: true })

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}
</script>

<template>
  <div class="layout">
    <Navbar @toggle-sidebar="toggleSidebar" />
    <div class="layout-body">
      <Sidebar
        v-if="showSidebar"
        :class="{ open: sidebarOpen }"
        @close="sidebarOpen = false"
      />
      <main class="main-content" :class="{ 'with-sidebar': showSidebar, 'no-sidebar': !showSidebar }">
        <router-view />
      </main>
      <div
        v-if="sidebarOpen && showSidebar"
        class="sidebar-overlay"
        @click="sidebarOpen = false"
      />
    </div>
  </div>
</template>

<style scoped>
.layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-body {
  display: flex;
  flex: 1;
  margin-top: 48px;
  overflow: hidden;
  position: relative;
}

.main-content {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  background: var(--bg-primary);
}

.main-content.with-sidebar {
  margin-left: 260px;
}

.main-content.no-sidebar {
  margin-left: 0;
}

.sidebar-overlay {
  position: fixed;
  inset: 48px 0 0 0;
  background: rgba(0, 0, 0, 0.2);
  z-index: calc(var(--z-sidebar) - 1);
}

@media (max-width: 1024px) {
  .main-content.with-sidebar {
    margin-left: 0;
  }
}
</style>
