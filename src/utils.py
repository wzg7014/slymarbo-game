"""
工具函数模块 - 字体和音效
"""
import pygame
import os
import array
import math

# ============================================================
# 字体初始化
# ============================================================
def find_cn_font():
    """查找中文字体文件（跨平台支持）"""
    import platform

    system = platform.system()
    font_candidates = []

    if system == "Windows":
        # Windows 字体路径
        fonts_dirs = ["C:/Windows/Fonts"]
        font_names = ['simhei.ttf', 'msyh.ttc', 'simsun.ttc', 'simkai.ttf']
    elif system == "Darwin":  # macOS
        # macOS 字体路径
        fonts_dirs = [
            "/System/Library/Fonts",
            "/Library/Fonts",
            os.path.expanduser("~/Library/Fonts")
        ]
        # macOS 常见中文字体
        font_names = [
            'PingFang.ttc',        # 苹方（现代 macOS 默认中文字体）
            'STHeiti Light.ttc',   # 黑体
            'STHeiti Medium.ttc',  # 黑体
            'Hiragino Sans GB.ttc', # 冬青黑体
            'Songti.ttc',          # 宋体
            'Arial Unicode.ttf',   # Unicode 字体（降级选项）
        ]
    else:  # Linux 和其他系统
        fonts_dirs = [
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts")
        ]
        font_names = [
            'NotoSansCJK-Regular.ttc',  # Noto CJK
            'WenQuanYiMicroHei.ttf',      # 文泉驿微米黑
            'DroidSansFallbackFull.ttf', # Droid 字体
        ]

    # 在所有可能的目录中查找字体
    for fonts_dir in fonts_dirs:
        if not os.path.exists(fonts_dir):
            continue
        for font_name in font_names:
            font_path = os.path.join(fonts_dir, font_name)
            if os.path.exists(font_path):
                print(f"[字体] 找到中文字体: {font_path}")
                return font_path

    print(f"[警告] 未找到中文字体，将使用默认字体（可能显示乱码）")
    print(f"[提示] {system} 系统建议安装中文字体以获得最佳显示效果")
    return None

_CN_FONT_PATH = None

def init_fonts():
    """初始化字体路径"""
    global _CN_FONT_PATH
    _CN_FONT_PATH = find_cn_font()

def make_font(size):
    """创建指定大小的字体"""
    if _CN_FONT_PATH:
        try:
            return pygame.font.Font(_CN_FONT_PATH, size)
        except Exception:
            pass
    return pygame.font.Font(None, size)

# 字体对象（需要在pygame初始化后调用init_fonts）
font_large = None
font_medium = None
font_small = None
font_tiny = None

def create_fonts():
    """创建所有字体对象"""
    global font_large, font_medium, font_small, font_tiny
    init_fonts()
    font_large = make_font(42)
    font_medium = make_font(28)
    font_small = make_font(22)
    font_tiny = make_font(16)

# ============================================================
# 音效生成
# ============================================================
def generate_sound(frequency, duration, volume=0.3, wave_type='square'):
    """生成音效"""
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    if n_samples == 0:
        n_samples = 1
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = float(i) / sample_rate
        if wave_type == 'square':
            val = 1.0 if math.sin(2 * math.pi * frequency * t) > 0 else -1.0
        else:
            val = math.sin(2 * math.pi * frequency * t)
        # 包络
        fade = int(n_samples * 0.1) or 1
        env = 1.0
        if i < fade:
            env = i / fade
        elif i > n_samples - fade:
            env = (n_samples - i) / fade
        buf[i] = int(volume * 32767 * val * env)
    return pygame.mixer.Sound(buffer=buf)

# 音效对象
snd_shoot = None
snd_hit = None
snd_kill = None
snd_levelup = None
snd_pickup = None
snd_melee = None
snd_boss_hit = None
snd_victory = None
snd_gameover = None

def create_sounds():
    """创建所有音效对象"""
    global snd_shoot, snd_hit, snd_kill, snd_levelup
    global snd_pickup, snd_melee, snd_boss_hit, snd_victory, snd_gameover
    try:
        snd_shoot = generate_sound(600, 0.07, 0.15)
        snd_hit = generate_sound(200, 0.1, 0.2)
        snd_kill = generate_sound(800, 0.12, 0.2)
        snd_levelup = generate_sound(1000, 0.3, 0.2, 'sine')
        snd_pickup = generate_sound(900, 0.1, 0.2, 'sine')
        snd_melee = generate_sound(300, 0.08, 0.2)
        snd_boss_hit = generate_sound(150, 0.12, 0.2)
        snd_victory = generate_sound(600, 0.5, 0.2, 'sine')
        snd_gameover = generate_sound(100, 0.4, 0.2)
    except Exception:
        pass

def play_sound(sound):
    """播放音效"""
    if sound:
        try:
            sound.play()
        except Exception:
            pass

def init_all():
    """初始化所有资源"""
    create_fonts()
    create_sounds()
