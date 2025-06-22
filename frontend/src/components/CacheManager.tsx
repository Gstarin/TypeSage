import { useState, useEffect } from 'react'
import { Trash2, Database, BarChart3, RefreshCw, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import { analysisAPI } from '../services/api'

interface CacheStats {
  success: boolean
  cache_stats: {
    analysis_records: number
    inference_history: number
    memory_patterns: number
    type_annotations: number
    total_entries: number
  }
  recent_records: Array<{
    code_hash: string
    created_at: string
    type: 'analysis' | 'annotation'
  }>
}

const CacheManager = () => {
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isClearing, setIsClearing] = useState(false)

  const fetchCacheStats = async () => {
    setIsLoading(true)
    try {
      const response = await analysisAPI.cache.getStats()
      setStats(response)
    } catch (error) {
      console.error('获取缓存统计失败:', error)
      toast.error('获取缓存统计失败')
    } finally {
      setIsLoading(false)
    }
  }

  const handleClearAllCache = async () => {
    if (!window.confirm('确定要清除所有缓存吗？这将删除所有分析记录、类型推导历史和记忆库模式。')) {
      return
    }

    setIsClearing(true)
    try {
      const response = await analysisAPI.cache.clearAll()
      if (response.success) {
        toast.success(`缓存清除成功！共清除 ${response.details.total_cleared} 条记录`)
        // 刷新统计信息
        await fetchCacheStats()
      } else {
        toast.error('清除缓存失败')
      }
    } catch (error) {
      console.error('清除缓存失败:', error)
      toast.error('清除缓存失败')
    } finally {
      setIsClearing(false)
    }
  }

  const handleClearSpecificCache = async (codeHash: string) => {
    if (!window.confirm(`确定要清除代码 ${codeHash.substring(0, 8)}... 的缓存吗？`)) {
      return
    }

    try {
      const response = await analysisAPI.cache.clearSpecific(codeHash)
      if (response.success) {
        toast.success(response.message)
        // 刷新统计信息
        await fetchCacheStats()
      } else {
        toast.error('清除特定缓存失败')
      }
    } catch (error) {
      console.error('清除特定缓存失败:', error)
      toast.error('清除特定缓存失败')
    }
  }

  useEffect(() => {
    fetchCacheStats()
  }, [])

  if (isLoading && !stats) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-600">加载缓存统计中...</span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 缓存统计卡片 */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center">
            <Database className="w-6 h-6 text-blue-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">缓存统计</h2>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={fetchCacheStats}
              disabled={isLoading}
              className="btn-secondary flex items-center"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              刷新
            </button>
            <button
              onClick={handleClearAllCache}
              disabled={isClearing}
              className="btn-danger flex items-center"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {isClearing ? '清除中...' : '清除所有缓存'}
            </button>
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center">
                <Database className="w-8 h-8 text-blue-600 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-blue-900">{stats.cache_stats.analysis_records}</div>
                  <div className="text-sm text-blue-600">分析记录</div>
                </div>
              </div>
            </div>
            
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <BarChart3 className="w-8 h-8 text-green-600 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-green-900">{stats.cache_stats.inference_history}</div>
                  <div className="text-sm text-green-600">推导历史</div>
                </div>
              </div>
            </div>
            
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="flex items-center">
                <Database className="w-8 h-8 text-purple-600 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-purple-900">{stats.cache_stats.memory_patterns}</div>
                  <div className="text-sm text-purple-600">记忆模式</div>
                </div>
              </div>
            </div>
            
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <div className="flex items-center">
                <BarChart3 className="w-8 h-8 text-orange-600 mr-3" />
                <div>
                  <div className="text-2xl font-bold text-orange-900">{stats.cache_stats.type_annotations}</div>
                  <div className="text-sm text-orange-600">类型注解</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 最近记录 */}
      {stats && stats.recent_records.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">最近记录</h3>
          <div className="space-y-2">
            {stats.recent_records.map((record, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-3 ${
                    record.type === 'analysis' ? 'bg-blue-500' : 'bg-orange-500'
                  }`}></div>
                  <div>
                    <code className="text-sm font-mono text-gray-700">
                      {record.code_hash.substring(0, 8)}...
                    </code>
                    <div className="text-xs text-gray-500">
                      {record.type === 'analysis' ? '分析记录' : '类型注解'} • {record.created_at}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => handleClearSpecificCache(record.code_hash)}
                  className="text-red-600 hover:text-red-800 p-1"
                  title="清除此记录"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 缓存说明 */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start">
          <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
          <div className="text-sm text-yellow-800">
            <h4 className="font-medium mb-2">缓存机制说明</h4>
            <ul className="space-y-1 text-xs">
              <li>• <strong>分析记录</strong>: 存储完整的代码分析结果，包括AST、符号表和AI建议</li>
              <li>• <strong>推导历史</strong>: 记录AI类型推导的历史，用于模型优化</li>
              <li>• <strong>记忆模式</strong>: 提取的代码模式，用于提升后续分析的准确性</li>
              <li>• <strong>类型注解</strong>: 缓存生成的类型注解结果，避免重复计算相同代码</li>
              <li>• 相同代码的重复分析会直接使用缓存结果，大幅提升响应速度</li>
              <li>• 取消勾选"使用缓存"可强制重新分析，不使用缓存数据</li>
              <li>• 类型注解缓存会区分是否使用AI分析，确保结果的准确性</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CacheManager 