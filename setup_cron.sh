#!/bin/bash
# 设置每周自动重建cron任务

echo "⏰ 设置每周自动重建任务..."
echo "========================================"

CRON_JOB="0 3 * * 0 cd /Users/wangdf/.openclaw/workspace/obsidian_semantic_search && ./automation_manager.sh rebuild >> logs/cron.log 2>&1"

# 检查是否已有cron任务
if crontab -l 2>/dev/null | grep -q "automation_manager.sh rebuild"; then
    echo "✅ cron任务已存在"
    crontab -l | grep "automation_manager.sh"
else
    # 创建crontab文件
    echo "$CRON_JOB" > /tmp/obsidian_cron
    
    # 加载cron任务
    crontab /tmp/obsidian_cron
    
    if [ $? -eq 0 ]; then
        echo "✅ cron任务设置成功"
        echo "   计划: 每周日凌晨3点运行全量重建"
        echo "   命令: $CRON_JOB"
    else
        echo "❌ cron任务设置失败"
        echo "   请手动添加以下行到crontab:"
        echo "   $CRON_JOB"
    fi
    
    rm -f /tmp/obsidian_cron
fi

echo ""
echo "📋 当前cron任务:"
echo "----------------------------------------"
crontab -l 2>/dev/null || echo "暂无cron任务"

echo ""
echo "💡 手动设置方法:"
echo "----------------------------------------"
echo "1. 编辑crontab: crontab -e"
echo "2. 添加以下行:"
echo "   0 3 * * 0 cd /Users/wangdf/.openclaw/workspace/obsidian_semantic_search && ./automation_manager.sh rebuild >> logs/cron.log 2>&1"
echo "3. 保存并退出"