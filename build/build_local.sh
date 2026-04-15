#!/bin/bash
# 本地构建脚本

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== Building Slymarbo ==="

# 清理旧构建
rm -rf dist/ build/*.spec.backup

# 构建
pyinstaller build/slymarbo.spec --clean

echo "=== Build complete ==="
echo "Output: dist/Slymarbo"
