import ast
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import json
import builtins

class ASTAnalyzer:
    """AST分析器"""
    
    def __init__(self):
        self.symbol_table = {}
        self.scopes = []
        self.current_scope = {}
        self.node_id_counter = 0
        
    def analyze(self, code: str) -> Dict[str, Any]:
        """分析Python代码，返回AST和符号表"""
        try:
            self.node_id_counter = 0  
            tree = ast.parse(code)
            ast_data = self._convert_ast_to_dict(tree)
            symbol_table = self._build_symbol_table(tree)
            
            # 使用完整的符号表信息重新推导变量类型
            self._improve_type_inference(symbol_table)
            
            return {
                "success": True,
                "ast": ast_data,
                "symbol_table": symbol_table,
                "error": None
            }
        except SyntaxError as e:
            return {
                "success": False,
                "ast": None,
                "symbol_table": None,
                "error": f"语法错误: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "ast": None,
                "symbol_table": None,
                "error": f"分析错误: {str(e)}"
            }
    
    def generate_type_annotated_code(self, code: str, type_suggestions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成带类型注解的代码"""
        try:
            tree = ast.parse(code)
            symbol_table = self._build_symbol_table(tree)
            
            # 收集所有变量和函数的类型信息
            type_info = self._collect_all_types(symbol_table, type_suggestions or {})
            
            # 生成带注解的代码
            annotated_code = self._insert_type_annotations(code, type_info, symbol_table)
            
            return {
                "success": True,
                "original_code": code,
                "annotated_code": annotated_code,
                "type_info": type_info,
                "annotations_count": len(type_info.get("variables", {})) + len(type_info.get("functions", {}))
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"类型注解生成失败: {str(e)}"
            }
    
    def _collect_all_types(self, symbol_table: Dict[str, Any], type_suggestions: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """收集所有变量和函数的类型信息"""
        type_info = {
            "variables": {},
            "functions": {},
            "parameters": {}
        }
        
        # 处理变量类型
        variables = symbol_table.get("variables", {})
        for var_name, var_info in variables.items():
            # 优先使用已有的类型注解
            if var_info.get("annotation"):
                var_type = var_info["annotation"]
            # 其次使用推断的类型
            elif var_info.get("inferred_type"):
                var_type = var_info["inferred_type"]
            # 最后使用LLM建议的类型
            elif type_suggestions and type_suggestions.get("inferences", {}).get(var_name):
                var_type = type_suggestions["inferences"][var_name]
            else:
                var_type = "Any"
            
            type_info["variables"][var_name] = {
                "type": self._normalize_type(var_type),
                "line": var_info.get("lineno"),
                "source": "annotation" if var_info.get("annotation") else "inferred"
            }
        
        # 处理函数类型
        functions = symbol_table.get("functions", {})
        for func_name, func_info in functions.items():
            params = {}
            
            # 处理函数参数类型 - 改进的推断逻辑
            for arg_name in func_info.get("args", []):
                param_type = "Any"
                
                # 1. 检查是否有明确的类型注解
                if func_info.get("arg_annotations", {}).get(arg_name):
                    param_type = func_info["arg_annotations"][arg_name]
                # 2. 从LLM建议中获取参数类型
                elif (type_suggestions and 
                      type_suggestions.get("function_suggestions", {}).get(func_name, {}).get("params", {}).get(arg_name)):
                    param_type = type_suggestions["function_suggestions"][func_name]["params"][arg_name]
                # 3. 通过参数的使用上下文推断类型
                else:
                    inferred_param_type = self._infer_parameter_type_from_usage(arg_name, func_name, symbol_table)
                    if inferred_param_type != "Any":
                        param_type = inferred_param_type
                
                params[arg_name] = self._normalize_type(param_type)
            
            # 处理返回值类型
            return_type = "None"
            if func_info.get("returns"):
                return_type = func_info["returns"]
            elif func_info.get("inferred_return_type"):
                return_type = func_info["inferred_return_type"]
            elif (type_suggestions and 
                  type_suggestions.get("function_suggestions", {}).get(func_name, {}).get("return")):
                return_type = type_suggestions["function_suggestions"][func_name]["return"]
            
            type_info["functions"][func_name] = {
                "params": params,
                "return": self._normalize_type(return_type),
                "line": func_info.get("lineno")
            }
        
        return type_info
    
    def _infer_parameter_type_from_usage(self, param_name: str, func_name: str, symbol_table: Dict[str, Any]) -> str:
        """通过分析参数在函数内的使用方式来推断参数类型"""
        # 这里可以进一步分析AST来推断参数类型
        # 基于参数的使用模式来推断类型
        
        # 常见的参数名称模式推断
        name_patterns = {
            "numbers": "list[int | float]",
            "items": "list",
            "data": "list",
            "text": "str",
            "value": "int | float",
            "count": "int",
            "index": "int",
            "name": "str",
            "path": "str",
            "file": "str",
            "content": "str"
        }
        
        # 根据参数名称推断
        for pattern, type_hint in name_patterns.items():
            if pattern in param_name.lower():
                return type_hint
        
        # 如果参数名以s结尾，可能是列表
        if param_name.endswith('s') and len(param_name) > 1:
            return "list"
        
        return "Any"
    
    def _normalize_type(self, type_str: str) -> str:
        """标准化类型字符串"""
        if not type_str or type_str == "unknown":
            return "Any"
        
        # 处理常见的类型映射
        type_mappings = {
            "return_of_": "Any",
            "NoneType": "None",
            "TextIOWrapper": "TextIO"
        }
        
        # 清理类型字符串
        cleaned = type_str.strip()
        
        # 处理以"return_of_"开头的类型
        if cleaned.startswith("return_of_"):
            return "Any"
        
        # 应用类型映射
        for old, new in type_mappings.items():
            if old in cleaned:
                cleaned = cleaned.replace(old, new)
        
        return cleaned
    
    def _improve_type_inference(self, symbol_table: Dict[str, Any]) -> None:
        """使用完整的符号表信息改进类型推导"""
        # 获取所有已定义的类
        classes = symbol_table.get("classes", {})
        variables = symbol_table.get("variables", {})
        
        # 重新解析代码，使用已知的类信息改进类型推导
        for var_name, var_info in variables.items():
            inferred_type = var_info.get("inferred_type", "")
            
            # 如果推导出的类型以 "return_of_" 开头，尝试进一步推导
            if inferred_type.startswith("return_of_"):
                func_name = inferred_type.replace("return_of_", "")
                # 检查是否是类名
                if func_name in classes:
                    var_info["inferred_type"] = func_name
                # 检查是否是大写开头的标识符（可能是类）
                elif func_name and func_name[0].isupper():
                    var_info["inferred_type"] = func_name
    
    def _insert_type_annotations(self, code: str, type_info: Dict[str, Any], symbol_table: Dict[str, Any]) -> str:
        """在代码中插入类型注解"""
        lines = code.split('\n')
        
        # 处理函数类型注解
        functions = symbol_table.get("functions", {})
        for func_name, func_info in functions.items():
            func_line = func_info.get("lineno", 1) - 1  # 转换为0基索引
            if 0 <= func_line < len(lines):
                original_line = lines[func_line]
                
                # 检查是否已有类型注解
                if "->" in original_line or any(":" in arg for arg in original_line.split("(")):
                    continue  # 跳过已有类型注解的函数
                
                # 生成新的函数定义行
                annotated_line = self._annotate_function_line(original_line, func_name, type_info)
                lines[func_line] = annotated_line
        
        # 处理变量类型注解
        variables = symbol_table.get("variables", {})
        for var_name, var_info in variables.items():
            var_line = var_info.get("lineno", 1) - 1  # 转换为0基索引
            if 0 <= var_line < len(lines):
                original_line = lines[var_line]
                
                # 检查是否已有类型注解
                if f"{var_name}:" in original_line:
                    continue  # 跳过已有类型注解的变量
                
                # 生成新的变量定义行
                annotated_line = self._annotate_variable_line(original_line, var_name, type_info)
                if annotated_line != original_line:
                    lines[var_line] = annotated_line
        
        return '\n'.join(lines)
    
    def _annotate_function_line(self, line: str, func_name: str, type_info: Dict[str, Any]) -> str:
        """为函数行添加类型注解"""
        func_type_info = type_info.get("functions", {}).get(func_name, {})
        if not func_type_info:
            return line
        
        params = func_type_info.get("params", {})
        return_type = func_type_info.get("return", "None")
        
        # 解析函数定义
        def_match = re.match(r'^(\s*def\s+' + re.escape(func_name) + r'\s*\()([^)]*)\)(\s*):(.*)$', line)
        if not def_match:
            return line
        
        prefix, args_str, middle, suffix = def_match.groups()
        
        # 处理参数类型注解
        if args_str.strip():
            args = [arg.strip() for arg in args_str.split(',')]
            annotated_args = []
            
            for arg in args:
                if '=' in arg:  # 默认参数
                    arg_name, default = arg.split('=', 1)
                    arg_name = arg_name.strip()
                    if arg_name in params:
                        annotated_args.append(f"{arg_name}: {params[arg_name]} = {default}")
                    else:
                        annotated_args.append(arg)
                else:  # 普通参数
                    arg_name = arg.strip()
                    if arg_name in params:
                        annotated_args.append(f"{arg_name}: {params[arg_name]}")
                    else:
                        annotated_args.append(arg)
            
            new_args = ', '.join(annotated_args)
        else:
            new_args = args_str
        
        # 添加返回值类型注解
        return f"{prefix}{new_args}) -> {return_type}:{suffix}"
    
    def _annotate_variable_line(self, line: str, var_name: str, type_info: Dict[str, Any]) -> str:
        """为变量行添加类型注解"""
        var_type_info = type_info.get("variables", {}).get(var_name, {})
        if not var_type_info:
            return line
        
        var_type = var_type_info.get("type", "Any")
        
        # 匹配赋值语句
        assignment_match = re.match(r'^(\s*)(' + re.escape(var_name) + r')(\s*=.*)$', line)
        if assignment_match:
            indent, var, rest = assignment_match.groups()
            return f"{indent}{var}: {var_type}{rest}"
        
        return line
    
    def _convert_ast_to_dict(self, node) -> Dict[str, Any]:
        """将AST节点转换为字典格式"""
        if isinstance(node, ast.AST):
            node_id = f"node_{self.node_id_counter}"
            self.node_id_counter += 1 
            result = {
                'id': node_id,
                'node_type': node.__class__.__name__,
                'lineno': getattr(node, 'lineno', None),
                'col_offset': getattr(node, 'col_offset', None)
            }
            
            for field, value in ast.iter_fields(node):
                if isinstance(value, list):
                    result[field] = [self._convert_ast_to_dict(item) for item in value]
                elif isinstance(value, ast.AST):
                    result[field] = self._convert_ast_to_dict(value)
                else:
                    result[field] = value
            
            return result
        else:
            return node
    
    def _build_symbol_table(self, tree) -> Dict[str, Any]:
        """构建符号表"""
        visitor = SymbolTableVisitor()
        visitor.visit(tree)
        return visitor.get_symbol_table()

class SymbolTableVisitor(ast.NodeVisitor):
    """符号表构建访问器"""
    
    def __init__(self):
        self.scopes = [{}]  # 作用域栈
        self.global_scope = self.scopes[0]
        self.functions = {}
        self.classes = {}
        self.variables = {}
        self.imports = {}
        
    def get_symbol_table(self) -> Dict[str, Any]:
        """获取符号表"""
        return {
            "global_scope": self.global_scope,
            "functions": self.functions,
            "classes": self.classes,
            "variables": self.variables,
            "imports": self.imports,
            "scopes_count": len(self.scopes)
        }
    
    def visit_FunctionDef(self, node):
        """访问函数定义"""
        # 分析函数内的return语句来推断返回值类型
        return_types = []
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Return) and stmt.value:
                return_type = self._infer_type_from_value(stmt.value)
                return_types.append(return_type)
        
        # 推断最终返回类型
        inferred_return_type = None
        if return_types:
            unique_types = list(set(return_types))
            if len(unique_types) == 1:
                inferred_return_type = unique_types[0]
            elif len(unique_types) > 1:
                inferred_return_type = " | ".join(unique_types)
        
        func_info = {
            "name": node.name,
            "lineno": node.lineno,
            "args": [arg.arg for arg in node.args.args],
            "returns": self._get_annotation(node.returns) if node.returns else inferred_return_type,
            "decorators": [self._get_decorator_name(dec) for dec in node.decorator_list],
            "scope": len(self.scopes),
            "inferred_return_type": inferred_return_type
        }
        
        self.functions[node.name] = func_info
        self.scopes[-1][node.name] = {
            "type": "function",
            "info": func_info
        }
        
        # 进入函数作用域
        self.scopes.append({})
        
        # 添加参数到作用域
        for arg in node.args.args:
            arg_annotation = self._get_annotation(arg.annotation) if arg.annotation else None
            self.scopes[-1][arg.arg] = {
                "type": "parameter",
                "annotation": arg_annotation,
                "lineno": node.lineno,
                "function": node.name
            }
        
        # 访问函数体
        for stmt in node.body:
            self.visit(stmt)
        
        # 退出函数作用域
        self.scopes.pop()
    
    def visit_ClassDef(self, node):
        """访问类定义"""
        class_info = {
            "name": node.name,
            "lineno": node.lineno,
            "bases": [self._get_name(base) for base in node.bases],
            "decorators": [self._get_decorator_name(dec) for dec in node.decorator_list],
            "methods": [],
            "attributes": []
        }
        
        self.classes[node.name] = class_info
        self.scopes[-1][node.name] = {
            "type": "class",
            "info": class_info
        }
        
        # 进入类作用域
        self.scopes.append({})
        
        # 访问类体
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef):
                class_info["methods"].append(stmt.name)
            self.visit(stmt)
        
        # 退出类作用域
        self.scopes.pop()
    
    def visit_Assign(self, node):
        """访问赋值语句"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_info = {
                    "name": target.id,
                    "lineno": node.lineno,
                    "inferred_type": self._infer_type_from_value(node.value),
                    "scope": len(self.scopes) - 1
                }
                
                self.variables[target.id] = var_info
                self.scopes[-1][target.id] = {
                    "type": "variable",
                    "info": var_info
                }
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node):
        """访问带类型注解的赋值"""
        if isinstance(node.target, ast.Name):
            var_info = {
                "name": node.target.id,
                "lineno": node.lineno,
                "annotation": self._get_annotation(node.annotation),
                "inferred_type": self._infer_type_from_value(node.value) if node.value else None,
                "scope": len(self.scopes) - 1
            }
            
            self.variables[node.target.id] = var_info
            self.scopes[-1][node.target.id] = {
                "type": "variable",
                "info": var_info
            }
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """访问import语句"""
        for alias in node.names:
            import_info = {
                "module": alias.name,
                "asname": alias.asname,
                "lineno": node.lineno,
                "type": "import"
            }
            
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = import_info
            self.scopes[-1][name] = {
                "type": "import",
                "info": import_info
            }
    
    def visit_ImportFrom(self, node):
        """访问from import语句"""
        for alias in node.names:
            import_info = {
                "module": node.module,
                "name": alias.name,
                "asname": alias.asname,  
                "lineno": node.lineno,
                "type": "from_import"
            }
            
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = import_info
            self.scopes[-1][name] = {
                "type": "import",
                "info": import_info
            }
    
    def _get_name(self, node) -> str:
        """获取节点名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)
    
    def _get_annotation(self, node) -> str:
        """获取类型注解"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_annotation(node.value)}[{self._get_annotation(node.slice)}]"
        else:
            return str(node)
    
    def _get_decorator_name(self, node) -> str:
        """获取装饰器名称"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return str(node)
    
    def _infer_type_from_value(self, node, context=None) -> str:
        """智能类型推导 - 基于AST节点、上下文和数据流分析"""
        return self._advanced_type_inference(node, context or {})
    
    def _advanced_type_inference(self, node, context: Dict[str, Any]) -> str:
        """高级类型推导引擎"""
        
        # 常量值直接推导
        if isinstance(node, ast.Constant):
            return self._infer_constant_type(node.value)
        
        # 容器类型智能推导
        elif isinstance(node, (ast.List, ast.Set, ast.Tuple)):
            return self._infer_container_type(node, context)
        
        # 字典类型智能推导
        elif isinstance(node, ast.Dict):
            return self._infer_dict_type(node, context)
        
        # 函数调用智能推导
        elif isinstance(node, ast.Call):
            return self._infer_call_type(node, context)
        
        # 运算表达式智能推导
        elif isinstance(node, ast.BinOp):
            return self._infer_binop_type(node, context)
        
        # 一元运算智能推导
        elif isinstance(node, ast.UnaryOp):
            return self._infer_unary_type(node, context)
        
        # 比较和逻辑运算
        elif isinstance(node, (ast.Compare, ast.BoolOp)):
            return 'bool'
        
        # 推导式智能推导
        elif isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
            return self._infer_comprehension_type(node, context)
        
        # 变量引用智能推导
        elif isinstance(node, ast.Name):
            return self._infer_name_type(node, context)
        
        # 属性访问智能推导
        elif isinstance(node, ast.Attribute):
            return self._infer_attribute_type(node, context)
        
        # 下标访问智能推导
        elif isinstance(node, ast.Subscript):
            return self._infer_subscript_type(node, context)
        
        # 条件表达式
        elif isinstance(node, ast.IfExp):
            return self._infer_conditional_type(node, context)
        
        # Lambda表达式
        elif isinstance(node, ast.Lambda):
            return self._infer_lambda_type(node, context)
        
        return "Any"
    
    def _infer_constant_type(self, value) -> str:
        """常量类型推导"""
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int):
            # 检查是否可能是枚举值或特殊常量
            if value in (0, 1, -1):
                return "int"  # 常见的特殊值
            return "int"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            # 分析字符串模式
            if value.isdigit():
                return "str"  # 虽然是数字字符串，但类型仍是str
            elif value.startswith(('http://', 'https://')):
                return "str"  # URL字符串
            elif len(value) == 1:
                return "str"  # 单字符
            return "str"
        elif isinstance(value, bytes):
            return "bytes"
        elif value is None:
            return "None"
        else:
            return f"Literal[{repr(value)}]"
    
    def _infer_container_type(self, node, context: Dict[str, Any]) -> str:
        """智能容器类型推导"""
        container_type = {
            ast.List: "list",
            ast.Set: "set", 
            ast.Tuple: "tuple"
        }[type(node)]
        
        if not node.elts:
            return container_type
        
        # 分析元素类型模式
        element_types = []
        type_distribution = {}
        
        # 采样策略：对于大容器，采样分析
        sample_size = min(len(node.elts), 10)
        sample_indices = self._get_sample_indices(len(node.elts), sample_size)
        
        for i in sample_indices:
            elt_type = self._advanced_type_inference(node.elts[i], context)
            element_types.append(elt_type)
            type_distribution[elt_type] = type_distribution.get(elt_type, 0) + 1
        
        # 智能类型合并
        unified_type = self._unify_types(element_types, type_distribution)
        
        if container_type == "tuple" and len(node.elts) <= 8:
            # 元组保持具体的每个元素类型
            all_types = [self._advanced_type_inference(elt, context) for elt in node.elts]
            return f"tuple[{', '.join(all_types)}]"
        
        return f"{container_type}[{unified_type}]" if unified_type != "Any" else container_type
    
    def _infer_dict_type(self, node, context: Dict[str, Any]) -> str:
        """智能字典类型推导"""
        if not node.keys or not node.values:
            return "dict"
        
        key_types = []
        value_types = []
        
        # 采样分析
        sample_size = min(len(node.keys), 10)
        sample_indices = self._get_sample_indices(len(node.keys), sample_size)
        
        for i in sample_indices:
            if node.keys[i]:  # 排除None键
                key_type = self._advanced_type_inference(node.keys[i], context)
                key_types.append(key_type)
            
            value_type = self._advanced_type_inference(node.values[i], context)
            value_types.append(value_type)
        
        # 统一类型
        unified_key_type = self._unify_types(key_types, {})
        unified_value_type = self._unify_types(value_types, {})
        
        if unified_key_type != "Any" and unified_value_type != "Any":
            return f"dict[{unified_key_type}, {unified_value_type}]"
        
        return "dict"
    
    def _infer_call_type(self, node, context: Dict[str, Any]) -> str:
        """智能函数调用类型推导"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # 扩展的内建函数类型推导
            builtin_returns = self._get_enhanced_builtin_returns()
            
            if func_name in builtin_returns:
                # 根据参数进行更精确的推导
                return self._refine_builtin_return_type(func_name, node.args, builtin_returns[func_name], context)
            
            # 类构造函数检测
            if func_name in self.classes:
                return func_name
            
            # 用户定义函数
            if func_name in self.functions:
                func_info = self.functions[func_name]
                if func_info.get('returns'):
                    return func_info['returns']
                
                # 尝试从函数体推导返回类型
                return self._infer_function_return_type(func_name, node.args, context)
            
            # 工厂函数模式检测
            if func_name.endswith('_factory') or func_name.startswith('create_'):
                return self._infer_factory_return_type(func_name, node.args, context)
            
            # 可能的类名（命名约定）
            if func_name[0].isupper():
                return func_name
                
            return f"return_of_{func_name}"
        
        elif isinstance(node.func, ast.Attribute):
            return self._infer_method_call_type(node, context)
        
        return "Any"
    
    def _infer_method_call_type(self, node, context: Dict[str, Any]) -> str:
        """智能方法调用类型推导"""
        attr_name = node.func.attr
        
        # 扩展的方法返回类型映射
        method_returns = self._get_enhanced_method_returns()
        
        if attr_name in method_returns:
            base_type = method_returns[attr_name]
            
            # 根据调用对象类型进行精化
            if hasattr(node.func, 'value'):
                obj_type = self._advanced_type_inference(node.func.value, context)
                return self._refine_method_return_type(attr_name, obj_type, base_type, node.args, context)
            
            return base_type
        
        # 链式调用模式检测
        if hasattr(node.func, 'value') and isinstance(node.func.value, ast.Call):
            chain_type = self._infer_call_chain_type(node, context)
            if chain_type != "Any":
                return chain_type
        
        return f"return_of_{attr_name}"
    
    def _infer_unary_type(self, node, context: Dict[str, Any]) -> str:
        """智能一元运算类型推导"""
        operand_type = self._advanced_type_inference(node.operand, context)
        
        if isinstance(node.op, ast.Not):
            return 'bool'
        elif isinstance(node.op, (ast.UAdd, ast.USub)):
            return operand_type
        elif isinstance(node.op, ast.Invert):
            return 'int'
        else:
            return operand_type
    
    def _infer_function_return_type(self, func_name: str, args: List, context: Dict[str, Any]) -> str:
        """推导用户定义函数的返回类型"""
        # 这里可以进行更复杂的分析，比如分析函数体中的return语句
        # 目前简化为返回函数信息中的推导类型
        if func_name in self.functions:
            func_info = self.functions[func_name]
            if func_info.get('inferred_return_type'):
                return func_info['inferred_return_type']
        
        return f"return_of_{func_name}"
    
    def _infer_factory_return_type(self, func_name: str, args: List, context: Dict[str, Any]) -> str:
        """推导工厂函数的返回类型"""
        # 基于函数名推测返回类型
        if func_name.endswith('_factory'):
            # 尝试从函数名推导类型
            base_name = func_name.replace('_factory', '')
            if base_name.title() in self.classes:
                return base_name.title()
        
        elif func_name.startswith('create_'):
            # create_user -> User
            type_name = func_name.replace('create_', '').title()
            if type_name in self.classes:
                return type_name
        
        return "Any"
    
    def _refine_method_return_type(self, method_name: str, obj_type: str, base_type: str, args: List, context: Dict[str, Any]) -> str:
        """根据对象类型精化方法返回类型"""
        # 链式方法通常返回同类型对象
        chainable_methods = {'strip', 'upper', 'lower', 'replace', 'format', 'join'}
        if method_name in chainable_methods and obj_type.startswith('str'):
            return 'str'
        
        # 容器方法的返回类型优化
        if obj_type.startswith('list[') and method_name == 'pop':
            # list[int].pop() -> int
            element_type = obj_type[5:-1]  # 提取元素类型
            return element_type
        
        return base_type
    
    def _infer_call_chain_type(self, node, context: Dict[str, Any]) -> str:
        """推导链式调用的类型"""
        # obj.method1().method2() 的类型推导
        if hasattr(node.func, 'value') and isinstance(node.func.value, ast.Call):
            prev_call_type = self._infer_call_type(node.func.value, context)
            method_name = node.func.attr
            
            # 基于前一个调用的返回类型和当前方法推导
            return self._refine_method_return_type(method_name, prev_call_type, "Any", node.args, context)
        
        return "Any"
    
    def _infer_matmul_type(self, left_type: str, right_type: str) -> str:
        """推导矩阵乘法返回类型"""
        # 简化的矩阵乘法类型推导
        numpy_types = {'ndarray', 'matrix'}
        if any(t in left_type for t in numpy_types) or any(t in right_type for t in numpy_types):
            return 'ndarray'
        
        return "Any"
    
    def _infer_tuple_element_type(self, generic_part: str, slice_node, context: Dict[str, Any]) -> str:
        """推导元组元素类型"""
        # 对于tuple[int, str, float]这样的类型，根据索引返回对应类型
        if isinstance(slice_node, ast.Constant) and isinstance(slice_node.value, int):
            index = slice_node.value
            types = [t.strip() for t in generic_part.split(',')]
            if 0 <= index < len(types):
                return types[index]
        
        # 如果索引超出范围或不是常量，返回Union类型
        types = [t.strip() for t in generic_part.split(',')]
        return " | ".join(types) if len(types) <= 3 else "Any"
    
    def _infer_binop_type(self, node, context: Dict[str, Any]) -> str:
        """智能二元运算类型推导"""
        left_type = self._advanced_type_inference(node.left, context)
        right_type = self._advanced_type_inference(node.right, context)
        
        # 数值运算类型推导
        if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Mod, ast.Pow)):
            return self._infer_arithmetic_result_type(node.op, left_type, right_type)
        
        elif isinstance(node.op, ast.Div):
            # 除法总是返回float（Python 3行为）
            return "float"
        
        elif isinstance(node.op, ast.FloorDiv):
            # 整除操作
            if "int" in [left_type, right_type] and "float" not in [left_type, right_type]:
                return "int"
            return "int | float"
        
        # 位运算
        elif isinstance(node.op, (ast.BitOr, ast.BitXor, ast.BitAnd, ast.LShift, ast.RShift)):
            return "int"
        
        # 矩阵乘法
        elif isinstance(node.op, ast.MatMult):
            return self._infer_matmul_type(left_type, right_type)
        
        return "Any"
    
    def _infer_comprehension_type(self, node, context: Dict[str, Any]) -> str:
        """智能推导式类型推导"""
        if isinstance(node, ast.ListComp):
            elt_type = self._advanced_type_inference(node.elt, context)
            return f"list[{elt_type}]" if elt_type != "Any" else "list"
        
        elif isinstance(node, ast.SetComp):
            elt_type = self._advanced_type_inference(node.elt, context)
            return f"set[{elt_type}]" if elt_type != "Any" else "set"
        
        elif isinstance(node, ast.DictComp):
            key_type = self._advanced_type_inference(node.key, context)
            value_type = self._advanced_type_inference(node.value, context)
            if key_type != "Any" and value_type != "Any":
                return f"dict[{key_type}, {value_type}]"
            return "dict"
        
        elif isinstance(node, ast.GeneratorExp):
            elt_type = self._advanced_type_inference(node.elt, context)
            return f"Generator[{elt_type}, None, None]" if elt_type != "Any" else "Generator"
        
        return "Any"
    
    def _infer_name_type(self, node, context: Dict[str, Any]) -> str:
        """智能变量名类型推导"""
        var_name = node.id
        
        # 查找变量信息
        if var_name in self.variables:
            var_info = self.variables[var_name]
            
            # 优先使用显式注解
            if var_info.get('annotation'):
                return var_info['annotation']
            
            # 使用推导的类型
            if var_info.get('inferred_type'):
                return var_info['inferred_type']
        
        # 上下文中的变量类型
        if var_name in context.get('local_vars', {}):
            return context['local_vars'][var_name]
        
        # 命名约定推导
        return self._infer_type_from_naming_convention(var_name)
    
    def _infer_attribute_type(self, node, context: Dict[str, Any]) -> str:
        """智能属性访问类型推导"""
        obj_type = self._advanced_type_inference(node.value, context)
        attr_name = node.attr
        
        # 常见属性类型映射
        common_attributes = {
            'str': {'upper': 'str', 'lower': 'str', 'strip': 'str', 'split': 'list[str]'},
            'list': {'append': 'None', 'pop': 'Any', 'index': 'int', 'count': 'int'},
            'dict': {'keys': 'dict_keys', 'values': 'dict_values', 'items': 'dict_items'},
        }
        
        base_type = obj_type.split('[')[0]  # 去掉泛型参数
        if base_type in common_attributes and attr_name in common_attributes[base_type]:
            return common_attributes[base_type][attr_name]
        
        return "Any"
    
    def _infer_subscript_type(self, node, context: Dict[str, Any]) -> str:
        """智能下标访问类型推导"""
        obj_type = self._advanced_type_inference(node.value, context)
        
        # 提取容器的元素类型
        if '[' in obj_type and ']' in obj_type:
            # 提取泛型参数
            generic_part = obj_type[obj_type.find('[') + 1:obj_type.rfind(']')]
            
            if obj_type.startswith('list[') or obj_type.startswith('set['):
                return generic_part
            elif obj_type.startswith('dict['):
                # 字典访问返回值类型
                if ',' in generic_part:
                    return generic_part.split(',')[1].strip()
                return "Any"
            elif obj_type.startswith('tuple['):
                # 元组可能需要更复杂的索引分析
                return self._infer_tuple_element_type(generic_part, node.slice, context)
        
        # 基础类型的下标访问
        base_type_mapping = {
            'list': 'Any',
            'dict': 'Any', 
            'tuple': 'Any',
            'str': 'str',
            'bytes': 'int'
        }
        
        base_type = obj_type.split('[')[0]
        return base_type_mapping.get(base_type, "Any")
    
    # 辅助方法
    def _get_sample_indices(self, total_size: int, sample_size: int) -> List[int]:
        """获取采样索引"""
        if total_size <= sample_size:
            return list(range(total_size))
        
        # 均匀采样
        step = total_size // sample_size
        indices = [i * step for i in range(sample_size)]
        
        # 确保包含首尾元素
        indices[0] = 0
        if total_size - 1 not in indices:
            indices[-1] = total_size - 1
            
        return indices
    
    def _unify_types(self, types: List[str], distribution: Dict[str, int]) -> str:
        """智能类型统一"""
        if not types:
            return "Any"
        
        # 去重并统计
        unique_types = list(set(types))
        
        if len(unique_types) == 1:
            return unique_types[0]
        
        # 数值类型统一
        numeric_types = {'int', 'float'}
        if all(t in numeric_types for t in unique_types):
            return 'float' if 'float' in unique_types else 'int'
        
        # 字符串和数值混合 - 通常是Any
        if any(t in numeric_types for t in unique_types) and 'str' in unique_types:
            return "Any"
        
        # Union类型（限制数量）
        if len(unique_types) <= 3:
            return " | ".join(sorted(unique_types))
        
        return "Any"
    
    def _get_enhanced_builtin_returns(self) -> Dict[str, str]:
        """获取增强的内建函数返回类型"""
        return {
            'len': 'int',
            'sum': 'int | float',
            'min': 'Any',  # 取决于参数
            'max': 'Any',  # 取决于参数
            'abs': 'int | float',
            'round': 'int | float',
            'str': 'str',
            'int': 'int',
            'float': 'float',
            'bool': 'bool',
            'list': 'list',
            'dict': 'dict',
            'set': 'set',
            'tuple': 'tuple',
            'type': 'type',
            'range': 'range',
            'enumerate': 'enumerate',
            'zip': 'zip',
            'map': 'map',
            'filter': 'filter',
            'sorted': 'list',
            'reversed': 'Iterator',
            'open': 'TextIOWrapper | BinaryIO',
            'input': 'str',
            'print': 'None',
            'next': 'Any',
            'iter': 'Iterator',
            'all': 'bool',
            'any': 'bool',
            'chr': 'str',
            'ord': 'int',
            'hex': 'str',
            'oct': 'str',
            'bin': 'str',
            'repr': 'str',
            'hash': 'int',
            'id': 'int',
            'callable': 'bool',
            'isinstance': 'bool',
            'hasattr': 'bool',
            'getattr': 'Any',
            'setattr': 'None',
            'delattr': 'None'
        }
    
    def _get_enhanced_method_returns(self) -> Dict[str, str]:
        """获取增强的方法返回类型"""
        return {
            # 列表方法
            'append': 'None', 'extend': 'None', 'insert': 'None',
            'remove': 'None', 'pop': 'Any', 'clear': 'None',
            'copy': 'list', 'count': 'int', 'index': 'int',
            'reverse': 'None', 'sort': 'None',
            
            # 字符串方法
            'join': 'str', 'split': 'list[str]', 'strip': 'str',
            'upper': 'str', 'lower': 'str', 'replace': 'str',
            'format': 'str', 'find': 'int', 'startswith': 'bool',
            'endswith': 'bool', 'isdigit': 'bool', 'isalpha': 'bool',
            
            # 字典方法
            'get': 'Any', 'keys': 'dict_keys', 'values': 'dict_values',
            'items': 'dict_items', 'update': 'None', 'setdefault': 'Any',
            
            # 集合方法
            'add': 'None', 'discard': 'None', 'remove': 'None',
            'union': 'set', 'intersection': 'set', 'difference': 'set',
            
            # 文件方法
            'read': 'str', 'readline': 'str', 'readlines': 'list[str]',
            'write': 'int', 'close': 'None', 'flush': 'None',
        }
    
    def _infer_type_from_naming_convention(self, var_name: str) -> str:
        """基于命名约定推导类型"""
        name_lower = var_name.lower()
        
        # 常见命名模式
        patterns = {
            'count': 'int', 'index': 'int', 'size': 'int', 'length': 'int',
            'flag': 'bool', 'enabled': 'bool', 'disabled': 'bool',
            'name': 'str', 'title': 'str', 'message': 'str', 'text': 'str',
            'path': 'str', 'filename': 'str', 'url': 'str',
            'items': 'list', 'data': 'list | dict', 'results': 'list',
            'config': 'dict', 'settings': 'dict', 'params': 'dict'
        }
        
        for pattern, type_hint in patterns.items():
            if pattern in name_lower:
                return type_hint
        
        # 复数形式可能是列表
        if name_lower.endswith('s') and len(name_lower) > 2:
            return "list"
        
        return "Any"
    
    def _refine_builtin_return_type(self, func_name: str, args: List, base_type: str, context: Dict[str, Any]) -> str:
        """根据参数精化内建函数返回类型"""
        if func_name in ('min', 'max') and args:
            # min/max返回与输入相同的类型
            arg_types = [self._advanced_type_inference(arg, context) for arg in args[:2]]
            return self._unify_types(arg_types, {})
        
        elif func_name == 'sum' and args:
            # sum的返回类型取决于输入
            first_arg_type = self._advanced_type_inference(args[0], context)
            if 'float' in first_arg_type:
                return 'float'
            elif 'int' in first_arg_type:
                return 'int'
        
        return base_type
    
    def _infer_arithmetic_result_type(self, op, left_type: str, right_type: str) -> str:
        """推导算术运算结果类型"""
        # 字符串特殊处理
        if isinstance(op, ast.Add) and ('str' in [left_type, right_type]):
            return 'str'
        
        if isinstance(op, ast.Mult) and ('str' in [left_type, right_type]) and ('int' in [left_type, right_type]):
            return 'str'
        
        # 数值运算
        if 'float' in [left_type, right_type]:
            return 'float'
        elif 'int' in [left_type, right_type]:
            return 'int'
        else:
            return 'int | float'
    
    def _infer_conditional_type(self, node, context: Dict[str, Any]) -> str:
        """推导条件表达式类型"""
        if_type = self._advanced_type_inference(node.body, context)
        else_type = self._advanced_type_inference(node.orelse, context)
        return self._unify_types([if_type, else_type], {})
    
    def _infer_lambda_type(self, node, context: Dict[str, Any]) -> str:
        """推导Lambda表达式类型"""
        # 简化的Lambda类型推导
        return_type = self._advanced_type_inference(node.body, context)
        return f"Callable[..., {return_type}]"

class TypeInferrer:
    """类型推导器"""
    
    def __init__(self):
        self.undeclared_vars = []
        self.type_suggestions = {}
    
    def analyze_undeclared_variables(self, code: str, symbol_table: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析未声明的变量"""
        tree = ast.parse(code)
        visitor = UndeclaredVariableVisitor(symbol_table)
        visitor.visit(tree)
        
        return visitor.get_undeclared_variables()

class UndeclaredVariableVisitor(ast.NodeVisitor):
    """未声明变量访问器"""
    
    def __init__(self, symbol_table: Dict[str, Any]):
        self.symbol_table = symbol_table
        self.undeclared_vars = []
        self.declared_names = set()
        self.current_function = None
        self.function_params = {}  # 存储每个函数的参数
        
        # 动态获取Python内建函数和类型
        # 优势：
        # 1. 自动包含所有内建函数，避免遗漏（如breakpoint、aiter、anext等）
        # 2. 适应不同Python版本的差异
        # 3. 减少维护工作，无需手动更新列表
        # 4. 更加准确和可靠
        self.builtins = set(dir(builtins))
        
        # 添加一些特殊的常量和关键字（虽然不在builtins中，但在Python中是预定义的）
        # 这些名称在模块级别可见，不应被识别为未声明变量
        special_names = {
            '__name__', '__file__', '__doc__', '__package__',
            '__spec__', '__loader__', '__cached__', '__builtins__',
            'Ellipsis', 'NotImplemented'
        }
        self.builtins.update(special_names)
        
        # 收集所有已声明的名称
        for scope in [symbol_table.get("global_scope", {}), 
                     symbol_table.get("variables", {}),
                     symbol_table.get("functions", {}),
                     symbol_table.get("classes", {}),
                     symbol_table.get("imports", {})]:
            self.declared_names.update(scope.keys())
        
        # 收集函数参数
        functions = symbol_table.get("functions", {})
        for func_name, func_info in functions.items():
            if 'args' in func_info:
                self.function_params[func_name] = set(func_info['args'])
    
    def visit_FunctionDef(self, node):
        """访问函数定义"""
        old_function = self.current_function
        self.current_function = node.name
        
        # 在函数内部，参数被认为是已声明的
        self.generic_visit(node)
        
        self.current_function = old_function
    
    def visit_Name(self, node):
        """访问名称节点"""
        if (isinstance(node.ctx, ast.Load) and 
            node.id not in self.declared_names and 
            node.id not in self.builtins):
            
            # 检查是否是当前函数的参数
            is_function_param = False
            if self.current_function and self.current_function in self.function_params:
                if node.id in self.function_params[self.current_function]:
                    is_function_param = True
            
            # 如果不是函数参数，才认为是未声明变量
            if not is_function_param:
                var_info = {
                    "name": node.id,
                    "lineno": node.lineno,
                    "col_offset": node.col_offset,
                    "context": "load",
                    "function": self.current_function
                }
                
                if var_info not in self.undeclared_vars:
                    self.undeclared_vars.append(var_info)
        
        self.generic_visit(node)
    
    def get_undeclared_variables(self) -> List[Dict[str, Any]]:
        """获取未声明变量列表"""
        return self.undeclared_vars

def generate_code_hash(code: str) -> str:
    """生成代码哈希"""
    return hashlib.md5(code.encode('utf-8')).hexdigest()

def extract_code_patterns(code: str) -> List[str]:
    """提取代码模式用于记忆库匹配"""
    patterns = []
    
    # 提取变量赋值模式
    var_assignments = re.findall(r'(\w+)\s*=\s*([^=\n]+)', code)
    for var, value in var_assignments:
        patterns.append(f"assignment_{var}_{value.strip()}")
    
    # 提取函数调用模式
    func_calls = re.findall(r'(\w+)\s*\([^)]*\)', code)
    for call in func_calls:
        patterns.append(f"function_call_{call}")
    
    # 提取控制流模式
    if 'if ' in code:
        patterns.append("control_flow_if")
    if 'for ' in code:
        patterns.append("control_flow_for")
    if 'while ' in code:
        patterns.append("control_flow_while")
    
    return patterns 