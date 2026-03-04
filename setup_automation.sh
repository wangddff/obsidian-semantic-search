#!/bin/bash
# Obsidian语义搜索自动化安装脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_header() {
    echo ""
    echo "================================================"
    echo -e "${BLUE}$1${NC}"
    echo "================================================"
    echo ""
}

# 检查是否以正确用户运行
check_user() {
    if [ "$(whoami)" != "wangdf" ]; then
        print_warning "建议以 'wangdf' 用户运行此脚本"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 步骤1：检查环境
step_check_environment() {
    print_header "步骤1: 检查环境"
    
    # 检查项目目录
    PROJECT_DIR="/Users/wangdf/.openclaw/workspace/obsidian_semantic_search"
    if [ ! -d "$PROJECT_DIR" ]; then
        print_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    # 检查虚拟环境
    VENV_PATH="$PROJECT_DIR/venv"
    if [ ! -d "$VENV_PATH" ]; then
        print_error "虚拟环境不存在: $VENV_PATH"
        print_info "请先创建虚拟环境: cd $PROJECT_DIR && python -m venv venv"
        exit 1
    fi
    
    # 检查依赖
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        print_error "requirements.txt 不存在"
        exit 1
    fi
    
    print_success "环境检查通过"
}

# 步骤2：安装依赖
step_install_dependencies() {
    print_header "步骤2: 安装依赖"
    
    cd "$PROJECT_DIR"
    
    # 激活虚拟环境
    source "$VENV_PATH/bin/activate"
    
    # 检查watchdog是否已安装
    if ! pip list | grep -q watchdog; then
        print_info "安装watchdog..."
        pip install watchdog
        if [ $? -eq 0 ]; then
            print_success "watchdog安装成功"
        else
            print_error "watchdog安装失败"
            exit 1
        fi
    else
        print_info "watchdog已安装"
    fi
    
    # 更新requirements.txt
    print_info "更新requirements.txt..."
    pip freeze | grep watchdog > requirements_watchdog.txt
    grep -v "watchdog" requirements.txt > requirements_temp.txt
    cat requirements_temp.txt requirements_watchdog.txt > requirements_new.txt
    mv requirements_new.txt requirements.txt
    rm -f requirements_temp.txt requirements_watchdog.txt
    
    print_success "依赖安装完成"
}

# 步骤3：测试监控功能
step_test_monitor() {
    print_header "步骤3: 测试监控功能"
    
    cd "$PROJECT_DIR"
    source "$VENV_PATH/bin/activate"
    
    print_info "运行监控测试..."
    if python test_monitor.py; then
        print_success "监控功能测试通过"
    else
        print_error "监控功能测试失败"
        print_info "请检查错误信息并修复"
        exit 1
    fi
}

# 步骤4：设置自动化脚本
step_setup_automation_scripts() {
    print_header "步骤4: 设置自动化脚本"
    
    # 确保自动化脚本有执行权限
    chmod +x "$PROJECT_DIR/automation_manager.sh"
    
    # 测试自动化脚本
    print_info "测试自动化脚本..."
    if "$PROJECT_DIR/automation_manager.sh" status; then
        print_success "自动化脚本测试通过"
    else
        print_warning "自动化脚本测试有警告，但继续安装"
    fi
}

# 步骤5：设置launchd服务
step_setup_launchd() {
    print_header "步骤5: 设置launchd服务 (macOS)"
    
    PLIST_SOURCE="$PROJECT_DIR/com.wangdf.obsidian-semantic-search.plist"
    PLIST_DEST="$HOME/Library/LaunchAgents/com.wangdf.obsidian-semantic-search.plist"
    
    # 创建LaunchAgents目录（如果不存在）
    mkdir -p "$HOME/Library/LaunchAgents"
    
    # 复制plist文件
    if [ -f "$PLIST_SOURCE" ]; then
        cp "$PLIST_SOURCE" "$PLIST_DEST"
        print_success "plist文件已复制到: $PLIST_DEST"
    else
        print_error "plist源文件不存在: $PLIST_SOURCE"
        exit 1
    fi
    
    # 加载服务
    print_info "加载launchd服务..."
    if launchctl list | grep -q "com.wangdf.obsidian-semantic-search"; then
        print_info "服务已存在，先卸载..."
        launchctl unload "$PLIST_DEST" 2>/dev/null || true
    fi
    
    launchctl load "$PLIST_DEST"
    
    if [ $? -eq 0 ]; then
        print_success "launchd服务加载成功"
        
        # 立即启动服务
        print_info "启动服务..."
        launchctl start com.wangdf.obsidian-semantic-search
        sleep 2
        
        # 检查服务状态
        if launchctl list | grep -q "com.wangdf.obsidian-semantic-search"; then
            print_success "服务启动成功"
        else
            print_warning "服务可能未启动，请检查日志"
        fi
    else
        print_error "launchd服务加载失败"
        exit 1
    fi
}

# 步骤6：设置cron任务
step_setup_cron() {
    print_header "步骤6: 设置cron定时任务"
    
    print_info "设置每周全量重建任务..."
    
    # 使用自动化脚本设置cron
    if "$PROJECT_DIR/automation_manager.sh" setup-cron; then
        print_success "cron任务设置成功"
        print_info "计划: 每周日凌晨3点运行全量重建"
    else
        print_error "cron任务设置失败"
        print_info "你可以手动设置:"
        echo "  0 3 * * 0 cd $PROJECT_DIR && ./automation_manager.sh rebuild >> logs/cron.log 2>&1"
    fi
}

# 步骤7：运行首次全量重建
step_first_rebuild() {
    print_header "步骤7: 运行首次全量重建"
    
    read -p "是否现在运行首次全量重建? (建议运行) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "开始首次全量重建..."
        
        if "$PROJECT_DIR/automation_manager.sh" rebuild; then
            print_success "首次全量重建完成"
            print_info "现在可以开始使用语义搜索了!"
        else
            print_error "首次全量重建失败"
            print_info "请检查日志并手动运行: ./automation_manager.sh rebuild"
        fi
    else
        print_info "跳过首次全量重建"
        print_info "你可以稍后手动运行: ./automation_manager.sh rebuild"
    fi
}

# 步骤8：显示完成信息
step_final_info() {
    print_header "安装完成!"
    
    echo ""
    echo "🎉 Obsidian语义搜索自动化系统已安装完成!"
    echo ""
    
    echo "📊 系统状态:"
    echo "   实时监控: ${GREEN}已启用${NC} (开机自启动)"
    echo "   定期重建: ${GREEN}已计划${NC} (每周日凌晨3点)"
    echo "   搜索功能: ${GREEN}就绪${NC}"
    echo ""
    
    echo "🚀 使用方法:"
    echo "   1. 监控管理:"
    echo "     启动监控:   ./automation_manager.sh start"
    echo "     停止监控:   ./automation_manager.sh stop"
    echo "     查看状态:   ./automation_manager.sh status"
    echo ""
    echo "   2. 索引管理:"
    echo "     全量重建:   ./automation_manager.sh rebuild"
    echo "     搜索测试:   python cli.py search \"查询内容\""
    echo ""
    echo "   3. 系统管理:"
    echo "     清理日志:   ./automation_manager.sh cleanup"
    echo "     移除cron:   ./automation_manager.sh remove-cron"
    echo ""
    
    echo "📁 重要文件:"
    echo "   项目目录:     $PROJECT_DIR"
    echo "   配置文件:     $PROJECT_DIR/config/config.yaml"
    echo "   监控配置:     $PROJECT_DIR/config/monitor_config.yaml"
    echo "   日志目录:     $PROJECT_DIR/logs/"
    echo ""
    
    echo "🔧 服务管理 (macOS):"
    echo "   启动服务:     launchctl start com.wangdf.obsidian-semantic-search"
    echo "   停止服务:     launchctl stop com.wangdf.obsidian-semantic-search"
    echo "   查看状态:     launchctl list | grep obsidian"
    echo "   卸载服务:     launchctl unload $HOME/Library/LaunchAgents/com.wangdf.obsidian-semantic-search.plist"
    echo ""
    
    echo "📝 下一步建议:"
    echo "   1. 运行首次全量重建建立索引"
    echo "   2. 测试文件监控功能（创建/修改/删除文件）"
    echo "   3. 测试语义搜索功能"
    echo "   4. 检查日志确保一切正常"
    echo ""
    
    echo "💡 提示: 所有操作日志都在 $PROJECT_DIR/logs/ 目录中"
    echo ""
}

# 主安装流程
main() {
    print_header "Obsidian语义搜索自动化安装向导"
    
    # 检查用户
    check_user
    
    # 定义项目目录
    PROJECT_DIR="/Users/wangdf/.openclaw/workspace/obsidian_semantic_search"
    VENV_PATH="$PROJECT_DIR/venv"
    
    # 执行安装步骤
    step_check_environment
    step_install_dependencies
    step_test_monitor
    step_setup_automation_scripts
    step_setup_launchd
    step_setup_cron
    step_first_rebuild
    step_final_info
    
    print_success "安装完成! 🎉"
}

# 运行主函数
main "$@"