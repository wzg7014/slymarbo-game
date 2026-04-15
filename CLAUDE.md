# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

像素风格魂斗罗游戏 - "The Adventures of Slymarbo"，使用 Pygame 开发的横版动作射击游戏。

## 运行命令

```bash
# 运行游戏
python3 main.py
```

**依赖要求：**
- Python 3.12+
- Pygame 2.6+

## 核心架构

### 模块组织

游戏采用单文件模块化设计，总代码量约4790行：

- **main.py** (190行) - 主循环与状态机分发
- **game.py** (2027行) - 游戏主类，关卡系统，敌人生成，碰撞检测
- **player.py** (520行) - 玩家逻辑：移动、射击、近战、升级系统
- **enemies.py** (986行) - 敌人AI与5种Boss实现
- **objects.py** (821行) - 游戏对象：平台、子弹、道具、特效
- **constants.py** (129行) - 全局常量：颜色、难度、关卡结构
- **utils.py** (117行) - 字体加载与音效生成

### 游戏状态机

主循环维护以下状态，每个状态有独立的事件处理和渲染：

- `start` - 开始界面
- `level_select` - 选关界面（5个大关）
- `settings` - 设置界面（难度选择、资料库入口）
- `codex` - 资料库浏览
- `codex_detail` - 资料库详情
- `playing` - 游戏主循环
- `paused` - 暂停菜单
- `levelup_select` - 升级选择界面（三选一）
- `gameover` / `victory` - 结局画面
- `level_complete` - 小关完成过渡

### 关卡系统

**大关结构：** 5个大关，每关包含多个小关，最后一个为BOSS关

```python
LEVEL_STRUCTURE = [
    {'sections': 3, 'boss_idx': 1},  # 关1: 2普通+BOSS红
    {'sections': 3, 'boss_idx': 2},  # 关2: 2普通+BOSS蓝
    {'sections': 4, 'boss_idx': 3},  # 关3: 3普通+BOSS紫
    {'sections': 4, 'boss_idx': 4},  # 关4: 3普通+BOSS绿
    {'sections': 4, 'boss_idx': 5},  # 关5: 3普通+BOSS金
]
```

**关卡状态流转：**
- `Game.current_level` (1-5) 当前大关
- `Game.current_section` (1-N) 当前小关
- `Game.global_section_idx` 全局小关编号（用于匹配平台/敌人配置）
- 每小关清空敌人后进入下一关，BOSS关后触发大关完成

### 玩家升级系统

玩家击杀敌人获得经验升级，每次升级从3个随机选项中选择：

```python
UPGRADE_POOL = {
    'bullet_damage',    # 子弹伤害+
    'max_hp_up',        # 生命上限+
    'shotgun',          # 解锁霰弹枪
    'laser',            # 解锁激光枪
    'melee_reflect',    # 近战反弹子弹
    'trap_immune',      # 陷阱免疫
    'kill_heal',        # 击杀回血
    'auto_shield',      # 自动护盾
}
```

已选升级存储在 `Player.upgrades` 字典中。

### 敌人系统

**敌人类型：**
- `Enemy` - 基础敌人（行走/射击）
- `FlyingEnemy` - 飞行敌人（追踪玩家）
- `TurretEnemy` - 炮台（固定射击）

**Boss类型：**
- `RedBoss` - 红色Boss（恐虐主题）
- `BlueBoss` - 蓝色Boss（奸奇主题）
- `PurpleBoss` - 紫色Boss（色孽主题）
- `GreenBoss` - 绿色Boss（纳垢主题）
- `GoldBoss` - 金色Boss（帝皇主题）

每个Boss有独特的攻击模式和特殊技能。

### 平台生成

平台采用预设配置 + 随机选择机制：
- `Game._gen_platforms(idx)` 根据 `global_section_idx` 选择平台布局
- 三层结构设计：地面Y=620，一层≈535，二层≈450，三层≈365
- 层间距约85px确保单次跳跃可达

### 碰撞检测

游戏使用矩形碰撞检测：
- 子弹碰撞：`Bullet` 与 `Enemy`/`Player`
- 近战攻击：`MeleeAttack` 扇形范围检测
- 平台检测：玩家与敌人都会检测平台着陆

## 操作控制

- **移动**：WASD 或 方向键
- **跳跃**：空格
- **攻击**：J 键（鼠标瞄准射击）
- **武器切换**：1（枪）/ 2（近战）
- **暂停**：ESC
- **界面导航**：方向键 + 回车确认

## 开发注意事项

### 音效系统
音效通过 `utils.generate_sound()` 程序化生成，不依赖外部音频文件。所有音效对象在 `utils.init_all()` 中初始化。

### 字体系统
游戏尝试加载系统中文字体（simhei/msyh/simsun），若失败则使用 Pygame 默认字体。

### 难度系数
```python
DIFFICULTY_SETTINGS = {
    '简单': {'enemy_hp_mult': 0.7, 'bullet_speed_mult': 0.8, ...},
    '普通': {'enemy_hp_mult': 1.0, ...},
    '困难': {'enemy_hp_mult': 1.5, ...},
}
```

难度设置存储在 `Game.difficulty`，在敌人生成时应用。

### 资料库系统
`Game._build_codex()` 构建游戏资料库，包含角色信息和敌人信息两个页面。

### 过渡动画
小关切换使用 `Game.transitioning` 状态，通过 `old_surface` 和 `new_surface` 实现淡入淡出效果。

## 代码风格

- 使用中文注释和文档字符串
- 类采用驼峰命名，变量使用下划线命名
- 所有绘制函数命名为 `draw_*`，更新函数命名为 `update`
- 常量全大写，定义在 `constants.py`