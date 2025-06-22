import sys
import time
sys.path.append('.')

from backend.app.core.analyzer import generate_code_hash
from backend.app.database import init_database, save_type_annotation_cache, get_type_annotation_cache

def test_annotation_cache():
    print("=== 类型注解缓存功能测试 ===")
    
    # 初始化数据库
    init_database()
    print("✅ 数据库初始化完成")
    
    # 测试代码
    test_code = """def calculate_average(numbers):
    total = sum(numbers)
    count = len(numbers)
    return total / count

result = calculate_average([1, 2, 3, 4, 5])
items = [1, 2, 3, 4, 5]
name = "TypeSage"
"""
    
    code_hash = generate_code_hash(test_code)
    print(f"代码哈希: {code_hash[:8]}...")
    
    # 模拟类型注解结果
    type_info = {
        "variables": {
            "total": {"type": "int | float", "line": 2},
            "count": {"type": "int", "line": 3},
            "result": {"type": "int | float", "line": 7},
            "items": {"type": "list[int]", "line": 8},
            "name": {"type": "str", "line": 9}
        },
        "functions": {
            "calculate_average": {
                "params": {"numbers": "list[int | float]"},
                "return": "int | float",
                "line": 1
            }
        }
    }
    
    annotated_code = """def calculate_average(numbers: list[int | float]) -> int | float:
    total: int | float = sum(numbers)
    count: int = len(numbers)
    return total / count

result: int | float = calculate_average([1, 2, 3, 4, 5])
items: list[int] = [1, 2, 3, 4, 5]
name: str = "TypeSage"
"""
    
    # 测试保存缓存
    print("\n=== 测试保存缓存 ===")
    save_type_annotation_cache(
        code_hash=code_hash,
        original_code=test_code,
        annotated_code=annotated_code,
        type_info=type_info,
        annotations_count=6,
        llm_suggestions_used=False,
        use_llm=True
    )
    print("✅ 类型注解缓存保存成功")
    
    # 测试读取缓存
    print("\n=== 测试读取缓存 ===")
    start_time = time.time()
    cached_result = get_type_annotation_cache(code_hash, use_llm=True)
    end_time = time.time()
    
    if cached_result:
        print("✅ 缓存读取成功")
        print(f"缓存读取耗时: {(end_time - start_time) * 1000:.2f}ms")
        print(f"注解数量: {cached_result['annotations_count']}")
        print(f"LLM建议使用: {cached_result['llm_suggestions_used']}")
        print(f"创建时间: {cached_result['created_at']}")
        
        print("\n=== 缓存的注解代码 ===")
        print(cached_result['annotated_code'])
    else:
        print("❌ 缓存读取失败")
    
    # 测试不同use_llm参数的缓存隔离
    print("\n=== 测试缓存隔离 ===")
    cached_false = get_type_annotation_cache(code_hash, use_llm=False)
    if cached_false:
        print("❌ 缓存隔离失败，不应该返回结果")
    else:
        print("✅ 缓存隔离正常，不同use_llm参数的缓存独立")
    
    # 保存另一个缓存记录（use_llm=False）
    save_type_annotation_cache(
        code_hash=code_hash,
        original_code=test_code,
        annotated_code=annotated_code,
        type_info=type_info,
        annotations_count=6,
        llm_suggestions_used=False,
        use_llm=False
    )
    
    # 再次测试读取
    cached_false = get_type_annotation_cache(code_hash, use_llm=False)
    if cached_false:
        print("✅ use_llm=False 的缓存保存和读取成功")
    else:
        print("❌ use_llm=False 的缓存读取失败")

if __name__ == "__main__":
    test_annotation_cache() 