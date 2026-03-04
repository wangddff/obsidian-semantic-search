#!/usr/bin/env python3
"""
集成测试模块
集成文本提取→分块处理→向量嵌入→索引构建的完整流程
"""

import os
import sys
import time
import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import numpy as np

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.text_extractor import TextExtractor
from src.chunk_processor import ChunkProcessor
from src.embedding_generator import EmbeddingGenerator
from src.vector_store import VectorStoreManager, SearchResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('./data/logs/pipeline.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PipelineStats:
    """管道处理统计信息"""
    total_files: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    total_records: int = 0
    extraction_time: float = 0.0
    chunking_time: float = 0.0
    embedding_time: float = 0.0
    indexing_time: float = 0.0
    total_time: float = 0.0
    memory_peak_mb: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def summary(self) -> str:
        """生成摘要字符串"""
        return (
            f"管道处理统计:\n"
            f"  文件数: {self.total_files}\n"
            f"  分块数: {self.total_chunks}\n"
            f"  嵌入向量数: {self.total_embeddings}\n"
            f"  数据库记录数: {self.total_records}\n"
            f"  总耗时: {self.total_time:.2f}秒\n"
            f"  提取耗时: {self.extraction_time:.2f}秒\n"
            f"  分块耗时: {self.chunking_time:.2f}秒\n"
            f"  嵌入耗时: {self.embedding_time:.2f}秒\n"
            f"  索引耗时: {self.indexing_time:.2f}秒\n"
            f"  内存峰值: {self.memory_peak_mb:.1f}MB\n"
            f"  错误数: {len(self.errors)}"
        )


class ObsidianSemanticSearchPipeline:
    """Obsidian语义搜索管道"""
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """
        初始化管道
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 初始化组件
        self.text_extractor = None
        self.chunk_processor = None
        self.embedding_generator = None
        self.vector_store_manager = None
        
        # 统计信息
        self.stats = PipelineStats()
        
        logger.info("初始化Obsidian语义搜索管道")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info(f"加载配置文件: {self.config_path}")
            return config
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            # 返回默认配置
            return {
                'file_processing': {
                    'supported_extensions': ['.md', '.txt', '.markdown']
                },
                'text_processing': {
                    'chunk_size': 3000,
                    'chunk_overlap': 300,
                    'min_chunk_size': 2000,
                    'max_chunk_size': 4000,
                    'adaptive_chunking': True
                },
                'model': {
                    'api': {
                        'base_url': 'http://192.168.1.4:1234',
                        'model_name': 'text-embedding-bge-m3',
                        'timeout': 30,
                        'max_retries': 3
                    },
                    'batch_size': 10,
                    'use_concurrent': True
                },
                'lancedb': {
                    'db_path': './data/lancedb',
                    'table_name': 'obsidian_embeddings_bge_m3',
                    'vector_dimension': 1024,
                    'metric_type': 'cosine'
                }
            }
    
    def initialize_components(self) -> bool:
        """
        初始化所有组件
        
        Returns:
            是否初始化成功
        """
        logger.info("初始化管道组件...")
        
        try:
            # 1. 文本提取器
            logger.info("初始化文本提取器...")
            self.text_extractor = TextExtractor(
                supported_extensions=self.config['file_processing']['supported_extensions']
            )
            
            # 2. 分块处理器
            logger.info("初始化分块处理器...")
            self.chunk_processor = ChunkProcessor(
                chunk_size=self.config['text_processing']['chunk_size'],
                chunk_overlap=self.config['text_processing']['chunk_overlap'],
                min_chunk_size=self.config['text_processing']['min_chunk_size'],
                max_chunk_size=self.config['text_processing']['max_chunk_size']
            )
            
            # 3. 嵌入生成器
            logger.info("初始化嵌入生成器...")
            self.embedding_generator = EmbeddingGenerator(
                api_config=self.config['model']['api'],
                batch_size=self.config['model']['batch_size'],
                use_concurrent=self.config['model']['use_concurrent']
            )
            
            # 4. 向量存储管理器
            logger.info("初始化向量存储管理器...")
            self.vector_store_manager = VectorStoreManager(
                config=self.config['lancedb']
            )
            
            # 设置管理器
            if not self.vector_store_manager.setup(self.embedding_generator):
                logger.error("设置向量存储管理器失败")
                return False
            
            logger.info("✅ 所有组件初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化组件失败: {e}")
            return False
    
    def process_directory(self, directory_path: str, recursive: bool = True) -> PipelineStats:
        """
        处理目录中的所有文件
        
        Args:
            directory_path: 目录路径
            recursive: 是否递归处理子目录
            
        Returns:
            处理统计信息
        """
        if not os.path.exists(directory_path):
            logger.error(f"目录不存在: {directory_path}")
            self.stats.errors.append(f"目录不存在: {directory_path}")
            return self.stats
        
        # 确保组件已初始化
        if not self.text_extractor or not self.chunk_processor:
            if not self.initialize_components():
                return self.stats
        
        logger.info(f"开始处理目录: {directory_path}")
        logger.info(f"  递归模式: {recursive}")
        
        pipeline_start_time = time.time()
        
        try:
            # 1. 提取文件列表和内容
            logger.info("步骤1: 扫描文件并提取内容...")
            extraction_start = time.time()
            
            # 使用extract_from_directory直接提取内容
            all_documents = self.text_extractor.extract_from_directory(
                directory_path, 
                extensions=self.config['file_processing']['supported_extensions']
            )
            self.stats.total_files = len(all_documents)
            
            if not all_documents:
                logger.warning("未找到可处理的文件")
                return self.stats
            
            logger.info(f"  找到 {len(all_documents)} 个文件")
            
            # 2. 更新提取时间统计
            self.stats.extraction_time = time.time() - extraction_start
            logger.info(f"  提取完成: {len(all_documents)} 个文档，耗时 {self.stats.extraction_time:.2f}秒")
            
            if not all_documents:
                logger.error("没有成功提取的文档")
                return self.stats
            
            # 3. 分块处理
            logger.info("步骤3: 分块处理...")
            chunking_start = time.time()
            
            try:
                all_chunks = self.chunk_processor.process_extracted_contents(all_documents)
                logger.info(f"  分块完成: {len(all_chunks)} 个分块")
            except Exception as e:
                error_msg = f"分块处理失败: {e}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)
                all_chunks = []
            
            chunking_time = time.time() - chunking_start
            self.stats.chunking_time = chunking_time
            self.stats.total_chunks = len(all_chunks)
            logger.info(f"  分块完成: {len(all_chunks)} 个分块，耗时 {chunking_time:.2f}秒")
            
            if not all_chunks:
                logger.error("没有生成分块")
                return self.stats
            
            # 4. 生成嵌入向量
            logger.info("步骤4: 生成嵌入向量...")
            embedding_start = time.time()
            
            try:
                # 转换为字典格式
                chunk_dicts = []
                for chunk in all_chunks:
                    chunk_dicts.append({
                        'text': chunk.text,
                        'metadata': chunk.metadata,
                        'chunk_id': chunk.chunk_id,
                        'start_pos': chunk.start_pos,
                        'end_pos': chunk.end_pos,
                        'file_path': chunk.file_path,
                        'file_name': chunk.file_name,
                        'heading_context': chunk.heading_context
                    })
                
                embeddings = self.embedding_generator.generate_embeddings_for_chunks(chunk_dicts)
                embedding_time = time.time() - embedding_start
                self.stats.embedding_time = embedding_time
                self.stats.total_embeddings = len(embeddings)
                
                logger.info(f"  嵌入完成: {len(embeddings)} 个向量，耗时 {embedding_time:.2f}秒")
                
                if not embeddings:
                    logger.error("没有生成嵌入向量")
                    return self.stats
                
                # 5. 索引到向量数据库
                logger.info("步骤5: 索引到向量数据库...")
                indexing_start = time.time()
                
                # 转换为字典格式
                embedding_dicts = [emb.to_dict() for emb in embeddings]
                
                # 索引分块
                index_result = self.vector_store_manager.index_chunks(chunk_dicts)
                indexing_time = time.time() - indexing_start
                self.stats.indexing_time = indexing_time
                self.stats.total_records = index_result.get('records_inserted', 0)
                
                logger.info(f"  索引完成: {self.stats.total_records} 条记录，耗时 {indexing_time:.2f}秒")
                
                # 记录内存使用
                try:
                    import psutil
                    process = psutil.Process()
                    memory_info = process.memory_info()
                    self.stats.memory_peak_mb = memory_info.rss / 1024 / 1024
                except ImportError:
                    logger.warning("psutil未安装，无法记录内存使用")
                
            except Exception as e:
                error_msg = f"嵌入/索引失败: {e}"
                logger.error(error_msg)
                self.stats.errors.append(error_msg)
            
            # 计算总时间
            total_time = time.time() - pipeline_start_time
            self.stats.total_time = total_time
            
            logger.info("=" * 60)
            logger.info("管道处理完成!")
            logger.info(self.stats.summary())
            logger.info("=" * 60)
            
            return self.stats
            
        except Exception as e:
            error_msg = f"管道处理失败: {e}"
            logger.error(error_msg)
            self.stats.errors.append(error_msg)
            return self.stats
    
    def search(self, query: str, limit: int = 10, filter_by_file: Optional[str] = None) -> List[SearchResult]:
        """
        搜索相似内容
        
        Args:
            query: 查询文本
            limit: 返回结果数量
            filter_by_file: 按文件名过滤
            
        Returns:
            搜索结果列表
        """
        if not self.vector_store_manager:
            logger.error("向量存储管理器未初始化")
            return []
        
        logger.info(f"搜索查询: {query}")
        
        try:
            results = self.vector_store_manager.search_similar(
                query=query,
                limit=limit,
                filter_by_file=filter_by_file
            )
            
            logger.info(f"搜索完成，找到 {len(results)} 个结果")
            
            # 记录搜索结果
            for i, result in enumerate(results[:3]):
                logger.info(f"  结果 {i+1}: 相似度={result.similarity:.4f}, 文件={result.record.file_name}")
                logger.info(f"      文本: {result.record.text[:100]}...")
            
            return results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库信息
        
        Returns:
            数据库信息
        """
        if not self.vector_store_manager:
            return {'error': '向量存储管理器未初始化'}
        
        return self.vector_store_manager.get_database_info()
    
    def save_pipeline_state(self, output_path: str = "./data/pipeline_state.json"):
        """
        保存管道状态
        
        Args:
            output_path: 输出文件路径
        """
        state = {
            'config': self.config,
            'stats': self.stats.to_dict(),
            'timestamp': time.time(),
            'components_initialized': all([
                self.text_extractor is not None,
                self.chunk_processor is not None,
                self.embedding_generator is not None,
                self.vector_store_manager is not None
            ])
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        logger.info(f"管道状态已保存到: {output_path}")
    
    def load_pipeline_state(self, input_path: str = "./data/pipeline_state.json") -> bool:
        """
        加载管道状态
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            是否加载成功
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # 更新配置
            self.config = state.get('config', self.config)
            
            # 更新统计信息
            stats_data = state.get('stats', {})
            self.stats = PipelineStats(**stats_data)
            
            logger.info(f"管道状态已从 {input_path} 加载")
            return True
            
        except Exception as e:
            logger.error(f"加载管道状态失败: {e}")
            return False
    
    def run_test_pipeline(self, test_data_dir: str = "/tmp/obsidian_test_data") -> PipelineStats:
        """
        运行测试管道
        
        Args:
            test_data_dir: 测试数据目录
            
        Returns:
            处理统计信息
        """
        logger.info("=" * 60)
        logger.info("运行测试管道")
        logger.info("=" * 60)
        
        # 初始化组件
        if not self.initialize_components():
            logger.error("组件初始化失败")
            return self.stats
        
        # 处理测试数据
        stats = self.process_directory(test_data_dir, recursive=False)
        
        # 测试搜索功能
        if stats.total_records > 0:
            logger.info("\n测试搜索功能...")
            
            test_queries = [
                "Telegram命令授权",
                "OpenClaw配置",
                "人工智能",
                "知识管理"
            ]
            
            for query in test_queries:
                logger.info(f"\n搜索: {query}")
                results = self.search(query, limit=3)
                
                if results:
                    for i, result in enumerate(results):
                        logger.info(f"  结果 {i+1}: 相似度={result.similarity:.4f}")
                        logger.info(f"      文件: {result.record.file_name}")
                        logger.info(f"      文本: {result.record.text[:80]}...")
                else:
                    logger.info("  未找到相关结果")
        
        return stats


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'memory_samples': [],
            'cpu_samples': []
        }
    
    def start_monitoring(self):
        """开始监控"""
        self.metrics['start_time'] = time.time()
        logger.info("性能监控已启动")
    
    def record_sample(self):
        """记录性能样本"""
        try:
            import psutil
            process = psutil.Process()
            
            # 内存使用
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.metrics['memory_samples'].append(memory_mb)
            
            # CPU使用
            cpu_percent = process.cpu_percent(interval=0.1)
            self.metrics['cpu_samples'].append(cpu_percent)
            
        except ImportError:
            pass
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """停止监控并返回结果"""
        self.metrics['end_time'] = time.time()
        
        result = {
            'duration_seconds': self.metrics['end_time'] - self.metrics['start_time'],
            'memory_avg_mb': 0.0,
            'memory_max_mb': 0.0,
            'cpu_avg_percent': 0.0,
            'cpu_max_percent': 0.0
        }
        
        if self.metrics['memory_samples']:
            result['memory_avg_mb'] = sum(self.metrics['memory_samples']) / len(self.metrics['memory_samples'])
            result['memory_max_mb'] = max(self.metrics['memory_samples'])
        
        if self.metrics['cpu_samples']:
            result['cpu_avg_percent'] = sum(self.metrics['cpu_samples']) / len(self.metrics['cpu_samples'])
            result['cpu_max_percent'] = max(self.metrics['cpu_samples'])
        
        logger.info(f"性能监控结果: {result}")
        return result


def run_full_test():
    """运行完整测试"""
    print("=" * 60)
    print("Obsidian语义搜索管道 - 完整测试")
    print("=" * 60)
    
    try:
        # 创建管道
        pipeline = ObsidianSemanticSearchPipeline()
        
        # 初始化性能监控
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # 运行测试管道
        stats = pipeline.run_test_pipeline("/tmp/obsidian_test_data")
        
        # 停止监控
        perf_results = monitor.stop_monitoring()
        
        # 输出结果
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        
        print(f"\n📊 处理统计:")
        print(stats.summary())
        
        print(f"\n⚡ 性能监控:")
        print(f"  总时长: {perf_results['duration_seconds']:.2f}秒")
        print(f"  平均内存: {perf_results['memory_avg_mb']:.1f}MB")
        print(f"  峰值内存: {perf_results['memory_max_mb']:.1f}MB")
        print(f"  平均CPU: {perf_results['cpu_avg_percent']:.1f}%")
        print(f"  峰值CPU: {perf_results['cpu_max_percent']:.1f}%")
        
        # 获取数据库信息
        db_info = pipeline.get_database_info()
        print(f"\n🗄️  数据库信息:")
        print(f"  表名: {db_info.get('config', {}).get('table_name', 'N/A')}")
        print(f"  记录数: {db_info.get('stats', {}).get('total_records', 0)}")
        print(f"  路径: {db_info.get('config', {}).get('db_path', 'N/A')}")
        
        # 保存管道状态
        pipeline.save_pipeline_state()
        
        print("\n" + "=" * 60)
        
        # 验收检查
        print("\n✅ 验收检查:")
        
        checks = [
            ("文件处理", stats.total_files > 0, f"处理了 {stats.total_files} 个文件"),
            ("分块生成", stats.total_chunks > 0, f"生成了 {stats.total_chunks} 个分块"),
            ("嵌入向量", stats.total_embeddings > 0, f"生成了 {stats.total_embeddings} 个嵌入向量"),
            ("数据库记录", stats.total_records > 0, f"索引了 {stats.total_records} 条记录"),
            ("处理时间", stats.total_time < 30, f"总耗时 {stats.total_time:.2f}秒 (<30秒)"),
            ("内存使用", stats.memory_peak_mb < 2000, f"峰值内存 {stats.memory_peak_mb:.1f}MB (<2GB)")
        ]
        
        all_passed = True
        for check_name, condition, message in checks:
            status = "✅" if condition else "❌"
            print(f"  {status} {check_name}: {message}")
            if not condition:
                all_passed = False
        
        if all_passed:
            print("\n🎉 所有验收检查通过！管道运行成功！")
        else:
            print("\n⚠️  部分验收检查未通过，请检查问题。")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_existing_chunks():
    """使用现有分块数据进行测试"""
    print("=" * 60)
    print("使用现有分块数据测试")
    print("=" * 60)
    
    try:
        # 加载现有分块数据
        chunks_path = "./data/test_results/chunks.json"
        if not os.path.exists(chunks_path):
            print(f"分块数据文件不存在: {chunks_path}")
            return False
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"加载了 {len(chunks)} 个分块")
        
        # 创建管道
        pipeline = ObsidianSemanticSearchPipeline()
        
        # 初始化组件
        if not pipeline.initialize_components():
            print("组件初始化失败")
            return False
        
        # 直接索引分块
        print("\n直接索引分块数据...")
        start_time = time.time()
        
        index_result = pipeline.vector_store_manager.index_chunks(chunks)
        
        total_time = time.time() - start_time
        
        print(f"索引完成:")
        print(f"  分块数: {len(chunks)}")
        print(f"  插入记录: {index_result.get('records_inserted', 0)}")
        print(f"  耗时: {total_time:.2f}秒")
        
        # 测试搜索
        print("\n测试搜索功能...")
        test_query = "Telegram命令"
        results = pipeline.search(test_query, limit=5)
        
        if results:
            print(f"搜索 '{test_query}' 结果:")
            for i, result in enumerate(results):
                print(f"  {i+1}. 相似度: {result.similarity:.4f}")
                print(f"     文件: {result.record.file_name}")
                print(f"     文本: {result.record.text[:80]}...")
        else:
            print("未找到相关结果")
        
        return True
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 确保日志目录存在
    os.makedirs("./data/logs", exist_ok=True)
    
    print("选择测试模式:")
    print("  1. 完整管道测试（处理文件）")
    print("  2. 使用现有分块数据测试")
    print("  3. 仅测试组件")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    if choice == "1":
        success = run_full_test()
        sys.exit(0 if success else 1)
        
    elif choice == "2":
        success = test_with_existing_chunks()
        sys.exit(0 if success else 1)
        
    elif choice == "3":
        # 仅测试组件
        print("\n测试组件初始化...")
        pipeline = ObsidianSemanticSearchPipeline()
        
        if pipeline.initialize_components():
            print("✅ 所有组件初始化成功")
            
            # 测试嵌入生成器
            print("\n测试嵌入生成器...")
            test_result = pipeline.embedding_generator.test_model()
            print(f"  模型: {test_result['model_name']}")
            print(f"  维度: {test_result['embedding_dim']}")
            
            # 测试向量存储
            print("\n测试向量存储...")
            db_info = pipeline.vector_store_manager.get_database_info()
            print(f"  数据库路径: {db_info.get('config', {}).get('db_path', 'N/A')}")
            print(f"  表名: {db_info.get('config', {}).get('table_name', 'N/A')}")
            
            print("\n✅ 组件测试完成")
        else:
            print("❌ 组件初始化失败")
            
    else:
        print("无效选择")