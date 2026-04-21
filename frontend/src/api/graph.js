import axios from 'axios'

const graphHttp = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 15000
})

export async function getGraph() {
  const { data } = await graphHttp.get('/api/graph')

  return {
    nodes: Array.isArray(data?.nodes) ? data.nodes : [],
    edges: Array.isArray(data?.edges) ? data.edges : []
  }
}

export default {
  getGraph
}
