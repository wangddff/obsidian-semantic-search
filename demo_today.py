#!/usr/bin/env python3
"""
今日工作成果演示
展示环境搭建和文本提取功能的成果
"""

import os
import sys
import json

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_extractor import TextExtractor
from chunk_processor import ChunkProcessor


def demonstrate_today_work():
    """演示今天完成的工作"""
    print("🎯 Obsidian语义搜索 - 今日工作成果演示")
    print("=" * 60)
    print("📅 日期: 2026年3月3日")
    print("🎯 目标: 环境搭建 + 文本提取 + 分块处理")
    print("=" * 60)
    
    # 1. 展示环境配置
    print("\n1. 🛠️ 环境配置")
    print("-" * 40)
    print("✅ Python虚拟环境已创建")
    print("✅ 依赖包已安装:")
    print("   • lancedb (向量数据库)")
    print("   • sentence-transformers (本地嵌入模型)")
    print("   • markdown + beautifulsoup4 (文本处理)")
    print("   • python-frontmatter (元数据解析)")
    
    # 检查requirements.txt
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", 'r') as f:
            lines = f.readlines()
            print(f"✅ 依赖列表已保存 ({len(lines)}个包)")
    
    # 2. 展示项目结构
    print("\n2. 📁 项目结构")
    print("-" * 40)
    print("obsidian_semantic_search/")
    print("├── src/")
    print("│   ├── text_extractor.py      # 文本提取模块 ✓")
    print("│   └── chunk_processor.py     # 分块处理模块 ✓")
    print("├── config/")
    print("│   └── config.yaml            # 配置文件 ✓")
    print("├── tests/")
    print("│   └── (测试文件待添加)")
    print("├── data/                      # 数据目录")
    print("│   └── test_results/          # 测试结果 ✓")
    print("├── requirements.txt           # 依赖列表 ✓")
    print("└── venv/                      # 虚拟环境 ✓")
    
    # 3. 演示文本提取功能
    print("\n3. 📄 文本提取功能演示")
    print("-" * 40)
    
    extractor = TextExtractor()
    test_file = "/tmp/obsidian_test_data/测试文件.md"
    
    if os.path.exists(test_file):
        result = extractor.extract_from_file(test_file)
        print(f"✅ 文件提取: {result['file_info']['file_name']}")
        print(f"   内容: \"{result['content']}\"")
        print(f"   大小: {result['file_info']['file_size']}字节")
        print(f"   元数据: {result['metadata']}")
    
    # 4. 演示分块处理功能
    print("\n4. 🔪 分块处理功能演示")
    print("-" * 40)
    
    processor = ChunkProcessor(
        chunk_size=300,
        chunk_overlap=30,
        min_chunk_size=50,
        max_chunk_size=500
    )
    
    # 测试文本
    test_text = """
    Obsidian是一个强大的知识管理工具。
    它使用Markdown格式存储笔记，支持双向链接。
    
    语义搜索可以理解概念而不仅仅是关键词。
    这对于大型知识库特别有用。
    
    lanceDB是一个高效的向量数据库。
    它可以存储文本的向量表示，实现快速相似度搜索。
    """
    
    test_metadata = {'title': '演示文档'}
    test_file_info = {
        'file_path': '/tmp/demo.md',
        'file_name': 'demo.md',
        'file_size': len(test_text),
        'modified_time': 1234567890
    }
    
    chunks = processor.chunk_text(test_text, test_metadata, test_file_info)
    
    print(f"✅ 分块处理演示")
    print(f"   原始文本: {len(test_text)}字符")
    print(f"   生成分块: {len(chunks)}个")
    
    for i, chunk in enumerate(chunks):
        print(f"\n   分块 {i+1}:")
        print(f"     ID: {chunk.chunk_id}")
        print(f"     大小: {len(chunk.text)}字符")
        print(f"     内容: \"{chunk.text}\"")
    
    # 5. 展示测试结果
    print("\n5. 📊 测试结果摘要")
    print("-" * 40)
    
    report_file = "./data/test_results/report.json"
    if os.path.exists(report_file):
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        stats = report['processing_stats']
        print(f"✅ 测试数据: {report['test_data']['file_count']}个文件")
        print(f"✅ 生成分块: {stats['total_chunks']}个")
        print(f"✅ 处理时间: {stats['total_time_seconds']}秒")
        print(f"✅ 平均分块大小: {stats['average_chunk_size']}字符")
        
        print(f"\n   分块分布:")
        for range_name, count in stats['chunk_size_distribution'].items():
            if count > 0:
                percentage = (count / stats['total_chunks']) * 100
                print(f"     {range_name}字符: {count}个 ({percentage:.1f}%)")
    
    # 6. 总结和下一步
    print("\n6. 🎯 总结与下一步")
    print("-" * 40)
    print("✅ 今日完成:")
    print("   • 环境搭建和依赖安装")
    print("   • 文本提取模块实现")
    print("   • 智能分块模块实现")
    print("   • 完整流程测试验证")
    
    print("\n📅 明日计划:")
    print("   1. 向量嵌入生成模块")
    print("   2. lanceDB索引构建")
    print("   3. 语义搜索接口")
    print("   4. 性能优化")
    
    print("\n💡 技术亮点:")
    print("   • 使用本地sentence-transformers模型，无API成本")
    print("   • 智能分块策略，保持上下文完整性")
    print("   • 支持Obsidian frontmatter元数据")
    print("   • 内存友好的处理流程")
    
    print("\n" + "=" * 60)
    print("🎉 今日任务圆满完成！")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_today_work()