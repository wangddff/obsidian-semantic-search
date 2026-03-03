#!/usr/bin/env python3
"""
向量嵌入生成模块
使用BGE-M3 API将文本分块转换为向量
"""

import os
import time
import logging
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass, asdict
try:
    from .bge_m3_client import BGE_M3_Client, BGE_M3_Config, EmbeddingResponse
except ImportError:
    # 直接导入，用于独立运行
    from bge_m3_client import BGE_M3_Client, BGE_M3_Config, EmbeddingResponse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """嵌入结果数据类"""
    chunk_id: str
    text: str
    embedding: np.ndarray
    metadata: Dict[str, Any]
    file_path: str
    file_name: str
    model_name: str
    embedding_dim: int
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于序列化"""
        result = asdict(self)
        # 将numpy数组转换为列表
        result['embedding'] = self.embedding.tolist()
        return result


class EmbeddingGenerator:
    """向量嵌入生成器"""
    
    def __init__(self, 
                 api_config: Optional[Dict[str, Any]] = None,
                 batch_size: int = 10,
                 use_concurrent: bool = True):
        """
        初始化嵌入生成器
        
        Args:
            api_config: API配置字典，包含以下字段：
                - base_url: API基础URL (默认: "http://192.168.1.4:1234")
                - model_name: 模型名称 (默认: "text-embedding-bge-m3")
                - timeout: 超时时间 (默认: 30)
                - max_retries: 最大重试次数 (默认: 3)
            batch_size: 批量大小
            use_concurrent: 是否使用并发处理
        """
        self.batch_size = batch_size
        self.use_concurrent = use_concurrent
        
        # 默认配置
        default_config = {
            'base_url': "http://192.168.1.4:1234",
            'model_name': "text-embedding-bge-m3",
            'timeout': 30,
            'max_retries': 3
        }
        
        # 合并配置
        if api_config:
            default_config.update(api_config)
        
        # 创建BGE-M3配置
        bge_config = BGE_M3_Config(
            base_url=default_config['base_url'],
            model_name=default_config['model_name'],
            timeout=default_config['timeout'],
            max_retries=default_config['max_retries'],
            batch_size=batch_size
        )
        
        logger.info(f"正在初始化BGE-M3客户端...")
        start_time = time.time()
        
        try:
            self.client = BGE_M3_Client(bge_config)
            self.embedding_dim = 1024  # BGE-M3固定维度
            
            load_time = time.time() - start_time
            logger.info(f"BGE-M3客户端初始化完成")
            logger.info(f"  API端点: {bge_config.base_url}/v1/embeddings")
            logger.info(f"  模型名称: {bge_config.model_name}")
            logger.info(f"  向量维度: {self.embedding_dim}")
            logger.info(f"  初始化时间: {load_time:.2f}秒")
            logger.info(f"  批量大小: {batch_size}")
            logger.info(f"  并发处理: {use_concurrent}")
            
            # 测试连通性
            if self.client.test_connectivity():
                logger.info("✅ API连通性测试通过")
            else:
                logger.warning("⚠️ API连通性测试失败，但继续初始化")
                
        except Exception as e:
            logger.error(f"BGE-M3客户端初始化失败: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str], metadata_list: List[Dict]) -> List[EmbeddingResult]:
        """
        为文本列表生成嵌入向量
        
        Args:
            texts: 文本列表
            metadata_list: 对应的元数据列表
            
        Returns:
            嵌入结果列表
        """
        if len(texts) != len(metadata_list):
            raise ValueError("文本列表和元数据列表长度必须相同")
        
        if not texts:
            return []
        
        logger.info(f"开始生成嵌入向量，文本数量: {len(texts)}")
        start_time = time.time()
        
        try:
            # 使用BGE-M3 API获取嵌入向量
            if self.use_concurrent:
                bge_responses = self.client.get_embeddings_concurrent(texts)
            else:
                bge_responses = self.client.get_embeddings_batch(texts)
            
            total_time = time.time() - start_time
            
            if len(bge_responses) != len(texts):
                logger.warning(f"API返回数量({len(bge_responses)})与请求数量({len(texts)})不匹配")
            
            # 计算统计信息
            successful_count = len(bge_responses)
            avg_request_time = 0
            if successful_count > 0:
                request_times = [r.request_time_ms for r in bge_responses if r.request_time_ms]
                if request_times:
                    avg_request_time = sum(request_times) / len(request_times)
            
            logger.info(f"嵌入向量生成完成，总耗时: {total_time:.2f}秒")
            logger.info(f"  成功数量: {successful_count}/{len(texts)}")
            logger.info(f"  平均API请求时间: {avg_request_time:.1f}ms")
            logger.info(f"  总向量数: {successful_count}")
            
            # 构建结果对象
            results = []
            for i, (text, metadata, bge_response) in enumerate(zip(texts, metadata_list, bge_responses)):
                # 从元数据中提取必要信息
                chunk_id = metadata.get('chunk_id', f'chunk_{i}')
                file_path = metadata.get('file_path', '')
                file_name = metadata.get('file_name', '')
                
                # 将列表转换为numpy数组
                embedding_array = np.array(bge_response.embedding, dtype=np.float32)
                
                # 归一化向量（便于余弦相似度计算）
                norm = np.linalg.norm(embedding_array)
                if norm > 0:
                    embedding_array = embedding_array / norm
                
                result = EmbeddingResult(
                    chunk_id=chunk_id,
                    text=text,
                    embedding=embedding_array,
                    metadata=metadata,
                    file_path=file_path,
                    file_name=file_name,
                    model_name=self.client.config.model_name,
                    embedding_dim=self.embedding_dim,
                    processing_time_ms=bge_response.request_time_ms or avg_request_time
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
    
    def generate_embeddings_for_chunks(self, chunks: List[Dict]) -> List[EmbeddingResult]:
        """
        为文本分块生成嵌入向量
        
        Args:
            chunks: 文本分块列表（字典格式）
            
        Returns:
            嵌入结果列表
        """
        # 提取文本和元数据
        texts = []
        metadata_list = []
        
        for chunk in chunks:
            texts.append(chunk['text'])
            
            # 构建元数据，处理可能缺失的字段
            metadata = {
                'chunk_id': chunk.get('chunk_id', 'unknown'),
                'file_path': chunk.get('file_path', ''),
                'file_name': chunk.get('file_name', ''),
                'original_metadata': chunk.get('metadata', {})
            }
            
            # 可选字段
            if 'start_pos' in chunk:
                metadata['start_pos'] = chunk['start_pos']
            if 'end_pos' in chunk:
                metadata['end_pos'] = chunk['end_pos']
            if 'heading_context' in chunk:
                metadata['heading_context'] = chunk['heading_context']
            
            metadata_list.append(metadata)
        
        return self.generate_embeddings(texts, metadata_list)
    
    def test_model(self, test_texts: List[str] = None) -> Dict:
        """
        测试模型功能
        
        Args:
            test_texts: 测试文本列表
            
        Returns:
            测试结果
        """
        if test_texts is None:
            test_texts = [
                "这是一个测试句子。",
                "语义搜索可以理解概念。",
                "Obsidian是一个知识管理工具。",
                "lanceDB是一个向量数据库。"
            ]
        
        logger.info("开始BGE-M3模型测试...")
        
        # 测试API连通性
        connectivity = self.client.test_connectivity()
        
        # 测试嵌入生成
        metadata_list = [{'test_id': i} for i in range(len(test_texts))]
        results = self.generate_embeddings(test_texts, metadata_list)
        
        # 测试相似度计算
        similarity_info = None
        if len(results) >= 2:
            emb1 = results[0].embedding
            emb2 = results[1].embedding
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            similarity_info = {
                'text1': test_texts[0],
                'text2': test_texts[1],
                'similarity': float(similarity)
            }
            
            logger.info(f"测试句子相似度: {similarity:.4f}")
        
        test_result = {
            'model_name': self.client.config.model_name,
            'embedding_dim': self.embedding_dim,
            'api_endpoint': f"{self.client.config.base_url}/v1/embeddings",
            'connectivity': connectivity,
            'test_texts': test_texts,
            'num_results': len(results),
            'embedding_shape': results[0].embedding.shape if results else None,
            'similarity': similarity_info
        }
        
        logger.info("BGE-M3模型测试完成")
        return test_result
    
    def save_embeddings(self, results: List[EmbeddingResult], output_path: str):
        """
        保存嵌入结果到文件
        
        Args:
            results: 嵌入结果列表
            output_path: 输出文件路径
        """
        import json
        
        # 转换为可序列化的字典列表
        serializable_results = [result.to_dict() for result in results]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"嵌入结果已保存到: {output_path}")
        logger.info(f"  保存数量: {len(results)}")
    
    def load_embeddings(self, input_path: str) -> List[EmbeddingResult]:
        """
        从文件加载嵌入结果
        
        Args:
            input_path: 输入文件路径
            
        Returns:
            嵌入结果列表
        """
        import json
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        results = []
        for item in data:
            # 转换回numpy数组
            embedding = np.array(item['embedding'])
            
            result = EmbeddingResult(
                chunk_id=item['chunk_id'],
                text=item['text'],
                embedding=embedding,
                metadata=item['metadata'],
                file_path=item['file_path'],
                file_name=item['file_name'],
                model_name=item['model_name'],
                embedding_dim=item['embedding_dim'],
                processing_time_ms=item['processing_time_ms']
            )
            results.append(result)
        
        logger.info(f"从 {input_path} 加载了 {len(results)} 个嵌入结果")
        return results


class MemoryOptimizedEmbeddingGenerator(EmbeddingGenerator):
    """内存优化的嵌入生成器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.memory_stats = {
            'total_texts_processed': 0,
            'total_batches_processed': 0,
            'peak_memory_mb': 0
        }
    
    def generate_embeddings_with_memory_control(self, texts: List[str], metadata_list: List[Dict], 
                                               max_memory_mb: int = 1024) -> List[EmbeddingResult]:
        """
        带内存控制的嵌入生成
        
        Args:
            texts: 文本列表
            metadata_list: 元数据列表
            max_memory_mb: 最大内存限制(MB)
            
        Returns:
            嵌入结果列表
        """
        logger.info(f"使用内存控制模式，最大内存: {max_memory_mb}MB")
        
        # 对于API调用，内存需求主要在向量存储，而不是模型
        # 估算内存需求：每个1024维向量约4KB
        estimated_memory_per_text = 1024 * 4 / 1024 / 1024  # MB (float32)
        batch_size = min(self.batch_size, int(max_memory_mb / estimated_memory_per_text / 2))
        
        if batch_size < 1:
            batch_size = 1
        
        logger.info(f"  估算每个文本内存: {estimated_memory_per_text:.2f}MB")
        logger.info(f"  调整批量大小: {batch_size} (原: {self.batch_size})")
        
        # 临时修改批量大小
        original_batch_size = self.batch_size
        self.batch_size = batch_size
        
        try:
            results = self.generate_embeddings(texts, metadata_list)
            return results
        finally:
            # 恢复原始批量大小
            self.batch_size = original_batch_size


if __name__ == "__main__":
    # 测试代码
    print("=" * 60)
    print("BGE-M3向量嵌入生成模块测试")
    print("=" * 60)
    
    try:
        # 初始化生成器
        generator = EmbeddingGenerator(
            api_config={
                'base_url': "http://192.168.1.4:1234",
                'model_name': "text-embedding-bge-m3",
                'timeout': 30,
                'max_retries': 3
            },
            batch_size=5,
            use_concurrent=True
        )
        
        # 测试模型
        test_result = generator.test_model()
        print(f"\n模型测试结果:")
        print(f"  模型名称: {test_result['model_name']}")
        print(f"  向量维度: {test_result['embedding_dim']}")
        print(f"  API端点: {test_result['api_endpoint']}")
        print(f"  连通性: {'✅ 通过' if test_result['connectivity'] else '❌ 失败'}")
        
        # 测试实际文本
        test_texts = [
            "人工智能是未来的发展方向。",
            "机器学习需要大量数据。",
            "深度学习是机器学习的一个分支。",
            "自然语言处理让计算机理解人类语言。",
            "BGE-M3是一个优秀的中文嵌入模型。"
        ]
        
        metadata_list = [
            {'chunk_id': 'test_1', 'file_name': 'test.md'},
            {'chunk_id': 'test_2', 'file_name': 'test.md'},
            {'chunk_id': 'test_3', 'file_name': 'test.md'},
            {'chunk_id': 'test_4', 'file_name': 'test.md'},
            {'chunk_id': 'test_5', 'file_name': 'test.md'}
        ]
        
        print(f"\n生成测试嵌入向量...")
        results = generator.generate_embeddings(test_texts, metadata_list)
        
        print(f"  生成数量: {len(results)}")
        print(f"  第一个向量形状: {results[0].embedding.shape}")
        print(f"  第一个向量前5个值: {results[0].embedding[:5]}")
        
        # 测试相似度
        if len(results) >= 2:
            emb1 = results[0].embedding
            emb2 = results[1].embedding
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            print(f"\n相似度测试:")
            print(f"  文本1: {test_texts[0]}")
            print(f"  文本2: {test_texts[1]}")
            print(f"  余弦相似度: {similarity:.4f}")
        
        # 测试保存和加载
        print(f"\n测试保存和加载...")
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        generator.save_embeddings(results, temp_path)
        loaded_results = generator.load_embeddings(temp_path)
        
        print(f"  保存文件: {temp_path}")
        print(f"  加载数量: {len(loaded_results)}")
        print(f"  数据一致性: {len(results) == len(loaded_results)}")
        
        # 清理临时文件
        os.unlink(temp_path)
        
        # 关闭客户端
        generator.client.close()
        
        print("\n" + "=" * 60)
        print("✅ BGE-M3向量嵌入生成模块测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()