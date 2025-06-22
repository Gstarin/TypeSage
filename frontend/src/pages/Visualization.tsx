import { useState, useEffect, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import { Network, Table, AlertCircle, Loader, Save, RotateCcw } from 'lucide-react'
import { analysisAPI } from '../services/api'
import SimpleASTVisualizer from '../components/SimpleASTVisualizer'
import SimpleSymbolTableVisualizer from '../components/SimpleSymbolTableVisualizer'
import { VisualizationStateManager, VisualizationState } from '../utils/storage'

// 定义数据类型
interface ASTNodeData {
  id: string
  label: string
  type: string
  line?: number
  col?: number
  level?: number
  [key: string]: any
}

interface ASTData {
  nodes?: ASTNodeData[]
  edges?: any[]
  original_code?: string
}

interface SymbolData {
  name: string
  type: string
  scope: string
  line?: number
  details?: {
    args?: string[]
    inferred_type?: string
    module?: string
    annotation?: string
    returns?: string
    [key: string]: any
  }
}

interface SymbolTableData {
  visualization_data?: {
    scopes?: Array<{
      id: string
      name: string
      type: string
      symbols: string[]
    }>
    symbols?: SymbolData[]
    relationships?: any[]
  }
  original_code?: string
}

const Visualization = () => {
  const { codeHash } = useParams<{ codeHash: string }>()
  const [activeTab, setActiveTab] = useState<'ast' | 'symbol-table'>('ast')
  const [astData, setAstData] = useState<ASTData | null>(null)
  const [symbolTableData, setSymbolTableData] = useState<SymbolTableData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stateManager] = useState(() => new VisualizationStateManager())
  const [isStateRestored, setIsStateRestored] = useState(false)
  const [hasCache, setHasCache] = useState(false)

  // 保存状态
  const saveCurrentState = useCallback(() => {
    if (!codeHash) return

    const state: VisualizationState = {
      activeTab,
      codeHash,
      astData: astData || undefined,
      symbolTableData: symbolTableData || undefined
    }

    const success = stateManager.saveState(state)
    if (success) {
      console.log('可视化状态已保存')
    }
  }, [activeTab, astData, symbolTableData, codeHash, stateManager])

  // 恢复状态
  useEffect(() => {
    if (!codeHash || isStateRestored) return

    const cachedState = stateManager.restoreState(codeHash)
    if (cachedState) {
      // 检查是否有缓存的数据
      const hasCachedData = stateManager.hasCachedData(codeHash)
      setHasCache(hasCachedData)

      if (hasCachedData) {
        setActiveTab(cachedState.activeTab)
        if (cachedState.astData) {
          setAstData(cachedState.astData)
        }
        if (cachedState.symbolTableData) {
          setSymbolTableData(cachedState.symbolTableData)
        }
        setLoading(false)
        setIsStateRestored(true)
        console.log('已恢复可视化状态', cachedState)
        return
      } else {
        // 只恢复标签页状态，数据需要重新加载
        setActiveTab(cachedState.activeTab)
      }
    }

    setIsStateRestored(true)
  }, [codeHash, stateManager, isStateRestored])

  // 加载可视化数据
  useEffect(() => {
    const loadVisualizationData = async () => {
      if (!codeHash || !isStateRestored) return

      // 如果已经有缓存数据，不需要重新加载
      if (hasCache && astData && symbolTableData) {
        console.log('使用缓存的可视化数据')
        return
      }

      try {
        setLoading(true)
        
        // 并行加载AST和符号表数据
        const [astResponse, symbolResponse] = await Promise.all([
          analysisAPI.getAstVisualization(codeHash),
          analysisAPI.getSymbolTableVisualization(codeHash)
        ])
        
        console.log('加载新的可视化数据', astResponse)
        setAstData(astResponse)
        setSymbolTableData(symbolResponse)
        
        // 保存新加载的数据
        setTimeout(() => {
          saveCurrentState()
        }, 100)
        
      } catch (error) {
        console.error('加载可视化数据失败:', error)
        setError('加载可视化数据失败，请检查网络连接')
      } finally {
        setLoading(false)
      }
    }

    loadVisualizationData()
  }, [codeHash, isStateRestored, hasCache, astData, symbolTableData, saveCurrentState])

  // 当活动标签页改变时保存状态
  useEffect(() => {
    if (isStateRestored) {
      saveCurrentState()
    }
  }, [activeTab, saveCurrentState, isStateRestored])

  // 清除缓存
  const clearCache = useCallback(() => {
    stateManager.clearState()
    setHasCache(false)
    console.log('可视化缓存已清除')
  }, [stateManager])

  // 手动刷新数据
  const refreshData = useCallback(async () => {
    if (!codeHash) return
    
    setLoading(true)
    setError(null)
    
    try {
      const [astResponse, symbolResponse] = await Promise.all([
        analysisAPI.getAstVisualization(codeHash),
        analysisAPI.getSymbolTableVisualization(codeHash)
      ])
      
      setAstData(astResponse)
      setSymbolTableData(symbolResponse)
      saveCurrentState()
      
    } catch (error) {
      console.error('刷新可视化数据失败:', error)
      setError('刷新可视化数据失败，请检查网络连接')
    } finally {
      setLoading(false)
    }
  }, [codeHash, saveCurrentState])

  if (loading) {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center h-64">
          <Loader className="w-8 h-8 animate-spin text-primary-600" />
          <span className="ml-2 text-gray-600">
            {hasCache ? '从缓存加载可视化数据...' : '加载可视化数据中...'}
          </span>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="card p-8 text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-red-500" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">加载失败</h2>
          <p className="text-gray-600">{error}</p>
          <button 
            onClick={refreshData}
            className="mt-4 btn btn-primary"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            重试
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">代码可视化</h1>
            <p className="mt-2 text-gray-600">
              查看代码的抽象语法树(AST)和符号表结构
            </p>
          </div>
          
          {/* 状态指示器和操作按钮 */}
          <div className="flex items-center space-x-3">
            {hasCache && (
              <div className="flex items-center text-sm text-green-600 bg-green-50 px-3 py-1 rounded">
                <Save className="w-4 h-4 mr-1" />
                已缓存状态
              </div>
            )}
            <button
              onClick={refreshData}
              className="btn btn-secondary btn-sm"
              title="刷新数据"
            >
              <RotateCcw className="w-4 h-4 mr-1" />
              刷新
            </button>
            <button
              onClick={clearCache}
              className="btn btn-outline btn-sm"
              title="清除缓存"
            >
              清除缓存
            </button>
          </div>
        </div>
      </div>

      {/* 标签页切换 */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('ast')}
              className={`${
                activeTab === 'ast'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
            >
              <Network className="w-4 h-4 mr-2" />
              抽象语法树 (AST)
            </button>
            <button
              onClick={() => setActiveTab('symbol-table')}
              className={`${
                activeTab === 'symbol-table'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              } whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center`}
            >
              <Table className="w-4 h-4 mr-2" />
              符号表
            </button>
          </nav>
        </div>
      </div>

      {/* 内容区域 */}
      <div className="space-y-6">
        {activeTab === 'ast' && astData && (
          <div className="space-y-6">
            {/* AST可视化 */}
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                抽象语法树结构
              </h2>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-4">
                  AST包含 {astData.nodes?.length || 0} 个节点，{astData.edges?.length || 0} 条边
                </p>
                <SimpleASTVisualizer 
                  nodes={astData.nodes?.map((node) => ({
                    id: node.id || `node_${node.label}`,
                    label: node.label,
                    type: node.type || node.label,
                    line: node.line,
                    col: node.col,
                    level: node.level
                  })) || []} 
                  edges={astData.edges || []}
                  initialViewState={stateManager.restoreState(codeHash)?.astViewState}
                  onViewStateChange={(viewState) => {
                    stateManager.saveViewState('ast', viewState)
                  }}
                />
              </div>
            </div>

            {/* AST节点列表 */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">节点详情</h3>
              <div className="max-h-96 overflow-y-auto">
                <div className="space-y-2">
                  {astData.nodes?.slice(0, 20).map((node: ASTNodeData, index: number) => (
                    <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                      <span className="font-mono text-sm">{node.label}</span>
                      <div className="text-xs text-gray-500">
                        {node.line && `第${node.line}行`}
                      </div>
                    </div>
                  ))}
                  {astData.nodes && astData.nodes.length > 20 && (
                    <div className="text-center text-sm text-gray-500 py-2">
                      还有 {astData.nodes.length - 20} 个节点...
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'symbol-table' && symbolTableData && (
          <div className="space-y-6">
            {/* 符号表可视化 */}
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                符号表结构
              </h2>
              
              {/* 符号表图表 */}
              <div className="mb-6">
                <SimpleSymbolTableVisualizer 
                  visualizationData={{
                    scopes: symbolTableData?.visualization_data?.scopes || [],
                    symbols: symbolTableData?.visualization_data?.symbols || [],
                    relationships: symbolTableData?.visualization_data?.relationships || []
                  }}
                  initialViewState={stateManager.restoreState(codeHash)?.symbolViewState}
                  onViewStateChange={(viewState) => {
                    stateManager.saveViewState('symbol-table', viewState)
                  }}
                />
              </div>
              
              {/* 作用域统计 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {symbolTableData?.visualization_data?.symbols?.filter((s: SymbolData) => s.type === 'function').length || 0}
                  </div>
                  <div className="text-sm text-blue-600">函数</div>
                </div>
                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {symbolTableData?.visualization_data?.symbols?.filter((s: SymbolData) => s.type === 'variable').length || 0}
                  </div>
                  <div className="text-sm text-green-600">变量</div>
                </div>
                <div className="bg-purple-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {symbolTableData?.visualization_data?.symbols?.filter((s: SymbolData) => s.type === 'class').length || 0}
                  </div>
                  <div className="text-sm text-purple-600">类</div>
                </div>
                <div className="bg-orange-50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {symbolTableData?.visualization_data?.symbols?.filter((s: SymbolData) => s.type === 'import').length || 0}
                  </div>
                  <div className="text-sm text-orange-600">导入</div>
                </div>
              </div>

              {/* 符号详情 */}
              <div className="space-y-4">
                {['function', 'class', 'variable', 'import'].map((symbolType) => {
                  const symbols = symbolTableData?.visualization_data?.symbols?.filter((s: SymbolData) => s.type === symbolType) || []
                  if (symbols.length === 0) return null

                  return (
                    <div key={symbolType} className="card p-4">
                      <h4 className="text-md font-semibold text-gray-900 mb-3 capitalize">
                        {symbolType === 'function' && '函数'}
                        {symbolType === 'class' && '类'}
                        {symbolType === 'variable' && '变量'}
                        {symbolType === 'import' && '导入'}
                        ({symbols.length})
                      </h4>
                      <div className="space-y-2">
                        {symbols.map((symbol: SymbolData, index: number) => (
                          <div key={index} className="flex justify-between items-start p-2 bg-gray-50 rounded">
                            <div>
                              <span className="font-mono text-sm font-semibold">{symbol.name}</span>
                              {symbol.details && (
                                <div className="text-xs text-gray-500 mt-1">
                                  {symbol.type === 'function' && symbol.details.args && (
                                    <span>参数: {symbol.details.args.join(', ')}</span>
                                  )}
                                  {symbol.type === 'variable' && symbol.details.inferred_type && (
                                    <span>类型: {symbol.details.inferred_type}</span>
                                  )}
                                  {symbol.type === 'import' && symbol.details.module && (
                                    <span>模块: {symbol.details.module}</span>
                                  )}
                                </div>
                              )}
                            </div>
                            <div className="text-xs text-gray-500">
                              {symbol.line && `第${symbol.line}行`}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 原始代码 */}
      {(astData?.original_code || symbolTableData?.original_code) && (
        <div className="mt-8 card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">原始代码</h3>
          <pre className="code-block whitespace-pre-wrap">
            {astData?.original_code || symbolTableData?.original_code}
          </pre>
        </div>
      )}
    </div>
  )
}

export default Visualization 