import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url)
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url)
    return response
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.config?.url, error.message)
    return Promise.reject(error)
  }
)

// 代码分析相关API
export interface CodeAnalysisRequest {
  code: string
  use_llm?: boolean
  save_to_memory?: boolean
  use_cache?: boolean  // 新增：是否使用缓存
}

export interface CodeAnalysisResponse {
  success: boolean
  code_hash: string
  ast_data?: any
  symbol_table?: any
  undeclared_variables?: any[]
  llm_suggestions?: any
  type_annotations?: any
  code_quality?: any
  cached?: boolean
  error?: string
}

export const analysisAPI = {
  // 分析代码
  analyzeCode: async (data: CodeAnalysisRequest): Promise<CodeAnalysisResponse> => {
    const response = await api.post('/api/analysis/analyze', data)
    return response.data
  },

  // 生成类型注解
  generateTypeAnnotations: async (data: { code: string; use_llm?: boolean; use_cache?: boolean }) => {
    const response = await api.post('/api/analysis/annotate', data)
    return response.data
  },

  // 获取AST可视化数据
  getAstVisualization: async (codeHash: string) => {
    const response = await api.get(`/api/analysis/ast/${codeHash}`)
    return response.data
  },

  // 获取符号表可视化数据
  getSymbolTableVisualization: async (codeHash: string) => {
    const response = await api.get(`/api/analysis/symbol-table/${codeHash}`)
    return response.data
  },

  // 获取分析服务状态
  getStatus: async () => {
    const response = await api.get('/api/analysis/status')
    return response.data
  },

  // 缓存管理相关API
  cache: {
    // 获取缓存统计信息
    getStats: async () => {
      const response = await api.get('/api/analysis/cache/stats')
      return response.data
    },

    // 清除所有缓存
    clearAll: async () => {
      const response = await api.delete('/api/analysis/cache')
      return response.data
    },

    // 清除特定缓存
    clearSpecific: async (codeHash: string) => {
      const response = await api.delete(`/api/analysis/cache/${codeHash}`)
      return response.data
    },
  },

  getAnalysisStatus: () => api.get('/analysis/status'),

  getCacheStats: () => api.get('/analysis/cache/stats'),
}

// 记忆库相关API
export const memoryAPI = {
  // 获取记忆库模式
  getPatterns: async (params?: { page?: number; page_size?: number }) => {
    const response = await api.get('/api/memory/patterns', { params })
    return response.data
  },

  // 获取类型推导历史
  getHistory: async () => {
    const response = await api.get('/api/memory/history')
    return response.data
  },

  // 获取统计信息
  getStatistics: async () => {
    const response = await api.get('/api/memory/statistics')
    return response.data
  },

  // 搜索模式
  searchPatterns: async (query: string = '', confidenceMin: number = 0.0) => {
    const response = await api.get('/api/memory/search', {
      params: { query, confidence_min: confidenceMin }
    })
    return response.data
  },

  // 导出数据
  exportData: async () => {
    const response = await api.get('/api/memory/export')
    return response.data
  },

  getTypeInferences: (params?: { page?: number; page_size?: number }) =>
    api.get('/memory/type-inferences', { params }),

  clearMemory: () => api.delete('/memory/clear'),
}

export default api 