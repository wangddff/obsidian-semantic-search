#!/usr/bin/env python3
"""
向量嵌入和存储基本功能测试
不依赖模型下载的简化测试
"""

import os
import sys
import json
import time
import numpy as np
from datetime import datetime

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_extractor import TextExtractor
from chunk_processor import ChunkProcessor


def test_basic_pipeline():
    """测试基本流程（不依赖模型下载）"""
    print("=" * 70)
    print("Obsidian语义搜索 - 基本功能测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 配置
    test_data_dir = "/tmp/obsidian_test_data/"
    output_dir = "./data/basic_test_results/"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n📄 步骤1: 文本提取和分块")
    print("-" * 40)
    
    start_time = time.time()
    
    # 检查缓存
    chunks_cache = os.path.join("./data/test_results/", "chunks.json")
    if os.path.exists(chunks_cache):
        print("使用缓存的分块结果...")
        with open(chunks_cache, 'r', encoding='utf-8') as f:
            chunks_data = json.load(f)
        print(f"✓ 从缓存加载 {len(chunks_data)} 个分块")
    else:
        print("重新生成分块...")
        extractor = TextExtractor()
        processor = ChunkProcessor()
        
        extracted_contents = extractor.extract_from_directory(test_data_dir)
        chunks = processor.process_extracted_contents(extracted_contents)
        chunks_data = [chunk.to_dict() for chunk in chunks]
        print(f"✓ 生成 {len(chunks_data)} 个分块")
    
    chunk_time = time.time() - start_time
    print(f"  耗时: {chunk_time:.2f}秒")
    
    # 保存分块数据
    chunks_output = os.path.join(output_dir, "chunks.json")
    with open(chunks_output, 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)
    print(f"  分块数据已保存: {chunks_output}")
    
    print("\n🔢 步骤2: 模拟向量生成")
    print("-" * 40)
    
    start_time = time.time()
    
    # 创建模拟的嵌入向量（用于测试存储功能）
    embeddings_data = []
    for i, chunk in enumerate(chunks_data):
        # 创建模拟的384维向量
        vector = np.random.randn(384).tolist()
        # 归一化
        norm = np.linalg.norm(vector)
        vector = (np.array(vector) / norm).tolist()
        
        embeddings_data.append({
            'chunk_id': chunk['chunk_id'],
            'text': chunk['text'][:500],  # 限制长度
            'embedding': vector,
            'file_path': chunk['file_path'],
            'file_name': chunk['file_name'],
            'metadata': chunk['metadata'],
            'model_name': 'all-MiniLM-L6-v2',
            'embedding_dim': 384
        })
    
    embed_time = time.time() - start_time
    print(f"✓ 模拟嵌入向量生成完成")
    print(f"  生成数量: {len(embeddings_data)}")
    print(f"  耗时: {embed_time:.2f}秒")
    
    # 保存模拟嵌入结果
    embeddings_output = os.path.join(output_dir, "simulated_embeddings.json")
    with open(embeddings_output, 'w', encoding='utf-8') as f:
        json.dump(embeddings_data, f, ensure_ascii=False, indent=2)
    print(f"  模拟嵌入结果已保存: {embeddings_output}")
    
    print("\n💾 步骤3: lanceDB向量存储测试")
    print("-" * 40)
    
    try:
        from vector_store import VectorStore
        
        start_time = time.time()
        
        print("初始化向量存储...")
        store = VectorStore(
            db_path="./data/test_vector_db",
            table_name="test_embeddings",
            vector_dimension=384,
            metric_type="cosine"
        )
        
        print("创建数据库表...")
        success = store.create_table(force_recreate=True)
        if not success:
            print("❌ 创建表失败")
            return False
        print(f"✓ 表创建成功")
        
        print(f"插入 {len(embeddings_data)} 个模拟嵌入向量...")
        inserted = store.insert_embeddings(embeddings_data)
        
        store_time = time.time() - start_time
        print(f"✓ 向量存储测试完成")
        print(f"  插入数量: {inserted}")
        print(f"  耗时: {store_time:.2f}秒")
        
        # 获取数据库统计
        stats = store.get_stats()
        print(f"  数据库统计:")
        print(f"    表名: {stats.get('table_name')}")
        print(f"    行数: {stats.get('row_count')}")
        
        # 测试搜索功能（使用模拟查询向量）
        print("\n🔍 步骤4: 向量搜索测试")
        print("-" * 40)
        
        # 创建模拟查询向量
        query_vector = np.random.randn(384).tolist()
        norm = np.linalg.norm(query_vector)
        query_vector = (np.array(query_vector) / norm).tolist()
        
        print("执行向量搜索...")
        search_results = store.search_similar(query_vector, limit=3)
        
        if search_results:
            print(f"✓ 搜索成功，找到 {len(search_results)} 个结果")
            for i, result in enumerate(search_results):
                print(f"  结果 {i+1}:")
                print(f"    文件: {result['file_name']}")
                print(f"    相似度: {result['similarity']:.4f}")
                print(f"    文本预览: {result['text'][:60]}...")
        else:
            print("⚠️  未找到搜索结果（可能是随机向量匹配度低）")
        
        print("\n📊 步骤5: 性能分析")
        print("-" * 40)
        
        total_time = chunk_time + embed_time + store_time
        total_chunks = len(chunks_data)
        
        print(f"总体性能:")
        print(f"  总处理时间: {total_time:.2f}秒")
        print(f"  总处理分块: {total_chunks}")
        print(f"  平均每个分块: {total_time/total_chunks*1000:.1f}毫秒")
        
        # 生成测试报告
        report = {
            'test_date': datetime.now().isoformat(),
            'test_type': 'basic_pipeline_without_model',
            'processing_stats': {
                'total_chunks': total_chunks,
                'simulated_embeddings': len(embeddings_data),
                'database_records': inserted,
                'total_time_seconds': round(total_time, 2),
                'avg_time_per_chunk_ms': round(total_time/total_chunks*1000, 1)
            },
            'database_stats': stats,
            'search_test': {
                'query_vector_used': True,
                'results_found': len(search_results) if search_results else 0
            },
            'output_files': {
                'chunks': chunks_output,
                'simulated_embeddings': embeddings_output,
                'database': './data/test_vector_db'
            },
            'next_steps': [
                "1. 下载并测试实际嵌入模型",
                "2. 实现增量更新功能",
                "3. 添加搜索接口和API",
                "4. 全量数据测试"
            ]
        }
        
        # 保存报告
        report_output = os.path.join(output_dir, "basic_pipeline_report.json")
        with open(report_output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ 测试报告已生成: {report_output}")
        
        print("\n" + "=" * 70)
        print("测试摘要")
        print("=" * 70)
        print(f"📁 测试数据: {len(chunks_data)} 个分块")
        print(f"🔢 模拟向量: {len(embeddings_data)} 个")
        print(f"💾 存储到DB: {inserted} 条记录")
        print(f"⏱️  总耗时: {total_time:.2f}秒")
        print(f"🔍 搜索测试: {'成功' if search_results else '未找到匹配'}")
        
        print("\n" + "=" * 70)
        print("✅ 基本功能测试成功完成！")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 向量存储测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_model_availability():
    """检查模型可用性"""
    print("\n🔍 检查模型可用性")
    print("-" * 40)
    
    try:
        from sentence_transformers import SentenceTransformer
        
        # 检查模型是否已缓存
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        model_name = "all-MiniLM-L6-v2"
        
        print(f"检查模型: {model_name}")
        
        # 尝试加载模型（会触发下载如果未缓存）
        print("尝试加载模型...")
        model = SentenceTransformer(model_name, device="cpu")
        
        print(f"✓ 模型加载成功")
        print(f"  向量维度: {model.get_sentence_embedding_dimension()}")
        print(f"  最大序列长度: {model.max_seq_length}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ 模型加载失败: {e}")
        print("\n💡 建议:")
        print("  1. 检查网络连接")
        print("  2. 手动下载模型: python -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer(\"all-MiniLM-L6-v2\")'")
        print("  3. 使用离线模式（如果已有缓存）")
        return False


if __name__ == "__main__":
    print("🚀 开始基本功能测试...")
    
    try:
        # 首先检查模型
        model_available = check_model_availability()
        
        if not model_available:
            print("\n⚠️ 模型不可用，进行基本功能测试（使用模拟向量）")
            if test_basic_pipeline():
                print("\n🎯 项目进展:")
                print("  ✅ 文本提取和分块模块: 完成")
                print("  ✅ 向量嵌入生成模块: 结构完成（需要模型）")
                print("  ✅ lanceDB向量存储模块: 完成")
                print("  ✅ 基本流程集成测试: 完成")
                
                print("\n📅 下一步:")
                print("  1. 解决模型下载问题")
                print("  2. 测试实际嵌入生成")
                print("  3. 实现语义搜索接口")
                print("  4. 性能优化")
        else:
            print("\n🎉 模型可用，可以进行完整测试")
            # 这里可以调用完整的测试流程
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)