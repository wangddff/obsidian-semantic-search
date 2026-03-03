#!/bin/bash

# Obsidian语义搜索 - 自动上传到GitHub脚本
# 使用HTTPS协议和个人访问令牌

set -e

GITHUB_USER="wangddff"
REPO_NAME="obsidian-semantic-search"
# 注意: 请在此处设置你的GitHub个人访问令牌
# GITHUB_TOKEN="your_github_token_here"

echo "🚀 开始上传Obsidian语义搜索项目到GitHub..."
echo "=========================================="
echo "GitHub用户: $GITHUB_USER"
echo "仓库名称: $REPO_NAME"
echo "=========================================="

# 1. 检查是否已存在.git目录
if [ -d ".git" ]; then
    echo "⚠️  发现已存在的.git目录，正在清理..."
    rm -rf .git
    echo "✅ 已清理旧的.git目录"
fi

# 2. 初始化Git仓库
echo "1. 初始化Git仓库..."
git init
git branch -M main
echo "✅ Git仓库初始化完成"

# 3. 添加文件
echo "2. 添加文件到暂存区..."
git add .
echo "✅ 文件已添加到暂存区"

# 4. 显示将要提交的文件
echo "3. 将要提交的文件统计:"
echo "   文件数量: $(git status --short | wc -l)"
git status --short | head -10
if [ $(git status --short | wc -l) -gt 10 ]; then
    echo "   ... 还有更多文件"
fi

# 5. 提交
echo "4. 提交更改..."
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
echo "✅ 提交完成"

# 6. 连接到GitHub
echo "5. 连接到GitHub仓库..."
GITHUB_URL="https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
git remote add origin "$GITHUB_URL"
echo "✅ 已连接到GitHub仓库"

# 7. 推送到GitHub
echo "6. 推送到GitHub..."
echo "   仓库URL: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo "   正在推送，请稍候..."

# 尝试推送
if git push -u origin main; then
    echo "🎉 推送成功！"
else
    echo "❌ 推送失败，尝试创建仓库..."
    
    # 尝试使用GitHub CLI创建仓库（如果可用）
    if command -v gh &> /dev/null; then
        echo "   使用GitHub CLI创建仓库..."
        gh repo create "$REPO_NAME" --public --description "Semantic search for Obsidian notes using BGE-M3 and LanceDB" --push --source=. --remote=origin
    else
        echo "⚠️  GitHub CLI未安装，请先在GitHub网站创建仓库:"
        echo "   https://github.com/new"
        echo "   仓库名: $REPO_NAME"
        echo "   然后重新运行推送命令"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "✅ 上传完成！"
echo ""
echo "项目信息:"
echo "  - GitHub仓库: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo "  - 文件数量: $(find . -type f ! -path "./venv/*" ! -path "./.git/*" | wc -l)"
echo "  - 代码行数: $(find src -name "*.py" -exec cat {} \; | wc -l) (仅src目录)"
echo "  - 项目大小: $(du -sh . --exclude=venv --exclude=.git | cut -f1)"
echo ""
echo "下一步建议:"
echo "  1. 访问仓库: https://github.com/${GITHUB_USER}/${REPO_NAME}"
echo "  2. 添加项目描述和标签"
echo "  3. 设置README.md中的徽章链接"
echo "  4. 考虑添加许可证文件"
echo ""
echo "📝 注意:"
echo "  - 令牌已用于认证，建议定期更新"
echo "  - 确保venv/目录未上传（已在.gitignore中排除）"
echo "  - 检查配置文件中的本地IP地址是否需要修改"
echo ""
echo "🎉 项目已成功上传到GitHub！"