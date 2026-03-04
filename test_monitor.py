#!/usr/bin/env python3
"""
测试文件监控功能
"""

import sys
import os
import time

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from file_monitor import ObsidianFileMonitor

def test_monitor():
    """测试监控功能"""
    print("🧪 测试文件监控功能")
    print("=" * 50)
    
    # 创建监控器
    monitor = ObsidianFileMonitor("./config/config.yaml")
    
    # 测试初始化
    print("1. 测试初始化...")
    if monitor.initialize():
        print("   ✅ 初始化成功")
    else:
        print("   ❌ 初始化失败")
        return False
    
    # 测试状态
    print("\n2. 测试状态查询...")
    status = monitor.status()
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # 测试启动（短暂运行）
    print("\n3. 测试启动监控（5秒）...")
    if monitor.start():
        print("   ✅ 监控启动成功")
        
        # 运行5秒
        print("   监控运行中...")
        time.sleep(5)
        
        # 停止监控
        print("   停止监控...")
        monitor.stop()
        print("   ✅ 监控停止成功")
    else:
        print("   ❌ 监控启动失败")
        return False
    
    print("\n🎉 所有测试通过！")
    return True

if __name__ == "__main__":
    if test_monitor():
        sys.exit(0)
    else:
        sys.exit(1)