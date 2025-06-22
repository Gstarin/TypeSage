from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from ..database import (
    get_memory_patterns, get_type_inference_history,
    get_analysis_record
)

logger = logging.getLogger(__name__)

router = APIRouter()

class MemoryPattern(BaseModel):
    id: int
    pattern_hash: str
    code_pattern: str
    inferred_types: Dict[str, Any]
    confidence_score: float
    usage_count: int
    created_at: str
    last_used: str

class TypeInferenceRecord(BaseModel):
    id: int
    variable_name: str
    context_code: str
    traditional_type: Optional[str]
    llm_inferred_type: Optional[str]
    final_type: Optional[str]
    confidence: float
    validation_result: str
    created_at: str

@router.get("/patterns", response_model=List[MemoryPattern])
async def get_memory_patterns_api():
    """获取所有记忆库模式"""
    try:
        patterns = get_memory_patterns()
        return [MemoryPattern(**pattern) for pattern in patterns]
    except Exception as e:
        logger.error(f"获取记忆库模式失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取记忆库模式失败: {str(e)}")

@router.get("/history", response_model=List[TypeInferenceRecord])
async def get_type_inference_history_api():
    """获取类型推导历史"""
    try:
        history = get_type_inference_history()
        return [TypeInferenceRecord(**record) for record in history]
    except Exception as e:
        logger.error(f"获取类型推导历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取类型推导历史失败: {str(e)}")

@router.get("/statistics")
async def get_memory_statistics():
    """获取记忆库统计信息"""
    try:
        patterns = get_memory_patterns()
        history = get_type_inference_history()
        
        # 计算统计信息
        total_patterns = len(patterns)
        total_inferences = len(history)
        
        # 最常用的模式
        most_used_patterns = sorted(patterns, key=lambda x: x['usage_count'], reverse=True)[:5]
        
        # 置信度分布
        confidence_distribution = {
            "high": len([p for p in patterns if p['confidence_score'] >= 0.8]),
            "medium": len([p for p in patterns if 0.5 <= p['confidence_score'] < 0.8]),
            "low": len([p for p in patterns if p['confidence_score'] < 0.5])
        }
        
        # 类型推导成功率
        successful_inferences = len([h for h in history if h['validation_result'] == 'llm_inferred'])
        success_rate = successful_inferences / total_inferences if total_inferences > 0 else 0
        
        return {
            "success": True,
            "statistics": {
                "total_patterns": total_patterns,
                "total_inferences": total_inferences,
                "success_rate": success_rate,
                "confidence_distribution": confidence_distribution,
                "most_used_patterns": [
                    {
                        "pattern": p['code_pattern'],
                        "usage_count": p['usage_count'],
                        "confidence": p['confidence_score']
                    }
                    for p in most_used_patterns
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"获取记忆库统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取记忆库统计信息失败: {str(e)}")

@router.get("/search")
async def search_memory_patterns(query: str = "", confidence_min: float = 0.0):
    """搜索记忆库模式"""
    try:
        patterns = get_memory_patterns()
        
        # 过滤模式
        filtered_patterns = []
        for pattern in patterns:
            # 按置信度过滤
            if pattern['confidence_score'] < confidence_min:
                continue
            
            # 按查询字符串过滤
            if query and query.lower() not in pattern['code_pattern'].lower():
                continue
            
            filtered_patterns.append(pattern)
        
        return {
            "success": True,
            "patterns": filtered_patterns,
            "total_found": len(filtered_patterns)
        }
        
    except Exception as e:
        logger.error(f"搜索记忆库模式失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索记忆库模式失败: {str(e)}")

@router.get("/analysis-cache")
async def get_analysis_cache_info():
    """获取分析缓存信息"""
    try:
        # 这里可以添加缓存统计逻辑
        # 由于我们使用简单的数据库存储，这里返回基本信息
        
        return {
            "success": True,
            "cache_info": {
                "description": "使用SQLite数据库存储分析结果",
                "storage_type": "persistent",
                "features": [
                    "代码哈希去重",
                    "AST数据缓存", 
                    "符号表缓存",
                    "LLM推理结果缓存"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"获取分析缓存信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取分析缓存信息失败: {str(e)}")

@router.get("/export")
async def export_memory_data():
    """导出记忆库数据"""
    try:
        patterns = get_memory_patterns()
        history = get_type_inference_history()
        
        export_data = {
            "export_time": "2024-01-01T00:00:00Z",  # 实际时间应该从datetime获取
            "version": "1.0",
            "data": {
                "memory_patterns": patterns,
                "type_inference_history": history
            },
            "metadata": {
                "total_patterns": len(patterns),
                "total_history_records": len(history)
            }
        }
        
        return {
            "success": True,
            "export_data": export_data
        }
        
    except Exception as e:
        logger.error(f"导出记忆库数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出记忆库数据失败: {str(e)}") 