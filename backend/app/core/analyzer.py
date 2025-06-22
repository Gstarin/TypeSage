import ast
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import json

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
    
    def _infer_type_from_value(self, node) -> str:
        """从值推断类型"""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return "str"
            elif isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "float"
            elif isinstance(node.value, bool):
                return "bool"
            elif node.value is None:
                return "None"
        elif isinstance(node, ast.List):
            # 分析列表元素类型
            if node.elts:
                element_types = set()
                for elt in node.elts[:3]:  # 只检查前3个元素
                    element_type = self._infer_type_from_value(elt)
                    element_types.add(element_type)
                if len(element_types) == 1:
                    return f"list[{element_types.pop()}]"
                else:
                    return "list"
            return "list"
        elif isinstance(node, ast.Dict):
            # 分析字典键值类型
            if node.keys and node.values:
                key_types = set()
                value_types = set()
                for key, value in zip(node.keys[:3], node.values[:3]):  # 只检查前3对
                    if key:  # 排除None键
                        key_type = self._infer_type_from_value(key)
                        key_types.add(key_type)
                    value_type = self._infer_type_from_value(value)
                    value_types.add(value_type)
                
                if len(key_types) == 1 and len(value_types) == 1:
                    return f"dict[{key_types.pop()}, {value_types.pop()}]"
                else:
                    return "dict"
            return "dict"
        elif isinstance(node, ast.Set):
            # 分析集合元素类型
            if node.elts:
                element_types = set()
                for elt in node.elts[:3]:  # 只检查前3个元素
                    element_type = self._infer_type_from_value(elt)
                    element_types.add(element_type)
                if len(element_types) == 1:
                    return f"set[{element_types.pop()}]"
                else:
                    return "set"
            return "set"
        elif isinstance(node, ast.Tuple):
            # 分析元组元素类型
            if node.elts:
                element_types = []
                for elt in node.elts:
                    element_type = self._infer_type_from_value(elt)
                    element_types.append(element_type)
                if len(element_types) <= 5:  # 如果元素不太多，显示具体类型
                    return f"tuple[{', '.join(element_types)}]"
                else:
                    return "tuple"
            return "tuple"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                # 内建函数返回类型推断
                builtin_returns = {
                    'len': 'int',
                    'sum': 'int | float',
                    'min': 'int | float',
                    'max': 'int | float',
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
                    'reversed': 'reversed',
                    'open': 'TextIOWrapper',
                    'input': 'str',
                    'print': 'None'
                }
                
                if func_name in builtin_returns:
                    return builtin_returns[func_name]
                else:
                    # 首先检查是否是类的构造函数调用
                    if func_name in self.classes:
                        return func_name  # 类的实例化返回该类的类型
                    # 然后检查是否是已定义的函数
                    elif func_name in self.functions:
                        func_info = self.functions[func_name]
                        if func_info.get('returns'):
                            return func_info['returns']
                        else:
                            return f"return_of_{func_name}"
                    # 检查是否是在全局作用域中可能的类名（大写开头的标识符可能是类）
                    elif func_name[0].isupper():
                        return func_name  # 假设大写开头的调用是类实例化
                    return f"return_of_{func_name}"
            elif isinstance(node.func, ast.Attribute):
                # 方法调用类型推断
                attr_name = node.func.attr
                method_returns = {
                    'append': 'None',
                    'extend': 'None',
                    'insert': 'None',
                    'remove': 'None',
                    'pop': 'Any',
                    'clear': 'None',
                    'copy': 'list',
                    'count': 'int',
                    'index': 'int',
                    'reverse': 'None',
                    'sort': 'None',
                    'join': 'str',
                    'split': 'list[str]',
                    'strip': 'str',
                    'upper': 'str',
                    'lower': 'str',
                    'replace': 'str',
                    'format': 'str',
                    'get': 'Any',
                    'keys': 'dict_keys',
                    'values': 'dict_values',
                    'items': 'dict_items',
                    'update': 'None',
                    'add': 'None',
                    'discard': 'None',
                    'union': 'set',
                    'intersection': 'set'
                }
                
                if attr_name in method_returns:
                    return method_returns[attr_name]
                else:
                    return f"return_of_{attr_name}"
        elif isinstance(node, ast.BinOp):
            # 二元运算符类型推断
            left_type = self._infer_type_from_value(node.left)
            right_type = self._infer_type_from_value(node.right)
            
            if isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
                # 算术运算
                if left_type == 'str' or right_type == 'str':
                    if isinstance(node.op, ast.Add):
                        return 'str'  # 字符串拼接
                    elif isinstance(node.op, ast.Mult):
                        return 'str'  # 字符串重复
                if 'float' in [left_type, right_type]:
                    return 'float'
                elif 'int' in [left_type, right_type]:
                    return 'int' if not isinstance(node.op, ast.Div) else 'float'
                else:
                    return 'int | float'
            elif isinstance(node.op, ast.FloorDiv):
                return 'int'
            elif isinstance(node.op, (ast.BitOr, ast.BitXor, ast.BitAnd, ast.LShift, ast.RShift)):
                return 'int'
        elif isinstance(node, ast.UnaryOp):
            # 一元运算符类型推断
            operand_type = self._infer_type_from_value(node.operand)
            if isinstance(node.op, ast.Not):
                return 'bool'
            elif isinstance(node.op, (ast.UAdd, ast.USub)):
                return operand_type
            elif isinstance(node.op, ast.Invert):
                return 'int'
        elif isinstance(node, ast.Compare):
            # 比较运算结果总是bool
            return 'bool'
        elif isinstance(node, ast.BoolOp):
            # 布尔运算结果总是bool
            return 'bool'
        elif isinstance(node, ast.ListComp):
            # 列表推导式
            return 'list'
        elif isinstance(node, ast.DictComp):
            # 字典推导式
            return 'dict'
        elif isinstance(node, ast.SetComp):
            # 集合推导式
            return 'set'
        elif isinstance(node, ast.GeneratorExp):
            # 生成器表达式
            return 'generator'
        elif isinstance(node, ast.Attribute):
            # 属性访问类型推断
            return 'Any'
        elif isinstance(node, ast.Subscript):
            # 下标访问类型推断
            return 'Any'
        elif isinstance(node, ast.Name):
            # 变量引用
            if node.id in self.variables:
                var_info = self.variables[node.id]
                if var_info.get('annotation'):
                    return var_info['annotation']
                elif var_info.get('inferred_type'):
                    return var_info['inferred_type']
            return 'Any'
        
        return "unknown"

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
        
        # Python内建函数和类型
        self.builtins = {
            # 常用函数
            'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
            'sum', 'min', 'max', 'abs', 'round', 'sorted', 'reversed', 'enumerate', 'zip',
            'map', 'filter', 'any', 'all', 'range', 'iter', 'next', 'open', 'type', 'isinstance',
            'hasattr', 'getattr', 'setattr', 'delattr', 'dir', 'vars', 'globals', 'locals',
            'eval', 'exec', 'compile', 'format', 'repr', 'chr', 'ord', 'hex', 'oct', 'bin',
            'input', 'help', 'id', 'hash', 'callable', 'classmethod', 'staticmethod', 'property',
            'super', 'slice', 'memoryview', 'bytearray', 'bytes', 'frozenset', 'complex',
            'divmod', 'pow', 'round',
            
            # 异常类
            'Exception', 'BaseException', 'ValueError', 'TypeError', 'IndexError', 'KeyError',
            'AttributeError', 'NameError', 'SyntaxError', 'RuntimeError', 'NotImplementedError',
            'ImportError', 'ModuleNotFoundError', 'FileNotFoundError', 'PermissionError',
            'OSError', 'IOError', 'ZeroDivisionError', 'OverflowError', 'RecursionError',
            
            # 常量
            'True', 'False', 'None', '__name__', '__file__', '__doc__', '__package__',
            '__spec__', '__loader__', '__cached__', '__builtins__',
            
            # 特殊方法常量
            'object', 'Ellipsis', 'NotImplemented'
        }
        
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