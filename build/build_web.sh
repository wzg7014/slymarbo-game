#!/bin/bash
# Web 版构建脚本 (pygbag)

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Building Slymarbo Web Version ==="

# 清理旧构建
rm -rf web/

# 创建 src/__main__.py 作为入口点
cat > src/__main__.py << 'EOF'
"""Web 版入口点"""
from src.main import main
main()
EOF

# 使用 pygbag 构建
pygbag --width 1000 --height 700 src/

# 移动输出到 web 目录
mv build/web web/

# 清理临时入口文件
rm src/__main__.py

echo "=== Web build complete ==="
echo "Output: web/"
ls -la web/
