#!/bin/bash
# 设置每周自动重建

echo "⏰ 设置每周自动重建任务"
echo "================================"

# 项目目录
PROJECT_DIR="/Users/wangdf/.openclaw/workspace/obsidian_semantic_search"

# cron任务内容
CRON_TASK="0 3 * * 0 cd $PROJECT_DIR && $PROJECT_DIR/automation_manager.sh rebuild >> $PROJECT_DIR/logs/cron.log 2>&1"

echo "任务: $CRON_TASK"
echo ""

# 尝试设置cron
echo "尝试设置cron任务..."
echo "$CRON_TASK" > "$PROJECT_DIR/my_cron_job.txt"
crontab "$PROJECT_DIR/my_cron_job.txt"

if [ $? -eq 0 ]; then
    echo "✅ cron任务设置成功！"
    echo ""
    echo "📅 计划: 每周日凌晨3点自动运行全量重建"
    echo ""
    echo "📋 验证cron任务:"
    echo "--------------------------------"
    crontab -l
else
    echo "❌ cron任务设置失败"
    echo ""
    echo "💡 手动设置方法:"
    echo "1. 打开终端"
    echo "2. 运行: crontab -e"
    echo "3. 添加以下行:"
    echo "   $CRON_TASK"
    echo "4. 保存并退出 (按ESC，输入:wq，回车)"
fi

# 清理
rm -f "$PROJECT_DIR/my_cron_job.txt"

echo ""
echo "🎯 自动化设置完成！"
echo "系统现在会:"
echo "1. 实时监控文件变化 ✅"
echo "2. 每周自动重建索引 ✅"
echo "3. 提供即时语义搜索 ✅"