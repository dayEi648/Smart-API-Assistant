import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/components/layout/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', name: 'chat', component: () => import('@/views/Chat.vue') },
        { path: 'knowledge', name: 'knowledge', component: () => import('@/views/Knowledge.vue') },
        { path: 'documents', name: 'documents', component: () => import('@/views/Documents.vue') },
      ],
    },
  ],
})

export default router
