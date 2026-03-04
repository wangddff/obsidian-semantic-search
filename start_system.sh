#!/bin/bash
# Obsidian语义搜索系统启动脚本

echo "🚀 启动Obsidian语义搜索系统..."
echo "========================================"

cd /Users/wangdf/.openclaw/workspace/obsidian_semantic_search

# 1. 激活虚拟环境
source venv/bin/activate

# 2. 检查监控是否已在运行
if ps aux | grep -q "cli.py monitor daemon" | grep -v grep; then
    echo "✅ 实时监控已在运行"
else
    echo "📡 启动实时监控..."
    nohup python cli.py monitor daemon > logs/monitor.log 2>&1 &
    echo "✅ 实时监控已启动 (后台运行)"
fi

# 3. 检查数据库状态
echo ""
echo "📊 系统状态:"
echo "----------------------------------------"

# 检查监控进程
MONITOR_PID=$(ps aux | grep "cli.py monitor daemon" | grep -v grep | awk '{print $2}')
if [ -n "$MONITOR_PID" ]; then
    echo "实时监控: ✅ 运行中 (PID: $MONITOR_PID)"
else
    echo "实时监控: ❌ 未运行"
fi

# 检查数据库记录
RECORD_COUNT=$(python -c "
import sys
sys.path.append('src')
try:
    from vector_store import LanceDBVectorStore
    store = LanceDBVectorStore('./data/lancedb', 'obsidian_embeddings_bge_m3', 1024)
    if store.connect():
        stats = store.get_stats()
        print(stats.get('total_records', 0))
    else:
        print('0')
except:
    print('0')
" 2>/dev/null)

echo "数据库记录: 📊 $RECORD_COUNT 条"

# 4. 检查日志目录
echo ""
echo "📁 日志文件:"
echo "----------------------------------------"
ls -la logs/ 2>/dev/null | head -5 || echo "日志目录为空"

# 5. 使用说明
echo ""
echo "💡 使用说明:"
echo "----------------------------------------"
echo "1. 搜索笔记: python cli.py search '查询内容'"
echo "2. 查看状态: python cli.py monitor status"
echo "3. 重建索引: python cli.py rebuild --full"
echo "4. 停止监控: kill $MONITOR_PID"
echo ""
echo "📝 监控日志: tail -f logs/monitor.log"
echo ""

echo "🎉 系统启动完成！"
echo "现在可以开始使用语义搜索了。"