#!/usr/bin/env python3
"""
lanceDB向量存储模块
创建向量数据库表，存储向量和文本元数据，支持相似度查询
"""

import os
import time
import logging
import json
from typing import List, Dict, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict, field
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    """向量记录数据类"""
    id: str  # 唯一标识符
    vector: np.ndarray  # 1024维向量
    text: str  # 原始文本
    chunk_id: str  # 分块ID
    file_path: str  # 文件路径
    file_name: str  # 文件名
    metadata: Dict[str, Any]  # 元数据
    created_at: float = field(default_factory=time.time)  # 创建时间戳
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于序列化"""
        result = asdict(self)
        # 将numpy数组转换为列表
        result['vector'] = self.vector.tolist()
        return result


@dataclass
class SearchResult:
    """搜索结果数据类"""
    record: VectorRecord
    similarity: float  # 余弦相似度
    distance: float  # 距离（1 - 相似度）
    rank: int  # 排名


class LanceDBVectorStore:
    """lanceDB向量存储管理器"""
    
    def __init__(self, 
                 db_path: str = "./data/lancedb",
                 table_name: str = "obsidian_embeddings",
                 vector_dimension: int = 1024,
                 metric_type: str = "cosine"):
        """
        初始化向量存储
        
        Args:
            db_path: lanceDB数据库路径
            table_name: 表名
            vector_dimension: 向量维度
            metric_type: 相似度度量方式 (cosine/l2)
        """
        self.db_path = db_path
        self.table_name = table_name
        self.vector_dimension = vector_dimension
        self.metric_type = metric_type
        
        # 延迟导入，避免依赖问题
        self.lancedb = None
        self.pyarrow = None
        self.db = None
        self.table = None
        
        logger.info(f"初始化lanceDB向量存储")
        logger.info(f"  数据库路径: {db_path}")
        logger.info(f"  表名: {table_name}")
        logger.info(f"  向量维度: {vector_dimension}")
        logger.info(f"  度量方式: {metric_type}")
        
        # 确保数据库目录存在
        os.makedirs(db_path, exist_ok=True)
    
    def _ensure_imports(self):
        """确保必要的库已导入"""
        if self.lancedb is None:
            try:
                import lancedb
                import pyarrow as pa
                self.lancedb = lancedb
                self.pyarrow = pa
            except ImportError as e:
                logger.error(f"导入lanceDB失败: {e}")
                logger.error("请安装: pip install lancedb pyarrow")
                raise
    
    def connect(self) -> bool:
        """
        连接到lanceDB数据库
        
        Returns:
            是否连接成功
        """
        try:
            self._ensure_imports()
            
            logger.info(f"连接到lanceDB数据库: {self.db_path}")
            self.db = self.lancedb.connect(self.db_path)
            
            # 检查表是否存在
            try:
                table_names = self.db.table_names()
                if self.table_name in table_names:
                    self.table = self.db.open_table(self.table_name)
                    logger.info(f"打开现有表: {self.table_name}")
                    logger.info(f"  表大小: {self.table.count_rows()} 条记录")
                else:
                    logger.info(f"表不存在，将在首次插入时创建: {self.table_name}")
            except Exception as e:
                logger.warning(f"检查表时出错: {e}")
                # 继续执行
            
            return True
            
        except Exception as e:
            logger.error(f"连接lanceDB失败: {e}")
            return False
    
    def create_table(self, force_recreate: bool = False) -> bool:
        """
        创建向量表
        
        Args:
            force_recreate: 是否强制重新创建
            
        Returns:
            是否创建成功
        """
        try:
            self._ensure_imports()
            
            # 确保已连接
            if self.db is None:
                if not self.connect():
                    return False
            
            # 检查表是否已存在
            try:
                table_names = self.db.table_names()
                if self.table_name in table_names:
                    if force_recreate:
                        logger.info(f"删除现有表: {self.table_name}")
                        self.db.drop_table(self.table_name)
                    else:
                        logger.info(f"表已存在: {self.table_name}")
                        self.table = self.db.open_table(self.table_name)
                        return True
            except Exception as e:
                logger.warning(f"检查表时出错: {e}")
                # 继续创建新表
            
            logger.info(f"创建表: {self.table_name}")
            
            # 创建schema
            schema = self.pyarrow.schema([
                self.pyarrow.field("id", self.pyarrow.string()),
                self.pyarrow.field("vector", self.pyarrow.list_(self.pyarrow.float32(), self.vector_dimension)),
                self.pyarrow.field("text", self.pyarrow.string()),
                self.pyarrow.field("chunk_id", self.pyarrow.string()),
                self.pyarrow.field("file_path", self.pyarrow.string()),
                self.pyarrow.field("file_name", self.pyarrow.string()),
                self.pyarrow.field("metadata", self.pyarrow.string()),
                self.pyarrow.field("created_at", self.pyarrow.float64())
            ])
            
            # 创建空表
            self.table = self.db.create_table(self.table_name, schema=schema)
            
            logger.info(f"表创建成功: {self.table_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建表失败: {e}")
            return False
    
    def add_records(self, records: List[VectorRecord]) -> int:
        """
        添加向量记录到数据库
        
        Args:
            records: 向量记录列表
            
        Returns:
            成功插入的记录数
        """
        if not records:
            logger.warning("没有记录需要插入")
            return 0
        
        try:
            self._ensure_imports()
            
            # 确保表存在
            if self.table is None:
                if not self.create_table():
                    return 0
            
            logger.info(f"开始插入 {len(records)} 条记录")
            start_time = time.time()
            
            # 准备数据
            data_to_insert = []
            for record in records:
                data_to_insert.append({
                    "id": record.id,
                    "vector": record.vector.tolist(),
                    "text": record.text,
                    "chunk_id": record.chunk_id,
                    "file_path": record.file_path,
                    "file_name": record.file_name,
                    "metadata": self._serialize_metadata(record.metadata),
                    "created_at": record.created_at
                })
            
            # 插入数据
            self.table.add(data_to_insert)
            
            total_time = time.time() - start_time
            logger.info(f"插入完成，共 {len(records)} 条记录")
            logger.info(f"  总耗时: {total_time:.2f}秒")
            logger.info(f"  平均每条: {total_time/len(records)*1000:.1f}毫秒")
            
            return len(records)
            
        except Exception as e:
            logger.error(f"插入记录失败: {e}")
            return 0
    
    def add_embeddings(self, embeddings: List[Dict], id_prefix: str = "emb") -> int:
        """
        添加嵌入结果到数据库
        
        Args:
            embeddings: 嵌入结果列表（来自EmbeddingGenerator）
            id_prefix: ID前缀
            
        Returns:
            成功插入的记录数
        """
        records = []
        
        for i, emb in enumerate(embeddings):
            # 创建向量记录
            record = VectorRecord(
                id=f"{id_prefix}_{i}_{int(time.time())}",
                vector=np.array(emb['embedding']),
                text=emb['text'],
                chunk_id=emb['chunk_id'],
                file_path=emb['file_path'],
                file_name=emb['file_name'],
                metadata=emb['metadata'],
                created_at=time.time()
            )
            records.append(record)
        
        return self.add_records(records)
    
    def search(self, 
               query_vector: np.ndarray, 
               limit: int = 10,
               filter_condition: Optional[str] = None) -> List[SearchResult]:
        """
        搜索相似向量
        
        Args:
            query_vector: 查询向量
            limit: 返回结果数量
            filter_condition: 过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            self._ensure_imports()
            
            if self.table is None:
                logger.error("表不存在，无法搜索")
                return []
            
            logger.info(f"搜索相似向量，限制: {limit}")
            
            # 准备查询
            query = query_vector.tolist()
            
            # 执行搜索
            start_time = time.time()
            
            if filter_condition:
                results = self.table.search(query).where(filter_condition).limit(limit).to_list()
            else:
                results = self.table.search(query).limit(limit).to_list()
            
            search_time = time.time() - start_time
            
            # 转换为SearchResult对象
            search_results = []
            for i, result in enumerate(results):
                # 解析元数据
                metadata = self._deserialize_metadata(result['metadata'])
                
                record = VectorRecord(
                    id=result['id'],
                    vector=np.array(result['vector']),
                    text=result['text'],
                    chunk_id=result['chunk_id'],
                    file_path=result['file_path'],
                    file_name=result['file_name'],
                    metadata=metadata,
                    created_at=result['created_at']
                )
                
                # 计算相似度（lanceDB返回的是距离）
                distance = result['_distance']
                similarity = 1.0 - distance  # 对于余弦距离
                
                search_result = SearchResult(
                    record=record,
                    similarity=similarity,
                    distance=distance,
                    rank=i + 1
                )
                search_results.append(search_result)
            
            logger.info(f"搜索完成，找到 {len(search_results)} 个结果")
            logger.info(f"  搜索耗时: {search_time:.3f}秒")
            
            return search_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def search_by_text(self, 
                       query_text: str, 
                       embedding_generator,
                       limit: int = 10,
                       filter_condition: Optional[str] = None) -> List[SearchResult]:
        """
        通过文本搜索
        
        Args:
            query_text: 查询文本
            embedding_generator: 嵌入生成器实例
            limit: 返回结果数量
            filter_condition: 过滤条件
            
        Returns:
            搜索结果列表
        """
        # 生成查询文本的嵌入向量
        logger.info(f"为查询文本生成嵌入向量: {query_text[:50]}...")
        
        embeddings = embedding_generator.generate_embeddings(
            [query_text], 
            [{'query': True}]
        )
        
        if not embeddings:
            logger.error("无法为查询文本生成嵌入向量")
            return []
        
        query_vector = embeddings[0].embedding
        
        # 搜索相似向量
        return self.search(query_vector, limit, filter_condition)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            self._ensure_imports()
            
            if self.table is None:
                return {'error': '表不存在'}
            
            stats = {
                'table_name': self.table_name,
                'total_records': self.table.count_rows(),
                'db_path': self.db_path,
                'vector_dimension': self.vector_dimension,
                'metric_type': self.metric_type
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {'error': str(e)}
    
    def delete_records(self, condition: str) -> int:
        """
        删除符合条件的记录
        
        Args:
            condition: 删除条件
            
        Returns:
            删除的记录数
        """
        try:
            self._ensure_imports()
            
            if self.table is None:
                logger.error("表不存在，无法删除")
                return 0
            
            logger.info(f"删除记录，条件: {condition}")
            
            # 获取删除前的记录数
            before_count = self.table.count_rows()
            
            # 执行删除
            self.table.delete(condition)
            
            # 获取删除后的记录数
            after_count = self.table.count_rows()
            deleted_count = before_count - after_count
            
            logger.info(f"删除完成，删除了 {deleted_count} 条记录")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            return 0
    
    def optimize_table(self) -> bool:
        """
        优化表性能
        
        Returns:
            是否优化成功
        """
        try:
            self._ensure_imports()
            
            if self.table is None:
                logger.error("表不存在，无法优化")
                return False
            
            logger.info("开始优化表性能...")
            start_time = time.time()
            
            # 压缩数据文件
            self.table.compact_files()
            
            optimize_time = time.time() - start_time
            logger.info(f"表优化完成，耗时: {optimize_time:.2f}秒")
            
            return True
            
        except Exception as e:
            logger.error(f"优化表失败: {e}")
            return False
    
    def export_records(self, output_path: str, limit: Optional[int] = None) -> int:
        """
        导出记录到文件
        
        Args:
            output_path: 输出文件路径
            limit: 导出数量限制
            
        Returns:
            导出的记录数
        """
        try:
            self._ensure_imports()
            
            if self.table is None:
                logger.error("表不存在，无法导出")
                return 0
            
            logger.info(f"导出记录到: {output_path}")
            
            # 查询数据
            query = self.table.to_arrow()
            if limit:
                query = query.limit(limit)
            
            # 转换为pandas DataFrame（如果可用）
            try:
                import pandas as pd
                df = query.to_pandas()
                
                # 保存到文件
                if output_path.endswith('.csv'):
                    df.to_csv(output_path, index=False, encoding='utf-8')
                elif output_path.endswith('.json'):
                    df.to_json(output_path, orient='records', force_ascii=False, indent=2)
                else:
                    # 默认保存为parquet
                    df.to_parquet(output_path)
                
                export_count = len(df)
                
            except ImportError:
                # 如果没有pandas，保存为JSON
                records = query.to_pylist()
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
                
                export_count = len(records)
            
            logger.info(f"导出完成，共 {export_count} 条记录")
            return export_count
            
        except Exception as e:
            logger.error(f"导出记录失败: {e}")
            return 0
    
    def _serialize_metadata(self, metadata: Dict) -> str:
        """序列化元数据为JSON字符串"""
        try:
            return json.dumps(metadata, ensure_ascii=False)
        except:
            return "{}"
    
    def _deserialize_metadata(self, metadata_str: str) -> Dict:
        """反序列化JSON字符串为元数据"""
        try:
            return json.loads(metadata_str)
        except:
            return {}


class VectorStoreManager:
    """向量存储管理器（高级封装）"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化向量存储管理器
        
        Args:
            config: 配置字典
        """
        if config is None:
            config = {
                'db_path': './data/lancedb',
                'table_name': 'obsidian_embeddings',
                'vector_dimension': 1024,
                'metric_type': 'cosine'
            }
        
        self.config = config
        self.vector_store = LanceDBVectorStore(**config)
        self.embedding_generator = None
        
        logger.info("初始化向量存储管理器")
    
    def setup(self, embedding_generator) -> bool:
        """
        设置管理器
        
        Args:
            embedding_generator: 嵌入生成器实例
            
        Returns:
            是否设置成功
        """
        self.embedding_generator = embedding_generator
        
        # 连接数据库
        if not self.vector_store.connect():
            return False
        
        return True
    
    def index_chunks(self, chunks: List[Dict], batch_size: int = 1000) -> Dict[str, Any]:
        """
        索引文本分块
        
        Args:
            chunks: 文本分块列表
            batch_size: 批量大小
            
        Returns:
            索引结果统计
        """
        if not self.embedding_generator:
            logger.error("未设置嵌入生成器")
            return {'error': '未设置嵌入生成器'}
        
        logger.info(f"开始索引 {len(chunks)} 个文本分块")
        start_time = time.time()
        
        # 生成嵌入向量
        embeddings = self.embedding_generator.generate_embeddings_for_chunks(chunks)
        
        if not embeddings:
            logger.error("无法生成嵌入向量")
            return {'error': '无法生成嵌入向量'}
        
        # 转换为字典格式
        embedding_dicts = [emb.to_dict() for emb in embeddings]
        
        # 添加到向量数据库
        inserted_count = self.vector_store.add_embeddings(embedding_dicts)
        
        total_time = time.time() - start_time
        
        result = {
            'total_chunks': len(chunks),
            'embeddings_generated': len(embeddings),
            'records_inserted': inserted_count,
            'total_time_seconds': total_time,
            'time_per_chunk_ms': total_time / len(chunks) * 1000 if chunks else 0,
            'success': inserted_count > 0
        }
        
        logger.info(f"索引完成: {result}")
        return result
    
    def search_similar(self, 
                       query: Union[str, np.ndarray], 
                       limit: int = 10,
                       filter_by_file: Optional[str] = None) -> List[SearchResult]:
        """
        搜索相似内容
        
        Args:
            query: 查询文本或向量
            limit: 返回结果数量
            filter_by_file: 按文件名过滤
            
        Returns:
            搜索结果列表
        """
        if not self.embedding_generator:
            logger.error("未设置嵌入生成器")
            return []
        
        # 构建过滤条件
        filter_condition = None
        if filter_by_file:
            filter_condition = f"file_name = '{filter_by_file}'"
        
        # 根据输入类型执行搜索
        if isinstance(query, str):
            # 文本搜索
            return self.vector_store.search_by_text(
                query, 
                self.embedding_generator, 
                limit, 
                filter_condition
            )
        elif isinstance(query, np.ndarray):
            # 向量搜索
            return self.vector_store.search(query, limit, filter_condition)
        else:
            logger.error(f"不支持的查询类型: {type(query)}")
            return []
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库信息
        
        Returns:
            数据库信息
        """
        stats = self.vector_store.get_stats()
        
        info = {
            'config': self.config,
            'stats': stats,
            'has_embedding_generator': self.embedding_generator is not None
        }
        
        return info
    
    def cleanup_old_records(self, days_old: int = 30) -> int:
        """
        清理旧记录
        
        Args:
            days_old: 保留天数
            
        Returns:
            删除的记录数
        """
        cutoff_time = time.time() - (days_old * 24 * 3600)
        condition = f"created_at < {cutoff_time}"
        
        return self.vector_store.delete_records(condition)
    
    def backup_database(self, backup_path: str) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份路径
            
        Returns:
            是否备份成功
        """
        try:
            import shutil
            
            logger.info(f"备份数据库到: {backup_path}")
            
            # 确保备份目录存在
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # 复制数据库文件
            if os.path.exists(self.config['db_path']):
                shutil.copytree(self.config['db_path'], backup_path, dirs_exist_ok=True)
                logger.info("数据库备份完成")
                return True
            else:
                logger.error("数据库路径不存在")
                return False
                
        except Exception as e:
            logger.error(f"备份数据库失败: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("lanceDB向量存储模块测试")
    print("=" * 60)
    
    try:
        # 测试向量记录
        print("\n1. 测试向量记录...")
        test_vector = np.random.randn(1024).astype(np.float32)
        test_record = VectorRecord(
            id="test_1",
            vector=test_vector,
            text="这是一个测试文本",
            chunk_id="test_chunk_1",
            file_path="/test/path.md",
            file_name="test.md",
            metadata={"test": True, "category": "demo"}
        )
        
        print(f"  记录ID: {test_record.id}")
        print(f"  文本: {test_record.text}")
        print(f"  向量形状: {test_record.vector.shape}")
        print(f"  元数据: {test_record.metadata}")
        
        # 测试序列化
        record_dict = test_record.to_dict()
        print(f"  序列化成功: {len(record_dict)} 个字段")
        
        # 测试向量存储
        print("\n2. 测试向量存储...")
        
        # 使用临时目录
        import tempfile
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_lancedb")
        
        vector_store = LanceDBVectorStore(
            db_path=db_path,
            table_name="test_embeddings",
            vector_dimension=1024
        )
        
        # 连接数据库
        if vector_store.connect():
            print(f"  ✅ 连接成功: {db_path}")
            
            # 创建表
            if vector_store.create_table():
                print(f"  ✅ 表创建成功")
                
                # 插入测试记录
                inserted = vector_store.add_records([test_record])
                if inserted > 0:
                    print(f"  ✅ 插入 {inserted} 条记录")
                    
                    # 获取统计信息
                    stats = vector_store.get_stats()
                    print(f"  📊 统计信息: {stats}")
                    
                    # 测试搜索
                    print("\n3. 测试搜索功能...")
                    search_results = vector_store.search(test_vector, limit=5)
                    
                    if search_results:
                        print(f"  ✅ 搜索到 {len(search_results)} 个结果")
                        for i, result in enumerate(search_results[:3]):
                            print(f"    结果 {i+1}: 相似度={result.similarity:.4f}, 文本={result.record.text[:50]}...")
                    else:
                        print("  ❌ 搜索失败")
                    
                    # 测试导出
                    print("\n4. 测试导出功能...")
                    export_path = os.path.join(temp_dir, "export.json")
                    exported = vector_store.export_records(export_path, limit=10)
                    
                    if exported > 0:
                        print(f"  ✅ 导出 {exported} 条记录到 {export_path}")
                    else:
                        print("  ❌ 导出失败")
                    
                else:
                    print("  ❌ 插入记录失败")
            else:
                print("  ❌ 创建表失败")
        else:
            print("  ❌ 连接数据库失败")
        
        # 测试管理器
        print("\n5. 测试向量存储管理器...")
        
        manager_config = {
            'db_path': os.path.join(temp_dir, "manager_lancedb"),
            'table_name': 'manager_test',
            'vector_dimension': 1024
        }
        
        manager = VectorStoreManager(manager_config)
        
        # 需要嵌入生成器来测试完整功能
        print("  ⚠️  需要嵌入生成器来测试完整索引功能")
        
        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n  🧹 清理临时目录: {temp_dir}")
        
        print("\n" + "=" * 60)
        print("✅ lanceDB向量存储模块基本功能测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()