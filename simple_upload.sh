#!/bin/bash

echo "🚀 简单上传方法..."
echo "=========================================="

# 1. 首先在GitHub网站创建仓库
echo "1. 请先在GitHub网站创建仓库:"
echo "   访问: https://github.com/new"
echo "   仓库名: obsidian-semantic-search"
echo "   描述: Semantic search for Obsidian notes using BGE-M3 and LanceDB"
echo "   选择: Public"
echo "   不要初始化README、.gitignore、许可证"
echo ""
read -p "创建完成后按回车继续..." </dev/tty

# 2. 连接到GitHub并推送
echo "2. 连接到GitHub并推送..."
# 注意: 请在此处设置你的GitHub个人访问令牌
# GITHUB_URL="https://wangddff:your_github_token_here@github.com/wangddff/obsidian-semantic-search.git"

# 移除可能存在的远程仓库
git remote remove origin 2>/dev/null || true

# 添加远程仓库
git remote add origin "$GITHUB_URL"

# 推送
echo "正在推送到GitHub..."
if git push -u origin main; then
    echo "✅ 推送成功！"
else
    echo "❌ 推送失败，请检查:"
    echo "   1. 仓库是否已创建"
    echo "   2. 仓库名是否正确"
    echo "   3. 网络连接是否正常"
    exit 1
fi

echo ""
echo "🎉 上传完成！"
echo "仓库地址: https://github.com/wangddff/obsidian-semantic-search"