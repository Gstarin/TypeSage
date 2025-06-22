import { useEffect, useRef, useState } from 'react'
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'
import { VisualizationViewState } from '../utils/storage'

interface ASTNode {
  id: string
  label: string
  type: string
  line?: number
  col?: number
  level?: number
}

interface ASTEdge {
  from: string
  to: string
}

interface SimpleASTVisualizerProps {
  nodes: ASTNode[]
  edges: Array<{ from: string; to: string }>
  initialViewState?: VisualizationViewState
  onViewStateChange?: (viewState: VisualizationViewState) => void
}

const SimpleASTVisualizer = ({ 
  nodes, 
  edges, 
  initialViewState,
  onViewStateChange
}: SimpleASTVisualizerProps) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const networkRef = useRef<any>(null) // 保存网络实例的引用
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [stats, setStats] = useState({ nodeCount: 0, edgeCount: 0, maxDepth: 0 })
  const [currentViewState, setCurrentViewState] = useState<VisualizationViewState>({
    showNodeLabels: true,
    showEdgeLabels: false,
    layoutType: 'hierarchical',
    nodeSize: 20,
    selectedNodes: [],
    ...initialViewState
  })

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
      console.warn('保存AST视图状态失败:', error)
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
      console.warn('恢复AST视图状态失败:', error)
    }
  }

  useEffect(() => {
    const initTreeVisualization = async () => {
      if (!containerRef.current || !nodes || !edges || nodes.length === 0) {
        setLoading(false)
        return
      }

      try {
        // 如果已有网络实例，先销毁它
        if (networkRef.current) {
          networkRef.current.destroy()
          networkRef.current = null
        }

        // 计算统计信息并验证level数据
        const maxDepth = Math.max(...nodes.map(node => node.level || 0))
        const levelDistribution = nodes.reduce((acc, node) => {
          const level = node.level ?? 0
          acc[level] = (acc[level] || 0) + 1
          return acc
        }, {} as Record<number, number>)
        
        console.log('AST Level分布:', levelDistribution)
        console.log('节点level信息:', nodes.map(n => ({ id: n.id, type: n.type, level: n.level })))
        
        setStats({ 
          nodeCount: nodes.length, 
          edgeCount: edges.length,
          maxDepth: maxDepth
        })

        // 处理节点数据 - 优化树形显示并确保level正确传递
        const processedNodes = nodes.map((node, index) => {
          const nodeType = node.type
          const nodeLevel = node.level ?? 0  // 确保level不为undefined
          
          // 根据节点类型定义颜色和形状
          const getNodeStyle = (type: string) => {
            const styles = {
              Module: { 
                color: { background: '#2E7D32', border: '#1B5E20' }, 
                shape: 'box',
                size: currentViewState.nodeSize || 25,
                font: { size: 16, color: 'white', face: 'Arial Black' }
              },
              FunctionDef: { 
                color: { background: '#1565C0', border: '#0D47A1' }, 
                shape: 'ellipse',
                size: currentViewState.nodeSize || 20,
                font: { size: 14, color: 'white', face: 'Arial' }
              },
              ClassDef: { 
                color: { background: '#6A1B9A', border: '#4A148C' }, 
                shape: 'diamond',
                size: currentViewState.nodeSize || 20,
                font: { size: 14, color: 'white', face: 'Arial' }
              },
              If: { 
                color: { background: '#EF6C00', border: '#E65100' }, 
                shape: 'triangle',
                size: currentViewState.nodeSize || 18,
                font: { size: 12, color: 'white', face: 'Arial' }
              },
              For: { 
                color: { background: '#C62828', border: '#B71C1C' }, 
                shape: 'triangle',
                size: currentViewState.nodeSize || 18,
                font: { size: 12, color: 'white', face: 'Arial' }
              },
              While: { 
                color: { background: '#C62828', border: '#B71C1C' }, 
                shape: 'triangle',
                size: currentViewState.nodeSize || 18,
                font: { size: 12, color: 'white', face: 'Arial' }
              },
              Assign: { 
                color: { background: '#4E342E', border: '#3E2723' }, 
                shape: 'box',
                size: currentViewState.nodeSize || 16,
                font: { size: 11, color: 'white', face: 'Arial' }
              },
              Name: { 
                color: { background: '#37474F', border: '#263238' }, 
                shape: 'circle',
                size: currentViewState.nodeSize || 14,
                font: { size: 10, color: 'white', face: 'Arial' }
              },
              Constant: { 
                color: { background: '#00838F', border: '#006064' }, 
                shape: 'square',
                size: currentViewState.nodeSize || 14,
                font: { size: 10, color: 'white', face: 'Arial' }
              },
              BinOp: { 
                color: { background: '#558B2F', border: '#33691E' }, 
                shape: 'dot',
                size: currentViewState.nodeSize || 16,
                font: { size: 11, color: 'white', face: 'Arial' }
              },
              Call: { 
                color: { background: '#283593', border: '#1A237E' }, 
                shape: 'ellipse',
                size: currentViewState.nodeSize || 16,
                font: { size: 11, color: 'white', face: 'Arial' }
              },
              Return: { 
                color: { background: '#4527A0', border: '#311B92' }, 
                shape: 'box',
                size: currentViewState.nodeSize || 16,
                font: { size: 11, color: 'white', face: 'Arial' }
              }
            }
            
            return styles[type as keyof typeof styles] || {
              color: { background: '#616161', border: '#424242' },
              shape: 'circle',
              size: currentViewState.nodeSize || 14,
              font: { size: 10, color: 'white', face: 'Arial' }
            }
          }

          const style = getNodeStyle(nodeType)
          
          // 简化标签显示
          let displayLabel = node.label
          if (displayLabel.length > 15) {
            displayLabel = displayLabel.substring(0, 12) + '...'
          }

          return {
            id: node.id,
            label: currentViewState.showNodeLabels ? displayLabel : '',
            title: `类型: ${nodeType}\n完整标签: ${node.label}\n行号: ${node.line || 'N/A'}\n层级: ${nodeLevel}`,
            ...style,
            level: nodeLevel,  // 明确使用处理过的level值
            margin: 8,
            borderWidth: 2,
            borderWidthSelected: 4,
            chosen: {
              node: true,
              label: false
            },
            // 添加调试信息
            x: undefined,  // 让vis.js自动计算位置
            y: undefined,  // 让vis.js自动计算位置
            fixed: false   // 允许自动布局
          }
        })

        // 处理边数据 - 优化连线显示
        const processedEdges = edges.map((edge, index) => ({
          id: `edge_${index}`,
          from: edge.from,
          to: edge.to,
          arrows: { 
            to: { 
              enabled: true, 
              scaleFactor: 0.8,
              type: 'arrow'
            } 
          },
          color: { 
            color: '#424242', 
            highlight: '#1976D2', 
            hover: '#1976D2',
            opacity: 0.8
          },
          width: 2,
          smooth: { 
            type: 'cubicBezier', 
            forceDirection: 'vertical', 
            roundness: 0.2 
          },
          length: 100,
          label: currentViewState.showEdgeLabels ? edge.from + '→' + edge.to : '',
          font: { size: 8, color: '#666' }
        }))

        // 创建数据集
        const visNodes = new (DataSet as any)(processedNodes)
        const visEdges = new (DataSet as any)(processedEdges)

        // vis.js 网络配置 - 强制使用level信息进行层次化布局
        const options = {
          layout: {
            hierarchical: {
              enabled: currentViewState.layoutType === 'hierarchical',
              direction: 'UD',        // 从上到下 (Up-Down)
              sortMethod: 'directed', // 使用有向图算法
              levelSeparation: 150,   // 增加层级间的垂直距离
              nodeSpacing: 200,       // 增加同层节点间的水平距离
              treeSpacing: 300,       // 增加不同树之间的距离
              blockShifting: true,    // 允许块移动以减少边的交叉
              edgeMinimization: true, // 最小化边的长度
              parentCentralization: true, // 父节点相对于子节点居中
              shakeTowards: 'roots'   // 摇摆方向朝向根节点
            }
          },
          physics: {
            enabled: currentViewState.layoutType !== 'hierarchical',  // 层次化布局时禁用物理引擎
            stabilization: {
              enabled: currentViewState.layoutType !== 'hierarchical'
            }
          },
          nodes: {
            chosen: {
              node: (values: any, id: any, selected: any, hovering: any) => {
                if (hovering) {
                  values.borderWidth = 4
                  values.borderColor = '#FFD54F'
                }
                if (selected) {
                  values.borderWidth = 5
                  values.borderColor = '#FF6F00'
                }
              }
            },
            heightConstraint: {
              minimum: 40,
              valign: 'middle'
            },
            widthConstraint: {
              minimum: 60,
              maximum: 200
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
            },
            hoverWidth: 3,
            selectionWidth: 4
          },
          interaction: {
            hover: true,
            hoverConnectedEdges: true,
            selectConnectedEdges: true,
            zoomView: true,
            dragView: true,
            dragNodes: currentViewState.layoutType !== 'hierarchical',  // 层次化布局时禁止拖拽节点
            multiselect: false,
            navigationButtons: true,
            keyboard: {
              enabled: true,
              speed: { x: 10, y: 10, zoom: 0.02 }
            }
          },
          configure: {
            enabled: false
          }
        }

        // 创建网络
        networkRef.current = new (Network as any)(
          containerRef.current,
          { nodes: visNodes, edges: visEdges },
          options
        )

        // 网络事件处理
        networkRef.current.on('click', (params: any) => {
          if (params.nodes.length > 0) {
            const nodeId = params.nodes[0]
            const node = nodes.find(n => n.id === nodeId)
            if (node) {
              console.log('选中节点:', node)
            }
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

        networkRef.current.on('hoverNode', () => {
          if (containerRef.current) {
            containerRef.current.style.cursor = 'pointer'
          }
        })

        networkRef.current.on('blurNode', () => {
          if (containerRef.current) {
            containerRef.current.style.cursor = 'default'
          }
        })

        // 网络稳定后自适应视图
        networkRef.current.once('afterDrawing', () => {
          setTimeout(() => {
            if (networkRef.current) {
              // 如果有初始视图状态，恢复它；否则自适应
              if (initialViewState?.position && initialViewState?.scale) {
                restoreViewState()
              } else {
                networkRef.current.fit({
                  animation: {
                    duration: 1500,
                    easingFunction: 'easeInOutQuart'
                  }
                })
              }
            }
          }, 100)
        })

        setLoading(false)

      } catch (err) {
        console.error('AST树形可视化初始化失败:', err)
        setError(`可视化组件加载失败: ${(err as Error).message}`)
        setLoading(false)
      }
    }

    initTreeVisualization()

    // 清理函数：组件卸载时销毁网络实例
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy()
        networkRef.current = null
      }
    }
  }, [nodes, edges, currentViewState.layoutType, currentViewState.showNodeLabels, currentViewState.showEdgeLabels, currentViewState.nodeSize, initialViewState])

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

  if (loading) {
    return (
      <div className="h-96 border border-gray-300 rounded flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50">
        <div className="text-center text-gray-600">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-3"></div>
          <p className="font-medium">正在构建AST树形结构...</p>
          <p className="text-sm mt-1">解析语法节点和层级关系</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-96 border border-red-300 rounded flex items-center justify-center bg-red-50">
        <div className="text-center text-red-600 max-w-md">
          <div className="text-red-500 mb-2">
            <svg className="w-8 h-8 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <p className="font-semibold mb-2">AST可视化加载失败</p>
          <p className="text-sm mb-2">{error}</p>
          <p className="text-xs">请确保vis-network库已正确安装并重新尝试</p>
        </div>
      </div>
    )
  }

  if (!nodes || nodes.length === 0) {
    return (
      <div className="h-96 border border-gray-300 rounded flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <div className="text-gray-400 mb-3">
            <svg className="w-12 h-12 mx-auto" fill="currentColor" viewBox="0 0 20 20">
              <path d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" />
            </svg>
          </div>
          <p className="font-medium mb-1">暂无AST数据</p>
          <p className="text-sm">请在代码分析页面输入代码并进行分析</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 信息栏和控制面板 */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex justify-between items-start mb-3">
          <h3 className="text-lg font-semibold text-gray-800">抽象语法树结构</h3>
          <div className="text-sm text-gray-600 bg-gray-100 px-3 py-1 rounded">
            节点: {stats.nodeCount} | 连接: {stats.edgeCount} | 最大深度: {stats.maxDepth}
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
            <div className="w-4 h-3 bg-green-700 mr-2 rounded"></div>
            <span>模块/根节点</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-3 bg-blue-700 rounded-full mr-2"></div>
            <span>函数定义</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-purple-700 mr-2" style={{transform: 'rotate(45deg)'}}></div>
            <span>类定义</span>
          </div>
          <div className="flex items-center">
            <div className="w-0 h-0 border-l-2 border-r-2 border-b-3 border-transparent border-b-orange-600 mr-2"></div>
            <span>控制流</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-gray-600 mr-2 rounded"></div>
            <span>表达式/其他</span>
          </div>
        </div>
      </div>

      {/* AST可视化容器 */}
      <div 
        ref={containerRef} 
        className="border border-gray-300 rounded-lg bg-white shadow-sm"
        style={{ height: '500px', minHeight: '500px' }}
      />
      
      {/* 操作提示 */}
      <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
        <div className="flex justify-between">
          <span>💡 操作提示: 滚轮缩放 | 拖拽平移 | 悬停查看详情 | 点击选择节点</span>
          <span>🌳 {currentViewState.layoutType === 'hierarchical' ? '层次化树形布局' : '交互式布局'} - 根节点在顶部</span>
        </div>
      </div>
    </div>
  )
}

export default SimpleASTVisualizer 