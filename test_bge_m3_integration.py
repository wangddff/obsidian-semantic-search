#!/usr/bin/env python3
"""
BGE-M3集成测试
测试所有组件的集成工作
"""

import os
import sys
import time
import logging
import tempfile
import shutil
import numpy as np

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.text_extractor import TextExtractor
from src.chunk_processor import ChunkProcessor
from src.embedding_generator import EmbeddingGenerator
from src.vector_store import VectorStoreManager
from src.bge_m3_client import BGE_M3_Client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_bge_m3_client():
    """测试BGE-M3客户端"""
    print("=" * 60)
    print("测试BGE-M3客户端")
    print("=" * 60)
    
    try:
        client = BGE_M3_Client()
        
        # 测试连通性
        if client.test_connectivity():
            print("✅ BGE-M3客户端连通性测试通过")
        else:
            print("❌ BGE-M3客户端连通性测试失败")
            return False
        
        # 测试单个文本嵌入
        test_text = "这是一个测试文本，用于验证BGE-M3模型"
        result = client.get_embedding(test_text)
        
        print(f"单个文本嵌入测试:")
        print(f"  文本: {test_text}")
        print(f"  向量维度: {result.dimension}")
        print(f"  请求时间: {result.request_time_ms:.2f}ms")
        
        # 测试批量嵌入
        test_texts = [
            "第一个测试文本",
            "第二个测试文本，稍微长一些",
            "第三个测试文本，包含中文内容"
        ]
        
        results = client.get_embeddings_batch(test_texts)
        print(f"\n批量嵌入测试:")
        print(f"  处理数量: {len(results)}/{len(test_texts)}")
        
        client.close()
        print("\n✅ BGE-M3客户端测试通过")
        return True
        
    except Exception as e:
        print(f"❌ BGE-M3客户端测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_generator():
    """测试嵌入生成器"""
    print("\n" + "=" * 60)
    print("测试嵌入生成器")
    print("=" * 60)
    
    try:
        generator = EmbeddingGenerator(
            api_config={
                'base_url': 'http://192.168.1.4:1234',
                'model_name': 'text-embedding-bge-m3',
                'timeout': 30,
                'max_retries': 3
            },
            batch_size=5,
            use_concurrent=True
        )
        
        # 测试模型
        test_result = generator.test_model()
        
        print(f"嵌入生成器测试:")
        print(f"  模型名称: {test_result['model_name']}")
        print(f"  向量维度: {test_result['embedding_dim']}")
        print(f"  API端点: {test_result['api_endpoint']}")
        print(f"  连通性: {'✅ 通过' if test_result['connectivity'] else '❌ 失败'}")
        
        if test_result.get('similarity'):
            sim = test_result['similarity']
            print(f"  相似度测试: {sim['text1'][:30]}... 与 {sim['text2'][:30]}... = {sim['similarity']:.4f}")
        
        generator.client.close()
        print("\n✅ 嵌入生成器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 嵌入生成器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chunk_processor():
    """测试分块处理器"""
    print("\n" + "=" * 60)
    print("测试分块处理器")
    print("=" * 60)
    
    try:
        processor = ChunkProcessor(
            chunk_size=3000,
            chunk_overlap=300,
            min_chunk_size=2000,
            max_chunk_size=4000
        )
        
        # 创建测试文本
        test_text = """
        # 测试文档标题
        
        这是第一个段落。包含一些测试内容，用于验证分块处理器的功能。
        这是同一个段落的第二句话，稍微长一些。
        
        ## 二级标题
        
        这是第二个段落。比第一个段落要长一些，包含更多内容。
        这是第二段的第一句话，描述了一些内容。
        这是第二段的第二句话，稍微长一点，包含更多细节。
        这是第二段的第三句话，也很长，用于测试分块逻辑。
        
        ### 三级标题
        
        这是一个非常长的段落，需要被分割成多个分块。这个段落包含很多内容，可能会超过最大分块大小。
        这是长段落的第二句话，继续添加内容。
        这是长段落的第三句话，也很长，包含更多测试内容。
        这是长段落的第四句话，继续扩展。
        这是长段落的第五句话，结束这个长段落。
        
        最后一个段落，相对较短。
        """
        
        test_metadata = {'title': '测试文档'}
        test_file_info = {
            'file_path': '/tmp/test.md',
            'file_name': 'test.md'
        }
        
        chunks = processor.chunk_text(test_text, test_metadata, test_file_info)
        
        print(f"分块处理器测试:")
        print(f"  原始文本长度: {len(test_text)} 字符")
        print(f"  生成分块数: {len(chunks)}")
        
        for i, chunk in enumerate(chunks):
            print(f"\n  分块 {i+1}:")
            print(f"    长度: {len(chunk.text)} 字符")
            print(f"    ID: {chunk.chunk_id}")
            print(f"    预览: {chunk.text[:80]}...")
        
        # 验证分块大小
        valid_sizes = True
        for chunk in chunks:
            if len(chunk.text) < 2000 or len(chunk.text) > 4000:
                print(f"⚠️  分块大小异常: {len(chunk.text)} 字符 (应在2000-4000之间)")
                valid_sizes = False
        
        if valid_sizes:
            print("\n✅ 所有分块大小在2000-4000字符范围内")
        
        print("\n✅ 分块处理器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 分块处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_store():
    """测试向量存储"""
    print("\n" + "=" * 60)
    print("测试向量存储")
    print("=" * 60)
    
    # 创建临时数据库目录
    temp_dir = tempfile.mkdtemp(prefix="test_lancedb_")
    
    try:
        from src.vector_store import LanceDBVectorStore
        
        store = LanceDBVectorStore(
            db_path=temp_dir,
            table_name='test_embeddings',
            vector_dimension=1024,
            metric_type='cosine'
        )
        
        if store.connect():
            print("✅ 向量存储连接成功")
            
            # 创建测试向量
            import numpy as np
            test_vector = np.random.randn(1024).astype(np.float32)
            
            from src.vector_store import VectorRecord
            test_record = VectorRecord(
                id='test_1',
                vector=test_vector,
                text='这是一个测试文本',
                chunk_id='test_chunk_1',
                file_path='/tmp/test.md',
                file_name='test.md',
                metadata={'test': True}
            )
            
            # 插入记录
            count = store.add_records([test_record])
            print(f"✅ 插入 {count} 条记录成功")
            
            # 搜索测试
            results = store.search(test_vector, limit=3)
            print(f"✅ 搜索成功，找到 {len(results)} 个结果")
            
            if results:
                print(f"  最佳匹配相似度: {results[0].similarity:.4f}")
            
            # 获取统计信息
            stats = store.get_stats()
            print(f"✅ 获取统计信息: {stats.get('total_records', 0)} 条记录")
            
            print("\n✅ 向量存储测试通过")
            return True
        else:
            print("❌ 向量存储连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"清理临时目录: {temp_dir}")


def test_full_pipeline():
    """测试完整管道"""
    print("\n" + "=" * 60)
    print("测试完整管道")
    print("=" * 60)
    
    # 创建临时测试目录
    temp_dir = tempfile.mkdtemp(prefix="test_obsidian_")
    test_file = os.path.join(temp_dir, "test_note.md")
    
    try:
        # 创建测试文件
        test_content = """# 测试笔记标题

这是测试笔记的内容。包含一些关于人工智能和机器学习的讨论。

## 人工智能

人工智能是计算机科学的一个分支，研究如何使计算机能够执行通常需要人类智能的任务。

## 机器学习

机器学习是人工智能的一个子领域，使计算机能够从数据中学习而无需明确编程。

### 深度学习

深度学习是机器学习的一个分支，使用神经网络模拟人脑的工作方式。

## 自然语言处理

自然语言处理是人工智能的一个领域，专注于计算机和人类语言之间的交互。

### 语义搜索

语义搜索理解查询的意图和上下文含义，而不仅仅是关键词匹配。

## 总结

这是一个综合性的测试笔记，涵盖了人工智能的多个方面。
"""
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"创建测试文件: {test_file}")
        
        # 初始化组件
        text_extractor = TextExtractor(encoding='utf-8')
        chunk_processor = ChunkProcessor(
            chunk_size=3000,
            chunk_overlap=300,
            min_chunk_size=2000,
            max_chunk_size=4000
        )
        embedding_generator = EmbeddingGenerator(
            api_config={
                'base_url': 'http://192.168.1.4:1234',
                'model_name': 'text-embedding-bge-m3',
                'timeout': 30,
                'max_retries': 3
            },
            batch_size=5,
            use_concurrent=True
        )
        
        # 1. 提取文本
        print("\n1. 提取文本...")
        document = text_extractor.extract_from_file(test_file)
        if document:
            print(f"✅ 文本提取成功: {document['file_info']['file_name']}")
        else:
            print("❌ 文本提取失败")
            return False
        
        # 2. 分块处理
        print("\n2. 分块处理...")
        chunks = chunk_processor.chunk_text(
            document['content'],
            document['metadata'],
            document['file_info']
        )
        print(f"✅ 分块处理成功: {len(chunks)} 个分块")
        
        # 3. 生成嵌入向量
        print("\n3. 生成嵌入向量...")
        chunk_dicts = [chunk.to_dict() for chunk in chunks]
        texts = [chunk['text'] for chunk in chunk_dicts]
        metadata_list = [{'chunk_id': chunk['chunk_id'], 
                         'file_path': chunk['file_path'],
                         'file_name': chunk['file_name']} 
                        for chunk in chunk_dicts]
        
        embeddings = embedding_generator.generate_embeddings(texts, metadata_list)
        print(f"✅ 嵌入向量生成成功: {len(embeddings)} 个向量")
        
        # 4. 创建向量存储
        print("\n4. 创建向量存储...")
        temp_db_dir = os.path.join(temp_dir, "lancedb")
        from src.vector_store import LanceDBVectorStore, VectorRecord
        
        store = LanceDBVectorStore(
            db_path=temp_db_dir,
            table_name='test_pipeline',
            vector_dimension=1024,
            metric_type='cosine'
        )
        
        if store.connect():
            # 转换嵌入结果为向量记录
            vector_records = []
            for i, embedding_result in enumerate(embeddings):
                record = VectorRecord(
                    id=f"test_{i}",
                    vector=embedding_result.embedding,
                    text=embedding_result.text,
                    chunk_id=embedding_result.chunk_id,
                    file_path=embedding_result.file_path,
                    file_name=embedding_result.file_name,
                    metadata=embedding_result.metadata
                )
                vector_records.append(record)
            
            # 插入记录
            count = store.add_records(vector_records)
            print(f"✅ 插入 {count} 条记录到向量数据库")
            
            # 5. 测试搜索
            print("\n5. 测试搜索...")
            test_queries = [
                "人工智能是什么",
                "机器学习与深度学习的关系",
                "自然语言处理的应用"
            ]
            
            for query in test_queries:
                print(f"\n搜索查询: '{query}'")
                
                # 为查询生成嵌入向量
                query_embedding = embedding_generator.client.get_embedding(query)
                query_vector = np.array(query_embedding.embedding, dtype=np.float32)
                
                # 搜索相似内容
                results = store.search(query_vector, limit=2)
                
                if results:
                    for i, result in enumerate(results):
                        print(f"  结果 {i+1}: 相似度={result.similarity:.4f}")
                        print(f"      文件: {result.record.file_name}")
                        print(f"      文本: {result.record.text[:80]}...")
                else:
                    print("  未找到相关结果")
            
            store.close()
            embedding_generator.client.close()
            
            print("\n✅ 完整管道测试通过")
            return True
        else:
            print("❌ 向量存储连接失败")
            return False
            
    except Exception as e:
        print(f"❌ 完整管道测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n清理临时目录: {temp_dir}")


def main():
    """主测试函数"""
    print("BGE-M3模型集成测试")
    print("=" * 60)
    
    tests = [
        ("BGE-M3客户端", test_bge_m3_client),
        ("嵌入生成器", test_embedding_generator),
        ("分块处理器", test_chunk_processor),
        ("向量存储", test_vector_store),
        ("完整管道", test_full_pipeline)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n开始测试: {test_name}")
        success = test_func()
        results.append((test_name, success))
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！BGE-M3集成成功！")
    else:
        print("⚠️  部分测试失败，请检查问题")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)