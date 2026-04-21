import { createRouter, createWebHistory } from 'vue-router'

import KnowledgeGraphView from '../views/KnowledgeGraphView.vue'

const routes = [
  {
    path: '/',
    redirect: '/knowledge-graph'
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: KnowledgeGraphView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
