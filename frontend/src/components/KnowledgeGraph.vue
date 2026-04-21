<template>
  <section class="knowledge-graph">
    <div class="graph-panel">
      <div class="graph-toolbar">
        <div class="legend" aria-label="节点类型图例">
          <span
            v-for="item in legendItems"
            :key="item.type"
            class="legend-item"
          >
            <span class="legend-dot" :style="{ backgroundColor: item.color }"></span>
            {{ item.type }}
          </span>
        </div>

        <div class="toolbar-actions">
          <button type="button" class="icon-button" title="重新布局" @click="rerunLayout">
            ↻
          </button>
          <button type="button" class="icon-button" title="适配视图" @click="fitGraph">
            ⛶
          </button>
        </div>
      </div>

      <div class="graph-stage">
        <div ref="graphContainer" class="graph-container"></div>

        <div v-if="loading" class="state-layer">
          <div class="state-title">正在加载图谱数据</div>
        </div>

        <div v-else-if="error" class="state-layer state-error">
          <div class="state-title">图谱加载失败</div>
          <div class="state-message">{{ error }}</div>
        </div>

        <div v-else-if="isEmpty" class="state-layer">
          <div class="state-title">暂无图谱数据</div>
          <div class="state-message">后端接口当前没有返回可展示的节点。</div>
        </div>
      </div>
    </div>

    <aside class="detail-panel">
      <template v-if="selectedNode">
        <div class="detail-heading">
          <span
            class="detail-type-dot"
            :style="{ backgroundColor: selectedNode.color }"
          ></span>
          <div>
            <h2>{{ selectedNode.label }}</h2>
            <p>{{ selectedNode.type }}</p>
          </div>
        </div>

        <dl class="meta-list">
          <div class="meta-row">
            <dt>ID</dt>
            <dd>{{ selectedNode.id }}</dd>
          </div>
          <div class="meta-row">
            <dt>Label</dt>
            <dd>{{ selectedNode.label }}</dd>
          </div>
          <div class="meta-row">
            <dt>Type</dt>
            <dd>{{ selectedNode.type }}</dd>
          </div>
        </dl>

        <div class="properties-block">
          <h3>Properties</h3>
          <dl v-if="propertyEntries.length" class="property-list">
            <div
              v-for="[key, value] in propertyEntries"
              :key="key"
              class="property-row"
            >
              <dt>{{ key }}</dt>
              <dd>{{ formatPropertyValue(value) }}</dd>
            </div>
          </dl>
          <p v-else class="muted-text">该节点没有额外属性。</p>
        </div>
      </template>

      <div v-else class="empty-detail">
        <h2>节点详情</h2>
        <p>选择一个节点后，这里会显示它的基础信息和属性。</p>
      </div>
    </aside>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import cytoscape from 'cytoscape'

const props = defineProps({
  graphData: {
    type: Object,
    default: () => ({
      nodes: [],
      edges: []
    })
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  }
})

const graphContainer = ref(null)
const cy = ref(null)
const resizeObserver = ref(null)
const selectedNode = ref(null)

const typeColors = {
  Person: '#2f6fed',
  Organization: '#00a376',
  Theory: '#8b5cf6',
  Award: '#f59e0b',
  Place: '#e05263',
  Skill: '#0ea5e9',
  Framework: '#14b8a6',
  Job: '#ef6c35',
  Unknown: '#64748b'
}

const nodes = computed(() => {
  return Array.isArray(props.graphData?.nodes) ? props.graphData.nodes : []
})

const edges = computed(() => {
  return Array.isArray(props.graphData?.edges) ? props.graphData.edges : []
})

const isEmpty = computed(() => !props.loading && !props.error && nodes.value.length === 0)

const legendItems = computed(() => {
  const types = new Set(nodes.value.map((node) => node.type || 'Unknown'))
  if (!types.size) {
    types.add('Unknown')
  }

  return Array.from(types).map((type) => ({
    type,
    color: getTypeColor(type)
  }))
})

const propertyEntries = computed(() => {
  if (!selectedNode.value?.properties) {
    return []
  }

  return Object.entries(selectedNode.value.properties)
})

watch(
  () => [props.graphData, props.loading, props.error],
  () => {
    renderGraph()
  },
  { deep: true }
)

onMounted(() => {
  renderGraph()

  if (graphContainer.value) {
    resizeObserver.value = new ResizeObserver(() => {
      cy.value?.resize()
      cy.value?.fit(undefined, 48)
    })
    resizeObserver.value.observe(graphContainer.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver.value?.disconnect()
  destroyGraph()
})

function getTypeColor(type) {
  return typeColors[type] || typeColors.Unknown
}

function normalizeNode(node) {
  const type = node?.type || 'Unknown'
  const id = String(node?.id ?? '')

  return {
    id,
    label: node?.label || node?.properties?.name || id,
    type,
    properties: node?.properties && typeof node.properties === 'object' ? node.properties : {},
    color: getTypeColor(type)
  }
}

function buildElements() {
  const normalizedNodes = nodes.value
    .filter((node) => node?.id !== undefined && node?.id !== null)
    .map((node) => normalizeNode(node))

  const nodeIds = new Set(normalizedNodes.map((node) => node.id))

  const normalizedEdges = edges.value
    .filter((edge) => {
      const source = String(edge?.source ?? '')
      const target = String(edge?.target ?? '')
      return source && target && nodeIds.has(source) && nodeIds.has(target)
    })
    .map((edge, index) => ({
      id: edge.id ? String(edge.id) : `${edge.source}-${edge.target}-${edge.label || 'REL'}-${index}`,
      source: String(edge.source),
      target: String(edge.target),
      label: edge.label || ''
    }))

  return [
    ...normalizedNodes.map((node) => ({
      group: 'nodes',
      data: node
    })),
    ...normalizedEdges.map((edge) => ({
      group: 'edges',
      data: edge
    }))
  ]
}

async function renderGraph() {
  await nextTick()

  if (!graphContainer.value || props.loading || props.error || isEmpty.value) {
    destroyGraph()
    return
  }

  const elements = buildElements()
  destroyGraph()

  cy.value = cytoscape({
    container: graphContainer.value,
    elements,
    minZoom: 0.2,
    maxZoom: 3,
    wheelSensitivity: 0.18,
    boxSelectionEnabled: false,
    style: [
      {
        selector: 'node',
        style: {
          width: 46,
          height: 46,
          'background-color': 'data(color)',
          'border-width': 3,
          'border-color': '#ffffff',
          label: 'data(label)',
          color: '#273449',
          'font-size': 12,
          'font-weight': 600,
          'text-valign': 'bottom',
          'text-halign': 'center',
          'text-margin-y': 8,
          'text-wrap': 'wrap',
          'text-max-width': 100,
          'overlay-opacity': 0,
          'transition-property': 'background-color, border-color, width, height',
          'transition-duration': 120
        }
      },
      {
        selector: 'node:selected',
        style: {
          width: 54,
          height: 54,
          'border-color': '#111827',
          'border-width': 4
        }
      },
      {
        selector: 'edge',
        style: {
          width: 2,
          'line-color': '#b8c2d6',
          'target-arrow-color': '#b8c2d6',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          label: 'data(label)',
          color: '#56647a',
          'font-size': 10,
          'font-weight': 600,
          'text-background-color': '#ffffff',
          'text-background-opacity': 0.9,
          'text-background-padding': 3,
          'text-rotation': 'autorotate',
          'overlay-opacity': 0
        }
      }
    ],
    layout: getLayoutOptions()
  })

  cy.value.on('tap', 'node', (event) => {
    selectedNode.value = normalizeNode(event.target.data())
  })

  cy.value.on('tap', (event) => {
    if (event.target === cy.value) {
      selectedNode.value = null
      cy.value.elements().unselect()
    }
  })
}

function getLayoutOptions() {
  return {
    name: 'cose',
    animate: false,
    fit: true,
    padding: 56,
    nodeRepulsion: 9000,
    idealEdgeLength: 120,
    edgeElasticity: 80,
    nestingFactor: 1.2,
    gravity: 0.25,
    numIter: 1000
  }
}

function destroyGraph() {
  if (cy.value) {
    cy.value.destroy()
    cy.value = null
  }
}

function rerunLayout() {
  if (!cy.value) {
    return
  }

  cy.value.layout(getLayoutOptions()).run()
}

function fitGraph() {
  cy.value?.fit(undefined, 56)
}

function formatPropertyValue(value) {
  if (value === null || value === undefined) {
    return '-'
  }

  if (typeof value === 'object') {
    return JSON.stringify(value)
  }

  return String(value)
}
</script>

<style scoped>
.knowledge-graph {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 18px;
  min-height: 620px;
}

.graph-panel,
.detail-panel {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 12px 35px rgba(31, 42, 68, 0.08);
}

.graph-panel {
  display: flex;
  min-width: 0;
  flex-direction: column;
  overflow: hidden;
}

.graph-toolbar {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid #e4eaf3;
  padding: 12px 16px;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #4d5b73;
  font-size: 13px;
  font-weight: 600;
}

.legend-dot,
.detail-type-dot {
  display: inline-block;
  flex: 0 0 auto;
  border-radius: 999px;
}

.legend-dot {
  width: 10px;
  height: 10px;
}

.toolbar-actions {
  display: flex;
  flex: 0 0 auto;
  gap: 8px;
}

.icon-button {
  display: inline-flex;
  width: 36px;
  height: 36px;
  align-items: center;
  justify-content: center;
  border: 1px solid #cfdae8;
  border-radius: 8px;
  background: #f8fafc;
  color: #26344d;
  font-size: 17px;
  line-height: 1;
}

.icon-button:hover {
  border-color: #aebcd0;
  background: #eef3f9;
}

.graph-stage {
  position: relative;
  min-height: 560px;
  flex: 1;
  background:
    linear-gradient(rgba(122, 139, 166, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(122, 139, 166, 0.12) 1px, transparent 1px),
    #fbfcfe;
  background-size: 32px 32px;
}

.graph-container {
  position: absolute;
  inset: 0;
}

.state-layer {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 8px;
  padding: 32px;
  background: rgba(251, 252, 254, 0.88);
  text-align: center;
}

.state-title {
  color: #182338;
  font-size: 18px;
  font-weight: 700;
}

.state-message {
  max-width: 460px;
  color: #66748a;
  font-size: 14px;
  line-height: 1.7;
}

.state-error .state-title {
  color: #b42318;
}

.detail-panel {
  min-width: 0;
  padding: 22px;
}

.detail-heading {
  display: flex;
  align-items: center;
  gap: 14px;
  border-bottom: 1px solid #e6edf5;
  padding-bottom: 18px;
}

.detail-type-dot {
  width: 18px;
  height: 18px;
}

.detail-heading h2,
.empty-detail h2 {
  overflow-wrap: anywhere;
  margin: 0;
  color: #172033;
  font-size: 20px;
  line-height: 1.3;
}

.detail-heading p,
.empty-detail p,
.muted-text {
  margin: 6px 0 0;
  color: #69778d;
  font-size: 14px;
  line-height: 1.7;
}

.meta-list,
.property-list {
  margin: 0;
}

.meta-list {
  display: grid;
  gap: 10px;
  padding: 18px 0;
  border-bottom: 1px solid #e6edf5;
}

.meta-row,
.property-row {
  display: grid;
  grid-template-columns: 78px minmax(0, 1fr);
  gap: 12px;
}

.meta-row dt,
.property-row dt {
  color: #748196;
  font-size: 13px;
  font-weight: 700;
}

.meta-row dd,
.property-row dd {
  min-width: 0;
  margin: 0;
  overflow-wrap: anywhere;
  color: #26344d;
  font-size: 14px;
  line-height: 1.55;
}

.properties-block {
  padding-top: 18px;
}

.properties-block h3 {
  margin: 0 0 12px;
  color: #172033;
  font-size: 15px;
}

.property-list {
  display: grid;
  gap: 12px;
}

.property-row {
  border-radius: 8px;
  background: #f7f9fc;
  padding: 10px;
}

.empty-detail {
  display: flex;
  min-height: 240px;
  flex-direction: column;
  justify-content: center;
  text-align: center;
}

@media (max-width: 960px) {
  .knowledge-graph {
    grid-template-columns: 1fr;
  }

  .detail-panel {
    min-height: 260px;
  }
}

@media (max-width: 640px) {
  .graph-toolbar {
    align-items: flex-start;
    flex-direction: column;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .graph-stage {
    min-height: 430px;
  }

  .detail-panel {
    padding: 18px;
  }
}
</style>
