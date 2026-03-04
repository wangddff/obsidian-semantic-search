#!/usr/bin/env python3
"""
测试小批量处理
"""

import os
import sys
import time

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from pipeline_integration import ObsidianSemanticSearchPipeline

def test_small_batch():
    """测试小批量处理"""
    print("🚀 开始小批量测试...")
    
    # 初始化管道
    pipeline = ObsidianSemanticSearchPipeline("./config/config.yaml")
    if not pipeline.initialize_components():
        print("❌ 初始化组件失败")
        return False
    
    # 只处理少量文件
    test_files = [
        "/Users/wangdf/workshop/obsidian-vault/当前Openclaw 拥有的技能.md",
        "/Users/wangdf/workshop/obsidian-vault/欢迎.md",
        "/Users/wangdf/workshop/obsidian-vault/测试文件.md",
        "/Users/wangdf/workshop/obsidian-vault/测试的文章.md"
    ]
    
    # 检查文件是否存在
    existing_files = []
    for file_path in test_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"✅ 找到文件: {os.path.basename(file_path)}")
        else:
            print(f"❌ 文件不存在: {file_path}")
    
    if not existing_files:
        print("❌ 没有找到测试文件")
        return False
    
    print(f"\n📄 将处理 {len(existing_files)} 个文件")
    
    # 处理文件
    start_time = time.time()
    
    # 提取文本
    from text_extractor import TextExtractor
    extractor = TextExtractor()
    
    all_documents = []
    for file_path in existing_files:
        try:
            content = extractor.extract_from_file(file_path)
            if content and content.get('content'):
                all_documents.append(content)
                print(f"  提取成功: {os.path.basename(file_path)}")
            else:
                print(f"  提取失败或内容为空: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"  提取异常: {os.path.basename(file_path)} - {e}")
    
    if not all_documents:
        print("❌ 没有成功提取的文档")
        return False
    
    # 分块处理
    from chunk_processor import ChunkProcessor
    chunk_processor = ChunkProcessor(
        chunk_size=3000,
        chunk_overlap=300,
        min_chunk_size=2000,
        max_chunk_size=4000
    )
    
    all_chunks = chunk_processor.process_extracted_contents(all_documents)
    print(f"🔪 生成 {len(all_chunks)} 个分块")
    
    # 生成嵌入向量
    print("🔢 生成嵌入向量...")
    embeddings = pipeline.embedding_generator.generate_embeddings_for_chunks(all_chunks)
    print(f"✅ 生成 {len(embeddings)} 个嵌入向量")
    
    # 存储到向量数据库
    print("💾 存储到向量数据库...")
    inserted = pipeline.vector_store_manager.vector_store.add_embeddings(
        [emb.to_dict() for emb in embeddings]
    )
    print(f"✅ 插入 {inserted} 条记录")
    
    total_time = time.time() - start_time
    print(f"\n⏱️  总耗时: {total_time:.2f}秒")
    
    # 测试搜索
    print("\n🔍 测试搜索功能...")
    test_queries = [
        "OpenClaw技能",
        "测试内容",
        "欢迎信息"
    ]
    
    for query in test_queries:
        print(f"\n搜索: '{query}'")
        results = pipeline.search(query, limit=3)
        if results:
            for i, result in enumerate(results):
                print(f"  {i+1}. {result.record.file_name} (相似度: {result.similarity:.3f})")
                print(f"     文本: {result.record.text[:80]}...")
        else:
            print("  未找到相关结果")
    
    return True

if __name__ == "__main__":
    if test_small_batch():
        print("\n🎉 小批量测试成功完成！")
    else:
        print("\n❌ 小批量测试失败")
        sys.exit(1)