#!/usr/bin/env python3
"""
路径解析器
用于将用户提到的路径别名解析为实际路径
"""

import os
import yaml
from typing import Dict, Optional, List


class PathResolver:
    """路径解析器"""
    
    def __init__(self, config_path: str = "./config/user_paths.yaml"):
        """
        初始化路径解析器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  加载路径配置文件失败: {e}")
            return {}
    
    def resolve(self, path_alias: str) -> Optional[str]:
        """
        解析路径别名
        
        Args:
            path_alias: 路径别名
            
        Returns:
            实际路径，如果无法解析则返回None
        """
        # 如果是绝对路径，直接返回
        if os.path.isabs(path_alias):
            return path_alias
        
        # 检查是否是Obsidian笔记库的别名
        obsidian_config = self.config.get('obsidian_vault', {})
        aliases = obsidian_config.get('aliases', [])
        
        if path_alias in aliases:
            primary_path = obsidian_config.get('primary')
            if primary_path and os.path.exists(primary_path):
                return primary_path
        
        # 检查是否是子目录的简单名称
        subdirectories = obsidian_config.get('subdirectories', [])
        if path_alias in subdirectories:
            primary_path = obsidian_config.get('primary')
            if primary_path:
                full_path = os.path.join(primary_path, path_alias)
                if os.path.exists(full_path):
                    return full_path
        
        # 检查其他路径
        other_paths = self.config.get('other_paths', {})
        if path_alias in other_paths:
            path_value = other_paths[path_alias]
            if os.path.exists(path_value):
                return path_value
        
        return None
    
    def get_obsidian_vault_path(self) -> Optional[str]:
        """获取Obsidian笔记库主路径"""
        obsidian_config = self.config.get('obsidian_vault', {})
        primary_path = obsidian_config.get('primary')
        if primary_path and os.path.exists(primary_path):
            return primary_path
        return None
    
    def get_subdirectory_path(self, subdir_name: str) -> Optional[str]:
        """获取子目录完整路径"""
        primary_path = self.get_obsidian_vault_path()
        if primary_path:
            full_path = os.path.join(primary_path, subdir_name)
            if os.path.exists(full_path):
                return full_path
        return None
    
    def list_subdirectories(self) -> List[str]:
        """列出所有子目录"""
        obsidian_config = self.config.get('obsidian_vault', {})
        subdirs = obsidian_config.get('subdirectories', [])
        
        # 过滤实际存在的子目录
        existing_subdirs = []
        primary_path = self.get_obsidian_vault_path()
        
        if primary_path:
            for subdir in subdirs:
                full_path = os.path.join(primary_path, subdir)
                if os.path.exists(full_path):
                    existing_subdirs.append(subdir)
        
        return existing_subdirs
    
    def get_semantic_search_status(self) -> Dict:
        """获取语义搜索状态"""
        obsidian_config = self.config.get('obsidian_vault', {})
        search_config = obsidian_config.get('semantic_search', {})
        
        return {
            'configured': search_config.get('configured', False),
            'indexed_subdirectories': search_config.get('indexed_subdirectories', []),
            'total_files': search_config.get('total_files', 0),
            'total_chunks': search_config.get('total_chunks', 0),
            'indexed_chunks': search_config.get('indexed_chunks', 0)
        }


# 全局实例
_default_resolver = None

def get_resolver() -> PathResolver:
    """获取全局路径解析器实例"""
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = PathResolver()
    return _default_resolver

def resolve_path(path_alias: str) -> Optional[str]:
    """解析路径别名（便捷函数）"""
    return get_resolver().resolve(path_alias)

def get_obsidian_vault_path() -> Optional[str]:
    """获取Obsidian笔记库路径（便捷函数）"""
    return get_resolver().get_obsidian_vault_path()


if __name__ == "__main__":
    # 测试代码
    resolver = PathResolver()
    
    print("🔍 路径解析器测试")
    print("=" * 50)
    
    # 测试别名解析
    test_aliases = [
        "我的Obsidian库",
        "我的Obsidian笔记库",
        "obsidian库",
        "笔记库",
        "OpenClaw",
        "2026",
        "Evernote"
    ]
    
    for alias in test_aliases:
        resolved = resolver.resolve(alias)
        if resolved:
            print(f"✅ '{alias}' → {resolved}")
        else:
            print(f"❌ '{alias}' → 无法解析")
    
    print("\n📁 Obsidian笔记库信息:")
    vault_path = resolver.get_obsidian_vault_path()
    if vault_path:
        print(f"   主路径: {vault_path}")
        print(f"   子目录: {', '.join(resolver.list_subdirectories())}")
        
        status = resolver.get_semantic_search_status()
        print(f"   语义搜索状态:")
        print(f"     已配置: {status['configured']}")
        print(f"     已索引子目录: {', '.join(status['indexed_subdirectories'])}")
        print(f"     总文件数: {status['total_files']}")
        print(f"     总分块数: {status['total_chunks']}")
        print(f"     已索引分块: {status['indexed_chunks']}")
    else:
        print("   ❌ 未找到Obsidian笔记库路径")