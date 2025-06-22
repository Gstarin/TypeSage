import httpx
import json
from typing import Dict, List, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    """Ollama客户端，用于与本地qwen2.5-coder:7b模型交互"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5-coder:7b"):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def generate_response(self, prompt: str, system_prompt: str = '') -> Dict[str, Any]:
        """生成响应"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 低温度以获得更一致的结果
                    "top_p": 0.9,
                    "max_tokens": 2048
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "content": result.get("message", {}).get("content", ""),
                    "model": result.get("model", self.model),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "content": "",
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            return {
                "success": False,
                "content": "",
                "error": f"连接错误: {str(e)}"
            }
    
    async def infer_variable_types(self, code: str, undeclared_vars: List[Dict[str, Any]]) -> Dict[str, Any]:
        """推断未声明变量的类型"""
        if not undeclared_vars:
            return {"success": True, "inferences": {}, "explanations": {}}
        
        system_prompt = """你是一个Python类型推导专家。请分析给定的代码上下文，为未声明的变量推断最可能的类型。

分析指导原则：
1. 仔细分析变量的使用上下文和模式
2. 考虑函数调用、运算符、方法调用等线索
3. 推断具体的类型注解，使用Python 3.9+的类型注解语法
4. 对于函数参数，分析函数内部如何使用这些参数
5. 对于函数返回值，分析return语句
6. 给出推理置信度(0.0-1.0)和详细解释

类型注解格式要求：
- 使用标准类型：int, float, str, bool, list, dict, set, tuple
- 使用泛型：list[int], dict[str, int], tuple[int, str]
- 使用联合类型：int | float, str | None
- 使用可选类型：Optional[int] 或 int | None

回复格式必须是JSON：
{
    "inferences": {
        "变量名": "推断类型"
    },
    "explanations": {
        "变量名": "详细推理过程"
    },
    "confidence": {
        "变量名": 0.85
    },
    "function_suggestions": {
        "函数名": {
            "params": {"参数名": "类型"},
            "return": "返回类型"
        }
    }
}"""
        
        var_names = [var["name"] for var in undeclared_vars]
        var_lines = [f"- {var['name']} (第{var['lineno']}行)" for var in undeclared_vars]
        
        prompt = f"""请分析以下Python代码，推断未声明变量的类型：

代码：
```python
{code}
```

未声明的变量：
{chr(10).join(var_lines)}

请仔细分析每个变量的使用上下文，给出类型推断、推理解释和置信度。
特别注意：
1. 分析函数参数在函数体内的使用方式
2. 推断函数的返回值类型
3. 考虑变量的赋值、运算、方法调用等使用模式
4. 给出具体的类型注解建议"""
        
        response = await self.generate_response(prompt, system_prompt)
        
        if response["success"]:
            try:
                # 尝试解析JSON响应
                content = response["content"].strip()
                
                # 提取JSON部分
                json_content = self._extract_json_from_response(content)
                
                # 清理JSON内容
                json_content = self._clean_json_content(json_content)
                
                result = json.loads(json_content)
                
                return {
                    "success": True,
                    "inferences": result.get("inferences", {}),
                    "explanations": result.get("explanations", {}),
                    "confidence": result.get("confidence", {}),
                    "function_suggestions": result.get("function_suggestions", {}),
                    "raw_response": content
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}, 原始响应: {response['content']}")
                # 尝试使用正则表达式提取变量和类型
                fallback_result = self._fallback_parse_type_inference(response["content"])
                if fallback_result:
                    return fallback_result
                
                return {
                    "success": False,
                    "error": f"LLM响应格式错误: {str(e)}",
                    "raw_response": response["content"]
                }
        else:
            return response
    
    async def suggest_type_annotations(self, code: str, symbol_table: Dict[str, Any]) -> Dict[str, Any]:
        """为代码中的函数和变量建议类型注解"""
        try:
            # 构建符号表摘要
            functions = symbol_table.get("functions", {})
            variables = symbol_table.get("variables", {})
            
            func_list = []
            for func_name, func_info in functions.items():
                args = func_info.get("args", [])
                func_list.append(f"def {func_name}({', '.join(args)})")
            
            var_list = []
            for var_name, var_info in variables.items():
                if not var_info.get("annotation"):  # 只处理没有类型注解的变量
                    var_list.append(var_name)
            
            prompt = f"""分析以下Python代码，为函数参数、返回值和变量提供类型注解建议：

代码：
```python
{code}
```

需要类型注解的函数：
{chr(10).join(func_list) if func_list else "无"}

需要类型注解的变量：
{', '.join(var_list) if var_list else "无"}

请分析代码并为每个函数和变量提供准确的类型注解建议。

返回JSON格式：
{{
    "success": true,
    "function_annotations": {{
        "函数名": {{
            "params": {{"参数名": "类型"}},
            "return": "返回类型"
        }}
    }},
    "variable_annotations": {{
        "变量名": "类型"
    }},
    "confidence": 0.9
}}

类型注解要求：
1. 使用Python 3.9+的类型提示语法
2. 优先使用具体类型（如list[int]而不是list）
3. 对于联合类型使用|语法（如int | float）
4. 考虑代码的实际使用方式
5. 如果无法确定，使用Any"""

            response = await self.generate_response(prompt)
            
            if response and response.get("success"):
                content = response.get("content", "")
                
                # 尝试解析JSON响应
                try:
                    result = json.loads(content)
                    if isinstance(result, dict) and result.get("success"):
                        return {
                            "success": True,
                            "function_annotations": result.get("function_annotations", {}),
                            "variable_annotations": result.get("variable_annotations", {}),
                            "confidence": result.get("confidence", 0.8)
                        }
                except json.JSONDecodeError:
                    pass
                
                # JSON解析失败，尝试从文本中提取信息
                return {
                    "success": False,
                    "error": "无法解析LLM响应为有效的JSON格式"
                }
            
            return {
                "success": False,
                "error": "LLM服务无响应或响应失败"
            }
            
        except Exception as e:
            logger.error(f"LLM类型注解建议失败: {str(e)}")
            return {
                "success": False,
                "error": f"类型注解建议失败: {str(e)}"
            }
    
    async def analyze_code_quality(self, code: str) -> Dict[str, Any]:
        """分析代码质量和潜在问题"""
        system_prompt = """你是一个Python代码质量分析专家。请分析给定的代码，找出潜在的问题和改进建议。

关注点：
1. 类型安全性
2. 代码风格
3. 潜在的运行时错误
4. 性能问题
5. 最佳实践

回复格式必须是JSON格式：
{
    "issues": [
        {
            "type": "问题类型",
            "line": 行号,
            "message": "问题描述",
            "severity": "严重程度(low/medium/high)"
        }
    ],
    "suggestions": [
        "改进建议"
    ],
    "score": 评分(0-100)
}"""
        
        prompt = f"""请分析以下Python代码的质量：

```python
{code}
```

请找出潜在问题并给出改进建议。"""
        
        response = await self.generate_response(prompt, system_prompt)
        
        if response["success"]:
            try:
                content = response["content"].strip()
                
                # 提取JSON部分
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "{" in content and "}" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
                
                result = json.loads(json_content)
                
                return {
                    "success": True,
                    "issues": result.get("issues", []),
                    "suggestions": result.get("suggestions", []),
                    "score": result.get("score", 0),
                    "raw_response": content
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}, 原始响应: {response['content']}")
                return {
                    "success": False,
                    "error": f"LLM响应格式错误: {str(e)}",
                    "raw_response": response["content"]
                }
        else:
            return response
    
    async def check_ollama_status(self) -> Dict[str, Any]:
        """检查Ollama服务状态"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                
                return {
                    "success": True,
                    "available": True,
                    "models": model_names,
                    "target_model_available": self.model in model_names
                }
            else:
                return {
                    "success": False,
                    "available": False,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "available": False,
                "error": str(e)
            }
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()
    
    def _extract_json_from_response(self, content: str) -> str:
        """从响应中提取JSON内容"""
        content = content.strip()
        
        # 方法1: 寻找json代码块
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            if json_end > json_start:
                return content[json_start:json_end].strip()
        
        # 方法2: 寻找第一个完整的JSON对象
        brace_count = 0
        start_index = -1
        for i, char in enumerate(content):
            if char == '{':
                if start_index == -1:
                    start_index = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_index != -1:
                    return content[start_index:i+1]
        
        # 方法3: 返回原内容
        return content
    
    def _clean_json_content(self, json_content: str) -> str:
        """清理JSON内容"""
        import re
        
        # 移除多余的空白字符
        json_content = json_content.strip()
        
        # 修复常见的JSON格式问题
        # 1. 将单引号替换为双引号（如果不在字符串内）
        json_content = re.sub(r"(?<!\\)'([^']*?)(?<!\\)'", r'"\1"', json_content)
        
        # 2. 在属性名周围添加双引号
        json_content = re.sub(r'(\w+)(\s*:)', r'"\1"\2', json_content)
        
        # 3. 移除注释
        json_content = re.sub(r'//.*$', '', json_content, flags=re.MULTILINE)
        json_content = re.sub(r'/\*.*?\*/', '', json_content, flags=re.DOTALL)
        
        # 4. 移除多余的逗号
        json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
        
        return json_content
    
    def _fallback_parse_type_inference(self, content: str) -> Optional[Dict[str, Any]]:
        """备用解析方法，使用正则表达式提取类型推导信息"""
        import re
        
        try:
            # 尝试提取变量和类型的模式
            inferences = {}
            explanations = {}
            
            # 模式1: "变量名": "类型"
            pattern1 = r'"([^"]+)"\s*:\s*"([^"]+)"'
            matches = re.findall(pattern1, content)
            for var_name, var_type in matches:
                if not var_name.startswith(('args', 'return', 'suggestions')):
                    inferences[var_name] = var_type
            
            # 模式2: 变量名: 类型 (解释)
            pattern2 = r'(\w+)\s*:\s*([^\n,}]+?)(?:\s*//\s*([^\n]+))?'
            matches = re.findall(pattern2, content)
            for var_name, var_type, explanation in matches:
                var_type = var_type.strip().strip('"\'')
                if var_type and not var_name.startswith(('function', 'variable', 'suggestions')):
                    inferences[var_name] = var_type
                    if explanation:
                        explanations[var_name] = explanation
            
            if inferences:
                return {
                    "success": True,
                    "inferences": inferences,
                    "explanations": explanations,
                    "confidence": {var: 0.7 for var in inferences.keys()},  # 默认置信度
                    "raw_response": content
                }
            
        except Exception as e:
            logger.error(f"备用解析也失败: {str(e)}")
        
        return None

# 全局客户端实例
llm_client = OllamaClient() 