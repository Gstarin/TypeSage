import { useEffect, useRef, useState } from 'react'
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'
import { VisualizationViewState } from '../utils/storage'

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

interface SymbolTableVisualizationData {
  scopes: Array<{
    id: string
    name: string
    type: string
    symbols: string[]
  }>
  symbols: SymbolData[]
  relationships: any[]
}

interface SimpleSymbolTableVisualizerProps {
  visualizationData: SymbolTableVisualizationData
  initialViewState?: VisualizationViewState
  onViewStateChange?: (viewState: VisualizationViewState) => void
}

const SimpleSymbolTableVisualizer = ({ 
  visualizationData,
  initialViewState,
  onViewStateChange
}: SimpleSymbolTableVisualizerProps) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const networkRef = useRef<any>(null) // 保存网络实例的引用
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [currentViewState, setCurrentViewState] = useState<VisualizationViewState>({
    showNodeLabels: true,
    showEdgeLabels: false,
    layoutType: 'hierarchical',
    nodeSize: 20,
    selectedNodes: [],
    ...initialViewState
  })

  console.log('符号表可视化数据:', visualizationData)

  // 保存当前视图状态
  const saveViewState = () => {
    if (!networkRef.current) return

    try {
      const position = networkRef.current.getViewPosition()
      const scale = networkRef.current.getScale()
      const selectedNodes = networkRef.current.getSelectedNodes()

      const newViewState: VisualizationViewState = {
        ...currentViewState,
        position,
        scale,
        selectedNodes
      }

      setCurrentViewState(newViewState)
      onViewStateChange?.(newViewState)
    } catch (error) {
      console.warn('保存符号表视图状态失败:', error)
    }
  }

  // 恢复视图状态
  const restoreViewState = () => {
    if (!networkRef.current || !currentViewState) return

    try {
      // 恢复位置和缩放
      if (currentViewState.position && currentViewState.scale) {
        networkRef.current.moveTo({
          position: currentViewState.position,
          scale: currentViewState.scale,
          animation: {
            duration: 500,
            easingFunction: 'easeInOutQuad'
          }
        })
      }

      // 恢复选中节点
      if (currentViewState.selectedNodes && currentViewState.selectedNodes.length > 0) {
        networkRef.current.selectNodes(currentViewState.selectedNodes)
      }
    } catch (error) {
      console.warn('恢复符号表视图状态失败:', error)
    }
  }

  useEffect(() => {
    const initNetwork = async () => {
      if (!containerRef.current || !visualizationData) {
        setLoading(false)
        return
      }

      try {
        // 如果已有网络实例，先销毁它
        if (networkRef.current) {
          networkRef.current.destroy()
          networkRef.current = null
        }

        const nodes: any[] = []
        const edges: any[] = []

        // 创建根节点 - 模块
        const rootNodeId = 'module_root'
        nodes.push({
          id: rootNodeId,
          label: currentViewState.showNodeLabels ? 'Python模块' : '',
          title: 'Python模块 - 根作用域',
          shape: 'box',
          color: {
            background: '#673AB7',
            border: '#512DA8',
            highlight: { background: '#7C4DFF', border: '#512DA8' }
          },
          font: { size: 16, color: '#fff' },
          level: 0,
          mass: 2,
          size: currentViewState.nodeSize || 25
        })

        // 全局作用域节点
        const globalScopeId = 'scope_global'
        const globalSymbols = visualizationData.symbols.filter(s => s.scope === 'global' || !s.scope)
        
        nodes.push({
          id: globalScopeId,
          label: currentViewState.showNodeLabels ? '全局作用域' : '',
          title: `全局作用域 - 包含${globalSymbols.length}个符号`,
          shape: 'ellipse',
          color: {
            background: '#2196F3',
            border: '#1976D2',
            highlight: { background: '#42A5F5', border: '#1976D2' }
          },
          font: { size: 14, color: '#fff' },
          level: 1,
          mass: 1.5,
          size: currentViewState.nodeSize || 20,
          nodeType: 'scope',
          scopeInfo: {
            type: 'global',
            symbols: globalSymbols
          }
        })

        edges.push({
          id: `edge_root_global`,
          from: rootNodeId,
          to: globalScopeId,
          color: { color: '#666' },
          label: currentViewState.showEdgeLabels ? '包含' : '',
          font: { size: 8, color: '#666' }
        })

        console.log('全局符号:', globalSymbols)

        // 为每个函数创建作用域节点
        const functionSymbols = visualizationData.symbols.filter(s => s.type === 'function')
        console.log('函数符号:', functionSymbols)

        functionSymbols.forEach((func, index) => {
          const funcScopeId = `scope_function_${func.name}`
          nodes.push({
            id: funcScopeId,
            label: currentViewState.showNodeLabels ? `函数: ${func.name}` : '',
            title: `函数作用域: ${func.name}\n行号: ${func.line || 'N/A'}\n参数: ${func.details?.args?.join(', ') || '无'}`,
            shape: 'ellipse',
            color: {
              background: '#4CAF50',
              border: '#388E3C',
              highlight: { background: '#66BB6A', border: '#388E3C' }
            },
            font: { size: 12, color: '#fff' },
            level: 2,
            mass: 1,
            size: currentViewState.nodeSize || 18,
            nodeType: 'function_scope',
            symbolInfo: func
          })

          edges.push({
            id: `edge_global_func_${func.name}`,
            from: globalScopeId,
            to: funcScopeId,
            color: { color: '#666' },
            label: currentViewState.showEdgeLabels ? '定义' : '',
            font: { size: 8, color: '#666' }
          })

          // 函数参数节点
          if (func.details?.args && func.details.args.length > 0) {
            func.details.args.forEach((arg: string, argIndex: number) => {
              const argNodeId = `arg_${func.name}_${arg}`
              nodes.push({
                id: argNodeId,
                label: currentViewState.showNodeLabels ? `参数: ${arg}` : '',
                title: `函数参数: ${arg}\n所属函数: ${func.name}`,
                shape: 'dot',
                color: {
                  background: '#81C784',
                  border: '#4CAF50',
                  highlight: { background: '#A5D6A7', border: '#4CAF50' }
                },
                font: { size: 10, color: '#333' },
                level: 3,
                size: (currentViewState.nodeSize || 20) * 0.7,
                nodeType: 'parameter',
                symbolInfo: { name: arg, type: 'parameter', functionName: func.name }
              })

              edges.push({
                id: `edge_func_arg_${func.name}_${arg}`,
                from: funcScopeId,
                to: argNodeId,
                color: { color: '#aaa' },
                label: currentViewState.showEdgeLabels ? '参数' : '',
                font: { size: 6, color: '#888' }
              })
            })
          }
        })

        // 为每个类创建作用域节点
        const classSymbols = visualizationData.symbols.filter(s => s.type === 'class')
        console.log('类符号:', classSymbols)

        classSymbols.forEach((cls, index) => {
          const classScopeId = `scope_class_${cls.name}`
          nodes.push({
            id: classScopeId,
            label: currentViewState.showNodeLabels ? `类: ${cls.name}` : '',
            title: `类作用域: ${cls.name}\n行号: ${cls.line || 'N/A'}`,
            shape: 'diamond',
            color: {
              background: '#FF9800',
              border: '#F57C00',
              highlight: { background: '#FFB74D', border: '#F57C00' }
            },
            font: { size: 12, color: '#fff' },
            level: 2,
            mass: 1,
            size: currentViewState.nodeSize || 18,
            nodeType: 'class_scope',
            symbolInfo: cls
          })

          edges.push({
            id: `edge_global_class_${cls.name}`,
            from: globalScopeId,
            to: classScopeId,
            color: { color: '#666' },
            label: currentViewState.showEdgeLabels ? '定义' : '',
            font: { size: 8, color: '#666' }
          })
        })

        // 全局变量和导入节点
        const globalVariables = visualizationData.symbols.filter(s => 
          (s.type === 'variable' || s.type === 'import') && (s.scope === 'global' || !s.scope)
        )
        console.log('全局变量和导入:', globalVariables)

        globalVariables.forEach((symbol) => {
          const symbolNodeId = `global_${symbol.type}_${symbol.name}`
          nodes.push({
            id: symbolNodeId,
            label: currentViewState.showNodeLabels ? `${symbol.name}` : '',
            title: `${getTypeLabel(symbol.type)}: ${symbol.name}${symbol.line ? ` (第${symbol.line}行)` : ''}`,
            shape: getSymbolShape(symbol.type),
            color: {
              background: getSymbolColor(symbol.type),
              border: getDarkerColor(getSymbolColor(symbol.type)),
              highlight: { 
                background: getLighterColor(getSymbolColor(symbol.type)), 
                border: getDarkerColor(getSymbolColor(symbol.type)) 
              }
            },
            font: { size: 10, color: '#333' },
            level: 2,
            size: (currentViewState.nodeSize || 20) * 0.8,
            nodeType: 'global_symbol',
            symbolInfo: symbol
          })

          edges.push({
            id: `edge_global_symbol_${symbol.name}`,
            from: globalScopeId,
            to: symbolNodeId,
            color: { color: '#aaa' },
            label: currentViewState.showEdgeLabels ? symbol.type : '',
            font: { size: 6, color: '#888' }
          })
        })

        // 打印节点的level信息用于调试
        console.log('节点level信息:', nodes.map(n => ({ id: n.id, label: n.label, level: n.level })))

        const visNodes = new (DataSet as any)(nodes)
        const visEdges = new (DataSet as any)(edges)

        // vis.js网络配置
        const options = {
          layout: {
            hierarchical: {
              enabled: currentViewState.layoutType === 'hierarchical',
              direction: 'UD',
              sortMethod: 'directed',
              nodeSpacing: 150,
              levelSeparation: 100,
              treeSpacing: 200
            }
          },
          physics: {
            enabled: currentViewState.layoutType !== 'hierarchical',
            stabilization: {
              enabled: currentViewState.layoutType !== 'hierarchical',
              iterations: 100
            }
          },
          nodes: {
            chosen: {
              node: (values: any, id: any, selected: any, hovering: any) => {
                if (hovering) {
                  values.borderWidth = 3
                  values.borderColor = '#FFD54F'
                }
                if (selected) {
                  values.borderWidth = 4
                  values.borderColor = '#FF6F00'
                }
              }
            }
          },
          edges: {
            chosen: {
              edge: (values: any, id: any, selected: any, hovering: any) => {
                if (hovering || selected) {
                  values.color = '#FF6F00'
                  values.width = 3
                }
              }
            }
          },
          interaction: {
            hover: true,
            hoverConnectedEdges: true,
            selectConnectedEdges: true,
            zoomView: true,
            dragView: true,
            dragNodes: currentViewState.layoutType !== 'hierarchical',
            multiselect: false,
            navigationButtons: true
          }
        }

        // 创建网络
        networkRef.current = new (Network as any)(containerRef.current, { nodes: visNodes, edges: visEdges }, options)

        // 网络事件处理
        networkRef.current.on('click', (params: any) => {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0]
            const node = nodes.find(n => n.id === nodeId)
            if (node) {
              setSelectedNode(node)
              setShowDetails(true)
              console.log('选中符号表节点:', node)
            }
          } else {
            setSelectedNode(null)
            setShowDetails(false)
          }
          // 保存选择状态
          setTimeout(saveViewState, 100)
        })

        networkRef.current.on('dragEnd', () => {
          // 拖拽结束后保存位置
          setTimeout(saveViewState, 100)
        })

        networkRef.current.on('zoom', () => {
          // 缩放后保存状态
          setTimeout(saveViewState, 200)
        })

        // 网络稳定后的处理
        networkRef.current.once('afterDrawing', () => {
          setTimeout(() => {
            if (networkRef.current) {
              // 如果有初始视图状态，恢复它；否则自适应
              if (initialViewState?.position && initialViewState?.scale) {
                restoreViewState()
              } else {
                networkRef.current.fit({
                  animation: {
                    duration: 1000,
                    easingFunction: 'easeInOutQuart'
                  }
                })
              }
            }
          }, 100)
        })

        setLoading(false)

      } catch (err) {
        console.error('符号表可视化初始化失败:', err)
        setError(`符号表可视化加载失败: ${(err as Error).message}`)
        setLoading(false)
      }
    }

    initNetwork()

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy()
        networkRef.current = null
      }
    }
  }, [visualizationData, currentViewState.layoutType, currentViewState.showNodeLabels, currentViewState.showEdgeLabels, currentViewState.nodeSize, initialViewState])

  // 视图控制函数
  const toggleNodeLabels = () => {
    const newState = { ...currentViewState, showNodeLabels: !currentViewState.showNodeLabels }
    setCurrentViewState(newState)
  }

  const toggleEdgeLabels = () => {
    const newState = { ...currentViewState, showEdgeLabels: !currentViewState.showEdgeLabels }
    setCurrentViewState(newState)
  }

  const changeLayout = (layoutType: 'hierarchical' | 'force' | 'circular') => {
    const newState = { ...currentViewState, layoutType }
    setCurrentViewState(newState)
  }

  const changeNodeSize = (nodeSize: number) => {
    const newState = { ...currentViewState, nodeSize }
    setCurrentViewState(newState)
  }

  const resetView = () => {
    if (networkRef.current) {
      networkRef.current.fit({
        animation: {
          duration: 1000,
          easingFunction: 'easeInOutQuart'
        }
      })
      setTimeout(saveViewState, 500)
    }
  }

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'function': '函数',
      'class': '类',
      'variable': '变量',
      'import': '导入',
      'parameter': '参数',
      'method': '方法'
    }
    return labels[type] || type
  }

  const getSymbolColor = (type: string) => {
    const colors: Record<string, string> = {
      'variable': '#E91E63',
      'import': '#795548'
    }
    return colors[type] || '#9E9E9E'
  }

  const getLighterColor = (color: string) => {
    const colorMap: Record<string, string> = {
      '#E91E63': '#F8BBD9',
      '#795548': '#D7CCC8'
    }
    return colorMap[color] || '#E0E0E0'
  }

  const getDarkerColor = (color: string) => {
    const colorMap: Record<string, string> = {
      '#E91E63': '#AD1457',
      '#795548': '#5D4037'
    }
    return colorMap[color] || '#666666'
  }

  const getSymbolShape = (type: string) => {
    const shapes: Record<string, string> = {
      'variable': 'circle',
      'import': 'square'
    }
    return shapes[type] || 'circle'
  }

  const renderNodeDetails = () => {
    if (!selectedNode) return null

    const { nodeType, symbolInfo, scopeInfo } = selectedNode

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-96 overflow-y-auto">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              {selectedNode.label}
            </h3>
            <button
              onClick={() => setShowDetails(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          {nodeType === 'scope' && scopeInfo && (
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium text-gray-600">作用域类型: </span>
                <span className="text-sm">{scopeInfo.type}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">符号数量: </span>
                <span className="text-sm">{scopeInfo.symbols.length}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">包含符号:</span>
                <div className="mt-2 space-y-1">
                  {scopeInfo.symbols.map((symbol: SymbolData, index: number) => (
                    <div key={index} className="text-xs bg-gray-100 p-2 rounded">
                      <span className="font-medium">{symbol.name}</span>
                      <span className="text-gray-600 ml-2">({getTypeLabel(symbol.type)})</span>
                      {symbol.line && <span className="text-gray-500 ml-2">第{symbol.line}行</span>}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {symbolInfo && (
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium text-gray-600">名称: </span>
                <span className="text-sm">{symbolInfo.name}</span>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">类型: </span>
                <span className="text-sm">{getTypeLabel(symbolInfo.type)}</span>
              </div>
              {symbolInfo.line && (
                <div>
                  <span className="text-sm font-medium text-gray-600">行号: </span>
                  <span className="text-sm">{symbolInfo.line}</span>
                </div>
              )}
              {symbolInfo.details && (
                <div className="space-y-2">
                  <span className="text-sm font-medium text-gray-600">详细信息:</span>
                  <div className="text-xs bg-gray-100 p-2 rounded">
                    <pre>{JSON.stringify(symbolInfo.details, null, 2)}</pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="h-96 border border-gray-300 rounded flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p>加载符号表可视化中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-96 border border-gray-300 rounded flex items-center justify-center bg-red-50">
        <div className="text-center text-red-500">
          <p>{error}</p>
          <p className="text-sm mt-2">请确保vis-network库已正确安装</p>
        </div>
      </div>
    )
  }

  if (!visualizationData || !visualizationData.symbols || visualizationData.symbols.length === 0) {
    return (
      <div className="h-96 border border-gray-300 rounded flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <p>暂无符号表数据</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 控制面板 */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-semibold text-gray-800">符号表可视化</h3>
          <div className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded">
            符号: {visualizationData.symbols.length} | 
            函数: {visualizationData.symbols.filter(s => s.type === 'function').length} | 
            类: {visualizationData.symbols.filter(s => s.type === 'class').length}
          </div>
        </div>
        
        {/* 视图控制 */}
        <div className="flex flex-wrap gap-4 items-center mb-4">
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">布局:</label>
            <select 
              value={currentViewState.layoutType} 
              onChange={(e) => changeLayout(e.target.value as any)}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="hierarchical">层次化</option>
              <option value="force">力导向</option>
              <option value="circular">环形</option>
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">节点大小:</label>
            <input
              type="range"
              min="10"
              max="40"
              value={currentViewState.nodeSize || 20}
              onChange={(e) => changeNodeSize(parseInt(e.target.value))}
              className="w-16"
            />
            <span className="text-sm text-gray-500">{currentViewState.nodeSize || 20}</span>
          </div>

          <button
            onClick={toggleNodeLabels}
            className={`text-sm px-3 py-1 rounded ${
              currentViewState.showNodeLabels 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            节点标签
          </button>

          <button
            onClick={toggleEdgeLabels}
            className={`text-sm px-3 py-1 rounded ${
              currentViewState.showEdgeLabels 
                ? 'bg-blue-100 text-blue-700' 
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            边标签
          </button>

          <button
            onClick={resetView}
            className="text-sm px-3 py-1 rounded bg-gray-100 text-gray-600 hover:bg-gray-200"
          >
            重置视图
          </button>
        </div>

        {/* 图例 */}
        <div className="flex flex-wrap gap-4 text-xs">
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-purple-600 mr-1"></div>
            <span>Python模块</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-blue-500 mr-1"></div>
            <span>全局作用域</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-green-500 mr-1"></div>
            <span>函数作用域 ({visualizationData.symbols.filter(s => s.type === 'function').length})</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-orange-500 mr-1" style={{transform: 'rotate(45deg)'}}></div>
            <span>类作用域 ({visualizationData.symbols.filter(s => s.type === 'class').length})</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 rounded-full bg-pink-500 mr-1"></div>
            <span>变量 ({visualizationData.symbols.filter(s => s.type === 'variable').length})</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-yellow-700 mr-1"></div>
            <span>导入 ({visualizationData.symbols.filter(s => s.type === 'import').length})</span>
          </div>
        </div>
      </div>
      
      {/* 可视化容器 */}
      <div 
        ref={containerRef} 
        className="border border-gray-300 rounded-lg bg-white shadow-sm"
        style={{ height: '500px', minHeight: '500px' }}
      />
      
      {/* 操作提示 */}
      <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
        <div className="flex justify-between">
          <span>💡 操作提示: 滚轮缩放 | 拖拽平移 | 悬停查看详情 | 点击查看节点详情</span>
          <span>📊 {currentViewState.layoutType === 'hierarchical' ? '层次化符号表布局' : '交互式符号表布局'}</span>
        </div>
      </div>

      {showDetails && renderNodeDetails()}
    </div>
  )
}

export default SimpleSymbolTableVisualizer 