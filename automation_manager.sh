#!/bin/bash
# Obsidian语义搜索自动化管理脚本
# 管理监控守护进程和定期重建任务

set -e

# 配置
PROJECT_DIR="/Users/wangdf/.openclaw/workspace/obsidian_semantic_search"
VENV_PATH="$PROJECT_DIR/venv"
PYTHON_CMD="$VENV_PATH/bin/python"
CLI_CMD="$PYTHON_CMD $PROJECT_DIR/cli.py"
CONFIG_FILE="$PROJECT_DIR/config/config.yaml"

# 日志目录
LOG_DIR="$PROJECT_DIR/logs"
MONITOR_LOG="$LOG_DIR/monitor.log"
REBUILD_LOG="$LOG_DIR/rebuild.log"
CRON_LOG="$LOG_DIR/cron.log"

# PID文件
MONITOR_PID_FILE="$PROJECT_DIR/.monitor.pid"
LOCK_FILE="$PROJECT_DIR/.automation.lock"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 函数：检查依赖
check_dependencies() {
    print_info "检查依赖..."
    
    # 检查项目目录
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    # 检查虚拟环境
    if [ ! -d "$VENV_PATH" ]; then
        print_error "虚拟环境不存在: $VENV_PATH"
        exit 1
    fi
    
    # 检查Python
    if [ ! -f "$PYTHON_CMD" ]; then
        print_error "Python不存在: $PYTHON_CMD"
        exit 1
    fi
    
    # 检查CLI
    if [ ! -f "$PROJECT_DIR/cli.py" ]; then
        print_error "CLI工具不存在: $PROJECT_DIR/cli.py"
        exit 1
    fi
    
    print_success "所有依赖检查通过"
}

# 函数：初始化环境
init_environment() {
    print_info "初始化环境..."
    
    # 创建日志目录
    mkdir -p "$LOG_DIR"
    
    # 激活虚拟环境
    source "$VENV_PATH/bin/activate"
    
    print_success "环境初始化完成"
}

# 函数：启动监控守护进程
start_monitor_daemon() {
    print_info "启动监控守护进程..."
    
    # 检查是否已经在运行
    if [ -f "$MONITOR_PID_FILE" ]; then
        PID=$(cat "$MONITOR_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            print_warning "监控进程已经在运行 (PID: $PID)"
            return 0
        else
            print_warning "发现旧的PID文件，清理..."
            rm -f "$MONITOR_PID_FILE"
        fi
    fi
    
    # 启动监控守护进程
    cd "$PROJECT_DIR"
    nohup "$PYTHON_CMD" -m src.file_monitor > "$MONITOR_LOG" 2>&1 &
    MONITOR_PID=$!
    
    # 保存PID
    echo "$MONITOR_PID" > "$MONITOR_PID_FILE"
    
    # 等待进程启动
    sleep 2
    
    if ps -p "$MONITOR_PID" > /dev/null 2>&1; then
        print_success "监控守护进程启动成功 (PID: $MONITOR_PID)"
        print_info "日志文件: $MONITOR_LOG"
    else
        print_error "监控守护进程启动失败"
        rm -f "$MONITOR_PID_FILE"
        return 1
    fi
    
    return 0
}

# 函数：停止监控守护进程
stop_monitor_daemon() {
    print_info "停止监控守护进程..."
    
    if [ ! -f "$MONITOR_PID_FILE" ]; then
        print_warning "没有找到监控PID文件"
        return 0
    fi
    
    PID=$(cat "$MONITOR_PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        print_info "停止进程 (PID: $PID)..."
        kill "$PID"
        
        # 等待进程停止
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        if ps -p "$PID" > /dev/null 2>&1; then
            print_warning "进程未正常停止，强制终止..."
            kill -9 "$PID"
        fi
        
        rm -f "$MONITOR_PID_FILE"
        print_success "监控守护进程已停止"
    else
        print_warning "监控进程未在运行，清理PID文件"
        rm -f "$MONITOR_PID_FILE"
    fi
    
    return 0
}

# 函数：重启监控守护进程
restart_monitor_daemon() {
    print_info "重启监控守护进程..."
    
    stop_monitor_daemon
    sleep 2
    start_monitor_daemon
}

# 函数：运行全量重建
run_full_rebuild() {
    print_info "运行全量重建..."
    
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    REBUILD_LOG_TIMESTAMP="$LOG_DIR/rebuild_$TIMESTAMP.log"
    
    cd "$PROJECT_DIR"
    
    # 运行重建命令
    print_info "开始重建索引..."
    "$PYTHON_CMD" "$PROJECT_DIR/cli.py" rebuild --full --vault "我的Obsidian库" > "$REBUILD_LOG_TIMESTAMP" 2>&1
    
    REBUILD_EXIT_CODE=$?
    
    if [ $REBUILD_EXIT_CODE -eq 0 ]; then
        print_success "全量重建完成"
        print_info "重建日志: $REBUILD_LOG_TIMESTAMP"
        
        # 更新主重建日志
        cat "$REBUILD_LOG_TIMESTAMP" >> "$REBUILD_LOG"
        
        # 发送通知（可选）
        send_notification "全量重建完成" "Obsidian语义搜索索引已重建"
    else
        print_error "全量重建失败 (退出码: $REBUILD_EXIT_CODE)"
        print_info "错误日志: $REBUILD_LOG_TIMESTAMP"
        
        # 发送错误通知（可选）
        send_notification "全量重建失败" "请检查日志: $REBUILD_LOG_TIMESTAMP"
    fi
    
    return $REBUILD_EXIT_CODE
}

# 函数：发送通知（占位符，可根据需要实现）
send_notification() {
    local title="$1"
    local message="$2"
    
    # 这里可以集成各种通知方式
    # 例如：Telegram、邮件、系统通知等
    
    # 暂时只记录到日志
    print_info "通知: $title - $message"
}

# 函数：设置cron任务
setup_cron_jobs() {
    print_info "设置cron任务..."
    
    # 每周日凌晨3点运行全量重建
    CRON_JOB="0 3 * * 0 cd $PROJECT_DIR && $PROJECT_DIR/automation_manager.sh rebuild >> $CRON_LOG 2>&1"
    
    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "automation_manager.sh rebuild"; then
        print_warning "cron任务已存在"
    else
        # 添加cron任务
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        
        if [ $? -eq 0 ]; then
            print_success "cron任务设置成功"
            print_info "计划: 每周日凌晨3点运行全量重建"
        else
            print_error "cron任务设置失败"
            return 1
        fi
    fi
    
    return 0
}

# 函数：移除cron任务
remove_cron_jobs() {
    print_info "移除cron任务..."
    
    # 移除所有相关cron任务
    crontab -l 2>/dev/null | grep -v "automation_manager.sh" | crontab -
    
    if [ $? -eq 0 ]; then
        print_success "cron任务已移除"
    else
        print_error "移除cron任务失败"
        return 1
    fi
    
    return 0
}

# 函数：查看状态
show_status() {
    print_info "系统状态检查..."
    
    echo ""
    echo "=== 项目信息 ==="
    echo "项目目录: $PROJECT_DIR"
    echo "虚拟环境: $VENV_PATH"
    echo "配置文件: $CONFIG_FILE"
    
    echo ""
    echo "=== 监控状态 ==="
    if [ -f "$MONITOR_PID_FILE" ]; then
        PID=$(cat "$MONITOR_PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "状态: ${GREEN}运行中${NC} (PID: $PID)"
            echo "运行时间: $(ps -o etime= -p "$PID" 2>/dev/null || echo "未知")"
        else
            echo "状态: ${RED}已停止${NC} (PID文件存在但进程不存在)"
        fi
    else
        echo "状态: ${YELLOW}未运行${NC}"
    fi
    
    echo ""
    echo "=== 日志文件 ==="
    echo "监控日志: $MONITOR_LOG"
    echo "重建日志: $REBUILD_LOG"
    echo "cron日志: $CRON_LOG"
    
    echo ""
    echo "=== cron任务 ==="
    crontab -l 2>/dev/null | grep -A2 -B2 "automation_manager.sh" || echo "未找到相关cron任务"
    
    echo ""
    echo "=== 数据库状态 ==="
    cd "$PROJECT_DIR"
    "$PYTHON_CMD" -c "
import sys
sys.path.append('src')
try:
    from vector_store import LanceDBVectorStore
    store = LanceDBVectorStore('./data/lancedb', 'obsidian_embeddings_bge_m3', 1024)
    if store.connect():
        stats = store.get_stats()
        print(f'表名: {stats.get(\"table_name\", \"N/A\")}')
        print(f'记录数: {stats.get(\"total_records\", 0)}')
    else:
        print('数据库连接失败')
except Exception as e:
    print(f'检查数据库失败: {e}')
" 2>/dev/null || echo "无法检查数据库状态"
}

# 函数：清理旧日志
cleanup_old_logs() {
    print_info "清理旧日志..."
    
    # 保留最近30天的日志
    find "$LOG_DIR" -name "rebuild_*.log" -mtime +30 -delete 2>/dev/null
    
    # 清理大日志文件（超过100MB）
    find "$LOG_DIR" -name "*.log" -size +100M -delete 2>/dev/null
    
    print_success "日志清理完成"
}

# 函数：显示帮助
show_help() {
    echo "Obsidian语义搜索自动化管理脚本"
    echo ""
    echo "使用方法: $0 <命令>"
    echo ""
    echo "命令:"
    echo "  start         启动监控守护进程"
    echo "  stop          停止监控守护进程"
    echo "  restart       重启监控守护进程"
    echo "  status        查看系统状态"
    echo "  rebuild       运行全量重建"
    echo "  setup-cron    设置cron定时任务"
    echo "  remove-cron   移除cron定时任务"
    echo "  cleanup       清理旧日志"
    echo "  help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start      启动实时监控"
    echo "  $0 rebuild    运行全量重建"
    echo "  $0 status     查看系统状态"
    echo ""
}

# 主函数
main() {
    # 检查依赖
    check_dependencies
    
    # 初始化环境
    init_environment
    
    # 解析命令
    COMMAND="${1:-help}"
    
    case "$COMMAND" in
        start)
            start_monitor_daemon
            ;;
        stop)
            stop_monitor_daemon
            ;;
        restart)
            restart_monitor_daemon
            ;;
        status)
            show_status
            ;;
        rebuild)
            run_full_rebuild
            ;;
        setup-cron)
            setup_cron_jobs
            ;;
        remove-cron)
            remove_cron_jobs
            ;;
        cleanup)
            cleanup_old_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"