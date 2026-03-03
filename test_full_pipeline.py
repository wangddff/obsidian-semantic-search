#!/usr/bin/env python3
"""
完整流程测试脚本
测试从文本提取到分块处理的完整流程
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_extractor import TextExtractor
from chunk_processor import ChunkProcessor


def test_full_pipeline():
    """测试完整流程"""
    print("=" * 70)
    print("Obsidian语义搜索 - 完整流程测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 配置
    test_data_dir = "/tmp/obsidian_test_data/"
    output_dir = "./data/test_results/"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 步骤1: 文本提取
    print("\n📄 步骤1: 文本提取")
    print("-" * 40)
    
    start_time = time.time()
    extractor = TextExtractor()
    
    print("正在提取文本内容...")
    extracted_contents = extractor.extract_from_directory(test_data_dir)
    
    extract_time = time.time() - start_time
    print(f"✓ 文本提取完成")
    print(f"  处理文件数: {len(extracted_contents)}")
    print(f"  耗时: {extract_time:.2f}秒")
    print(f"  平均每个文件: {extract_time/len(extracted_contents):.2f}秒" if extracted_contents else "N/A")
    
    # 保存提取结果
    extract_output = os.path.join(output_dir, "extracted_contents.json")
    with open(extract_output, 'w', encoding='utf-8') as f:
        # 只保存必要信息，避免文件过大
        simplified = []
        for content in extracted_contents:
            simplified.append({
                'file_name': content['file_info']['file_name'],
                'file_path': content['file_info']['file_path'],
                'content_preview': content['content'][:200] + "..." if len(content['content']) > 200 else content['content'],
                'content_length': len(content['content']),
                'metadata': content['metadata']
            })
        json.dump(simplified, f, ensure_ascii=False, indent=2)
    
    print(f"  提取结果已保存: {extract_output}")
    
    # 步骤2: 分块处理
    print("\n🔪 步骤2: 分块处理")
    print("-" * 40)
    
    start_time = time.time()
    processor = ChunkProcessor(
        chunk_size=500,
        chunk_overlap=50,
        min_chunk_size=100,
        max_chunk_size=1000
    )
    
    print("正在分块处理...")
    chunks = processor.process_extracted_contents(extracted_contents)
    
    chunk_time = time.time() - start_time
    print(f"✓ 分块处理完成")
    print(f"  生成分块数: {len(chunks)}")
    print(f"  耗时: {chunk_time:.2f}秒")
    print(f"  平均每个分块: {chunk_time/len(chunks):.3f}秒" if chunks else "N/A")
    
    # 统计信息
    total_chars = sum(len(chunk.text) for chunk in chunks)
    avg_chunk_size = total_chars / len(chunks) if chunks else 0
    
    print(f"  总字符数: {total_chars}")
    print(f"  平均分块大小: {avg_chunk_size:.1f}字符")
    
    # 分块大小分布
    size_ranges = {
        "0-100": 0,
        "101-300": 0,
        "301-500": 0,
        "501-1000": 0,
        "1000+": 0
    }
    
    for chunk in chunks:
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
    
    print("  分块大小分布:")
    for range_name, count in size_ranges.items():
        if count > 0:
            percentage = (count / len(chunks)) * 100
            print(f"    {range_name}字符: {count}个 ({percentage:.1f}%)")
    
    # 保存分块结果
    chunk_output = os.path.join(output_dir, "chunks.json")
    chunks_data = [chunk.to_dict() for chunk in chunks]
    with open(chunk_output, 'w', encoding='utf-8') as f:
        json.dump(chunks_data, f, ensure_ascii=False, indent=2)
    
    print(f"  分块结果已保存: {chunk_output}")
    
    # 步骤3: 生成测试报告
    print("\n📊 步骤3: 生成测试报告")
    print("-" * 40)
    
    # 收集样本
    sample_chunks = []
    for i, chunk in enumerate(chunks[:5]):  # 取前5个作为样本
        sample_chunks.append({
            'chunk_id': chunk.chunk_id,
            'file_name': chunk.file_name,
            'text_preview': chunk.text[:150] + "..." if len(chunk.text) > 150 else chunk.text,
            'text_length': len(chunk.text),
            'heading_context': chunk.heading_context
        })
    
    # 生成报告
    report = {
        'test_date': datetime.now().isoformat(),
        'test_data': {
            'directory': test_data_dir,
            'file_count': len(extracted_contents),
            'file_names': [content['file_info']['file_name'] for content in extracted_contents]
        },
        'processing_stats': {
            'extraction_time_seconds': round(extract_time, 2),
            'chunking_time_seconds': round(chunk_time, 2),
            'total_time_seconds': round(extract_time + chunk_time, 2),
            'total_chunks': len(chunks),
            'total_characters': total_chars,
            'average_chunk_size': round(avg_chunk_size, 1),
            'chunk_size_distribution': size_ranges
        },
        'sample_chunks': sample_chunks,
        'output_files': {
            'extracted_contents': extract_output,
            'chunks': chunk_output,
            'report': os.path.join(output_dir, "report.json")
        },
        'next_steps': [
            "1. 向量嵌入生成（使用sentence-transformers模型）",
            "2. lanceDB索引构建",
            "3. 语义搜索接口实现",
            "4. 性能优化和测试"
        ]
    }
    
    # 保存报告
    report_output = os.path.join(output_dir, "report.json")
    with open(report_output, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 测试报告已生成")
    print(f"  报告文件: {report_output}")
    
    # 显示摘要
    print("\n" + "=" * 70)
    print("测试摘要")
    print("=" * 70)
    print(f"📁 测试数据: {len(extracted_contents)} 个文件")
    print(f"🔪 生成分块: {len(chunks)} 个")
    print(f"⏱️  总耗时: {extract_time + chunk_time:.2f}秒")
    print(f"📊 平均分块大小: {avg_chunk_size:.1f}字符")
    print(f"💾 输出文件保存在: {output_dir}")
    
    # 显示样本
    print("\n📋 样本分块:")
    for i, sample in enumerate(sample_chunks):
        print(f"\n  {i+1}. {sample['file_name']} (ID: {sample['chunk_id']})")
        print(f"     大小: {sample['text_length']}字符")
        print(f"     预览: {sample['text_preview']}")
        if sample['heading_context']:
            print(f"     标题: {', '.join(sample['heading_context'])}")
    
    print("\n" + "=" * 70)
    print("✅ 完整流程测试成功完成！")
    print("=" * 70)
    
    return True


def check_memory_usage():
    """检查内存使用情况"""
    print("\n💾 内存使用检查")
    print("-" * 40)
    
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        print(f"  当前内存使用: {memory_info.rss / 1024 / 1024:.1f} MB")
        print(f"  虚拟内存: {memory_info.vms / 1024 / 1024:.1f} MB")
        
        # 估算1.5GB数据的内存需求
        # 假设当前测试数据约15KB，1.5GB ≈ 100,000倍
        estimated_rss = memory_info.rss * 100000 / 1024 / 1024 / 1024  # GB
        print(f"  估算1.5GB数据内存需求: {estimated_rss:.1f} GB")
        
        if estimated_rss > 8:  # 假设系统有8GB内存
            print("  ⚠️  警告: 处理全量数据可能需要优化内存使用")
            print("     建议: 使用分批处理、流式处理或内存映射文件")
        
    except ImportError:
        print("  ℹ️  未安装psutil，跳过内存检查")
        print("     安装: pip install psutil")


if __name__ == "__main__":
    # 创建数据目录
    os.makedirs("./data", exist_ok=True)
    
    print("🚀 开始测试Obsidian语义搜索完整流程...")
    
    try:
        if test_full_pipeline():
            check_memory_usage()
            
            print("\n🎯 今日任务完成情况:")
            print("  ✅ 环境搭建: 完成")
            print("  ✅ 文本提取: 完成")
            print("  ✅ 分块处理: 完成")
            print("  ⏳ 向量嵌入: 明日计划")
            print("  ⏳ 索引构建: 明日计划")
            
            print("\n📅 明日计划:")
            print("  1. 实现向量嵌入生成模块")
            print("  2. 实现lanceDB索引构建")
            print("  3. 测试嵌入模型性能")
            print("  4. 优化内存使用")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)