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
| 攻击 | J 键（鼠标瞄准射击）|
| 武器切换 | 1（枪）/ 2（近战）|
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
