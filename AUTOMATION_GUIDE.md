# Obsidian语义搜索自动化指南

## 🎯 系统概述

这是一个**纯watchdog实时监控 + 定期全量重建**的Obsidian语义搜索自动化系统。

### 核心特性
- ✅ **实时监控**: 文件创建、修改、删除、移动即时处理
- ✅ **定期重建**: 每周全量重建修复数据不一致
- ✅ **开机自启**: launchd服务管理，自动启动
- ✅ **完整CLI**: 丰富的命令行工具
- ✅ **详细日志**: 完整的运行日志和监控

## 🚀 快速开始

### 1. 一键安装
```bash
cd /Users/wangdf/.openclaw/workspace/obsidian_semantic_search
./setup_automation.sh
```

### 2. 手动安装步骤
```bash
# 1. 安装依赖
cd /Users/wangdf/.openclaw/workspace/obsidian_semantic_search
source venv/bin/activate
pip install watchdog

# 2. 测试监控
python test_monitor.py

# 3. 设置自动化
./automation_manager.sh setup-cron

# 4. 启动监控
./automation_manager.sh start

# 5. 首次重建
./automation_manager.sh rebuild
```

## 📊 系统架构

```
┌─────────────────────────────────────────────────────┐
│               自动化系统架构                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. 🎯 实时监控 (watchdog)                          │
│     • 监听文件系统事件                              │
│     • 即时处理增、删、改、移                        │
│     • 保持索引实时性                                │
│                                                     │
│  2. 🛡️  定期全量重建 (cron)                         │
│     • 每周日凌晨3点                                │
│     • 重建完整索引                                  │
│     • 修复数据不一致问题                            │
│                                                     │
│  3. 🔄 自动化管理 (launchd)                         │
│     • 开机自启动                                    │
│     • 进程监控和重启                                │
│     • 日志管理                                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 🛠️ 管理命令

### 自动化管理脚本
```bash
# 查看所有命令
./automation_manager.sh help

# 启动监控
./automation_manager.sh start

# 停止监控  
./automation_manager.sh stop

# 重启监控
./automation_manager.sh restart

# 查看状态
./automation_manager.sh status

# 运行全量重建
./automation_manager.sh rebuild

# 设置cron任务
./automation_manager.sh setup-cron

# 清理旧日志
./automation_manager.sh cleanup
```

### 语义搜索CLI
```bash
# 搜索内容
python cli.py search "查询内容"

# 查看路径信息
python cli.py paths

# 测试系统连接
python cli.py test

# 处理目录
python cli.py process "我的Obsidian库"

# 重建索引
python cli.py rebuild --full
```

## ⚙️ 配置说明

### 监控配置 (`config/monitor_config.yaml`)
```yaml
obsidian_vault: "/Users/wangdf/workshop/obsidian-vault"
monitoring:
  enabled: true
  mode: "realtime"
  events: ["created", "modified", "deleted", "moved"]
rebuild:
  schedule: "0 3 * * 0"  # 每周日凌晨3点
```

### 路径别名
- `"我的Obsidian库"` → `/Users/wangdf/workshop/obsidian-vault`
- `"我的Obsidian笔记库"` → 同上
- `"OpenClaw"` → 子目录路径

## 🔄 工作流程

### 日常使用
```
1. 系统启动 → launchd自动启动监控
2. 新增笔记 → watchdog检测 → 立即索引 → 可立即搜索
3. 修改笔记 → watchdog检测 → 更新索引 → 搜索结果更新
4. 删除笔记 → watchdog检测 → 删除索引 → 搜索结果排除
5. 移动笔记 → watchdog检测 → 更新路径 → 保持搜索
```

### 每周维护
```
每周日凌晨3点 → cron触发 → 全量重建 → 
  1. 删除旧表，创建新表
  2. 处理所有笔记文件
  3. 修复监控可能遗漏的问题
  4. 优化数据库性能
```

## 📁 文件结构

```
obsidian_semantic_search/
├── src/                    # 源代码
│   ├── file_monitor.py     # 文件监控器
│   ├── pipeline_integration.py
│   ├── vector_store.py
│   └── ...
├── config/                 # 配置文件
│   ├── config.yaml         # 主配置
│   └── monitor_config.yaml # 监控配置
├── logs/                   # 日志文件
│   ├── monitor.log         # 监控日志
│   ├── rebuild.log         # 重建日志
│   └── cron.log           # cron任务日志
├── data/                   # 数据文件
│   └── lancedb/           # 向量数据库
├── automation_manager.sh   # 自动化管理脚本
├── setup_automation.sh     # 安装脚本
├── cli.py                  # 命令行工具
└── *.plist                 # launchd配置文件
```

## 🐛 故障排除

### 常见问题

#### 1. 监控未启动
```bash
# 检查服务状态
./automation_manager.sh status

# 检查launchd服务
launchctl list | grep obsidian

# 查看日志
tail -f logs/monitor.log
```

#### 2. 搜索无结果
```bash
# 检查数据库状态
python cli.py stats

# 运行全量重建
./automation_manager.sh rebuild

# 测试搜索
python cli.py search "测试"
```

#### 3. 文件变化未检测到
```bash
# 检查监控事件
tail -f logs/monitor.log

# 手动测试文件处理
touch test.md
# 观察日志是否检测到
```

### 日志文件
- `logs/monitor.log` - 监控进程日志
- `logs/rebuild.log` - 重建任务日志  
- `logs/cron.log` - cron任务日志
- `logs/launchd.log` - launchd服务日志

## 🔧 高级配置

### 调整监控频率
编辑 `config/monitor_config.yaml`:
```yaml
monitoring:
  mode: "realtime"  # 实时监控
  # 或使用轮询模式
  # mode: "polling"
  # polling:
  #   interval: 60  # 每60秒轮询一次
```

### 调整重建计划
```bash
# 查看当前cron任务
crontab -l

# 编辑cron任务
crontab -e

# 示例：每天凌晨2点重建
0 2 * * * cd /path/to/project && ./automation_manager.sh rebuild
```

### 监控特定事件
```yaml
monitoring:
  events:
    - "created"    # 文件创建
    - "modified"   # 文件修改  
    - "deleted"    # 文件删除
    - "moved"      # 文件移动/重命名
```

## 📈 性能监控

### 资源使用
```bash
# 查看监控进程资源
ps aux | grep file_monitor

# 查看日志文件大小
du -sh logs/*.log

# 查看数据库大小
du -sh data/lancedb/
```

### 定期维护
```bash
# 每周清理旧日志
./automation_manager.sh cleanup

# 每月检查系统状态
./automation_manager.sh status

# 季度性优化
# 1. 备份数据库
# 2. 检查依赖更新
# 3. 验证配置
```

## 🔒 安全注意事项

1. **文件权限**: 确保只有授权用户可访问笔记库
2. **日志管理**: 定期清理包含敏感信息的日志
3. **网络访问**: 监控只访问本地文件，不涉及网络
4. **备份策略**: 定期备份向量数据库和配置

## 📞 支持与反馈

### 获取帮助
```bash
# 查看系统状态
./automation_manager.sh status

# 查看详细日志
tail -100 logs/monitor.log

# 测试基本功能
python cli.py test
```

### 报告问题
1. 收集相关日志
2. 描述重现步骤
3. 提供系统信息
4. 检查常见问题

---

## 🎉 开始使用！

现在你的Obsidian语义搜索系统已经完全自动化：

1. **实时监控** - 文件变化即时处理
2. **定期重建** - 每周自动修复数据
3. **开机自启** - 无需手动干预
4. **完整搜索** - 随时查找笔记内容

享受智能的语义搜索体验吧！ 🐱