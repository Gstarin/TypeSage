import { useState, useEffect } from 'react'
import { Database, Search, Download, TrendingUp, Clock, Hash } from 'lucide-react'
import { memoryAPI } from '../services/api'

const Memory = () => {
  const [patterns, setPatterns] = useState([])
  const [history, setHistory] = useState([])
  const [statistics, setStatistics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [confidenceFilter, setConfidenceFilter] = useState(0.0)
  const [activeTab, setActiveTab] = useState<'patterns' | 'history' | 'stats'>('patterns')

  useEffect(() => {
    loadMemoryData()
  }, [])

  const loadMemoryData = async () => {
    try {
      setLoading(true)
      const [patternsRes, historyRes, statsRes] = await Promise.all([
        memoryAPI.getPatterns(),
        memoryAPI.getHistory(),
        memoryAPI.getStatistics()
      ])
      
      setPatterns(patternsRes)
      setHistory(historyRes)
      setStatistics(statsRes.statistics)
    } catch (error) {
      console.error('加载记忆库数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    try {
      const result = await memoryAPI.searchPatterns(searchQuery, confidenceFilter)
      setPatterns(result.patterns)
    } catch (error) {
      console.error('搜索失败:', error)
    }
  }

  const handleExport = async () => {
    try {
      const result = await memoryAPI.exportData()
      const blob = new Blob([JSON.stringify(result.export_data, null, 2)], {
        type: 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'typesage_memory_export.json'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('导出失败:', error)
    }
  }

  if (loading) {
    return (
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center h-64">
          <Database className="w-8 h-8 animate-pulse text-primary-600" />
          <span className="ml-2 text-gray-600">加载记忆库数据中...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">记忆库</h1>
            <p className="mt-2 text-gray-600">
              半参数化系统的模式存储和类型推导历史
            </p>
          </div>
          <button
            onClick={handleExport}
            className="btn-secondary flex items-center"
          >
            <Download className="w-4 h-4 mr-2" />
            导出数据
          </button>
        </div>
      </div>

      {/* 简化的内容显示 */}
      <div className="space-y-6">
        <div className="card p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">记忆库概览</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">{patterns.length}</div>
              <div className="text-sm text-gray-600">记忆模式</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{history.length}</div>
              <div className="text-sm text-gray-600">推导历史</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-purple-600">85%</div>
              <div className="text-sm text-gray-600">平均置信度</div>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">功能说明</h3>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <Hash className="w-5 h-5 text-blue-500 mt-0.5" />
              <div>
                <h4 className="font-medium text-gray-900">记忆模式</h4>
                <p className="text-sm text-gray-600">存储代码模式和对应的类型推断结果，支持模式匹配和复用</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Clock className="w-5 h-5 text-green-500 mt-0.5" />
              <div>
                <h4 className="font-medium text-gray-900">推导历史</h4>
                <p className="text-sm text-gray-600">记录每次类型推导的过程和结果，包括传统分析和AI推断的对比</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <TrendingUp className="w-5 h-5 text-purple-500 mt-0.5" />
              <div>
                <h4 className="font-medium text-gray-900">统计分析</h4>
                <p className="text-sm text-gray-600">分析系统性能，包括推导成功率、置信度分布等指标</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Memory 