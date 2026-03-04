#!/usr/bin/env python3
"""
Obsidian文件监控器
使用watchdog库实时监控文件变化
"""

import os
import sys
import time
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Set

# watchdog相关导入
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

# 项目模块
try:
    from pipeline_integration import ObsidianSemanticSearchPipeline
except ImportError:
    # 尝试相对导入
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from pipeline_integration import ObsidianSemanticSearchPipeline

logger = logging.getLogger(__name__)


class ObsidianFileEventHandler(FileSystemEventHandler):
    """
    Obsidian文件事件处理器
    处理文件创建、修改、删除、移动事件
    """
    
    def __init__(self, pipeline: ObsidianSemanticSearchPipeline, vault_path: str):
        """
        初始化事件处理器
        
        Args:
            pipeline: 语义搜索管道
            vault_path: Obsidian笔记库路径
        """
        self.pipeline = pipeline
        self.vault_path = vault_path
        self.file_hashes: Dict[str, str] = {}  # 文件哈希缓存
        
        logger.info(f"初始化Obsidian文件事件处理器，监控路径: {vault_path}")
    
    def _is_obsidian_file(self, path: str) -> bool:
        """检查是否是Obsidian笔记文件"""
        return path.endswith('.md') and self.vault_path in path
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """计算文件内容哈希"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"计算文件哈希失败 {file_path}: {e}")
            return None
    
    def on_created(self, event: FileSystemEvent):
        """文件创建事件"""
        if not event.is_directory and self._is_obsidian_file(event.src_path):
            logger.info(f"📝 检测到新文件: {event.src_path}")
            
            # 计算文件哈希
            file_hash = self._calculate_file_hash(event.src_path)
            if file_hash:
                self.file_hashes[event.src_path] = file_hash
            
            # 索引新文件
            self._index_file(event.src_path)
    
    def on_modified(self, event: FileSystemEvent):
        """文件修改事件"""
        if not event.is_directory and self._is_obsidian_file(event.src_path):
            # 检查内容是否真的改变了
            old_hash = self.file_hashes.get(event.src_path)
            new_hash = self._calculate_file_hash(event.src_path)
            
            if new_hash and old_hash != new_hash:
                logger.info(f"✏️  检测到文件修改: {event.src_path}")
                
                # 更新哈希缓存
                self.file_hashes[event.src_path] = new_hash
                
                # 先删除旧索引，再重新索引
                self._delete_file_from_index(event.src_path)
                self._index_file(event.src_path)
    
    def on_deleted(self, event: FileSystemEvent):
        """文件删除事件"""
        if not event.is_directory and self._is_obsidian_file(event.src_path):
            logger.info(f"🗑️  检测到文件删除: {event.src_path}")
            
            # 从索引中删除
            self._delete_file_from_index(event.src_path)
            
            # 从哈希缓存中移除
            if event.src_path in self.file_hashes:
                del self.file_hashes[event.src_path]
    
    def on_moved(self, event: FileSystemEvent):
        """文件移动/重命名事件"""
        if (not event.is_directory and 
            self._is_obsidian_file(event.src_path) and 
            self._is_obsidian_file(event.dest_path)):
            
            logger.info(f"📂 检测到文件移动: {event.src_path} → {event.dest_path}")
            
            # 从旧路径删除索引
            self._delete_file_from_index(event.src_path)
            
            # 在新路径创建索引
            self._index_file(event.dest_path)
            
            # 更新哈希缓存
            if event.src_path in self.file_hashes:
                self.file_hashes[event.dest_path] = self.file_hashes[event.src_path]
                del self.file_hashes[event.src_path]
    
    def _index_file(self, file_path: str):
        """索引单个文件"""
        try:
            # 使用管道处理单个文件
            logger.debug(f"开始索引文件: {file_path}")
            
            # 这里需要扩展pipeline以支持单个文件处理
            # 暂时使用简化实现
            from text_extractor import TextExtractor
            from chunk_processor import ChunkProcessor
            
            # 提取文本
            extractor = TextExtractor()
            content = extractor.extract_from_file(file_path)
            
            if content and content.get('content'):
                # 分块处理
                chunk_processor = ChunkProcessor(
                    chunk_size=3000,
                    chunk_overlap=300,
                    min_chunk_size=2000,
                    max_chunk_size=4000
                )
                
                chunks = chunk_processor.process_extracted_contents([content])
                
                # 生成嵌入向量
                embeddings = self.pipeline.embedding_generator.generate_embeddings_for_chunks(chunks)
                
                # 存储到向量数据库
                inserted = self.pipeline.vector_store_manager.vector_store.add_embeddings(
                    [emb.to_dict() for emb in embeddings]
                )
                
                logger.info(f"✅ 文件索引完成: {file_path} (插入 {inserted} 条记录)")
            else:
                logger.warning(f"文件内容为空或提取失败: {file_path}")
                
        except Exception as e:
            logger.error(f"索引文件失败 {file_path}: {e}")
    
    def _delete_file_from_index(self, file_path: str):
        """从索引中删除文件"""
        try:
            # 这里需要扩展vector_store以支持按文件路径删除
            # 暂时使用简化实现
            vector_store = self.pipeline.vector_store_manager.vector_store
            
            # 假设vector_store有delete_by_file_path方法
            if hasattr(vector_store, 'delete_by_file_path'):
                deleted = vector_store.delete_by_file_path(file_path)
                logger.info(f"✅ 从索引中删除文件: {file_path} (删除 {deleted} 条记录)")
            else:
                logger.warning(f"向量存储不支持按文件路径删除: {file_path}")
                
        except Exception as e:
            logger.error(f"删除文件索引失败 {file_path}: {e}")


class ObsidianFileMonitor:
    """
    Obsidian文件监控器
    管理文件监控的启动、停止和状态
    """
    
    def __init__(self, config_path: str = "./config/config.yaml"):
        """
        初始化文件监控器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.pipeline: Optional[ObsidianSemanticSearchPipeline] = None
        self.event_handler: Optional[ObsidianFileEventHandler] = None
        self.observer: Optional[Observer] = None
        self.is_running = False
        
        logger.info(f"初始化Obsidian文件监控器，配置: {config_path}")
    
    def initialize(self) -> bool:
        """初始化监控器组件"""
        try:
            # 初始化管道
            self.pipeline = ObsidianSemanticSearchPipeline(self.config_path)
            if not self.pipeline.initialize_components():
                logger.error("初始化管道组件失败")
                return False
            
            # 获取Obsidian笔记库路径
            vault_path = self._get_vault_path()
            if not vault_path:
                logger.error("无法获取Obsidian笔记库路径")
                return False
            
            # 创建事件处理器
            self.event_handler = ObsidianFileEventHandler(self.pipeline, vault_path)
            
            # 创建观察者
            self.observer = Observer()
            
            logger.info("✅ 文件监控器初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"初始化文件监控器失败: {e}")
            return False
    
    def _get_vault_path(self) -> Optional[str]:
        """获取Obsidian笔记库路径"""
        try:
            # 从配置文件读取
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 优先使用配置文件中的路径
            if 'obsidian_vault' in config:
                vault_path = config['obsidian_vault']
                if os.path.exists(vault_path):
                    return vault_path
            
            # 使用路径解析器
            from path_resolver import get_obsidian_vault_path
            vault_path = get_obsidian_vault_path()
            if vault_path and os.path.exists(vault_path):
                return vault_path
            
            return None
            
        except Exception as e:
            logger.error(f"获取Obsidian笔记库路径失败: {e}")
            return None
    
    def start(self) -> bool:
        """启动文件监控"""
        if self.is_running:
            logger.warning("文件监控已经在运行")
            return True
        
        if not self.initialize():
            logger.error("初始化失败，无法启动监控")
            return False
        
        try:
            vault_path = self._get_vault_path()
            if not vault_path:
                logger.error("无法获取Obsidian笔记库路径")
                return False
            
            # 开始监控
            self.observer.schedule(self.event_handler, vault_path, recursive=True)
            self.observer.start()
            self.is_running = True
            
            logger.info(f"✅ 文件监控已启动，监控路径: {vault_path}")
            logger.info("  监控事件: 创建、修改、删除、移动")
            logger.info("  按 Ctrl+C 停止监控")
            
            return True
            
        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")
            return False
    
    def stop(self) -> bool:
        """停止文件监控"""
        if not self.is_running:
            logger.warning("文件监控未在运行")
            return True
        
        try:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            
            logger.info("✅ 文件监控已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止文件监控失败: {e}")
            return False
    
    def status(self) -> Dict:
        """获取监控状态"""
        return {
            "is_running": self.is_running,
            "vault_path": self._get_vault_path(),
            "observer": "运行中" if self.is_running and self.observer else "未运行",
            "event_handler": "已初始化" if self.event_handler else "未初始化",
            "pipeline": "已初始化" if self.pipeline else "未初始化"
        }


def run_monitor_daemon(config_path: str = "./config/config.yaml"):
    """
    运行监控守护进程
    
    Args:
        config_path: 配置文件路径
    """
    monitor = ObsidianFileMonitor(config_path)
    
    if not monitor.start():
        logger.error("启动监控失败")
        return
    
    try:
        # 保持进程运行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在停止监控...")
        monitor.stop()
        
    except Exception as e:
        logger.error(f"监控进程异常: {e}")
        monitor.stop()


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行监控
    run_monitor_daemon()