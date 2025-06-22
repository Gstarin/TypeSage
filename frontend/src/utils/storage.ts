// 状态持久化工具类
export class StorageManager {
  private static instance: StorageManager
  private storage: Storage

  private constructor() {
    this.storage = typeof window !== 'undefined' ? window.localStorage : ({} as Storage)
  }

  public static getInstance(): StorageManager {
    if (!StorageManager.instance) {
      StorageManager.instance = new StorageManager()
    }
    return StorageManager.instance
  }

  // 安全地设置数据到localStorage
  public set(key: string, value: any): boolean {
    try {
      const serialized = JSON.stringify(value)
      this.storage.setItem(key, serialized)
      return true
    } catch (error) {
      console.warn(`Failed to save to localStorage (${key}):`, error)
      return false
    }
  }

  // 安全地从localStorage获取数据
  public get<T>(key: string, defaultValue?: T): T | null {
    try {
      const item = this.storage.getItem(key)
      if (item === null) {
        return defaultValue || null
      }
      return JSON.parse(item) as T
    } catch (error) {
      console.warn(`Failed to read from localStorage (${key}):`, error)
      return defaultValue || null
    }
  }

  // 删除指定key
  public remove(key: string): boolean {
    try {
      this.storage.removeItem(key)
      return true
    } catch (error) {
      console.warn(`Failed to remove from localStorage (${key}):`, error)
      return false
    }
  }

  // 清除所有指定前缀的keys
  public clearByPrefix(prefix: string): boolean {
    try {
      const keys = Object.keys(this.storage).filter(key => key.startsWith(prefix))
      keys.forEach(key => this.storage.removeItem(key))
      return true
    } catch (error) {
      console.warn(`Failed to clear localStorage by prefix (${prefix}):`, error)
      return false
    }
  }

  // 检查localStorage是否可用
  public isAvailable(): boolean {
    try {
      const testKey = '__storage_test__'
      this.storage.setItem(testKey, 'test')
      this.storage.removeItem(testKey)
      return true
    } catch {
      return false
    }
  }

  // 获取存储大小（近似值）
  public getStorageSize(): number {
    try {
      let total = 0
      for (const key in this.storage) {
        if (this.storage.hasOwnProperty(key)) {
          total += this.storage[key].length + key.length
        }
      }
      return total
    } catch {
      return 0
    }
  }
}

// TypeSage特定的存储键
export const STORAGE_KEYS = {
  ANALYZER_CODE: 'typesage_analyzer_code',
  ANALYZER_RESULT: 'typesage_analyzer_result',
  ANALYZER_SETTINGS: 'typesage_analyzer_settings',
  ANALYZER_LAST_SAVED: 'typesage_analyzer_last_saved',
  
  // 可视化状态相关
  VISUALIZATION_ACTIVE_TAB: 'typesage_visualization_active_tab',
  VISUALIZATION_AST_DATA: 'typesage_visualization_ast_data',
  VISUALIZATION_SYMBOL_DATA: 'typesage_visualization_symbol_data',
  VISUALIZATION_AST_VIEW_STATE: 'typesage_visualization_ast_view_state',
  VISUALIZATION_SYMBOL_VIEW_STATE: 'typesage_visualization_symbol_view_state',
  VISUALIZATION_LAST_CODE_HASH: 'typesage_visualization_last_code_hash',
  VISUALIZATION_LAST_SAVED: 'typesage_visualization_last_saved',
  
  MEMORY_FILTERS: 'typesage_memory_filters'
} as const

// 分析器状态接口
export interface AnalyzerState {
  code: string
  settings: {
    useLLM: boolean
    saveToMemory: boolean
    useCache: boolean
  }
  analysisResult?: any
  lastSaved?: string
}

// 可视化视图状态接口
export interface VisualizationViewState {
  // 网络视图状态
  position?: { x: number; y: number }
  scale?: number
  selectedNodes?: string[]
  expandedNodes?: string[]
  
  // 显示设置
  showNodeLabels?: boolean
  showEdgeLabels?: boolean
  layoutType?: 'hierarchical' | 'force' | 'circular'
  nodeSize?: number
  
  // 过滤设置
  nodeTypeFilters?: string[]
  minDepthFilter?: number
  maxDepthFilter?: number
}

// 可视化状态接口
export interface VisualizationState {
  activeTab: 'ast' | 'symbol-table'
  codeHash?: string
  astData?: any
  symbolTableData?: any
  astViewState?: VisualizationViewState
  symbolViewState?: VisualizationViewState
  lastSaved?: string
}

// 分析器状态管理器
export class AnalyzerStateManager {
  private storage: StorageManager

  constructor() {
    this.storage = StorageManager.getInstance()
  }

  // 保存完整状态
  public saveState(state: AnalyzerState): boolean {
    const now = new Date().toISOString()
    const success = [
      this.storage.set(STORAGE_KEYS.ANALYZER_CODE, state.code),
      this.storage.set(STORAGE_KEYS.ANALYZER_SETTINGS, state.settings),
      this.storage.set(STORAGE_KEYS.ANALYZER_LAST_SAVED, now)
    ].every(Boolean)

    if (state.analysisResult) {
      this.storage.set(STORAGE_KEYS.ANALYZER_RESULT, state.analysisResult)
    }

    return success
  }

  // 恢复完整状态
  public restoreState(): AnalyzerState | null {
    if (!this.storage.isAvailable()) {
      return null
    }

    const defaultCode = `# 示例Python代码
def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count

# 未声明变量示例
result = calculate_average(data)  # data未声明
print(f"平均值: {result}")

# 未类型提示示例
items = [1, 2, 3, 4, 5]
filtered = [x for x in items if x > threshold]  # threshold未声明`

    const defaultSettings = {
      useLLM: true,
      saveToMemory: true,
      useCache: true
    }

    return {
      code: this.storage.get(STORAGE_KEYS.ANALYZER_CODE, defaultCode) || defaultCode,
      settings: this.storage.get(STORAGE_KEYS.ANALYZER_SETTINGS, defaultSettings) || defaultSettings,
      analysisResult: this.storage.get(STORAGE_KEYS.ANALYZER_RESULT),
      lastSaved: this.storage.get(STORAGE_KEYS.ANALYZER_LAST_SAVED) || undefined
    }
  }

  // 清除分析结果（当代码改变时）
  public clearAnalysisResult(): boolean {
    return this.storage.remove(STORAGE_KEYS.ANALYZER_RESULT)
  }

  // 清除所有分析器状态
  public clearAll(): boolean {
    return [
      STORAGE_KEYS.ANALYZER_CODE,
      STORAGE_KEYS.ANALYZER_RESULT,
      STORAGE_KEYS.ANALYZER_SETTINGS,
      STORAGE_KEYS.ANALYZER_LAST_SAVED
    ].map(key => this.storage.remove(key)).every(Boolean)
  }

  // 获取最后保存时间的友好显示
  public getLastSavedTimeText(): string | null {
    const lastSaved = this.storage.get<string>(STORAGE_KEYS.ANALYZER_LAST_SAVED)
    if (!lastSaved) return null

    const savedTime = new Date(lastSaved)
    const now = new Date()
    const diffMinutes = Math.floor((now.getTime() - savedTime.getTime()) / (1000 * 60))

    if (diffMinutes < 1) return '刚才'
    if (diffMinutes < 60) return `${diffMinutes}分钟前`
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}小时前`
    return `${Math.floor(diffMinutes / 1440)}天前`
  }
}

// 可视化状态管理器
export class VisualizationStateManager {
  private storage: StorageManager

  constructor() {
    this.storage = StorageManager.getInstance()
  }

  // 保存可视化状态
  public saveState(state: VisualizationState): boolean {
    const now = new Date().toISOString()
    
    const success = [
      this.storage.set(STORAGE_KEYS.VISUALIZATION_ACTIVE_TAB, state.activeTab),
      this.storage.set(STORAGE_KEYS.VISUALIZATION_LAST_SAVED, now)
    ].every(Boolean)

    // 保存关联的codeHash
    if (state.codeHash) {
      this.storage.set(STORAGE_KEYS.VISUALIZATION_LAST_CODE_HASH, state.codeHash)
    }

    // 保存数据（如果有）
    if (state.astData) {
      this.storage.set(STORAGE_KEYS.VISUALIZATION_AST_DATA, state.astData)
    }
    if (state.symbolTableData) {
      this.storage.set(STORAGE_KEYS.VISUALIZATION_SYMBOL_DATA, state.symbolTableData)
    }

    // 保存视图状态
    if (state.astViewState) {
      this.storage.set(STORAGE_KEYS.VISUALIZATION_AST_VIEW_STATE, state.astViewState)
    }
    if (state.symbolViewState) {
      this.storage.set(STORAGE_KEYS.VISUALIZATION_SYMBOL_VIEW_STATE, state.symbolViewState)
    }

    return success
  }

  // 恢复可视化状态
  public restoreState(currentCodeHash?: string): VisualizationState | null {
    if (!this.storage.isAvailable()) {
      return null
    }

    const lastCodeHash = this.storage.get<string>(STORAGE_KEYS.VISUALIZATION_LAST_CODE_HASH)
    
    // 如果codeHash不匹配，返回默认状态（不加载过时的数据）
    if (currentCodeHash && lastCodeHash && currentCodeHash !== lastCodeHash) {
          return {
      activeTab: (this.storage.get(STORAGE_KEYS.VISUALIZATION_ACTIVE_TAB, 'ast') as 'ast' | 'symbol-table') || 'ast',
      codeHash: currentCodeHash
    }
    }

    return {
      activeTab: (this.storage.get(STORAGE_KEYS.VISUALIZATION_ACTIVE_TAB, 'ast') as 'ast' | 'symbol-table') || 'ast',
      codeHash: lastCodeHash || undefined,
      astData: this.storage.get(STORAGE_KEYS.VISUALIZATION_AST_DATA),
      symbolTableData: this.storage.get(STORAGE_KEYS.VISUALIZATION_SYMBOL_DATA),
      astViewState: this.storage.get(STORAGE_KEYS.VISUALIZATION_AST_VIEW_STATE) || undefined,
      symbolViewState: this.storage.get(STORAGE_KEYS.VISUALIZATION_SYMBOL_VIEW_STATE) || undefined,
      lastSaved: this.storage.get(STORAGE_KEYS.VISUALIZATION_LAST_SAVED) || undefined
    }
  }

  // 清除可视化状态
  public clearState(): boolean {
    return [
      STORAGE_KEYS.VISUALIZATION_ACTIVE_TAB,
      STORAGE_KEYS.VISUALIZATION_AST_DATA,
      STORAGE_KEYS.VISUALIZATION_SYMBOL_DATA,
      STORAGE_KEYS.VISUALIZATION_AST_VIEW_STATE,
      STORAGE_KEYS.VISUALIZATION_SYMBOL_VIEW_STATE,
      STORAGE_KEYS.VISUALIZATION_LAST_CODE_HASH,
      STORAGE_KEYS.VISUALIZATION_LAST_SAVED
    ].map(key => this.storage.remove(key)).every(Boolean)
  }

  // 仅保存视图状态（位置、缩放等）
  public saveViewState(viewType: 'ast' | 'symbol-table', viewState: VisualizationViewState): boolean {
    const key = viewType === 'ast' 
      ? STORAGE_KEYS.VISUALIZATION_AST_VIEW_STATE 
      : STORAGE_KEYS.VISUALIZATION_SYMBOL_VIEW_STATE
    return this.storage.set(key, viewState)
  }

  // 获取最后保存时间的友好显示
  public getLastSavedTimeText(): string | null {
    const lastSaved = this.storage.get<string>(STORAGE_KEYS.VISUALIZATION_LAST_SAVED)
    if (!lastSaved) return null

    const savedTime = new Date(lastSaved)
    const now = new Date()
    const diffMinutes = Math.floor((now.getTime() - savedTime.getTime()) / (1000 * 60))

    if (diffMinutes < 1) return '刚才'
    if (diffMinutes < 60) return `${diffMinutes}分钟前`
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}小时前`
    return `${Math.floor(diffMinutes / 1440)}天前`
  }

  // 检查是否有缓存的数据可以恢复
  public hasCachedData(codeHash: string): boolean {
    const lastCodeHash = this.storage.get<string>(STORAGE_KEYS.VISUALIZATION_LAST_CODE_HASH)
    return lastCodeHash === codeHash && (
      this.storage.get(STORAGE_KEYS.VISUALIZATION_AST_DATA) !== null ||
      this.storage.get(STORAGE_KEYS.VISUALIZATION_SYMBOL_DATA) !== null
    )
  }
}

export default StorageManager 