#!/usr/bin/env python3
"""
环境测试脚本
测试环境搭建和文本提取功能
"""

import os
import sys
import yaml

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_extractor import TextExtractor
from chunk_processor import ChunkProcessor


def test_environment():
    """测试环境是否正常"""
    print("=" * 60)
    print("环境测试开始")
    print("=" * 60)
    
    # 测试1: 检查依赖
    print("\n1. 检查Python依赖...")
    try:
        import lancedb
        print(f"  ✓ lancedb版本: {lancedb.__version__}")
    except ImportError:
        print("  ✗ 未安装lancedb")
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        print(f"  ✓ sentence-transformers已安装")
    except ImportError:
        print("  ✗ 未安装sentence-transformers")
        return False
    
    try:
        import markdown
        print(f"  ✓ markdown版本: {markdown.__version__}")
    except ImportError:
        print("  ✗ 未安装markdown")
        return False
    
    try:
        import frontmatter
        print(f"  ✓ python-frontmatter已安装")
    except ImportError:
        print("  ✗ 未安装python-frontmatter")
        return False
    
    # 测试2: 检查测试数据
    print("\n2. 检查测试数据...")
    test_data_dir = "/tmp/obsidian_test_data/"
    if os.path.exists(test_data_dir):
        files = os.listdir(test_data_dir)
        md_files = [f for f in files if f.endswith('.md')]
        print(f"  ✓ 测试数据目录存在，包含 {len(md_files)} 个Markdown文件")
        
        # 显示文件列表
        print("  文件列表:")
        for i, file in enumerate(md_files[:5]):  # 只显示前5个
            print(f"    {i+1}. {file}")
        if len(md_files) > 5:
            print(f"    ... 还有 {len(md_files) - 5} 个文件")
    else:
        print(f"  ✗ 测试数据目录不存在: {test_data_dir}")
        return False
    
    # 测试3: 测试文本提取
    print("\n3. 测试文本提取...")
    extractor = TextExtractor()
    
    # 测试单个文件
    test_file = os.path.join(test_data_dir, "测试文件.md")
    if os.path.exists(test_file):
        result = extractor.extract_from_file(test_file)
        if result:
            print(f"  ✓ 成功提取文件: {result['file_info']['file_name']}")
            print(f"    内容预览: {result['content'][:50]}...")
        else:
            print(f"  ✗ 提取文件失败: {test_file}")
            return False
    else:
        print(f"  ✗ 测试文件不存在: {test_file}")
        return False
    
    # 测试目录提取
    results = extractor.extract_from_directory(test_data_dir)
    if results:
        print(f"  ✓ 成功提取目录，共 {len(results)} 个文件")
    else:
        print(f"  ✗ 目录提取失败")
        return False
    
    # 测试4: 测试分块处理
    print("\n4. 测试分块处理...")
    processor = ChunkProcessor(
        chunk_size=500,
        chunk_overlap=50,
        min_chunk_size=100,
        max_chunk_size=1000
    )
    
    # 使用第一个提取的结果进行测试
    if results:
        test_content = results[0]
        chunks = processor.chunk_text(
            test_content['content'],
            test_content['metadata'],
            test_content['file_info']
        )
        
        print(f"  ✓ 成功分块，生成 {len(chunks)} 个分块")
        if chunks:
            print(f"    第一个分块预览: {chunks[0].text[:100]}...")
    
    # 测试5: 处理所有提取的内容
    print("\n5. 批量处理测试...")
    all_chunks = processor.process_extracted_contents(results)
    print(f"  ✓ 批量处理完成，共生成 {len(all_chunks)} 个分块")
    
    # 统计信息
    total_chars = sum(len(chunk.text) for chunk in all_chunks)
    avg_chunk_size = total_chars / len(all_chunks) if all_chunks else 0
    
    print(f"    总字符数: {total_chars}")
    print(f"    平均分块大小: {avg_chunk_size:.1f} 字符")
    
    # 显示分块分布
    size_ranges = {
        "0-100": 0,
        "101-300": 0,
        "301-500": 0,
        "501-1000": 0,
        "1000+": 0
    }
    
    for chunk in all_chunks:
        size = len(chunk.text)
        if size <= 100:
            size_ranges["0-100"] += 1
        elif size <= 300:
            size_ranges["101-300"] += 1
        elif size <= 500:
            size_ranges["301-500"] += 1
        elif size <= 1000:
            size_ranges["501-1000"] += 1
        else:
            size_ranges["1000+"] += 1
    
    print("    分块大小分布:")
    for range_name, count in size_ranges.items():
        if count > 0:
            percentage = (count / len(all_chunks)) * 100
            print(f"      {range_name}字符: {count}个 ({percentage:.1f}%)")
    
    print("\n" + "=" * 60)
    print("环境测试完成！所有测试通过 ✓")
    print("=" * 60)
    
    return True


def save_test_results(chunks):
    """保存测试结果"""
    output_dir = "./data/test_results/"
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存分块信息
    chunks_data = []
    for chunk in chunks:
        chunks_data.append(chunk.to_dict())
    
    import json
    with open(os.path.join(output_dir, "chunks.json"), 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n测试结果已保存到: {output_dir}")
    
    # 生成统计报告
    report = {
        "total_chunks": len(chunks),
        "unique_files": len(set(chunk.file_name for chunk in chunks)),
        "avg_chunk_size": sum(len(chunk.text) for chunk in chunks) / len(chunks) if chunks else 0,
        "sample_chunks": [
            {
                "file": chunk.file_name,
                "text_preview": chunk.text[:100] + "..." if len(chunk.text) > 100 else chunk.text,
                "size": len(chunk.text)
            }
            for chunk in chunks[:5]  # 前5个作为示例
        ]
    }
    
    with open(os.path.join(output_dir, "report.json"), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return output_dir


if __name__ == "__main__":
    # 创建数据目录
    os.makedirs("./data", exist_ok=True)
    
    # 运行测试
    if test_environment():
        print("\n🎉 环境搭建和文本提取功能测试成功！")
        print("\n下一步计划:")
        print("1. 向量嵌入生成（使用sentence-transformers）")
        print("2. lanceDB索引构建")
        print("3. 语义搜索接口实现")
        print("4. 完整流程测试")
        
        # 如果需要保存测试结果，可以取消下面的注释
        # extractor = TextExtractor()
        # processor = ChunkProcessor()
        # results = extractor.extract_from_directory("/tmp/obsidian_test_data/")
        # chunks = processor.process_extracted_contents(results)
        # save_test_results(chunks)
    else:
        print("\n❌ 环境测试失败，请检查依赖和配置")
        sys.exit(1)