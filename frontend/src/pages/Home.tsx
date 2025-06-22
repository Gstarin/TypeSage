import { Link } from 'react-router-dom'
import { Brain, Code, Database, Network, ArrowRight, CheckCircle } from 'lucide-react'

const Home = () => {
  const features = [
    {
      title: 'Python类型推导',
      description: '基于代码上下文和大模型推理进行智能类型推导',
      icon: Brain,
      color: 'text-blue-600',
      bgColor: 'bg-blue-100'
    },
    {
      title: '代码类型标注',
      description: '自动为代码添加合适的类型标注，提升代码质量',
      icon: Code,
      color: 'text-green-600',
      bgColor: 'bg-green-100'
    },
    {
      title: '语法树可视化',
      description: '展示Python代码的抽象语法树(AST)结构',
      icon: Network,
      color: 'text-purple-600',
      bgColor: 'bg-purple-100'
    },
    {
      title: '半参数化记忆库',
      description: '将模型推理结果存入记忆库供后续复用',
      icon: Database,
      color: 'text-orange-600',
      bgColor: 'bg-orange-100'
    }
  ]

  const highlights = [
    '集成本地Ollama qwen2.5-coder:7b模型',
    '传统类型检查与AI推理结合',
    '智能识别未声明变量类型',
    '可视化AST和符号表结构',
    '记忆库系统提升分析效率'
  ]

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      {/* Hero区域 */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 sm:text-5xl md:text-6xl">
          <span className="block">TypeSage</span>
          <span className="block text-primary-600 text-3xl sm:text-4xl md:text-5xl mt-2">
            大模型驱动的语义分析增强
          </span>
        </h1>
        <p className="mt-6 max-w-3xl mx-auto text-xl text-gray-500">
          在传统类型检查基础上，引入大模型解决复杂上下文推导问题。
          对未声明变量进行智能推测，提供可视化的AST和符号表分析。
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <Link
            to="/analyzer"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 transition-colors"
          >
            开始分析
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
          <Link
            to="/memory"
            className="inline-flex items-center px-6 py-3 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            查看记忆库
          </Link>
        </div>
      </div>

      {/* 功能特性 */}
      <div className="py-12">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">核心功能</h2>
          <p className="mt-4 text-lg text-gray-600">
            结合传统编译技术与现代AI能力
          </p>
        </div>
        
        <div className="mt-12 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => {
            const Icon = feature.icon
            return (
              <div key={feature.title} className="card p-6 text-center">
                <div className={`inline-flex items-center justify-center p-3 rounded-lg ${feature.bgColor} mb-4`}>
                  <Icon className={`h-6 w-6 ${feature.color}`} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>
      </div>

      {/* 技术亮点 */}
      <div className="py-12 bg-gray-50 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900">技术亮点</h2>
            <p className="mt-4 text-lg text-gray-600">
              编译原理与人工智能的完美结合
            </p>
          </div>
          
          <div className="mt-12 grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="card p-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">
                技术特色
              </h3>
              <ul className="space-y-3">
                {highlights.map((highlight, index) => (
                  <li key={index} className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                    <span className="text-gray-700">{highlight}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="card p-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-6">
                技术栈
              </h3>
              <div className="space-y-4">
                <div>
                  <span className="font-medium text-gray-900">前端：</span>
                  <span className="text-gray-700 ml-2">React + TypeScript + Tailwind CSS</span>
                </div>
                <div>
                  <span className="font-medium text-gray-900">后端：</span>
                  <span className="text-gray-700 ml-2">FastAPI + Python 3.10</span>
                </div>
                <div>
                  <span className="font-medium text-gray-900">数据库：</span>
                  <span className="text-gray-700 ml-2">SQLite3</span>
                </div>
                <div>
                  <span className="font-medium text-gray-900">AI模型：</span>
                  <span className="text-gray-700 ml-2">Ollama + qwen2.5-coder:7b</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 使用流程 */}
      <div className="py-12">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">使用流程</h2>
          <p className="mt-4 text-lg text-gray-600">
            简单三步，完成代码分析
          </p>
        </div>
        
        <div className="mt-12 max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary-600 text-white font-bold text-lg mb-4">
                1
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                输入代码
              </h3>
              <p className="text-gray-600">
                在代码编辑器中输入或粘贴Python代码
              </p>
            </div>
            
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary-600 text-white font-bold text-lg mb-4">
                2
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                AI分析
              </h3>
              <p className="text-gray-600">
                系统自动进行AST解析、符号表构建和类型推导
              </p>
            </div>
            
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-primary-600 text-white font-bold text-lg mb-4">
                3
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                查看结果
              </h3>
              <p className="text-gray-600">
                获得详细的分析报告和可视化结果
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Home 