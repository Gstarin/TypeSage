#!/usr/bin/env python3
"""
改进的类型推导功能测试脚本

测试目标：
1. 验证类实例化的类型推导是否正确
2. 确保 g: Any = Greeter("Alice") 现在应该推导为 g: Greeter = Greeter("Alice")
3. 测试其他相关的类型推导场景
"""

import sys
import os
sys.path.append('.')

from backend.app.core.analyzer import ASTAnalyzer

def test_class_instantiation_inference():
    print("=== 类实例化类型推导测试 ===")
    
    # 测试代码：类实例化
    test_code = '''class Greeter:
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        print("Hello", self.name)

# 使用类
g = Greeter("Alice")
g.greet()
'''
    
    analyzer = ASTAnalyzer()
    result = analyzer.analyze(test_code)
    
    if result["success"]:
        print("✅ 代码分析成功")
        
        # 检查符号表中的变量类型
        variables = result["symbol_table"].get("variables", {})
        classes = result["symbol_table"].get("classes", {})
        
        print(f"\n发现的类: {list(classes.keys())}")
        print(f"发现的变量: {list(variables.keys())}")
        
        # 检查变量 g 的类型推导
        if "g" in variables:
            g_info = variables["g"]
            inferred_type = g_info.get("inferred_type", "unknown")
            print(f"\n变量 'g' 的推导类型: {inferred_type}")
            
            if inferred_type == "Greeter":
                print("✅ 类型推导正确！'g' 被正确推导为 'Greeter' 类型")
            else:
                print(f"❌ 类型推导有误，期望 'Greeter'，实际得到 '{inferred_type}'")
        else:
            print("❌ 变量 'g' 未找到")
    else:
        print(f"❌ 代码分析失败: {result['error']}")

def test_type_annotation_generation():
    print("\n=== 类型注解生成测试 ===")
    
    test_code = '''class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(result)
        return result

calc = Calculator()
result = calc.add(5, 3)
'''
    
    analyzer = ASTAnalyzer()
    annotation_result = analyzer.generate_type_annotated_code(test_code)
    
    if annotation_result["success"]:
        print("✅ 类型注解生成成功")
        print(f"注解数量: {annotation_result['annotations_count']}")
        
        print("\n原始代码:")
        print(annotation_result["original_code"])
        
        print("\n带类型注解的代码:")
        print(annotation_result["annotated_code"])
        
        # 检查是否正确推导了 calc 变量的类型
        type_info = annotation_result.get("type_info", {})
        variables = type_info.get("variables", {})
        
        if "calc" in variables:
            calc_type = variables["calc"]["type"]
            print(f"\n变量 'calc' 的类型: {calc_type}")
            if calc_type == "Calculator":
                print("✅ 'calc' 变量类型推导正确")
            else:
                print(f"❌ 'calc' 变量类型推导有误，期望 'Calculator'，实际 '{calc_type}'")
    else:
        print(f"❌ 类型注解生成失败: {annotation_result['error']}")

def test_multiple_class_instances():
    print("\n=== 多个类实例测试 ===")
    
    test_code = '''class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

class Car:
    def __init__(self, brand, model):
        self.brand = brand
        self.model = model

person = Person("Alice", 30)
car = Car("Toyota", "Camry")
another_person = Person("Bob", 25)
'''
    
    analyzer = ASTAnalyzer()
    result = analyzer.analyze(test_code)
    
    if result["success"]:
        print("✅ 代码分析成功")
        
        variables = result["symbol_table"].get("variables", {})
        
        test_cases = [
            ("person", "Person"),
            ("car", "Car"),
            ("another_person", "Person")
        ]
        
        for var_name, expected_type in test_cases:
            if var_name in variables:
                actual_type = variables[var_name].get("inferred_type", "unknown")
                if actual_type == expected_type:
                    print(f"✅ {var_name}: {actual_type} (正确)")
                else:
                    print(f"❌ {var_name}: {actual_type} (期望 {expected_type})")
            else:
                print(f"❌ 变量 '{var_name}' 未找到")
    else:
        print(f"❌ 代码分析失败: {result['error']}")

def test_builtin_vs_custom_classes():
    print("\n=== 内置类型 vs 自定义类测试 ===")
    
    test_code = '''class MyList:
    def __init__(self):
        self.items = []

my_list = MyList()
builtin_list = list()
builtin_dict = dict()
builtin_set = set()
'''
    
    analyzer = ASTAnalyzer()
    result = analyzer.analyze(test_code)
    
    if result["success"]:
        print("✅ 代码分析成功")
        
        variables = result["symbol_table"].get("variables", {})
        
        test_cases = [
            ("my_list", "MyList"),
            ("builtin_list", "list"),
            ("builtin_dict", "dict"),
            ("builtin_set", "set")
        ]
        
        for var_name, expected_type in test_cases:
            if var_name in variables:
                actual_type = variables[var_name].get("inferred_type", "unknown")
                if actual_type == expected_type:
                    print(f"✅ {var_name}: {actual_type} (正确)")
                else:
                    print(f"❌ {var_name}: {actual_type} (期望 {expected_type})")
            else:
                print(f"❌ 变量 '{var_name}' 未找到")
    else:
        print(f"❌ 代码分析失败: {result['error']}")

if __name__ == "__main__":
    print("开始测试改进的类型推导功能...\n")
    
    test_class_instantiation_inference()
    test_type_annotation_generation()
    test_multiple_class_instances()
    test_builtin_vs_custom_classes()
    
    print("\n测试完成！") 