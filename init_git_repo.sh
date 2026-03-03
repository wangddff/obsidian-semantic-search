#!/bin/bash

# Obsidian语义搜索 - Git仓库初始化脚本
# 用法: ./init_git_repo.sh [仓库名]

set -e

REPO_NAME="${1:-obsidian-semantic-search}"

echo "🚀 初始化Git仓库: $REPO_NAME"
echo "=========================================="

# 1. 检查是否已存在.git目录
if [ -d ".git" ]; then
    echo "⚠️  警告: 已存在.git目录"
    read -p "是否重新初始化? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消操作"
        exit 1
    fi
    rm -rf .git
    echo "已删除旧的.git目录"
fi

# 2. 初始化Git仓库
echo "1. 初始化Git仓库..."
git init
echo "   ✅ Git仓库初始化完成"

# 3. 设置分支名称为main
echo "2. 设置分支名称..."
git branch -M main
echo "   ✅ 分支名称设置为: main"

# 4. 添加文件
echo "3. 添加文件到暂存区..."
git add .
echo "   ✅ 文件已添加到暂存区"

# 5. 显示将要提交的文件
echo "4. 将要提交的文件:"
git status --short

# 6. 提交
echo "5. 提交更改..."
git commit -m "初始提交: Obsidian语义搜索项目 v1.0

项目特性:
- BGE-M3模型集成 (1024维向量)
- LanceDB向量存储
- 智能分块处理 (2000-4000字符)
- 完整的语义搜索管道
- 详细的测试套件
- 生产就绪配置

技术栈:
- Python 3.14+
- BGE-M3 via LM Studio API
- LanceDB 0.29.2
- 支持Obsidian笔记格式

状态: 90%完成，核心功能全部实现"
echo "   ✅ 提交完成"

# 7. 显示提交信息
echo "6. 提交信息:"
git log --oneline -1

# 8. 提供GitHub连接指南
echo ""
echo "=========================================="
echo "🎉 Git仓库初始化完成！"
echo ""
echo "下一步: 连接到GitHub仓库"
echo ""
echo "方法1: 在GitHub创建新仓库"
echo "  1. 访问: https://github.com/new"
echo "  2. 仓库名称: $REPO_NAME"
echo "  3. 描述: Semantic search for Obsidian notes using BGE-M3 and LanceDB"
echo "  4. 选择: Public 或 Private"
echo "  5. 不要初始化README、.gitignore或许可证"
echo "  6. 点击创建仓库"
echo ""
echo "方法2: 使用GitHub CLI (如果已安装)"
echo "  gh repo create $REPO_NAME --public --source=. --remote=origin --push"
echo ""
echo "连接命令:"
echo "  git remote add origin https://github.com/YOUR_USERNAME/$REPO_NAME.git"
echo "  git push -u origin main"
echo ""
echo "或者使用SSH:"
echo "  git remote add origin git@github.com:YOUR_USERNAME/$REPO_NAME.git"
echo "  git push -u origin main"
echo ""
echo "📝 注意:"
echo "  - 请将 YOUR_USERNAME 替换为你的GitHub用户名"
echo "  - 确保venv/目录已被.gitignore排除"
echo "  - 首次推送可能需要GitHub身份验证"
echo ""
echo "项目信息:"
echo "  - 文件数量: $(find . -type f ! -path "./venv/*" ! -path "./.git/*" | wc -l)"
echo "  - 代码行数: $(find src -name "*.py" -exec cat {} \; | wc -l) (仅src目录)"
echo "  - 项目大小: $(du -sh . --exclude=venv --exclude=.git | cut -f1)"
echo ""
echo "✅ 准备就绪，可以上传到GitHub！"