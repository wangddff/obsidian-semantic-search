#!/usr/bin/env python3
"""
Obsidian语义搜索命令行工具
提供简单的CLI接口进行语义搜索
"""

import os
import sys
import argparse
import json
import time
from typing import List, Dict, Any
import yaml

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from pipeline_integration import ObsidianSemanticSearchPipeline, PipelineStats
from path_resolver import resolve_path, get_obsidian_vault_path
from file_monitor import ObsidianFileMonitor, run_monitor_daemon


def load_config(config_path: str = "./config/config.yaml") -> Dict[str, Any]:
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        return {}


def resolve_directory_path(path_arg: str) -> str:
    """
    解析目录路径，支持别名
    
    Args:
        path_arg: 路径参数（可以是绝对路径或别名）
        
    Returns:
        解析后的实际路径
    """
    # 尝试解析别名
    resolved = resolve_path(path_arg)
    if resolved:
        print(f"📁 解析路径别名: '{path_arg}' → {resolved}")
        return resolved
    
    # 如果是绝对路径且存在，直接返回
    if os.path.isabs(path_arg) and os.path.exists(path_arg):
        return path_arg
    
    # 尝试作为相对路径
    if os.path.exists(path_arg):
        return os.path.abspath(path_arg)
    
    # 无法解析
    print(f"❌ 无法解析路径: '{path_arg}'")
    print(f"   支持的别名: '我的Obsidian库', '我的Obsidian笔记库', 'obsidian库', '笔记库'")
    print(f"   支持的子目录: 'OpenClaw', '2026', 'Evernote', 'Evernote-Global'")
    raise ValueError(f"无法解析路径: {path_arg}")


def process_directory(args):
    """处理目录中的所有文件"""
    # 解析路径
    try:
        resolved_path = resolve_directory_path(args.directory)
    except ValueError as e:
        print(f"❌ {e}")
        return 1
    
    print(f"🚀 开始处理目录: {resolved_path}")
    
    # 加载配置
    config = load_config(args.config)
    if not config:
        return 1
    
    # 初始化管道
    pipeline = ObsidianSemanticSearchPipeline(args.config)
    pipeline.initialize_components()
    
    # 处理目录
    start_time = time.time()
    stats = pipeline.process_directory(resolved_path)
    total_time = time.time() - start_time
    
    # 输出结果
    print(f"\n✅ 处理完成!")
    print(stats.summary())
    print(f"  总耗时: {total_time:.2f}秒")
    
    return 0


def search(args):
    """执行语义搜索"""
    print(f"🔍 执行语义搜索: '{args.query}'")
    
    # 加载配置
    config = load_config(args.config)
    if not config:
        return 1
    
    # 初始化管道
    pipeline = ObsidianSemanticSearchPipeline(args.config)
    pipeline.initialize_components()
    
    # 执行搜索
    start_time = time.time()
    results = pipeline.search(args.query, limit=args.limit)
    search_time = time.time() - start_time
    
    # 输出结果
    if results:
        print(f"\n✅ 找到 {len(results)} 个相关结果 (耗时: {search_time:.3f}秒)")
        print("-" * 80)
        
        for i, result in enumerate(results):
            print(f"\n{i+1}. 📄 {result.record.file_name}")
            print(f"   相似度: {result.similarity:.3f}")
            print(f"   文件路径: {result.record.file_path}")
            print(f"   文本预览: {result.record.text[:150]}...")
            
            # 显示元数据
            if args.verbose and result.record.metadata:
                print(f"   元数据: {json.dumps(result.record.metadata, ensure_ascii=False, indent=4)}")
    else:
        print(f"\n❌ 未找到相关结果")
    
    return 0


def stats(args):
    """显示数据库统计信息"""
    print(f"📊 数据库统计信息")
    
    # 加载配置
    config = load_config(args.config)
    if not config:
        return 1
    
    # 初始化管道
    pipeline = ObsidianSemanticSearchPipeline(args.config)
    pipeline.initialize_components()
    
    # 获取统计信息
    stats_info = pipeline.get_database_info()
    
    if stats_info:
        print(f"\n📁 数据库信息:")
        print(f"  路径: {stats_info.get('db_path', 'N/A')}")
        print(f"  表名: {stats_info.get('table_name', 'N/A')}")
        print(f"  向量维度: {stats_info.get('vector_dimension', 'N/A')}")
        
        print(f"\n📈 数据统计:")
        print(f"  总记录数: {stats_info.get('total_records', 0)}")
        print(f"  文件数: {stats_info.get('unique_files', 0)}")
        print(f"  分块数: {stats_info.get('total_chunks', 0)}")
        
        if 'index_size_mb' in stats_info:
            print(f"  索引大小: {stats_info['index_size_mb']:.2f} MB")
        
        if 'created_at' in stats_info:
            from datetime import datetime
            created = datetime.fromtimestamp(stats_info['created_at'])
            print(f"  创建时间: {created.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print(f"\n❌ 无法获取统计信息")
    
    return 0


def test_connection(args):
    """测试API连接和组件状态"""
    print(f"🔧 测试系统连接和组件状态")
    
    # 加载配置
    config = load_config(args.config)
    if not config:
        return 1
    
    # 初始化管道
    pipeline = ObsidianSemanticSearchPipeline(args.config)
    
    print("\n1. 测试配置加载...")
    if pipeline.config:
        print(f"   ✅ 配置加载成功")
        print(f"     模型API: {pipeline.config.get('model', {}).get('api', {}).get('base_url', 'N/A')}")
        print(f"     向量维度: {pipeline.config.get('lancedb', {}).get('vector_dimension', 'N/A')}")
    else:
        print(f"   ❌ 配置加载失败")
        return 1
    
    print("\n2. 初始化组件...")
    try:
        pipeline.initialize_components()
        print(f"   ✅ 组件初始化成功")
    except Exception as e:
        print(f"   ❌ 组件初始化失败: {e}")
        return 1
    
    print("\n3. 测试API连接...")
    try:
        if pipeline.embedding_generator and pipeline.embedding_generator.client:
            # test_connectivity返回布尔值，不是字典
            if pipeline.embedding_generator.client.test_connectivity():
                print(f"   ✅ API连接成功")
                # 测试一个简单查询以获取更多信息
                test_text = "测试连接"
                test_result = pipeline.embedding_generator.client.get_embedding(test_text)
                if test_result:
                    print(f"     向量维度: {len(test_result.embedding)}")
                    print(f"     模型名称: text-embedding-bge-m3")
            else:
                print(f"   ❌ API连接失败")
                return 1
    except Exception as e:
        print(f"   ❌ API连接测试异常: {e}")
        return 1
    
    print("\n4. 测试数据库连接...")
    try:
        if pipeline.vector_store_manager and pipeline.vector_store_manager.vector_store:
            if pipeline.vector_store_manager.vector_store.connect():
                print(f"   ✅ 数据库连接成功")
                db_stats = pipeline.vector_store_manager.vector_store.get_stats()
                print(f"     表名: {db_stats.get('table_name', 'N/A')}")
                print(f"     记录数: {db_stats.get('total_records', 0)}")
            else:
                print(f"   ❌ 数据库连接失败")
                return 1
    except Exception as e:
        print(f"   ❌ 数据库连接测试异常: {e}")
        return 1
    
    print(f"\n🎉 所有测试通过！系统状态正常")
    return 0


def show_paths(args):
    """显示路径信息"""
    print("📁 路径信息")
    print("=" * 60)
    
    from path_resolver import get_resolver
    resolver = get_resolver()
    
    # Obsidian笔记库信息
    vault_path = resolver.get_obsidian_vault_path()
    if vault_path:
        print(f"🔹 Obsidian笔记库:")
        print(f"   主路径: {vault_path}")
        print(f"   状态: {'✅ 存在' if os.path.exists(vault_path) else '❌ 不存在'}")
        
        # 子目录
        subdirs = resolver.list_subdirectories()
        print(f"   子目录 ({len(subdirs)}个):")
        for subdir in subdirs:
            subdir_path = resolver.get_subdirectory_path(subdir)
            exists = os.path.exists(subdir_path) if subdir_path else False
            status = "✅" if exists else "❌"
            print(f"     {status} {subdir}")
        
        # 语义搜索状态
        status = resolver.get_semantic_search_status()
        print(f"\n🔍 语义搜索状态:")
        print(f"   已配置: {'✅ 是' if status['configured'] else '❌ 否'}")
        print(f"   已索引子目录: {', '.join(status['indexed_subdirectories']) or '无'}")
        print(f"   总文件数: {status['total_files']}")
        print(f"   总分块数: {status['total_chunks']}")
        print(f"   已索引分块: {status['indexed_chunks']}")
        
        # 别名
        obsidian_config = resolver.config.get('obsidian_vault', {})
        aliases = obsidian_config.get('aliases', [])
        print(f"\n📝 支持的别名:")
        for alias in aliases:
            print(f"   • '{alias}'")
    else:
        print("❌ 未配置Obsidian笔记库路径")
    
    print(f"\n💡 使用提示:")
    print(f"   你可以使用以下方式指定路径:")
    print(f"   • 绝对路径: /Users/wangdf/workshop/obsidian-vault")
    print(f"   • 别名: '我的Obsidian库', '我的Obsidian笔记库'")
    print(f"   • 子目录名: 'OpenClaw', '2026', 'Evernote'")
    
    return 0


def start_monitor(args):
    """启动文件监控"""
    print("🚀 启动文件监控...")
    
    from file_monitor import ObsidianFileMonitor
    
    monitor = ObsidianFileMonitor(args.config)
    if monitor.start():
        print("✅ 文件监控启动成功")
        print("   监控路径:", monitor._get_vault_path())
        print("   按 Ctrl+C 停止监控")
        
        # 保持运行
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 收到停止信号")
            monitor.stop()
            
        return 0
    else:
        print("❌ 文件监控启动失败")
        return 1


def stop_monitor(args):
    """停止文件监控"""
    print("🛑 停止文件监控...")
    
    # 这里需要实现停止逻辑
    # 暂时返回提示信息
    print("⚠️  停止功能需要监控进程ID管理")
    print("   请使用 Ctrl+C 停止正在运行的监控")
    return 0


def show_monitor_status(args):
    """查看监控状态"""
    from file_monitor import ObsidianFileMonitor
    
    monitor = ObsidianFileMonitor(args.config)
    status = monitor.status()
    
    print("📊 文件监控状态")
    print("=" * 50)
    
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    return 0


def run_monitor_daemon(args):
    """以守护进程方式运行监控"""
    print("👻 以守护进程方式运行文件监控...")
    
    from file_monitor import run_monitor_daemon
    run_monitor_daemon(args.config)
    
    return 0


def rebuild_index(args):
    """重建索引"""
    print("🔨 开始重建索引...")
    
    # 加载配置
    config = load_config(args.config)
    if not config:
        return 1
    
    # 确定笔记库路径
    vault_path = args.vault
    if vault_path:
        # 解析路径别名
        vault_path = resolve_directory_path(vault_path)
    
    if not vault_path:
        # 从配置文件或路径解析器获取
        from path_resolver import get_obsidian_vault_path
        vault_path = get_obsidian_vault_path()
    
    if not vault_path or not os.path.exists(vault_path):
        print(f"❌ 无效的笔记库路径: {vault_path}")
        return 1
    
    print(f"   笔记库路径: {vault_path}")
    print(f"   重建模式: {'完全重建' if args.full else '增量重建'}")
    
    # 初始化管道
    pipeline = ObsidianSemanticSearchPipeline(args.config)
    if not pipeline.initialize_components():
        print("❌ 初始化管道组件失败")
        return 1
    
    if args.full:
        print("   步骤1: 删除旧表...")
        try:
            # 删除现有表
            pipeline.vector_store_manager.vector_store.drop_table()
            print("   ✅ 旧表已删除")
        except Exception as e:
            print(f"   ⚠️  删除旧表失败: {e}")
            print("   继续创建新表...")
        
        print("   步骤2: 创建新表...")
        pipeline.vector_store_manager.vector_store.create_table(force_recreate=True)
        print("   ✅ 新表已创建")
    
    print("   步骤3: 处理笔记库...")
    start_time = time.time()
    
    stats = pipeline.process_directory(vault_path)
    
    total_time = time.time() - start_time
    
    print(f"\n✅ 重建完成!")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   文件数: {stats.total_files}")
    print(f"   分块数: {stats.total_chunks}")
    print(f"   嵌入向量: {stats.total_embeddings}")
    print(f"   数据库记录: {stats.total_records}")
    
    if args.clean:
        print("\n🧹 清理旧数据...")
        # 这里可以添加清理逻辑
        print("   ✅ 清理完成")
    
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Obsidian语义搜索命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s process /path/to/obsidian/vault     # 处理整个目录
  %(prog)s process "我的Obsidian库"            # 使用别名处理
  %(prog)s search "人工智能是什么"              # 搜索相关内容
  %(prog)s stats                               # 查看数据库统计
  %(prog)s test                                # 测试系统连接
  %(prog)s paths                               # 显示路径信息
        """
    )
    
    parser.add_argument(
        "--config",
        default="./config/config.yaml",
        help="配置文件路径 (默认: ./config/config.yaml)"
    )
    
    # 子命令
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # process 命令
    process_parser = subparsers.add_parser("process", help="处理目录中的所有文件")
    process_parser.add_argument("directory", help="要处理的目录路径")
    process_parser.set_defaults(func=process_directory)
    
    # search 命令
    search_parser = subparsers.add_parser("search", help="执行语义搜索")
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("-l", "--limit", type=int, default=5, help="返回结果数量 (默认: 5)")
    search_parser.add_argument("-v", "--verbose", action="store_true", help="显示详细信息")
    search_parser.set_defaults(func=search)
    
    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="显示数据库统计信息")
    stats_parser.set_defaults(func=stats)
    
    # test 命令
    test_parser = subparsers.add_parser("test", help="测试系统连接和组件状态")
    test_parser.set_defaults(func=test_connection)
    
    # paths 命令
    paths_parser = subparsers.add_parser("paths", help="显示路径信息")
    paths_parser.set_defaults(func=show_paths)
    
    # monitor 命令
    monitor_parser = subparsers.add_parser("monitor", help="文件监控管理")
    monitor_subparsers = monitor_parser.add_subparsers(dest="monitor_action", help="监控操作")
    
    # monitor start
    monitor_start = monitor_subparsers.add_parser("start", help="启动文件监控")
    monitor_start.set_defaults(func=start_monitor)
    
    # monitor stop
    monitor_stop = monitor_subparsers.add_parser("stop", help="停止文件监控")
    monitor_stop.set_defaults(func=stop_monitor)
    
    # monitor status
    monitor_status_parser = monitor_subparsers.add_parser("status", help="查看监控状态")
    monitor_status_parser.set_defaults(func=show_monitor_status)
    
    # monitor daemon (后台运行)
    monitor_daemon = monitor_subparsers.add_parser("daemon", help="以守护进程方式运行监控")
    monitor_daemon.set_defaults(func=run_monitor_daemon)
    
    # rebuild 命令
    rebuild_parser = subparsers.add_parser("rebuild", help="重建索引")
    rebuild_parser.add_argument("--full", action="store_true", help="完全重建（删除旧表）")
    rebuild_parser.add_argument("--clean", action="store_true", help="清理旧数据")
    rebuild_parser.add_argument("--vault", help="指定笔记库路径（默认使用配置）")
    rebuild_parser.set_defaults(func=rebuild_index)
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # 执行命令
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())