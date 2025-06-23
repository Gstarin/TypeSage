import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Editor from '@monaco-editor/react'
import { Play, Download, Eye, Settings, AlertCircle, CheckCircle, Clock, Database, FileText, Code } from 'lucide-react'
import toast from 'react-hot-toast'
import { analysisAPI, CodeAnalysisRequest, CodeAnalysisResponse } from '../services/api'
import CacheManager from '../components/CacheManager'
import { AnalyzerStateManager, AnalyzerState } from '../utils/storage'
import type { editor } from 'monaco-editor'

interface AnalysisResult {
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

interface TypeAnnotationResult {
  success: boolean
  code_hash: string
  original_code: string
  annotated_code: string
  type_info: any
  annotations_count: number
  llm_suggestions_used: boolean
  error?: string
}

const Analyzer = () => {
  const stateManager = new AnalyzerStateManager()
  const navigate = useNavigate()
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null)

  // 从存储恢复初始状态
  const initialState = stateManager.restoreState()
  
  const [code, setCode] = useState(initialState?.code || '')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isGeneratingAnnotations, setIsGeneratingAnnotations] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(initialState?.analysisResult || null)
  const [annotationResult, setAnnotationResult] = useState<TypeAnnotationResult | null>(null)
  const [useLLM, setUseLLM] = useState(initialState?.settings?.useLLM ?? true)
  const [saveToMemory, setSaveToMemory] = useState(initialState?.settings?.saveToMemory ?? true)
  const [useCache, setUseCache] = useState(initialState?.settings?.useCache ?? true)
  const [showCacheManager, setShowCacheManager] = useState(false)
  const [showAnnotatedCode, setShowAnnotatedCode] = useState(false)

  // 自动保存状态
  const saveCurrentState = () => {
    const currentState: AnalyzerState = {
      code,
      settings: {
        useLLM,
        saveToMemory,
        useCache
      },
      analysisResult
    }
    stateManager.saveState(currentState)
  }

  // 定期保存状态
  useEffect(() => {
    const timeoutId = setTimeout(saveCurrentState, 1000)
    return () => clearTimeout(timeoutId)
  }, [code, useLLM, saveToMemory, useCache, analysisResult])

  // 页面卸载时保存状态
  useEffect(() => {
    const handleBeforeUnload = () => saveCurrentState()
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
      saveCurrentState()
    }
  }, [code, useLLM, saveToMemory, useCache, analysisResult])

  // 显示状态恢复提示
  useEffect(() => {
    const lastSavedText = stateManager.getLastSavedTimeText()
    if (lastSavedText && analysisResult) {
      toast.success(`已恢复${lastSavedText}的代码和分析结果`)
    }
  }, [])

  const handleCodeChange = (value: string | undefined) => {
    const newCode = value || ''
    setCode(newCode)
    
    // 如果代码发生实质性改变，清除分析结果
    if (analysisResult && newCode.trim() !== code.trim()) {
      setAnalysisResult(null)
      stateManager.clearAnalysisResult()
    }
  }

  const handleAnalyze = async () => {
    if (!code.trim()) {
      toast.error('请输入要分析的代码')
      return
    }

    setIsAnalyzing(true)
    
    try {
      const request: CodeAnalysisRequest = {
        code: code,
        use_llm: useLLM,
        save_to_memory: saveToMemory,
        use_cache: useCache
      }
      
      const result = await analysisAPI.analyzeCode(request)
      setAnalysisResult(result)
      
      if (result.success) {
        toast.success(result.cached ? '从缓存获取分析结果' : 'AI分析完成')
      } else {
        toast.error(result.error || '分析失败')
      }
    } catch (error) {
      console.error('分析错误:', error)
      toast.error('分析服务暂时不可用，请检查后端服务和Ollama是否正常运行')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleGenerateAnnotations = async () => {
    if (!code.trim()) {
      toast.error('请输入要分析的代码')
      return
    }

    setIsGeneratingAnnotations(true)
    try {
      const result = await analysisAPI.generateTypeAnnotations({
        code,
        use_llm: useLLM,
        use_cache: useCache
      })
      setAnnotationResult(result)
      setShowAnnotatedCode(true)
      
      // 显示缓存状态提示
      if (result.success) {
        if (result.cached) {
          toast.success('从缓存获取类型注解结果')
        } else {
          toast.success('类型注解生成完成')
        }
      } else {
        toast.error(result.error || '类型注解生成失败')
      }
    } catch (error) {
      console.error('生成类型注解失败:', error)
      toast.error('生成类型注解失败，请检查网络连接和后端服务')
    } finally {
      setIsGeneratingAnnotations(false)
    }
  }

  const handleApplyAnnotations = () => {
    if (annotationResult?.annotated_code) {
      setCode(annotationResult.annotated_code)
      setShowAnnotatedCode(false)
      setAnnotationResult(null)
    }
  }

  const handleVisualize = () => {
    if (analysisResult?.code_hash) {
      navigate(`/visualization/${analysisResult.code_hash}`)
    }
  }

  const handleExportResult = () => {
    if (analysisResult) {
      const blob = new Blob([JSON.stringify(analysisResult, null, 2)], {
        type: 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `analysis_${analysisResult.code_hash}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('分析结果已导出')
    }
  }

  const handleClearAll = () => {
    if (window.confirm('确定要清除所有数据吗？这将删除当前代码、分析结果和设置。')) {
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
      
      setCode(defaultCode)
      setAnalysisResult(null)
      setAnnotationResult(null)
      setUseLLM(true)
      setSaveToMemory(true)
      setUseCache(true)
      stateManager.clearAll()
      toast.success('已清除所有数据')
    }
  }

  // 设置项变化处理函数
  const handleUseLLMChange = (checked: boolean) => {
    setUseLLM(checked)
  }

  const handleSaveToMemoryChange = (checked: boolean) => {
    setSaveToMemory(checked)
  }

  const handleUseCacheChange = (checked: boolean) => {
    setUseCache(checked)
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">代码分析</h1>
            <p className="mt-2 text-gray-600">
              输入Python代码，系统将进行AST解析、符号表构建和AI驱动的类型推导
            </p>
          </div>
          
          {/* 状态指示器和清除按钮 */}
          <div className="flex items-center space-x-3">
            {analysisResult && (
              <div className="flex items-center space-x-2 text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full">
                <CheckCircle className="w-4 h-4" />
                <span>已保存状态</span>
              </div>
            )}
            <button
              onClick={handleClearAll}
              className="text-sm text-gray-500 hover:text-red-600 px-3 py-1 rounded border border-gray-300 hover:border-red-300"
            >
              清除数据
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：代码编辑器 */}
        <div className="space-y-4">
          <div className="card p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">代码编辑器</h2>
              <div className="flex items-center space-x-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={useLLM}
                    onChange={(e) => handleUseLLMChange(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">启用AI分析</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={saveToMemory}
                    onChange={(e) => handleSaveToMemoryChange(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">保存到记忆库</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={useCache}
                    onChange={(e) => handleUseCacheChange(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm text-gray-700">使用缓存</span>
                </label>
              </div>
            </div>
            
            <div className="border rounded-lg overflow-hidden">
              <Editor
                height="500px"
                defaultLanguage="python"
                value={code}
                onChange={handleCodeChange}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  lineNumbers: 'on',
                  wordWrap: 'on',
                  automaticLayout: true
                }}
                onMount={(editor) => {
                  editorRef.current = editor
                }}
              />
            </div>
            
            <div className="flex justify-between mt-4">
              <div className="flex space-x-2">
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  className="btn-primary flex items-center"
                >
                  {isAnalyzing ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      分析中...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      开始分析
                    </>
                  )}
                </button>
                
                <button
                  onClick={handleGenerateAnnotations}
                  disabled={isGeneratingAnnotations}
                  className="btn-secondary flex items-center"
                >
                  {isGeneratingAnnotations ? (
                    <>
                      <Clock className="w-4 h-4 mr-2 animate-spin" />
                      生成中...
                    </>
                  ) : (
                    <>
                      <Code className="w-4 h-4 mr-2" />
                      类型标注
                    </>
                  )}
                </button>
                
                {analysisResult && (
                  <>
                    <button
                      onClick={handleVisualize}
                      className="btn-secondary flex items-center"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      可视化
                    </button>
                    
                    <button
                      onClick={handleExportResult}
                      className="btn-secondary flex items-center"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      导出
                    </button>
                  </>
                )}
              </div>
              
              <button
                onClick={() => setShowCacheManager(!showCacheManager)}
                className={`flex items-center px-4 py-2 rounded-lg border transition-colors ${
                  showCacheManager 
                    ? 'bg-blue-50 border-blue-300 text-blue-700' 
                    : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Database className="w-4 h-4 mr-2" />
                {showCacheManager ? '隐藏缓存管理' : '缓存管理'}
              </button>
            </div>
          </div>
        </div>

        {/* 右侧：分析结果 */}
        <div className="space-y-4">
          {analysisResult ? (
            <>
              {/* 分析状态 */}
              <div className="card p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">分析状态</h3>
                  <div className="flex items-center">
                    {analysisResult.success ? (
                      <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                    ) : (
                      <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                    )}
                    <span className={`text-sm ${analysisResult.success ? 'text-green-600' : 'text-red-600'}`}>
                      {analysisResult.success ? '分析成功' : '分析失败'}
                    </span>
                  </div>
                </div>
                
                {analysisResult.cached && (
                  <div className="mt-2 text-sm text-blue-600">
                    ⚡ 从缓存中获取结果
                  </div>
                )}
                
                {analysisResult.error && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                    {analysisResult.error}
                  </div>
                )}
              </div>

              {/* 未声明变量 */}
              {analysisResult.undeclared_variables && analysisResult.undeclared_variables.length > 0 && (
                <div className="card p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">未声明变量</h3>
                  <div className="space-y-2">
                    {analysisResult.undeclared_variables.map((variable, index) => (
                      <div key={index} className="flex justify-between items-center p-2 bg-yellow-50 border border-yellow-200 rounded">
                        <span className="font-mono text-sm">{variable.name}</span>
                        <span className="text-xs text-gray-500">第{variable.lineno}行</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI推理结果 */}
              {analysisResult.llm_suggestions?.type_inference && (
                <div className="card p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">AI类型推导</h3>
                  {analysisResult.llm_suggestions.type_inference.success ? (
                    <div className="space-y-3">
                      {Object.entries(analysisResult.llm_suggestions.type_inference.inferences || {}).map(([varName, type]) => (
                        <div key={varName} className="border-l-4 border-blue-500 pl-3">
                          <div className="font-mono text-sm font-semibold">{varName}</div>
                          <div className="text-sm text-gray-600">推断类型: <code className="bg-gray-100 px-1 rounded">{type as string}</code></div>
                          {analysisResult.llm_suggestions.type_inference.explanations?.[varName] && (
                            <div className="text-xs text-gray-500 mt-1">
                              {analysisResult.llm_suggestions.type_inference.explanations[varName]}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-red-600">
                      AI推理失败: {analysisResult.llm_suggestions.type_inference.error}
                    </div>
                  )}
                </div>
              )}

              {/* 符号表摘要 */}
              {analysisResult.symbol_table && (
                <div className="card p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">符号表摘要</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">函数: </span>
                      <span className="font-semibold">{Object.keys(analysisResult.symbol_table.functions || {}).length}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">变量: </span>
                      <span className="font-semibold">{Object.keys(analysisResult.symbol_table.variables || {}).length}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">类: </span>
                      <span className="font-semibold">{Object.keys(analysisResult.symbol_table.classes || {}).length}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">导入: </span>
                      <span className="font-semibold">{Object.keys(analysisResult.symbol_table.imports || {}).length}</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="card p-8 text-center text-gray-500">
              <Settings className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>点击"开始分析"按钮来分析你的Python代码</p>
              <p className="text-sm mt-2">系统将自动进行AST解析、符号表构建和AI类型推导</p>
            </div>
          )}
        </div>
      </div>

      {/* 缓存管理器 */}
      {showCacheManager && (
        <div className="mb-6">
          <CacheManager />
        </div>
      )}

      {/* 类型注解结果弹窗 */}
      {showAnnotatedCode && annotationResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">类型注解结果</h2>
                <button
                  onClick={() => setShowAnnotatedCode(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              {annotationResult.success ? (
                <div className="mt-2 text-sm text-gray-600">
                  成功为 {annotationResult.annotations_count} 个函数/变量添加了类型注解
                  {annotationResult.llm_suggestions_used && (
                    <span className="ml-2 text-blue-600">• 使用了AI智能推断</span>
                  )}
                </div>
              ) : (
                <div className="mt-2 text-sm text-red-600">
                  类型注解生成失败: {annotationResult.error}
                </div>
              )}
            </div>
            
            {annotationResult.success && (
              <div className="p-6 max-h-[calc(90vh-200px)] overflow-y-auto">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* 原始代码 */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-3">原始代码</h3>
                    <div className="border rounded-lg overflow-hidden">
                      <Editor
                        height="400px"
                        defaultLanguage="python"
                        value={annotationResult.original_code}
                        theme="vs-dark"
                        options={{
                          readOnly: true,
                          minimap: { enabled: false },
                          fontSize: 12,
                          lineNumbers: 'on'
                        }}
                      />
                    </div>
                  </div>
                  
                  {/* 带注解的代码 */}
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-3">类型注解后的代码</h3>
                    <div className="border rounded-lg overflow-hidden">
                      <Editor
                        height="400px"
                        defaultLanguage="python"
                        value={annotationResult.annotated_code}
                        theme="vs-dark"
                        options={{
                          readOnly: true,
                          minimap: { enabled: false },
                          fontSize: 12,
                          lineNumbers: 'on'
                        }}
                      />
                    </div>
                  </div>
                </div>
                
                {/* 类型信息摘要 */}
                <div className="mt-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">类型信息摘要</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* 变量类型 */}
                    {annotationResult.type_info?.variables && 
                     Object.keys(annotationResult.type_info.variables).length > 0 && (
                      <div className="card p-4">
                        <h4 className="font-medium text-gray-900 mb-2">变量类型</h4>
                        <div className="space-y-2">
                          {Object.entries(annotationResult.type_info.variables).map(([varName, varInfo]: [string, any]) => (
                            <div key={varName} className="flex justify-between items-center">
                              <code className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                                {varName}
                              </code>
                              <span className="text-sm text-blue-600 font-medium">
                                {varInfo.type}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* 函数类型 */}
                    {annotationResult.type_info?.functions && 
                     Object.keys(annotationResult.type_info.functions).length > 0 && (
                      <div className="card p-4">
                        <h4 className="font-medium text-gray-900 mb-2">函数类型</h4>
                        <div className="space-y-3">
                          {Object.entries(annotationResult.type_info.functions).map(([funcName, funcInfo]: [string, any]) => (
                            <div key={funcName} className="border-l-4 border-blue-500 pl-3">
                              <div className="font-mono text-sm font-medium">{funcName}</div>
                              <div className="text-xs text-gray-600 mt-1">
                                参数: {Object.entries(funcInfo.params).map(([param, type]) => 
                                  `${param}: ${type}`
                                ).join(', ') || '无'}
                              </div>
                              <div className="text-xs text-gray-600">
                                返回值: <span className="text-blue-600">{funcInfo.return}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
            
            <div className="p-6 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowAnnotatedCode(false)}
                className="btn-secondary"
              >
                取消
              </button>
              {annotationResult.success && (
                <button
                  onClick={handleApplyAnnotations}
                  className="btn-primary"
                >
                  应用类型注解
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Analyzer 