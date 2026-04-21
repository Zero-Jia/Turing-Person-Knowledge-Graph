<template>
  <main class="page-shell">
    <header class="page-header">
      <div>
        <p class="eyebrow">Neo4j Knowledge Graph</p>
        <h1>图灵人物知识图谱</h1>
      </div>

      <div class="header-actions">
        <div class="stat-group">
          <div class="stat-item">
            <span>{{ nodeCount }}</span>
            节点
          </div>
          <div class="stat-item">
            <span>{{ edgeCount }}</span>
            关系
          </div>
        </div>

        <button type="button" class="refresh-button" :disabled="loading" @click="loadGraph">
          {{ loading ? '加载中' : '刷新图谱' }}
        </button>
      </div>
    </header>

    <KnowledgeGraph
      :graph-data="graphData"
      :loading="loading"
      :error="error"
    />
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import { getGraph } from '../api/graph'
import KnowledgeGraph from '../components/KnowledgeGraph.vue'

const graphData = ref({
  nodes: [],
  edges: []
})
const loading = ref(false)
const error = ref('')

const nodeCount = computed(() => graphData.value.nodes.length)
const edgeCount = computed(() => graphData.value.edges.length)

onMounted(() => {
  loadGraph()
})

async function loadGraph() {
  loading.value = true
  error.value = ''

  try {
    graphData.value = await getGraph()
  } catch (err) {
    graphData.value = {
      nodes: [],
      edges: []
    }
    error.value = getErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function getErrorMessage(err) {
  const responseData = err?.response?.data

  if (typeof responseData === 'string') {
    return responseData
  }

  return (
    responseData?.detail ||
    responseData?.message ||
    responseData?.error ||
    err?.message ||
    '请求 /api/graph 失败'
  )
}
</script>

<style scoped>
.page-shell {
  min-height: 100vh;
  padding: 28px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(245, 247, 251, 0.95)),
    #f5f7fb;
}

.page-header {
  display: flex;
  max-width: 1440px;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin: 0 auto 20px;
}

.page-shell :deep(.knowledge-graph) {
  max-width: 1440px;
  margin: 0 auto;
}

.eyebrow {
  margin: 0 0 8px;
  color: #0f7f73;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  color: #111827;
  font-size: 32px;
  line-height: 1.2;
}

.header-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 14px;
}

.stat-group {
  display: flex;
  overflow: hidden;
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
}

.stat-item {
  min-width: 88px;
  padding: 10px 14px;
  color: #637089;
  font-size: 13px;
  font-weight: 700;
  text-align: center;
}

.stat-item + .stat-item {
  border-left: 1px solid #dbe3ef;
}

.stat-item span {
  display: block;
  color: #142033;
  font-size: 20px;
  line-height: 1.1;
}

.refresh-button {
  min-width: 106px;
  border: 1px solid #186ade;
  border-radius: 8px;
  background: #186ade;
  color: #ffffff;
  padding: 11px 16px;
  font-size: 14px;
  font-weight: 800;
}

.refresh-button:hover:not(:disabled) {
  background: #125ac0;
}

.refresh-button:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

@media (max-width: 760px) {
  .page-shell {
    padding: 18px;
  }

  .page-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
    align-items: stretch;
    flex-direction: column;
  }

  .stat-group {
    width: 100%;
  }

  .stat-item {
    flex: 1;
  }

  .refresh-button {
    width: 100%;
  }

  h1 {
    font-size: 26px;
  }
}
</style>
