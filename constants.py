"""
常量定义模块
"""
import pygame

# ============================================================
# 屏幕设置
# ============================================================
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
GROUND_Y = 620

# ============================================================
# 颜色定义
# ============================================================
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 50, 50)
DARK_RED = (150, 30, 30)
GREEN = (50, 200, 50)
DARK_GREEN = (30, 120, 30)
BLUE = (50, 100, 220)
DARK_BLUE = (30, 60, 150)
YELLOW = (255, 220, 50)
PURPLE = (180, 50, 220)
DARK_PURPLE = (120, 30, 150)
GOLD = (255, 200, 50)
ORANGE = (255, 150, 50)
CYAN = (50, 220, 220)
GRAY = (150, 150, 150)
DARK_GRAY = (80, 80, 80)
BROWN = (139, 90, 43)
SKIN = (240, 195, 150)
LIGHT_BLUE = (120, 170, 255)
LIGHT_GREEN = (100, 255, 100)
LIGHT_RED = (255, 100, 100)
PINK = (255, 140, 200)
LIME = (150, 255, 50)

# ============================================================
# 背景颜色
# ============================================================
BG_START = (15, 15, 35)
BG_SETTINGS = (35, 20, 15)
BG_LEVELS = [
    (10, 20, 10),   # 关卡1
    (15, 22, 12),   # 关卡2
    (30, 12, 12),   # BOSS1(红)
    (10, 12, 25),   # 关卡4
    (12, 15, 28),   # 关卡5
    (18, 10, 28),   # BOSS2(蓝)
    (22, 10, 22),   # 关卡7
    (25, 12, 25),   # 关卡8
    (28, 12, 22),   # BOSS3(紫)
    (12, 22, 18),   # 关卡10
    (10, 25, 15),   # 关卡11
    (10, 28, 10),   # BOSS4(绿)
    (25, 22, 10),   # 关卡13
    (28, 25, 10),   # 关卡14
    (30, 25, 8),    # BOSS5(金)
]

# ============================================================
# 难度设置
# ============================================================
DIFFICULTY_SETTINGS = {
    '简单': {
        'enemy_hp_mult': 0.7,
        'bullet_speed_mult': 0.8,
        'enemy_damage': 1,
        'boss_hp_mult': 0.6,
    },
    '普通': {
        'enemy_hp_mult': 1.0,
        'bullet_speed_mult': 1.0,
        'enemy_damage': 1,
        'boss_hp_mult': 1.0,
    },
    '困难': {
        'enemy_hp_mult': 1.5,
        'bullet_speed_mult': 1.3,
        'enemy_damage': 2,
        'boss_hp_mult': 1.5,
    },
}

# ============================================================
# 按键映射
# ============================================================
KEY_LEFT = [pygame.K_a, pygame.K_LEFT]
KEY_RIGHT = [pygame.K_d, pygame.K_RIGHT]
KEY_UP = [pygame.K_w, pygame.K_UP]
KEY_DOWN = [pygame.K_s, pygame.K_DOWN]
KEY_JUMP = pygame.K_SPACE
KEY_ATTACK = pygame.K_j
KEY_GUN = pygame.K_1
KEY_SWORD = pygame.K_2
KEY_PAUSE = pygame.K_ESCAPE

# ============================================================
# 大关结构配置
# ============================================================
LEVEL_STRUCTURE = [
    {'sections': 3, 'boss_idx': 1},   # Level 1: 2普通 + Boss红
    {'sections': 3, 'boss_idx': 2},   # Level 2: 2普通 + Boss蓝
    {'sections': 4, 'boss_idx': 3},   # Level 3: 3普通 + Boss紫
    {'sections': 4, 'boss_idx': 4},   # Level 4: 3普通 + Boss绿
    {'sections': 4, 'boss_idx': 5},   # Level 5: 3普通 + Boss金
]
TOTAL_LEVELS = 5

# 每个大关的小怪颜色主题（与BOSS统一）
# 每大关3个色阶: [主色, 深色, 亮色]
LEVEL_COLORS = {
    1: [RED, DARK_RED, ORANGE],             # 红色系 (恐虐)
    2: [BLUE, DARK_BLUE, LIGHT_BLUE],       # 蓝色系 (奸奇)
    3: [PURPLE, DARK_PURPLE, PINK],         # 紫色系 (色孽)
    4: [GREEN, DARK_GREEN, LIME],           # 绿色系 (纳垢)
    5: [GOLD, (180, 140, 30), YELLOW],      # 金色系 (帝皇)
}
# 飞行敌人子弹颜色
LEVEL_BULLET_COLORS = {
    1: ORANGE,
    2: CYAN,
    3: PINK,
    4: LIME,
    5: YELLOW,
}
