#!/usr/bin/env python3
"""
可视化状态缓存功能测试脚本

这个脚本演示了如何测试语法树可视化的状态缓存功能。
用户可以：
1. 在页面上调整AST和符号表的视图（缩放、位置、节点大小等）
2. 切换到其他页面或刷新页面
3. 返回可视化页面时状态应该被恢复

测试步骤：
1. 运行 TypeSage 应用
2. 在分析页面输入代码并进行分析
3. 进入可视化页面
4. 调整视图设置（缩放、移动、修改节点大小、切换标签等）
5. 切换到其他页面
6. 返回可视化页面验证状态是否恢复
"""

# 测试用的Python代码
TEST_CODE = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a, b):
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

# 全局变量
numbers = [1, 2, 3, 4, 5]
calc = Calculator()

# 使用示例
fib_result = fibonacci(10)
sum_result = calc.add(5, 3)
product_result = calc.multiply(4, 7)

print(f"斐波那契数列第10项: {fib_result}")
print(f"5 + 3 = {sum_result}")
print(f"4 * 7 = {product_result}")
print(f"计算历史: {calc.history}")
"""

def main():
    print("可视化状态缓存功能测试")
    print("=" * 50)
    print("\n测试代码:")
    print(TEST_CODE)
    print("\n测试步骤:")
    print("1. 启动 TypeSage 应用 (运行 start.bat 或 start.sh)")
    print("2. 在分析页面粘贴上面的测试代码")
    print("3. 点击 '开始分析' 按钮")
    print("4. 进入 '代码可视化' 页面")
    print("5. 在AST和符号表视图中:")
    print("   - 调整缩放级别")
    print("   - 拖拽改变视图位置")
    print("   - 修改节点大小")
    print("   - 切换节点/边标签显示")
    print("   - 更改布局类型")
    print("   - 选择不同的节点")
    print("6. 切换到其他页面（如首页）")
    print("7. 返回可视化页面")
    print("8. 验证以下状态是否被恢复:")
    print("   ✓ 活动标签页 (AST/符号表)")
    print("   ✓ 视图位置和缩放级别")
    print("   ✓ 节点大小设置")
    print("   ✓ 标签显示设置")
    print("   ✓ 布局类型")
    print("   ✓ 选中的节点")
    print("   ✓ 缓存状态指示器")
    print("\n预期结果:")
    print("- 右上角显示 '已缓存状态' 指示器")
    print("- 加载提示显示 '从缓存加载可视化数据...'")
    print("- 所有视图设置都应该与离开前保持一致")
    print("- 刷新页面后状态依然保持")
    print("\n注意:")
    print("- 不同的代码会有不同的缓存")
    print("- 清除缓存按钮可以重置所有状态")
    print("- 刷新数据按钮会重新获取服务器数据")

if __name__ == "__main__":
    main() 