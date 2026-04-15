# 多平台发布实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 Slymarbo 游戏打包发布到 Windows、macOS 和 Web 三端，并通过 GitHub Releases 分发。

**Architecture:** 使用 PyInstaller 打包桌面版，pygbag 编译 WebAssembly 版本，GitHub Actions 自动构建和发布。

**Tech Stack:** PyInstaller, pygbag, GitHub Actions, Python 3.12+, Pygame 2.6+

---

## Task 1: 项目目录重构

**Files:**
- Create: `src/` 目录
- Move: 所有 `.py` 文件从根目录移至 `src/`

- [ ] **Step 1: 创建 src 目录并移动源码文件**

```bash
mkdir -p src
mv main.py game.py player.py enemies.py objects.py constants.py utils.py src/
```

- [ ] **Step 2: 更新 src/main.py 的导入路径**

修改 `src/main.py` 第 6-8 行的导入：

```python
# 原代码
from constants import *
import utils
from game import Game

# 改为
from src.constants import *
from src import utils
from src.game import Game
```

- [ ] **Step 3: 更新 src/game.py 的导入路径**

修改 `src/game.py` 顶部的导入（约第 1-10 行）：

```python
# 原代码
from constants import *
from player import Player
from enemies import Enemy, FlyingEnemy, TurretEnemy, RedBoss, BlueBoss, PurpleBoss, GreenBoss, GoldBoss
from objects import Platform, Bullet, MeleeAttack, Item, Explosion
import utils

# 改为
from src.constants import *
from src.player import Player
from src.enemies import Enemy, FlyingEnemy, TurretEnemy, RedBoss, BlueBoss, PurpleBoss, GreenBoss, GoldBoss
from src.objects import Platform, Bullet, MeleeAttack, Item, Explosion
from src import utils
```

- [ ] **Step 4: 更新 src/player.py 的导入路径**

修改 `src/player.py` 顶部导入：

```python
# 原代码
from constants import *
from objects import Bullet, MeleeAttack
import utils

# 改为
from src.constants import *
from src.objects import Bullet, MeleeAttack
from src import utils
```

- [ ] **Step 5: 更新 src/enemies.py 的导入路径**

修改 `src/enemies.py` 顶部导入：

```python
# 原代码
from constants import *
from objects import Bullet
import utils

# 改为
from src.constants import *
from src.objects import Bullet
from src import utils
```

- [ ] **Step 6: 更新 src/objects.py 的导入路径**

修改 `src/objects.py` 顶部导入：

```python
# 原代码
from constants import *
import utils

# 改为
from src.constants import *
from src import utils
```

- [ ] **Step 7: 更新 src/utils.py 的导入路径**

`src/utils.py` 只使用标准库和 pygame，无需修改导入。

- [ ] **Step 8: 验证重构后游戏可运行**

```bash
cd /Users/liepin/Desktop/contra
python3 -c "from src.main import main; print('Import OK')"
```

Expected: 输出 `Import OK`

- [ ] **Step 9: 提交重构**

```bash
git add src/
git rm main.py game.py player.py enemies.py objects.py constants.py utils.py
git commit -m "refactor: 移动源码到 src/ 目录"
```

---

## Task 2: 添加基础发布文件

**Files:**
- Create: `requirements.txt`
- Create: `README.md`
- Create: `LICENSE`
- Modify: `.gitignore`

- [ ] **Step 1: 创建 requirements.txt**

```text
pygame>=2.6.0
pyinstaller>=6.0.0
pygbag>=0.8.0
```

- [ ] **Step 2: 创建 LICENSE (MIT)**

```text
MIT License

Copyright (c) 2026 xiaoguang

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 3: 创建 README.md**

```markdown
# Slymarbo Game

像素风格魂斗罗游戏 - "The Adventures of Slymarbo"，使用 Pygame 开发的横版动作射击游戏。

## 游戏特色

- 5个大关，每关包含多个小关和独特Boss
- 升级系统：击杀敌人获得经验，从三个随机升级中选择
- 多种武器：枪械（可解锁霰弹枪、激光枪）和近战攻击
- 三种难度：简单、普通、困难
- 程序化音效生成，无需外部音频文件

## 下载

前往 [Releases](../../releases) 页面下载：

- `slymarbo-windows.exe` - Windows 版本
- `slymarbo-macos.zip` - macOS 版本（解压后运行 .app）
- `slymarbo-web.zip` - Web 版本（需部署到服务器）

## 本地运行

```bash
# 安装依赖
pip install pygame

# 运行游戏
python3 -m src.main
```

## 操作说明

| 操作 | 按键 |
|------|------|
| 移动 | WASD 或 方向键 |
| 跳跃 | 空格 |
| 攻击 | J 键（鼠标瞄准射击） |
| 武器切换 | 1（枪）/ 2（近战） |
| 暂停 | ESC |

## 开发

依赖要求：
- Python 3.12+
- Pygame 2.6+

```bash
# 安装开发依赖
pip install -r requirements.txt

# 构建桌面版
pyinstaller build/slymarbo.spec

# 构建 Web 版
./build/build_web.sh
```

## License

MIT License - 详见 [LICENSE](LICENSE)
```

- [ ] **Step 4: 更新 .gitignore**

追加到现有 `.gitignore`：

```text
# 构建输出
dist/
build/
web/

# PyInstaller
*.spec.backup

# Python
__pycache__/
*.pyc
*.pyo
.pytest_cache/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 5: 提交基础文件**

```bash
git add requirements.txt README.md LICENSE .gitignore
git commit -m "docs: 添加 requirements.txt, README.md, LICENSE"
```

---

## Task 3: 创建 PyInstaller 构建配置

**Files:**
- Create: `build/slymarbo.spec`
- Create: `build/build_local.sh`

- [ ] **Step 1: 创建 build 目录**

```bash
mkdir -p build
```

- [ ] **Step 2: 创建 PyInstaller spec 文件**

`build/slymarbo.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# 获取项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

a = Analysis(
    [os.path.join(project_root, 'src', 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pygame',
        'pygame.mixer',
        'pygame.font',
        'src.constants',
        'src.utils',
        'src.game',
        'src.player',
        'src.enemies',
        'src.objects',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Slymarbo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可后续添加图标
)
```

- [ ] **Step 3: 创建本地构建脚本**

`build/build_local.sh`:

```bash
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
```

- [ ] **Step 4: 提交构建配置**

```bash
git add build/
git commit -m "build: 添加 PyInstaller 构建配置"
```

---

## Task 4: 创建 pygbag Web 构建脚本

**Files:**
- Create: `build/build_web.sh`

- [ ] **Step 1: 创建 Web 构建脚本**

`build/build_web.sh`:

```bash
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
pygbag --build-name "Slymarbo" --width 1000 --height 700 src/

# 移动输出到 web 目录
mv build/web web/

# 清理临时入口文件
rm src/__main__.py

echo "=== Web build complete ==="
echo "Output: web/"
ls -la web/
```

- [ ] **Step 2: 提交 Web 构建脚本**

```bash
git add build/build_web.sh
git commit -m "build: 添加 pygbag Web 构建脚本"
```

---

## Task 5: 创建 GitHub Actions 工作流

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: 创建工作流目录**

```bash
mkdir -p .github/workflows
```

- [ ] **Step 2: 创建 release.yml 工作流**

`.github/workflows/release.yml`:

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install pygame pyinstaller
      
      - name: Build Windows executable
        run: |
          pyinstaller build/slymarbo.spec --clean
      
      - name: Rename output
        run: |
          mv dist/Slymarbo.exe dist/slymarbo-windows.exe
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: windows-build
          path: dist/slymarbo-windows.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install pygame pyinstaller
      
      - name: Build macOS app
        run: |
          pyinstaller build/slymarbo.spec --clean
      
      - name: Create zip archive
        run: |
          cd dist
          zip -r slymarbo-macos.zip Slymarbo.app
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: macos-build
          path: dist/slymarbo-macos.zip

  build-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install pygame pygbag
      
      - name: Create entry point
        run: |
          echo 'from src.main import main; main()' > src/__main__.py
      
      - name: Build Web version
        run: |
          pygbag --build-name "Slymarbo" --width 1000 --height 700 src/
      
      - name: Prepare output
        run: |
          mkdir -p web-output
          cp -r build/web/* web-output/
          cd web-output
          zip -r slymarbo-web.zip .
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: web-build
          path: web-output/slymarbo-web.zip

  release:
    needs: [build-windows, build-macos, build-web]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            artifacts/windows-build/slymarbo-windows.exe
            artifacts/macos-build/slymarbo-macos.zip
            artifacts/web-build/slymarbo-web.zip
          body: |
            ## Slymarbo Game Release
            
            ### 下载
            
            | 平台 | 文件 |
            |------|------|
            | Windows | `slymarbo-windows.exe` |
            | macOS | `slymarbo-macos.zip` |
            | Web | `slymarbo-web.zip` |
            
            ### Web 版部署
            
            解压 `slymarbo-web.zip`，将内容上传到服务器静态目录即可。
```

- [ ] **Step 3: 提交工作流**

```bash
git add .github/workflows/release.yml
git commit -m "ci: 添加 GitHub Actions 自动构建发布工作流"
```

---

## Task 6: GitHub 仓库初始化

**Files:**
- 无新文件，执行 git 操作

- [ ] **Step 1: 创建 GitHub 仓库**

```bash
gh repo create slymarbo-game --public --source=. --remote=origin --push
```

Expected: 创建成功并推送代码

- [ ] **Step 2: 验证仓库状态**

```bash
git remote -v
gh repo view slymarbo-game
```

Expected: 显示仓库信息

---

## Task 7: 首次发布 (v1.0.0)

**Files:**
- 无新文件，执行 git 操作

- [ ] **Step 1: 确保所有更改已提交**

```bash
git status
```

Expected: `nothing to commit, working tree clean`

- [ ] **Step 2: 创建并推送版本标签**

```bash
git tag -a v1.0.0 -m "Release v1.0.0 - First multi-platform release"
git push origin v1.0.0
```

Expected: 标签推送成功

- [ ] **Step 3: 监控 GitHub Actions 构建**

```bash
gh run list --limit 5
```

Expected: 显示正在运行的 workflow

- [ ] **Step 4: 等待构建完成后查看 Release**

```bash
gh release view v1.0.0
```

Expected: Release 包含三端下载文件

---

## Task 8: Web 版部署指南（用户手动执行）

此任务为用户提供服务器部署步骤，不在本地执行。

- [ ] **Step 1: 用户提供部署命令**

用户在服务器上执行：

```bash
# 下载 Web 版
wget https://github.com/你的用户名/slymarbo-game/releases/download/v1.0.0/slymarbo-web.zip

# 解压到网站目录
unzip slymarbo-web.zip -d /var/www/slymarbo/

# 配置 Nginx（示例）
# 添加到 nginx 配置：
# location /slymarbo/ {
#     alias /var/www/slymarbo/;
#     types {
#         application/wasm wasm;
#         application/octet-stream data;
#     }
# }
```

---

## 计划自检

### 1. Spec 覆盖检查

| Spec 需求 | 对应 Task |
|-----------|-----------|
| 目录结构重构 | Task 1 |
| requirements.txt | Task 2 |
| README.md | Task 2 |
| LICENSE (MIT) | Task 2 |
| .gitignore 更新 | Task 2 |
| PyInstaller spec | Task 3 |
| Web 构建脚本 | Task 4 |
| GitHub Actions | Task 5 |
| GitHub 仓库创建 | Task 6 |
| 首次发布 | Task 7 |
| Web 部署指南 | Task 8 |

✅ 所有 Spec 需求已覆盖

### 2. Placeholder 扫描

✅ 无 TBD/TODO 占位符
✅ 无 "添加适当错误处理" 等模糊描述
✅ 无缺失的代码块

### 3. 类型一致性

✅ 导入路径统一使用 `src.` 前缀
✅ 构建输出命名一致：`slymarbo-{platform}`