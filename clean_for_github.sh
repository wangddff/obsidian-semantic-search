#!/bin/bash

# Obsidian Semantic Search - GitHub上传准备脚本
# 用法: ./clean_for_github.sh

set -e

echo "🧹 开始清理项目文件，准备上传到GitHub..."

# 1. 删除Python缓存文件
echo "1. 删除Python缓存文件..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name "*~" -delete
find . -name ".coverage" -delete
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

# 2. 删除IDE配置文件
echo "2. 删除IDE配置文件..."
rm -rf .vscode .idea .vs .ropeproject 2>/dev/null || true

# 3. 删除系统文件
echo "3. 删除系统文件..."
find . -name ".DS_Store" -delete
find . -name "Thumbs.db" -delete
find . -name "desktop.ini" -delete

# 4. 删除虚拟环境（但保留requirements.txt）
echo "4. 检查虚拟环境..."
if [ -d "venv" ]; then
    echo "   ⚠️  发现venv目录 (1.1GB)，建议排除不上传"
    echo "   在.gitignore中已排除venv/"
else
    echo "   ✅ 没有venv目录"
fi

# 5. 检查数据文件
echo "5. 检查数据文件..."
if [ -d "data" ]; then
    echo "   📁 data目录存在 (640KB)"
    # 保留.gitkeep文件
    find data -type f ! -name ".gitkeep" -name "*.db" -o -name "*.sqlite" -o -name "*.parquet" -o -name "*.feather" -o -name "*.lancedb" 2>/dev/null | while read file; do
        echo "   删除: $file"
        rm -f "$file"
    done
fi

# 6. 创建必要的.gitkeep文件
echo "6. 确保目录结构..."
for dir in data data/test_results config; do
    if [ -d "$dir" ]; then
        touch "$dir/.gitkeep"
        echo "   创建: $dir/.gitkeep"
    fi
done

# 7. 检查文件大小
echo "7. 检查大文件..."
find . -type f -size +10M 2>/dev/null | while read file; do
    size=$(du -h "$file" | cut -f1)
    echo "   ⚠️  大文件: $file ($size)"
done

# 8. 验证.gitignore
echo "8. 验证.gitignore..."
if [ -f ".gitignore" ]; then
    echo "   ✅ .gitignore文件存在"
    echo "   内容预览:"
    head -20 .gitignore
else
    echo "   ❌ 错误: .gitignore文件不存在"
    exit 1
fi

# 9. 验证README文件
echo "9. 验证文档文件..."
if [ -f "README_GITHUB.md" ]; then
    echo "   ✅ README_GITHUB.md存在"
    # 复制为README.md
    cp README_GITHUB.md README.md
    echo "   已复制为README.md"
else
    echo "   ⚠️  README_GITHUB.md不存在，使用原有README.md"
fi

# 10. 验证许可证文件
echo "10. 验证许可证文件..."
if [ -f "LICENSE" ]; then
    echo "   ✅ LICENSE文件存在"
else
    echo "   ⚠️  LICENSE文件不存在"
fi

# 11. 验证配置文件
echo "11. 验证配置文件..."
if [ -f "config/config.yaml" ]; then
    echo "   ✅ config/config.yaml存在"
    # 检查是否包含敏感信息
    if grep -q "api_key\|password\|secret\|token" config/config.yaml 2>/dev/null; then
        echo "   ⚠️  警告: 配置文件中可能包含敏感信息"
        echo "   请检查: config/config.yaml"
    fi
else
    echo "   ❌ 错误: config/config.yaml不存在"
fi

# 12. 验证源代码
echo "12. 验证源代码..."
src_count=$(find src -name "*.py" 2>/dev/null | wc -l)
if [ "$src_count" -gt 0 ]; then
    echo "   ✅ src目录包含 $src_count 个Python文件"
else
    echo "   ❌ 错误: src目录中没有Python文件"
fi

echo ""
echo "🎉 清理完成！"
echo ""
echo "下一步操作:"
echo "1. 检查敏感信息: grep -r 'api_key\|password\|secret\|token' . --include='*.py' --include='*.yaml' --include='*.yml'"
echo "2. 初始化Git仓库: git init"
echo "3. 添加文件: git add ."
echo "4. 提交: git commit -m '初始提交: Obsidian语义搜索项目'"
echo "5. 连接到GitHub: git remote add origin https://github.com/你的用户名/仓库名.git"
echo "6. 推送: git push -u origin main"
echo ""
echo "建议仓库名:"
echo "  - obsidian-semantic-search"
echo "  - obsidian-bge-m3-search"
echo "  - obsidian-lancedb-search"
echo ""
echo "📝 注意: 请确保venv/目录已被.gitignore排除，不上传到GitHub"