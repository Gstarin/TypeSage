import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

DATABASE_PATH = "database/typesage.db"

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_tables(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建分析记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_hash TEXT UNIQUE NOT NULL,
                original_code TEXT NOT NULL,
                ast_data TEXT,
                symbol_table TEXT,
                type_inference TEXT,
                llm_suggestions TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建记忆库表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_hash TEXT UNIQUE NOT NULL,
                code_pattern TEXT NOT NULL,
                inferred_types TEXT,
                confidence_score REAL,
                usage_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建类型推导历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS type_inference_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                variable_name TEXT NOT NULL,
                context_code TEXT,
                traditional_type TEXT,
                llm_inferred_type TEXT,
                final_type TEXT,
                confidence REAL,
                validation_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建类型注解缓存表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS type_annotation_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_hash TEXT UNIQUE NOT NULL,
                original_code TEXT NOT NULL,
                annotated_code TEXT NOT NULL,
                type_info TEXT,
                annotations_count INTEGER,
                llm_suggestions_used BOOLEAN,
                use_llm BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

# 数据库实例
db = Database()

def init_database():
    """初始化数据库"""
    db.init_tables()

async def init_db():
    """异步初始化数据库"""
    db.init_tables()

def save_analysis_record(code_hash: str, original_code: str, ast_data: Dict, 
                        symbol_table: Dict, type_inference: Dict, llm_suggestions: Dict) -> int | None:
    """保存分析记录到数据库"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO analysis_records 
            (code_hash, original_code, ast_data, symbol_table, type_inference, llm_suggestions, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            code_hash,
            original_code,
            json.dumps(ast_data, ensure_ascii=False),
            json.dumps(symbol_table, ensure_ascii=False),
            json.dumps(type_inference, ensure_ascii=False),
            json.dumps(llm_suggestions, ensure_ascii=False),
            datetime.now().isoformat()
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        return record_id
    finally:
        conn.close()

def get_analysis_record(code_hash: str) -> Optional[Dict]:
    """根据代码哈希获取分析记录"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM analysis_records WHERE code_hash = ?', (code_hash,))
        row = cursor.fetchone()
        
        if row:
            return {
                'id': row['id'],
                'code_hash': row['code_hash'],
                'original_code': row['original_code'],
                'ast_data': json.loads(row['ast_data']) if row['ast_data'] else {},
                'symbol_table': json.loads(row['symbol_table']) if row['symbol_table'] else {},
                'type_inference': json.loads(row['type_inference']) if row['type_inference'] else {},
                'llm_suggestions': json.loads(row['llm_suggestions']) if row['llm_suggestions'] else {},
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            }
        return None
    finally:
        conn.close()

def save_memory_pattern(pattern_hash: str, code_pattern: str, inferred_types: Dict, confidence_score: float):
    """保存模式到记忆库"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO memory_store 
            (pattern_hash, code_pattern, inferred_types, confidence_score, last_used)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            pattern_hash,
            code_pattern,
            json.dumps(inferred_types, ensure_ascii=False),
            confidence_score,
            datetime.now().isoformat()
        ))
        
        # 更新使用次数
        cursor.execute('''
            UPDATE memory_store 
            SET usage_count = usage_count + 1 
            WHERE pattern_hash = ?
        ''', (pattern_hash,))
        
        conn.commit()
    finally:
        conn.close()

def get_memory_patterns() -> List[Dict]:
    """获取所有记忆库模式"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM memory_store ORDER BY usage_count DESC, last_used DESC')
        rows = cursor.fetchall()
        
        return [
            {
                'id': row['id'],
                'pattern_hash': row['pattern_hash'],
                'code_pattern': row['code_pattern'],
                'inferred_types': json.loads(row['inferred_types']) if row['inferred_types'] else {},
                'confidence_score': row['confidence_score'],
                'usage_count': row['usage_count'],
                'created_at': row['created_at'],
                'last_used': row['last_used']
            }
            for row in rows
        ]
    finally:
        conn.close()

def save_type_inference_history(variable_name: str, context_code: str, traditional_type: str,
                               llm_inferred_type: str, final_type: str, confidence: float,
                               validation_result: str):
    """保存类型推导历史"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO type_inference_history 
            (variable_name, context_code, traditional_type, llm_inferred_type, 
             final_type, confidence, validation_result)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            variable_name, context_code, traditional_type, llm_inferred_type,
            final_type, confidence, validation_result
        ))
        
        conn.commit()
    finally:
        conn.close()

def get_type_inference_history() -> List[Dict]:
    """获取类型推导历史"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM type_inference_history ORDER BY created_at DESC LIMIT 100')
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    finally:
        conn.close()

def save_type_annotation_cache(code_hash: str, original_code: str, annotated_code: str, 
                               type_info: dict, annotations_count: int, 
                               llm_suggestions_used: bool, use_llm: bool):
    """保存类型注解缓存"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO type_annotation_cache 
            (code_hash, original_code, annotated_code, type_info, annotations_count, 
             llm_suggestions_used, use_llm, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            code_hash,
            original_code,
            annotated_code,
            json.dumps(type_info),
            annotations_count,
            llm_suggestions_used,
            use_llm
        ))
        
        conn.commit()
    finally:
        conn.close()

def get_type_annotation_cache(code_hash: str, use_llm: bool) -> Optional[Dict[str, Any]]:
    """获取类型注解缓存"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT original_code, annotated_code, type_info, annotations_count, 
                   llm_suggestions_used, created_at
            FROM type_annotation_cache 
            WHERE code_hash = ? AND use_llm = ?
        ''', (code_hash, use_llm))
        
        row = cursor.fetchone()
        if row:
            return {
                "original_code": row[0],
                "annotated_code": row[1],
                "type_info": json.loads(row[2]),
                "annotations_count": row[3],
                "llm_suggestions_used": bool(row[4]),
                "created_at": row[5]
            }
        return None
    finally:
        conn.close() 