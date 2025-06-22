from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import hashlib
import logging

from ..core.analyzer import ASTAnalyzer, TypeInferrer, generate_code_hash, extract_code_patterns
from ..core.llm_client import llm_client
from ..database import (
    save_analysis_record, get_analysis_record, 
    save_memory_pattern, save_type_inference_history,
    save_type_annotation_cache, get_type_annotation_cache,
    db
)

logger = logging.getLogger(__name__)

router = APIRouter()

class CodeAnalysisRequest(BaseModel):
    code: str
    use_llm: bool = True
    save_to_memory: bool = True
    use_cache: bool = True  # 新增：是否使用缓存

class CodeAnalysisResponse(BaseModel):
    success: bool
    code_hash: str
    ast_data: Optional[Dict[str, Any]] = None
    symbol_table: Optional[Dict[str, Any]] = None
    undeclared_variables: Optional[List[Dict[str, Any]]] = None
    llm_suggestions: Optional[Dict[str, Any]] = None
    type_annotations: Optional[Dict[str, Any]] = None
    code_quality: Optional[Dict[str, Any]] = None
    cached: bool = False
    error: Optional[str] = None

@router.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """分析Python代码"""
    try:
        code_hash = generate_code_hash(request.code)
        
        # 检查缓存（仅在启用缓存时）
        if request.use_cache:
            cached_result = get_analysis_record(code_hash)
            if cached_result:
                logger.info(f"从缓存中获取分析结果: {code_hash}")
                return CodeAnalysisResponse(
                    success=True,
                    code_hash=code_hash,
                    ast_data=cached_result["ast_data"],
                    symbol_table=cached_result["symbol_table"],
                    undeclared_variables=cached_result["type_inference"].get("undeclared_variables", []),
                    llm_suggestions=cached_result["llm_suggestions"],
                    cached=True
                )
        else:
            logger.info(f"跳过缓存，重新分析代码: {code_hash}")
        
        # 执行AST分析
        analyzer = ASTAnalyzer()
        ast_result = analyzer.analyze(request.code)
        
        if not ast_result["success"]:
            return CodeAnalysisResponse(
                success=False,
                code_hash=code_hash,
                error=ast_result["error"]
            )
        
        # 分析未声明变量
        type_inferrer = TypeInferrer()
        undeclared_vars = type_inferrer.analyze_undeclared_variables(
            request.code, ast_result["symbol_table"]
        )
        
        type_inference_result = {
            "undeclared_variables": undeclared_vars,
            "patterns": extract_code_patterns(request.code)
        }
        
        llm_suggestions = {}
        type_annotations = {}
        code_quality = {}
        
        # 如果启用了LLM分析
        if request.use_llm:
            try:
                # 推断未声明变量类型
                if undeclared_vars:
                    type_inference = await llm_client.infer_variable_types(
                        request.code, undeclared_vars
                    )
                    llm_suggestions["type_inference"] = type_inference
                    
                    # 保存类型推导历史
                    if type_inference.get("success") and request.save_to_memory:
                        for var_name, inferred_type in type_inference.get("inferences", {}).items():
                            save_type_inference_history(
                                var_name, request.code, "unknown", inferred_type,
                                inferred_type, type_inference.get("confidence", {}).get(var_name, 0.5),
                                "llm_inferred"
                            )
                
                # 建议类型注解
                annotations = await llm_client.suggest_type_annotations(
                    request.code, ast_result["symbol_table"]
                )
                type_annotations = annotations
                
                # 分析代码质量
                quality = await llm_client.analyze_code_quality(request.code)
                code_quality = quality
                
                llm_suggestions.update({
                    "type_annotations": annotations,
                    "code_quality": quality
                })
                
            except Exception as e:
                logger.error(f"LLM分析失败: {str(e)}")
                llm_suggestions["error"] = f"LLM分析失败: {str(e)}"
        
        # 保存到数据库
        try:
            save_analysis_record(
                code_hash, request.code, ast_result["ast"],
                ast_result["symbol_table"], type_inference_result, llm_suggestions
            )
            
            # 保存到记忆库
            if request.save_to_memory and type_inference_result.get("patterns"):
                for pattern in type_inference_result["patterns"]:
                    pattern_hash = hashlib.md5(pattern.encode('utf-8')).hexdigest()
                    save_memory_pattern(
                        pattern_hash, pattern,
                        llm_suggestions.get("type_inference", {}).get("inferences", {}),
                        0.8  # 默认置信度
                    )
        except Exception as e:
            logger.error(f"保存分析结果失败: {str(e)}")
        
        return CodeAnalysisResponse(
            success=True,
            code_hash=code_hash,
            ast_data=ast_result["ast"],
            symbol_table=ast_result["symbol_table"],
            undeclared_variables=undeclared_vars,
            llm_suggestions=llm_suggestions,
            type_annotations=type_annotations,
            code_quality=code_quality,
            cached=False
        )
        
    except Exception as e:
        logger.error(f"代码分析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"代码分析失败: {str(e)}")

@router.get("/status")
async def get_analysis_status():
    """获取分析服务状态"""
    try:
        # 检查Ollama状态
        ollama_status = await llm_client.check_ollama_status()
        
        return {
            "success": True,
            "services": {
                "ast_analyzer": True,
                "symbol_table_builder": True,
                "type_inferrer": True,
                "ollama": ollama_status.get("available", False),
                "database": True
            },
            "ollama_details": ollama_status
        }
        
    except Exception as e:
        logger.error(f"获取服务状态失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "services": {
                "ast_analyzer": True,
                "symbol_table_builder": True,
                "type_inferrer": True,
                "ollama": False,
                "database": True
            }
        }

@router.get("/ast/{code_hash}")
async def get_ast_visualization(code_hash: str):
    """获取AST可视化数据"""
    try:
        record = get_analysis_record(code_hash)
        if not record:
            raise HTTPException(status_code=404, detail="分析记录不存在")
        
        ast_data = record["ast_data"]
        
        # 转换为可视化格式 - 重新设计确保level正确设置
        node_counter = [0]  # 使用列表以便在嵌套函数中修改
        
        def convert_for_visualization(node, parent_id=None, depth=0):
            """
            递归转换AST节点为可视化格式
            
            Args:
                node: AST节点
                parent_id: 父节点ID
                depth: 当前深度/层级
                
            Returns:
                (nodes, edges): 节点列表和边列表
            """
            if not isinstance(node, dict) or depth > 20:  # 防止过深的递归
                return [], []
            
            nodes = []
            edges = []
            
            # 生成唯一ID - 使用全局计数器确保唯一性
            node_type = node.get('node_type', 'Unknown')
            node_counter[0] += 1
            node_id = f"node_{node_counter[0]}"  # 简化ID生成，确保绝对唯一
            
            # 优化节点标签显示
            node_label = node_type
            
            # 为特定节点类型添加更多信息
            if node_type == 'Name' and 'id' in node:
                node_label = f"Name: {node['id']}"
            elif node_type == 'Constant' and 'value' in node:
                value_str = str(node['value'])
                if len(value_str) > 15:
                    value_str = value_str[:12] + "..."
                node_label = f"Const: {value_str}"
            elif node_type == 'FunctionDef' and 'name' in node:
                node_label = f"Func: {node['name']}"
            elif node_type == 'ClassDef' and 'name' in node:
                node_label = f"Class: {node['name']}"
            elif node_type == 'BinOp':
                op_type = node.get('op', {}).get('node_type', '')
                if op_type:
                    node_label = f"BinOp: {op_type}"
            elif node_type == 'Call' and 'func' in node:
                func_info = node['func']
                if isinstance(func_info, dict) and func_info.get('node_type') == 'Name':
                    node_label = f"Call: {func_info.get('id', 'func')}"
            elif node_type == 'Attribute' and 'attr' in node:
                node_label = f"Attr: {node['attr']}"
            elif node_type == 'Assign' and 'targets' in node:
                targets = node['targets']
                if targets and isinstance(targets[0], dict) and targets[0].get('node_type') == 'Name':
                    node_label = f"Assign: {targets[0].get('id', 'var')}"
            
            # 创建当前节点
            current_node = {
                "id": node_id,
                "label": node_label,
                "type": node_type,
                "line": node.get("lineno"),
                "col": node.get("col_offset"),
                "level": depth,  # 明确设置层级
                "parent_id": parent_id
            }
            nodes.append(current_node)
            
            # 添加边（父子关系）
            if parent_id:
                edges.append({
                    "from": parent_id,
                    "to": node_id,
                    "id": f"edge_{parent_id}_to_{node_id}"
                })
            
            # 处理子节点 - 按照AST的重要字段顺序
            child_depth = depth + 1
            important_fields = [
                'body', 'orelse', 'finalbody',  # 代码块
                'left', 'right', 'op',          # 二元操作
                'test', 'comparators', 'ops',   # 比较和测试
                'targets', 'value',             # 赋值
                'func', 'args', 'keywords',     # 函数调用
                'iter', 'target',               # 循环
                'elts', 'keys', 'values',       # 容器类型
                'name', 'bases', 'decorator_list'  # 定义类型
            ]
            
            # 首先处理重要字段
            for field_name in important_fields:
                if field_name in node:
                    field_value = node[field_name]
                    child_nodes, child_edges = process_ast_field(
                        field_name, field_value, node_id, child_depth
                    )
                    nodes.extend(child_nodes)
                    edges.extend(child_edges)
            
            # 然后处理其他字段
            other_fields = [field for field in node.keys() 
                          if field not in important_fields 
                          and field not in ["node_type", "lineno", "col_offset", "end_lineno", "end_col_offset"]]
            
            for field_name in other_fields:
                field_value = node[field_name]
                child_nodes, child_edges = process_ast_field(
                    field_name, field_value, node_id, child_depth
                )
                nodes.extend(child_nodes)
                edges.extend(child_edges)
            
            return nodes, edges
        
        def process_ast_field(field_name, field_value, parent_id, depth):
            """处理AST字段，生成子节点"""
            nodes = []
            edges = []
            
            if isinstance(field_value, list):
                # 处理列表类型的字段
                for i, item in enumerate(field_value):
                    if isinstance(item, dict) and "node_type" in item:
                        child_nodes, child_edges = convert_for_visualization(
                            item, parent_id, depth
                        )
                        nodes.extend(child_nodes)
                        edges.extend(child_edges)
            elif isinstance(field_value, dict) and "node_type" in field_value:
                # 处理单个AST节点
                child_nodes, child_edges = convert_for_visualization(
                    field_value, parent_id, depth
                )
                nodes.extend(child_nodes)
                edges.extend(child_edges)
            
            return nodes, edges
        
        nodes, edges = convert_for_visualization(ast_data)
        
        return {
            "success": True,
            "nodes": nodes,
            "edges": edges,
            "original_code": record["original_code"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取AST可视化数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取AST可视化数据失败: {str(e)}")

@router.get("/symbol-table/{code_hash}")
async def get_symbol_table_visualization(code_hash: str):
    """获取符号表可视化数据"""
    try:
        record = get_analysis_record(code_hash)
        if not record:
            raise HTTPException(status_code=404, detail="分析记录不存在")
        
        symbol_table = record["symbol_table"]
        
        # 转换为可视化格式
        visualization_data = {
            "scopes": [],
            "symbols": [],
            "relationships": []
        }
        
        # 全局作用域
        global_scope = symbol_table.get("global_scope", {})
        if global_scope:
            visualization_data["scopes"].append({
                "id": "global",
                "name": "全局作用域",
                "type": "global",
                "symbols": list(global_scope.keys())
            })
        
        # 函数
        functions = symbol_table.get("functions", {})
        for func_name, func_info in functions.items():
            visualization_data["symbols"].append({
                "id": f"func_{func_name}",
                "name": func_name,
                "type": "function",
                "scope": "global",
                "line": func_info.get("lineno"),
                "details": func_info
            })
        
        # 类
        classes = symbol_table.get("classes", {})
        for class_name, class_info in classes.items():
            visualization_data["symbols"].append({
                "id": f"class_{class_name}",
                "name": class_name,
                "type": "class",
                "scope": "global",
                "line": class_info.get("lineno"),
                "details": class_info
            })
        
        # 变量
        variables = symbol_table.get("variables", {})
        for var_name, var_info in variables.items():
            visualization_data["symbols"].append({
                "id": f"var_{var_name}",
                "name": var_name,
                "type": "variable",
                "scope": f"scope_{var_info.get('scope', 0)}",
                "line": var_info.get("lineno"),
                "details": var_info
            })
        
        # 导入
        imports = symbol_table.get("imports", {})
        for import_name, import_info in imports.items():
            visualization_data["symbols"].append({
                "id": f"import_{import_name}",
                "name": import_name,
                "type": "import",
                "scope": "global",
                "line": import_info.get("lineno"),
                "details": import_info
            })
        
        return {
            "success": True,
            "visualization_data": visualization_data,
            "original_code": record["original_code"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取符号表可视化数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取符号表可视化数据失败: {str(e)}")

@router.delete("/cache")
async def clear_all_cache():
    """清除所有分析缓存"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 清除分析记录表
        cursor.execute("DELETE FROM analysis_records")
        analysis_count = cursor.rowcount
        
        # 清除类型推导历史表  
        cursor.execute("DELETE FROM type_inference_history")
        inference_count = cursor.rowcount
        
        # 清除记忆库模式表
        cursor.execute("DELETE FROM memory_store")
        memory_count = cursor.rowcount
        
        # 清除类型注解缓存表
        cursor.execute("DELETE FROM type_annotation_cache")
        annotation_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"清除缓存完成 - 分析记录: {analysis_count}, 推导历史: {inference_count}, 记忆模式: {memory_count}, 类型注解: {annotation_count}")
        
        return {
            "success": True,
            "message": "缓存清除成功",
            "details": {
                "analysis_records_cleared": analysis_count,
                "inference_history_cleared": inference_count,
                "memory_patterns_cleared": memory_count,
                "type_annotations_cleared": annotation_count,
                "total_cleared": analysis_count + inference_count + memory_count + annotation_count
            }
        }
        
    except Exception as e:
        logger.error(f"清除缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")

@router.delete("/cache/{code_hash}")
async def clear_specific_cache(code_hash: str):
    """清除特定代码的缓存"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 清除特定代码的分析记录
        cursor.execute("DELETE FROM analysis_records WHERE code_hash = ?", (code_hash,))
        analysis_count = cursor.rowcount
        
        # 清除特定代码的类型注解缓存
        cursor.execute("DELETE FROM type_annotation_cache WHERE code_hash = ?", (code_hash,))
        annotation_count = cursor.rowcount
        
        total_cleared = analysis_count + annotation_count
        
        if total_cleared == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="未找到指定的缓存记录")
        
        conn.commit()
        conn.close()
        
        logger.info(f"清除特定缓存完成 - 代码哈希: {code_hash}, 分析记录: {analysis_count}, 类型注解: {annotation_count}")
        
        return {
            "success": True,
            "message": f"已清除代码 {code_hash[:8]}... 的缓存",
            "code_hash": code_hash,
            "details": {
                "analysis_records_cleared": analysis_count,
                "type_annotations_cleared": annotation_count,
                "total_cleared": total_cleared
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除特定缓存失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清除特定缓存失败: {str(e)}")

@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # 统计分析记录
        cursor.execute("SELECT COUNT(*) FROM analysis_records")
        analysis_count = cursor.fetchone()[0]
        
        # 统计类型推导历史
        cursor.execute("SELECT COUNT(*) FROM type_inference_history")
        inference_count = cursor.fetchone()[0]
        
        # 统计记忆库模式
        cursor.execute("SELECT COUNT(*) FROM memory_store")
        memory_count = cursor.fetchone()[0]
        
        # 统计类型注解缓存
        cursor.execute("SELECT COUNT(*) FROM type_annotation_cache")
        annotation_count = cursor.fetchone()[0]
        
        # 获取最近的分析记录
        cursor.execute("""
            SELECT code_hash, created_at 
            FROM analysis_records 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        recent_records = [
            {"code_hash": row[0], "created_at": row[1], "type": "analysis"} 
            for row in cursor.fetchall()
        ]
        
        # 获取最近的类型注解记录
        cursor.execute("""
            SELECT code_hash, created_at 
            FROM type_annotation_cache 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        recent_annotations = [
            {"code_hash": row[0], "created_at": row[1], "type": "annotation"} 
            for row in cursor.fetchall()
        ]
        
        # 合并最近记录
        all_recent = recent_records + recent_annotations
        all_recent.sort(key=lambda x: x["created_at"], reverse=True)
        all_recent = all_recent[:5]  # 取最近5条
        
        conn.close()
        
        return {
            "success": True,
            "cache_stats": {
                "analysis_records": analysis_count,
                "inference_history": inference_count,
                "memory_patterns": memory_count,
                "type_annotations": annotation_count,
                "total_entries": analysis_count + inference_count + memory_count + annotation_count
            },
            "recent_records": all_recent
        }
        
    except Exception as e:
        logger.error(f"获取缓存统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")

@router.post("/annotate")
async def generate_type_annotations(request: CodeAnalysisRequest):
    """生成带类型注解的代码"""
    try:
        code_hash = generate_code_hash(request.code)
        
        # 检查缓存（仅在启用缓存时）
        if request.use_cache:
            cached_result = get_type_annotation_cache(code_hash, request.use_llm)
            if cached_result:
                logger.info(f"从缓存中获取类型注解结果: {code_hash}")
                return {
                    "success": True,
                    "code_hash": code_hash,
                    "original_code": cached_result["original_code"],
                    "annotated_code": cached_result["annotated_code"],
                    "type_info": cached_result["type_info"],
                    "annotations_count": cached_result["annotations_count"],
                    "llm_suggestions_used": cached_result["llm_suggestions_used"],
                    "cached": True,
                    "cache_time": cached_result["created_at"]
                }
        else:
            logger.info(f"跳过缓存，重新生成类型注解: {code_hash}")
        
        # 首先进行完整分析
        analyzer = ASTAnalyzer()
        ast_result = analyzer.analyze(request.code)
        
        if not ast_result["success"]:
            return {
                "success": False,
                "error": ast_result["error"]
            }
        
        # 获取LLM的类型建议
        type_suggestions = {}
        if request.use_llm:
            try:
                # 分析未声明变量
                type_inferrer = TypeInferrer()
                undeclared_vars = type_inferrer.analyze_undeclared_variables(
                    request.code, ast_result["symbol_table"]
                )
                
                # 获取LLM类型推断
                if undeclared_vars:
                    inference_result = await llm_client.infer_variable_types(
                        request.code, undeclared_vars
                    )
                    if inference_result.get("success"):
                        type_suggestions.update(inference_result)
                
                # 获取类型注解建议
                annotation_result = await llm_client.suggest_type_annotations(
                    request.code, ast_result["symbol_table"]
                )
                if annotation_result.get("success"):
                    # 合并函数类型建议
                    if "function_annotations" in annotation_result:
                        type_suggestions["function_suggestions"] = {}
                        for func_name, func_info in annotation_result["function_annotations"].items():
                            type_suggestions["function_suggestions"][func_name] = {
                                "params": func_info.get("params", {}),
                                "return": func_info.get("return", "None")
                            }
                
            except Exception as e:
                logger.error(f"LLM类型推断失败: {str(e)}")
        
        # 生成类型注解代码
        annotation_result = analyzer.generate_type_annotated_code(request.code, type_suggestions)
        
        if annotation_result["success"]:
            # 保存到缓存
            try:
                save_type_annotation_cache(
                    code_hash=code_hash,
                    original_code=request.code,
                    annotated_code=annotation_result["annotated_code"],
                    type_info=annotation_result["type_info"],
                    annotations_count=annotation_result["annotations_count"],
                    llm_suggestions_used=bool(type_suggestions),
                    use_llm=request.use_llm
                )
                logger.info(f"类型注解结果已保存到缓存: {code_hash}")
            except Exception as e:
                logger.error(f"保存类型注解缓存失败: {str(e)}")
            
            return {
                "success": True,
                "code_hash": code_hash,
                "original_code": request.code,
                "annotated_code": annotation_result["annotated_code"],
                "type_info": annotation_result["type_info"],
                "annotations_count": annotation_result["annotations_count"],
                "llm_suggestions_used": bool(type_suggestions),
                "cached": False
            }
        else:
            return {
                "success": False,
                "error": annotation_result["error"]
            }
            
    except Exception as e:
        logger.error(f"生成类型注解失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成类型注解失败: {str(e)}")