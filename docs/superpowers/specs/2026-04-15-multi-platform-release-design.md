# Slymarbo Game 多平台发布设计

## 概述

将 Pygame 游戏 "The Adventures of Slymarbo" 打包发布到三个平台：Windows、macOS 和 Web，并通过 GitHub 开源分发。

## 目标平台

| 平台 | 输出格式 | 分发方式 | 技术方案 |
|------|----------|----------|----------|
| Windows | `.exe` 单文件 | GitHub Releases | PyInstaller |
| macOS | `.app` 应用包 | GitHub Releases | PyInstaller |
| Web | WebAssembly | 自有服务器静态托管 | pygbag |

## 技术选型

### 桌面打包：PyInstaller

- 成熟稳定，Pygame 社区广泛使用
- 单文件输出，分发简单
- 跨平台支持

### Web 编译：pygbag

- Pygame 官方推荐的 Web 方案
- 将 Python 编译为 WebAssembly
- 代码零改动或极小改动
- 适合个人/小范围使用场景

### CI/CD：GitHub Actions

- 推送标签自动构建三端
- 自动创建 GitHub Release
- 无需本地构建环境

## 目录结构

```
slymarbo-game/
├── src/                        # 游戏源码
│   ├── main.py
│   ├── game.py
│   ├── player.py
│   ├── enemies.py
│   ├── objects.py
│   ├── constants.py
│   └── utils.py
├── build/                      # 构建配置
│   ├── slymarbo.spec          # PyInstaller 配置
│   └── build_web.sh           # Web 构建脚本
├── .github/workflows/          # CI/CD
│   └── release.yml            # 自动构建发布
├── web/                        # Web 版输出（gitignored）
├── dist/                       # 桌面版输出（gitignored）
├── requirements.txt
├── README.md
└── LICENSE
```

## GitHub Actions 工作流

触发条件：推送 `v*` 标签（如 `v1.0.0`）

执行步骤：
1. Windows 构建 → 生成 `slymarbo-windows.exe`
2. macOS 构建 → 生成 `slymarbo-macos.zip`
3. Web 构建 → 生成 `slymarbo-web.zip`
4. 创建 GitHub Release，上传三端产物

## Web 部署流程

用户在自有服务器上执行：

```bash
# 首次部署
git clone https://github.com/用户名/slymarbo-game.git
cd slymarbo-game

# 后续更新
git pull
cp -r web/* /var/www/slymarbo/
```

需要确保服务器：
- 已配置 HTTPS（Let's Encrypt 免费）
- Nginx/Apache 正确设置 MIME 类型（.wasm, .data）

## 开源信息

- **仓库名称**: `slymarbo-game`
- **开源协议**: MIT
- **README 语言**: 中文

## 用户群体

自己和朋友游玩，接受 pygbag 的首次加载延迟（10-30秒）。

## 不在范围内

- Android/iOS 移动端
- 商业化运营
- 多语言支持（目前仅中文）