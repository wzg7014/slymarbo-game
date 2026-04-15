"""
游戏主类模块 —— 大关 / 小关 / 过渡动画
"""
import pygame
import random
import time as time_module
from src.constants import *
from src.player import Player
from src.enemies import Enemy, FlyingEnemy, TurretEnemy, RedBoss, BlueBoss, PurpleBoss, GreenBoss, GoldBoss
from src.objects import Platform, Bullet, MeleeAttack, Item, Spike, ItemBox, LaserBeam, SpinAttack, GroundHand, PoisonCloud, PoisonPool, HitParticle
from src.utils import (play_sound, snd_pickup, snd_gameover, snd_victory,
                       font_large, font_medium, font_small, font_tiny)


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.state = 'start'
        self.difficulty_name = '普通'
        self.difficulty = DIFFICULTY_SETTINGS['普通']
        self.difficulty_options = ['简单', '普通', '困难']
        self.difficulty_index = 1
        self.prev_state = 'start'

        # ---- 选关界面 ----
        self.level_select_idx = 0  # 当前选中的大关 (0~4)

        # ---- 资料库 ----
        self.codex_idx = 0         # 列表页选中索引
        self.codex_page = 0        # 0=角色, 1=敌人
        self.codex_entries = self._build_codex()

        self.player = Player()
        self.bullets = []
        self.melee_attacks = []
        self.enemies = []
        self.boss = None
        self.items = []
        self.platforms = []
        self.spikes = []       # 地刺列表
        self.item_boxes = []   # 道具箱列表
        self.laser_beams = []  # 激光列表
        self.special_attacks = []  # Boss特殊攻击列表
        self.poison_pools = []     # 毒池列表
        self.hit_particles = []    # 受击粒子特效
        self.ground_y = GROUND_Y

        # ---- 大关 / 小关 ----
        self.current_level = 1          # 当前大关 (1~5)
        self.current_section = 1        # 当前小关 (1~N)
        self.sections_in_level = 3      # 当前大关小关总数
        self.section_cleared = False    # 当前小关敌人是否全灭
        self.global_section_idx = 0     # 全局小关编号(用于选平台/敌人配置)

        # ---- 过渡动画 ----
        self.transitioning = False
        self.transition_progress = 0.0
        self.transition_speed = 0.025   # ~40帧完成
        self.old_surface = None         # 旧画面截图
        self.new_surface = None         # 新画面截图

        # ---- 箭头闪烁 ----
        self.arrow_timer = 0

        self.start_time = 0.0
        self.total_time = 0.0

        # ---- 升级选择 ----
        self.levelup_options = []   # 当前3个可选升级ID
        self.levelup_selected = 0  # 高亮索引

        # 预生成开始界面装饰
        self.start_deco = []
        for i in range(0, SCREEN_WIDTH, 16):
            h = random.randint(4, 18)
            self.start_deco.append((i, h))

    # ==============================================================
    # 关卡设置
    # ==============================================================
    def _level_info(self, level):
        """获取大关信息"""
        idx = max(0, min(level - 1, len(LEVEL_STRUCTURE) - 1))
        return LEVEL_STRUCTURE[idx]

    def _is_boss_section(self):
        """当前小关是否为 BOSS 关"""
        return self.current_section == self.sections_in_level

    def _calc_global_section(self):
        """计算全局小关编号 (从0开始)，用于索引平台/敌人配置"""
        idx = 0
        for i in range(self.current_level - 1):
            idx += LEVEL_STRUCTURE[i]['sections']
        idx += self.current_section - 1
        return idx

    def setup_section(self):
        """设置当前小关"""
        self.enemies = []
        self.boss = None
        self.bullets = []
        self.melee_attacks = []
        self.items = []
        self.section_cleared = False
        self.arrow_timer = 0
        self.spikes = []
        self.item_boxes = []
        self.laser_beams = []
        self.special_attacks = []
        self.poison_pools = []
        self.hit_particles = []
        self.player.x = 80
        self.player.y = 400

        info = self._level_info(self.current_level)
        self.sections_in_level = info['sections']
        self.global_section_idx = self._calc_global_section()

        self.platforms = self._gen_platforms(self.global_section_idx)

        if self._is_boss_section():
            self._setup_boss(info['boss_idx'])
        else:
            self._setup_enemies(self.global_section_idx)

        # 生成地刺和道具箱
        self._setup_hazards(self.global_section_idx)

    def _gen_platforms(self, idx):
        """生成平台 —— 三层结构，每层间距 ~85px 确保一跳可达
        地面 Y=620, 一层≈535, 二层≈450, 三层≈365
        """
        configs = [
            # 配置0: 入门阶梯
            [
                (80, 535, 140), (280, 535, 120), (500, 535, 140), (750, 535, 160),
                (160, 450, 130), (420, 450, 140), (680, 450, 130),
                (300, 365, 150),
            ],
            # 配置1: 交错平台
            [
                (50, 535, 130), (250, 535, 110), (450, 535, 130), (680, 535, 130), (870, 535, 100),
                (130, 450, 150), (380, 450, 130), (620, 450, 120), (830, 450, 100),
                (250, 365, 140), (520, 365, 160), (770, 365, 120),
            ],
            # 配置2: BOSS竞技场 (宽阔)
            [
                (100, 535, 200), (400, 535, 200), (700, 535, 200),
                (200, 450, 180), (550, 450, 180),
                (350, 365, 200),
            ],
            # 配置3: 左右对称+中央高台
            [
                (40, 535, 120), (220, 535, 120), (500, 535, 120), (700, 535, 120), (880, 535, 100),
                (100, 450, 140), (400, 450, 160), (720, 450, 140),
                (200, 365, 120), (550, 365, 120), (800, 365, 100),
                (380, 290, 180),
            ],
            # 配置4: 密集小平台
            [
                (60, 535, 100), (200, 535, 100), (360, 535, 100), (520, 535, 100),
                (680, 535, 100), (840, 535, 100),
                (120, 450, 110), (300, 450, 110), (480, 450, 110), (660, 450, 110), (840, 450, 110),
                (200, 365, 120), (420, 365, 120), (640, 365, 120), (830, 365, 100),
            ],
            # 配置5: BOSS竞技场 — 多层逃跑路线
            [
                (60, 535, 180), (350, 535, 180), (650, 535, 180),
                (150, 450, 160), (500, 450, 160), (800, 450, 140),
                (80, 365, 140), (350, 365, 180), (680, 365, 140),
            ],
            # 配置6: Z字形攀爬
            [
                (50, 535, 150), (300, 535, 130), (550, 535, 130), (800, 535, 150),
                (180, 450, 140), (450, 450, 140), (720, 450, 130),
                (60, 365, 130), (320, 365, 160), (600, 365, 140), (860, 365, 100),
            ],
            # 配置7: 岛屿群
            [
                (80, 535, 100), (250, 535, 80), (420, 535, 100), (590, 535, 80),
                (760, 535, 100), (900, 535, 80),
                (150, 450, 90), (350, 450, 90), (550, 450, 90), (750, 450, 90),
                (250, 365, 100), (480, 365, 100), (700, 365, 100),
                (380, 290, 120),
            ],
            # 配置8: BOSS竞技场 — 快速
            [
                (80, 535, 160), (330, 535, 160), (580, 535, 160), (830, 535, 140),
                (180, 450, 200), (520, 450, 200), (820, 450, 120),
                (100, 365, 150), (380, 365, 200), (700, 365, 150),
            ],
            # 配置9: 大型迷宫
            [
                (40, 535, 110), (200, 535, 110), (380, 535, 110), (560, 535, 110),
                (740, 535, 110), (900, 535, 80),
                (100, 450, 120), (320, 450, 120), (540, 450, 120), (760, 450, 120),
                (60, 365, 100), (240, 365, 130), (460, 365, 130), (680, 365, 130), (880, 365, 100),
                (340, 290, 140), (600, 290, 140),
            ],
            # 配置10: 高塔
            [
                (60, 535, 140), (280, 535, 130), (520, 535, 130), (760, 535, 140),
                (150, 450, 150), (430, 450, 150), (700, 450, 140),
                (80, 365, 120), (300, 365, 160), (570, 365, 160), (830, 365, 120),
                (200, 290, 130), (460, 290, 130), (720, 290, 130),
            ],
            # 配置11: BOSS竞技场 — 宽大空间
            [
                (50, 535, 200), (330, 535, 200), (630, 535, 200),
                (150, 450, 180), (480, 450, 180), (780, 450, 160),
                (60, 365, 160), (320, 365, 200), (640, 365, 160), (880, 365, 100),
            ],
            # 配置12: 阶梯+陷阱布局
            [
                (50, 535, 100), (220, 535, 100), (430, 535, 120), (640, 535, 100),
                (820, 535, 120),
                (120, 450, 110), (340, 450, 130), (560, 450, 110), (760, 450, 130),
                (60, 365, 100), (240, 365, 120), (460, 365, 140), (680, 365, 120), (880, 365, 100),
                (300, 290, 150), (600, 290, 150),
            ],
            # 配置13: 终极挑战
            [
                (40, 535, 90), (180, 535, 90), (340, 535, 90), (500, 535, 90),
                (660, 535, 90), (820, 535, 90),
                (100, 450, 100), (280, 450, 100), (460, 450, 100), (640, 450, 100), (820, 450, 100),
                (50, 365, 110), (230, 365, 110), (410, 365, 110), (590, 365, 110),
                (770, 365, 110),
                (300, 290, 120), (530, 290, 120), (760, 290, 100),
            ],
            # 配置14: 最终BOSS竞技场 — 多层立体
            [
                (60, 535, 180), (330, 535, 180), (630, 535, 180), (880, 535, 100),
                (120, 450, 160), (430, 450, 180), (730, 450, 160),
                (50, 365, 140), (280, 365, 200), (580, 365, 200), (860, 365, 120),
                (380, 290, 200),
            ],
            # 配置15~17: 额外配置 (用于更多小关)
            [
                (70, 535, 130), (260, 535, 130), (480, 535, 140), (720, 535, 130),
                (140, 450, 120), (380, 450, 150), (640, 450, 120), (850, 450, 100),
                (240, 365, 140), (500, 365, 140), (760, 365, 120),
            ],
            [
                (50, 535, 160), (300, 535, 120), (530, 535, 160), (780, 535, 140),
                (160, 450, 140), (420, 450, 130), (680, 450, 140),
                (80, 365, 120), (300, 365, 150), (560, 365, 150), (820, 365, 120),
                (350, 290, 160),
            ],
            [
                (40, 535, 100), (200, 535, 120), (400, 535, 100), (600, 535, 120),
                (800, 535, 100),
                (100, 450, 130), (330, 450, 130), (560, 450, 130), (780, 450, 120),
                (200, 365, 110), (450, 365, 140), (700, 365, 110),
                (340, 290, 130), (580, 290, 130),
            ],
        ]
        real_idx = idx % len(configs)
        return [Platform(px, py, pw) for px, py, pw in configs[real_idx]]

    def _setup_enemies(self, global_idx):
        """设置敌人 —— 按大关颜色统一，包含地面/高台/飞行三种敌人"""
        d = self.difficulty
        base_hp = max(1, int(3 * d['enemy_hp_mult']))

        # 获取当前大关颜色主题
        level_colors = LEVEL_COLORS.get(self.current_level, LEVEL_COLORS[1])
        bullet_color = LEVEL_BULLET_COLORS.get(self.current_level, ORANGE)

        # 根据全局进度决定各类敌人数量
        if global_idx <= 1:
            ground_count = 2
            plat_count = 1
            fly_count = 1
            turret_count = 1
            shoot_chance = 0.0 if global_idx == 0 else 0.3
        elif global_idx <= 5:
            ground_count = 3
            plat_count = 2
            fly_count = 1
            turret_count = 1
            shoot_chance = 0.4
        elif global_idx <= 9:
            ground_count = 3
            plat_count = 2
            fly_count = 2
            turret_count = 2
            shoot_chance = 0.5
        elif global_idx <= 13:
            ground_count = 3
            plat_count = 3
            fly_count = 2
            turret_count = 2
            shoot_chance = 0.6
        else:
            ground_count = 4
            plat_count = 3
            fly_count = 3
            turret_count = 2
            shoot_chance = 0.7

        hp = base_hp + global_idx // 3

        # ---- 地面敌人（主色和深色） ----
        for i in range(ground_count):
            ex = random.randint(200, SCREEN_WIDTH - 80)
            ey = self.ground_y - 60
            can_shoot = random.random() < shoot_chance
            spd = 1.5 + random.random() * 0.8
            c = level_colors[i % 2]  # 交替主色/深色
            self.enemies.append(Enemy(ex, ey, hp, can_shoot, spd, c))

        # ---- 高台敌人（站在高层平台上，亮色） ----
        if self.platforms:
            # 筛选高层平台 (y <= 480，即二层及以上)
            high_plats = [p for p in self.platforms if p.rect.y <= 480]
            if not high_plats:
                high_plats = list(self.platforms)
            random.shuffle(high_plats)
            for i in range(min(plat_count, len(high_plats))):
                p = high_plats[i]
                ex = p.rect.x + random.randint(10, max(10, p.rect.width - 30))
                ey = p.rect.y - 40
                can_shoot = random.random() < (shoot_chance + 0.2)
                spd = 0.8 + random.random() * 0.4
                c = level_colors[2]  # 亮色
                e = Enemy(ex, ey, hp, can_shoot, spd, c)
                e.move_range = min(e.move_range, p.rect.width - 10)
                e.start_x = ex
                self.enemies.append(e)

        # ---- 飞行敌人（空中浮动，主色，追踪射击） ----
        for i in range(fly_count):
            fx = random.randint(150, SCREEN_WIDTH - 150)
            fy = random.randint(120, 320)  # 中高空区域
            fly_hp = max(1, hp - 1)
            fly_spd = 1.0 + random.random() * 0.8
            self.enemies.append(
                FlyingEnemy(fx, fy, fly_hp, fly_spd, level_colors[0], bullet_color)
            )

        # ---- 炮台敌人（固定在平台上，深色，瞄准射击） ----
        if self.platforms:
            # 用尚未被高台敌人占用的平台，优先选一层平台(y~535)
            turret_plats = list(self.platforms)
            random.shuffle(turret_plats)
            turret_hp = hp + 1  # 炮台血量比普通敌人多1
            for i in range(min(turret_count, len(turret_plats))):
                p = turret_plats[i]
                tx = p.rect.x + p.rect.width // 2 - 12  # 平台中央
                ty = p.rect.y - 22
                self.enemies.append(
                    TurretEnemy(tx, ty, turret_hp, level_colors[1], bullet_color)
                )

    def _drop_item(self, x, y):
        """道具箱破坏后随机掉落道具"""
        roll = random.random()
        if roll < 0.45:
            self.items.append(Item(x, y, 'health'))
        elif roll < 0.75:
            self.items.append(Item(x, y, 'shield'))
        else:
            self.items.append(Item(x, y, 'power_up'))

    def _setup_hazards(self, global_idx):
        """生成地刺和道具箱"""
        # 地刺数量随关卡递增
        if global_idx <= 1:
            spike_count = 1
            box_count = 2
        elif global_idx <= 5:
            spike_count = 2
            box_count = 2
        elif global_idx <= 9:
            spike_count = 3
            box_count = 3
        else:
            spike_count = 4
            box_count = 3

        # BOSS关减少地刺，增加道具箱
        if self._is_boss_section():
            spike_count = max(1, spike_count - 1)
            box_count += 1

        # ---- 放置地刺 ----
        # 地面地刺
        used_x = set()
        for _ in range(spike_count):
            w = random.choice([20, 30, 40])
            for attempt in range(20):
                sx = random.randint(150, SCREEN_WIDTH - w - 50)
                # 避免和已有地刺重叠
                overlap = False
                for ux in used_x:
                    if abs(sx - ux) < 60:
                        overlap = True
                        break
                if not overlap:
                    used_x.add(sx)
                    self.spikes.append(Spike(sx, self.ground_y - 10, w))
                    break

        # 平台上地刺（随机选一个平台）
        if self.platforms and spike_count >= 2:
            plat = random.choice(self.platforms)
            sw = min(30, plat.rect.width - 10)
            if sw >= 20:
                sx = plat.rect.x + random.randint(5, max(5, plat.rect.width - sw - 5))
                self.spikes.append(Spike(sx, plat.rect.y - 10, sw))

        # ---- 放置道具箱 ----
        for _ in range(box_count):
            # 优先放在平台上
            if self.platforms and random.random() < 0.7:
                plat = random.choice(self.platforms)
                bx = plat.rect.x + random.randint(10, max(10, plat.rect.width - 32))
                by = plat.rect.y - 22
            else:
                bx = random.randint(120, SCREEN_WIDTH - 80)
                by = self.ground_y - 22
            self.item_boxes.append(ItemBox(bx, by))

    def _setup_boss(self, boss_idx):
        """设置BOSS"""
        bx = SCREEN_WIDTH - 140
        by = self.ground_y - 120
        d = self.difficulty
        boss_classes = {1: RedBoss, 2: BlueBoss, 3: PurpleBoss, 4: GreenBoss, 5: GoldBoss}
        cls = boss_classes.get(boss_idx)
        if cls:
            self.boss = cls(bx, by, d)

    # ==============================================================
    # 背景 & 地面
    # ==============================================================
    def _spawn_hit_particles(self, x, y, color, count=6):
        """在指定位置生成受击粒子"""
        self.hit_particles.append(HitParticle(x, y, color, count))

    def _bg_color(self):
        """获取当前关卡背景颜色"""
        idx = min(self.global_section_idx, len(BG_LEVELS) - 1)
        return BG_LEVELS[idx]

    def _draw_ground(self, surface):
        """绘制地面 —— 多层泥土+草坪"""
        gy = self.ground_y
        gw = SCREEN_WIDTH
        gh = SCREEN_HEIGHT - gy
        # 泥土层（深到浅）
        pygame.draw.rect(surface, (50, 32, 14), (0, gy + 8, gw, gh - 8))   # 深层泥土
        pygame.draw.rect(surface, (65, 42, 18), (0, gy + 4, gw, 8))        # 中层
        pygame.draw.rect(surface, (80, 55, 25), (0, gy, gw, 5))            # 表层土壤
        # 草坪层
        pygame.draw.rect(surface, (40, 100, 35), (0, gy, gw, 3))
        pygame.draw.rect(surface, (60, 135, 50), (0, gy, gw, 1))           # 草尖高光
        # 草丛细节
        for i in range(0, gw, 8):
            h = 2 + (i * 7 % 5)
            pygame.draw.line(surface, (50, 120, 40), (i + 3, gy), (i + 3, gy - h))
        # 泥土纹理
        for i in range(0, gw, 20):
            pygame.draw.rect(surface, (42, 28, 10), (i + 3, gy + 14, 8, 3))
            pygame.draw.rect(surface, (55, 38, 15), (i + 12, gy + 22, 6, 2))
        # 小石子
        for i in range(0, gw, 50):
            pygame.draw.rect(surface, (90, 80, 65), (i + 15, gy + 6, 3, 2))
            pygame.draw.rect(surface, (75, 65, 50), (i + 35, gy + 8, 2, 2))

    # ==============================================================
    # HUD
    # ==============================================================
    def _draw_hud(self, surface):
        """绘制HUD —— 精美半透明面板"""
        from utils import font_tiny, font_large

        # 背景面板（圆角效果通过嵌套矩形模拟）
        hud = pygame.Surface((285, 135), pygame.SRCALPHA)
        pygame.draw.rect(hud, (0, 0, 0, 170), (2, 2, 281, 131))
        pygame.draw.rect(hud, (60, 80, 120, 80), (0, 0, 285, 135), 1)  # 边框
        pygame.draw.line(hud, (80, 110, 160, 60), (4, 0), (281, 0))     # 顶部亮线
        surface.blit(hud, (5, 5))
        p = self.player

        # HP 标签
        if font_tiny:
            text = font_tiny.render(f"HP: {p.hp}/{p.max_hp}", False, WHITE)
            surface.blit(text, (12, 10))

        # HP 条 —— 渐变+高光
        bar_x, bar_y, bar_w, bar_h = 85, 11, 104, 14
        pygame.draw.rect(surface, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h))
        hw = int((bar_w - 4) * p.hp / max(p.max_hp, 1))
        ratio = p.hp / max(p.max_hp, 1)
        if ratio > 0.5:
            hc = (50, 200, 50)
        elif ratio > 0.25:
            hc = (220, 200, 40)
        else:
            hc = (220, 50, 40)
        if hw > 0:
            pygame.draw.rect(surface, hc, (bar_x + 2, bar_y + 2, hw, bar_h - 4))
            # HP 条高光
            highlight = (min(hc[0] + 60, 255), min(hc[1] + 60, 255), min(hc[2] + 60, 255))
            pygame.draw.line(surface, highlight, (bar_x + 2, bar_y + 2), (bar_x + 2 + hw, bar_y + 2))
        pygame.draw.rect(surface, (150, 160, 180), (bar_x, bar_y, bar_w, bar_h), 1)

        if font_tiny:
            # 信息行 —— 带图标色彩
            surface.blit(font_tiny.render(f"击杀: {p.kills}", False, (200, 200, 200)), (12, 30))
            surface.blit(font_tiny.render(f"经验: {p.xp}", False, (180, 220, 180)), (12, 47))
            surface.blit(font_tiny.render(f"等级: {p.level}", False, YELLOW), (12, 64))
            wn = {"gun": "枪", "sword": "刀", "shotgun": "霸弹", "laser": "激光"}.get(p.weapon, "枪")
            wc = {"gun": (100,220,255), "sword": (255,180,100), "shotgun": ORANGE, "laser": CYAN}.get(p.weapon, WHITE)
            surface.blit(font_tiny.render(f"武器: {wn}", False, wc), (12, 81))
            # 关卡信息
            lvl_text = f"大关{self.current_level} - 小关{self.current_section}/{self.sections_in_level}"
            surface.blit(font_tiny.render(lvl_text, False, WHITE), (12, 98))
            # 难度标签 —— 颜色区分
            dc = {'简单': (100, 200, 100), '普通': ORANGE, '困难': (255, 80, 80)}
            surface.blit(font_tiny.render(f"难度: {self.difficulty_name}", False,
                                          dc.get(self.difficulty_name, ORANGE)), (170, 98))
            # Buff 状态
            buff_texts = []
            if p.shield > 0:
                buff_texts.append(('护盾', f"{p.shield}", (100, 180, 255)))
            if p.power_up_timer > 0:
                secs = p.power_up_timer // 60
                buff_texts.append(('增伤', f"{secs}s", (255, 100, 100)))
            bx = 12
            for bname, bval, bc in buff_texts:
                surface.blit(font_tiny.render(f"{bname}:{bval}", False, bc), (bx, 115))
                bx += 70

        if p.levelup_timer > 0 and font_large:
            # 升级提示 —— 带光晕
            t = font_large.render("升级！", False, GOLD)
            tr = t.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
            glow = pygame.Surface((t.get_width() + 20, t.get_height() + 20), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 200, 50, 40), glow.get_rect())
            surface.blit(glow, (tr.x - 10, tr.y - 10))
            surface.blit(t, tr)

    def _draw_arrow_hint(self, surface):
        """小关清除后绘制右侧闪烁箭头提示"""
        self.arrow_timer += 1
        if (self.arrow_timer // 15) % 2 == 0:
            ax = SCREEN_WIDTH - 50
            ay = SCREEN_HEIGHT // 2
            # 箭头光晕
            glow = pygame.Surface((50, 60), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 200, 50, 40), (0, 0, 50, 60))
            surface.blit(glow, (ax - 10, ay - 30))
            # 箭头主体
            points = [(ax, ay - 25), (ax + 30, ay), (ax, ay + 25)]
            pygame.draw.polygon(surface, GOLD, points)
            # 箭头高光
            pygame.draw.line(surface, (255, 240, 150), (ax, ay - 25), (ax + 28, ay), 2)
            # 文字提示
            from utils import font_large
            if font_large:
                t = font_large.render(">>>", False, GOLD)
                surface.blit(t, t.get_rect(center=(SCREEN_WIDTH - 55, ay - 45)))

    # ==============================================================
    # 游戏逻辑
    # ==============================================================
    def handle_playing(self, events, keys):
        """处理游戏中的逻辑"""
        # 如果正在过渡动画中，不处理游戏逻辑
        if self.transitioning:
            self._update_transition()
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == KEY_PAUSE:
                    self.state = 'paused'
                    return
                if event.key in (pygame.K_SPACE, pygame.K_w):
                    self.player.jump()
                if event.key == KEY_GUN:
                    self.player.weapon = 'gun'
                if event.key == KEY_SWORD:
                    self.player.weapon = 'sword'
                if event.key == pygame.K_3 and self.player.has_shotgun:
                    self.player.weapon = 'shotgun'
                if event.key == pygame.K_4 and self.player.has_laser:
                    self.player.weapon = 'laser'
            # 鼠标左键射击（限制最大子弹数）
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if len(self.bullets) < 200:
                    mx, my = event.pos
                    result = self.player.shoot(mx, my)
                    if result:
                        if isinstance(result, list):
                            self.bullets.extend(result)
                        elif isinstance(result, Bullet):
                            self.bullets.append(result)
                        elif isinstance(result, MeleeAttack):
                            self.melee_attacks.append(result)
                        elif isinstance(result, LaserBeam):
                            self.laser_beams.append(result)

        # 更新玩家（传入是否允许向右走出屏幕）
        right_limit = SCREEN_WIDTH + 40 if self.section_cleared else SCREEN_WIDTH - self.player.width
        self.player.update(self.ground_y, self.platforms, right_limit)

        # 更新子弹
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.alive]

        # 更新近战
        for m in self.melee_attacks:
            m.update()
        self.melee_attacks = [m for m in self.melee_attacks if m.alive]

        # 更新激光
        for laser in self.laser_beams:
            laser.update()
        self.laser_beams = [l for l in self.laser_beams if l.alive]

        # 更新道具
        for item in self.items:
            item.update(self.ground_y, self.platforms)

        # 更新地刺
        for spike in self.spikes:
            spike.update()

        # 更新道具箱
        for box in self.item_boxes:
            box.update()
        self.item_boxes = [b for b in self.item_boxes if b.alive]

        # 更新敌人
        for enemy in self.enemies:
            bullet = enemy.update(self.ground_y, self.platforms, self.player.x, self.player.y)
            if bullet:
                self.bullets.append(bullet)

        # 更新BOSS
        if self.boss and self.boss.alive:
            if isinstance(self.boss, RedBoss):
                boss_bullets, specials = self.boss.update(
                    self.ground_y, self.platforms, self.player.x, self.player.y)
                self.bullets.extend(boss_bullets)
                self.special_attacks.extend(specials)
            elif isinstance(self.boss, GreenBoss):
                boss_bullets, summons, specials = self.boss.update(
                    self.ground_y, self.platforms, self.player.x, self.player.y)
                self.bullets.extend(boss_bullets)
                for s in summons:
                    self.enemies.append(s)
                self.special_attacks.extend(specials)
            else:
                boss_bullets = self.boss.update(
                    self.ground_y, self.platforms, self.player.x, self.player.y)
                if boss_bullets:
                    self.bullets.extend(boss_bullets)

        # 更新特殊攻击
        for sa in self.special_attacks:
            sa.update()
            # PoisonCloud消散后生成PoisonPool
            if isinstance(sa, PoisonCloud) and not sa.alive:
                pool_rect = sa.get_rect()
                self.poison_pools.append(PoisonPool(pool_rect.centerx, self.ground_y, width=80, duration=180))
        self.special_attacks = [sa for sa in self.special_attacks if sa.alive]

        # 更新毒池
        for pool in self.poison_pools:
            pool.update()
        self.poison_pools = [p for p in self.poison_pools if p.alive]

        # 更新受击粒子
        for hp_fx in self.hit_particles:
            hp_fx.update()
        self.hit_particles = [h for h in self.hit_particles if h.alive]

        player_rect = self.player.get_rect()

        # 玩家子弹碰撞
        for b in self.bullets:
            if not b.alive:
                continue
            if b.owner == 'player':
                for enemy in self.enemies:
                    if enemy.alive and id(enemy) not in b.hit_set and b.get_rect().colliderect(enemy.get_rect()):
                        killed = enemy.take_damage(b.damage)
                        er = enemy.get_rect()
                        self._spawn_hit_particles(er.centerx, er.centery, enemy.color)
                        if b.piercing:
                            b.hit_set.add(id(enemy))
                        else:
                            b.alive = False
                        if killed:
                            self.player.kills += 1
                            self.player.gain_xp(5)
                            # 击杀回血
                            if self.player.kill_heal_chance > 0 and random.random() < self.player.kill_heal_chance:
                                self.player.heal(1)
                            elif random.random() < 0.3:
                                self.items.append(Item(enemy.x, enemy.y, 'health'))
                        if not b.alive:
                            break
                if b.alive and self.boss and self.boss.alive:
                    if id(self.boss) not in b.hit_set and b.get_rect().colliderect(self.boss.get_rect()):
                        killed = self.boss.take_damage(b.damage)
                        br = self.boss.get_rect()
                        self._spawn_hit_particles(br.centerx, br.centery, self.boss.color, 8)
                        if b.piercing:
                            b.hit_set.add(id(self.boss))
                        else:
                            b.alive = False
                        if killed:
                            self.player.kills += 1
                            self.player.gain_xp(25)
                            if self.player.kill_heal_chance > 0 and random.random() < self.player.kill_heal_chance:
                                self.player.heal(1)
                            elif random.random() < 0.5:
                                self.items.append(Item(self.boss.x + 20, self.boss.y, 'health'))
            elif b.owner == 'enemy':
                if b.get_rect().colliderect(player_rect):
                    dead = self.player.take_damage(self.difficulty['enemy_damage'])
                    b.alive = False
                    if dead:
                        self.state = 'gameover'
                        play_sound(snd_gameover)
                        return

        self.bullets = [b for b in self.bullets if b.alive]

        # 近战碰撞
        for m in self.melee_attacks:
            # 命中敌人
            for enemy in self.enemies:
                if enemy.alive and id(enemy) not in m.hit_enemies:
                    if m.rect.colliderect(enemy.get_rect()):
                        killed = enemy.take_damage(m.damage)
                        er = enemy.get_rect()
                        self._spawn_hit_particles(er.centerx, er.centery, enemy.color, 8)
                        m.hit_enemies.add(id(enemy))
                        if killed:
                            self.player.kills += 1
                            self.player.gain_xp(5)
                            if random.random() < 0.3:
                                self.items.append(Item(enemy.x, enemy.y, 'health'))
            if self.boss and self.boss.alive and id(self.boss) not in m.hit_enemies:
                if m.rect.colliderect(self.boss.get_rect()):
                    killed = self.boss.take_damage(m.damage)
                    br = self.boss.get_rect()
                    self._spawn_hit_particles(br.centerx, br.centery, self.boss.color, 10)
                    m.hit_enemies.add(id(self.boss))
                    if killed:
                        self.player.kills += 1
                        self.player.gain_xp(25)
                        if random.random() < 0.5:
                            self.items.append(Item(self.boss.x + 20, self.boss.y, 'health'))
            # 消除/反弹敌人子弹
            for b in self.bullets:
                if b.alive and b.owner == 'enemy' and id(b) not in m.hit_bullets:
                    if m.rect.colliderect(b.get_rect()):
                        m.hit_bullets.add(id(b))
                        if self.player.melee_reflect:
                            # 反弹：反转方向，变为玩家子弹
                            b.dx = -b.dx
                            b.dy = -b.dy
                            b.owner = 'player'
                            b.color = CYAN
                            b.damage = self.player._calc_bullet_damage()
                        else:
                            b.alive = False

        # 激光碰撞 —— 对线上所有敌人造成伤害
        for laser in self.laser_beams:
            for enemy in self.enemies:
                if enemy.alive and id(enemy) not in laser.hit_enemies:
                    if laser.hits_rect(enemy.get_rect()):
                        killed = enemy.take_damage(laser.damage)
                        er = enemy.get_rect()
                        self._spawn_hit_particles(er.centerx, er.centery, enemy.color)
                        laser.hit_enemies.add(id(enemy))
                        if killed:
                            self.player.kills += 1
                            self.player.gain_xp(5)
                            if self.player.kill_heal_chance > 0 and random.random() < self.player.kill_heal_chance:
                                self.player.heal(1)
                            elif random.random() < 0.3:
                                self.items.append(Item(enemy.x, enemy.y, 'health'))
            if self.boss and self.boss.alive and id(self.boss) not in laser.hit_enemies:
                if laser.hits_rect(self.boss.get_rect()):
                    killed = self.boss.take_damage(laser.damage)
                    br = self.boss.get_rect()
                    self._spawn_hit_particles(br.centerx, br.centery, self.boss.color, 8)
                    laser.hit_enemies.add(id(self.boss))
                    if killed:
                        self.player.kills += 1
                        self.player.gain_xp(25)
                        if self.player.kill_heal_chance > 0 and random.random() < self.player.kill_heal_chance:
                            self.player.heal(1)
                        elif random.random() < 0.5:
                            self.items.append(Item(self.boss.x + 20, self.boss.y, 'health'))

        # 接触伤害：敌人
        for enemy in self.enemies:
            if enemy.alive and player_rect.colliderect(enemy.get_rect()):
                dead = self.player.take_damage(self.difficulty['enemy_damage'])
                if dead:
                    self.state = 'gameover'
                    play_sound(snd_gameover)
                    return

        # 接触伤害：BOSS
        if self.boss and self.boss.alive:
            if player_rect.colliderect(self.boss.get_rect()):
                dead = self.player.take_damage(self.difficulty['enemy_damage'])
                if dead:
                    self.state = 'gameover'
                    play_sound(snd_gameover)
                    return
            if isinstance(self.boss, GoldBoss) and self.boss.check_laser_hit(player_rect):
                dead = self.player.take_damage(self.difficulty['enemy_damage'])
                if dead:
                    self.state = 'gameover'
                    play_sound(snd_gameover)
                    return

        # 特殊攻击碰撞检测
        for sa in self.special_attacks:
            if isinstance(sa, SpinAttack) and not sa.hit_player:
                if sa.hits_rect(player_rect):
                    sa.hit_player = True
                    dead = self.player.take_damage(sa.damage)
                    if dead:
                        self.state = 'gameover'
                        play_sound(snd_gameover)
                        return
            elif isinstance(sa, GroundHand) and not sa.hit_player:
                hr = sa.get_rect()
                if hr and hr.colliderect(player_rect):
                    sa.hit_player = True
                    dead = self.player.take_damage(sa.damage)
                    if dead:
                        self.state = 'gameover'
                        play_sound(snd_gameover)
                        return
            elif isinstance(sa, PoisonCloud):
                if sa.get_rect().colliderect(player_rect) and sa.can_hit():
                    dead = self.player.take_damage(sa.damage)
                    if dead:
                        self.state = 'gameover'
                        play_sound(snd_gameover)
                        return

        # 毒池站立伤害
        for pool in self.poison_pools:
            if pool.get_rect().colliderect(player_rect) and pool.can_hit():
                dead = self.player.take_damage(pool.damage)
                if dead:
                    self.state = 'gameover'
                    play_sound(snd_gameover)
                    return

        # 拾取道具
        for item in self.items[:]:
            if player_rect.colliderect(item.get_rect()):
                if item.item_type == 'health':
                    self.player.heal(1)
                elif item.item_type == 'shield':
                    self.player.shield = min(self.player.shield + 3, 5)
                elif item.item_type == 'power_up':
                    self.player.power_up_timer = 600  # ~10秒
                play_sound(snd_pickup)
                self.items.remove(item)

        # 地刺伤害检测
        if not self.player.trap_immune:
            for spike in self.spikes:
                if spike.check_damage(player_rect):
                    dead = self.player.take_damage(1)
                    if dead:
                        self.state = 'gameover'
                        play_sound(snd_gameover)
                        return

        # 子弹击中道具箱
        for b in self.bullets:
            if b.alive and b.owner == 'player':
                for box in self.item_boxes:
                    if box.alive and b.get_rect().colliderect(box.get_rect()):
                        b.alive = False
                        destroyed = box.take_damage(b.damage)
                        if destroyed:
                            self._drop_item(box.x, box.y)
                        break

        # 近战击中道具箱
        for m in self.melee_attacks:
            for box in self.item_boxes:
                if box.alive and id(box) not in m.hit_enemies:
                    if m.rect.colliderect(box.get_rect()):
                        m.hit_enemies.add(id(box))
                        destroyed = box.take_damage(m.damage)
                        if destroyed:
                            self._drop_item(box.x, box.y)

        # 激光击中道具箱
        for laser in self.laser_beams:
            for box in self.item_boxes:
                if box.alive and id(box) not in laser.hit_enemies:
                    if laser.hits_rect(box.get_rect()):
                        laser.hit_enemies.add(id(box))
                        destroyed = box.take_damage(laser.damage)
                        if destroyed:
                            self._drop_item(box.x, box.y)

        # 清除死敌人
        self.enemies = [e for e in self.enemies if e.alive]

        # ---- 检测小关完成 ----
        if not self.section_cleared:
            if self._is_boss_section():
                if self.boss and not self.boss.alive and len(self.enemies) == 0:
                    self.section_cleared = True
            else:
                if len(self.enemies) == 0:
                    self.section_cleared = True

        # ---- 小关已清除：检测过渡条件 ----
        if self.section_cleared:
            if self._is_boss_section():
                # BOSS关清除 → 大关完成或胜利
                if self.current_level >= TOTAL_LEVELS:
                    self.total_time = time_module.time() - self.start_time
                    self.state = 'victory'
                    play_sound(snd_victory)
                else:
                    self.state = 'level_complete'
            else:
                # 普通小关清除 → 玩家走到右边界触发过渡
                if self.player.x > SCREEN_WIDTH - 30:
                    self._start_transition()

        # ---- 检测升级选择 ----
        if self.player.pending_levelup:
            opts = self.player.get_upgrade_options()
            if opts:
                self.levelup_options = opts
                self.levelup_selected = 0
                self.state = 'levelup_select'
            else:
                self.player.pending_levelup = False

    # ==============================================================
    # 过渡动画
    # ==============================================================
    def _start_transition(self):
        """开始小关过渡动画"""
        # 截取当前画面
        self.old_surface = self.screen.copy()

        # 设置下一小关
        self.current_section += 1
        self.setup_section()

        # 绘制新画面到临时 surface
        self.new_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self._draw_scene(self.new_surface)

        self.transitioning = True
        self.transition_progress = 0.0

    def _update_transition(self):
        """更新过渡动画进度"""
        self.transition_progress += self.transition_speed
        if self.transition_progress >= 1.0:
            self.transition_progress = 1.0
            self.transitioning = False
            self.old_surface = None
            self.new_surface = None

    def _draw_transition(self, surface):
        """绘制过渡动画 —— 旧画面左滑，新画面右滑入"""
        t = self.transition_progress
        # 使用 ease-out 缓动
        t = 1 - (1 - t) ** 2
        offset = int(SCREEN_WIDTH * t)

        if self.old_surface:
            surface.blit(self.old_surface, (-offset, 0))
        if self.new_surface:
            surface.blit(self.new_surface, (SCREEN_WIDTH - offset, 0))

    # ==============================================================
    # 进入下一大关
    # ==============================================================
    def advance_to_next_level(self):
        """进入下一大关"""
        self.current_level += 1
        self.current_section = 1
        info = self._level_info(self.current_level)
        self.sections_in_level = info['sections']
        self.setup_section()
        self.state = 'playing'

    def start_from_level(self, level):
        """从指定大关开始游戏"""
        self.player = Player()
        self.bullets = []
        self.melee_attacks = []
        self.enemies = []
        self.boss = None
        self.items = []
        self.spikes = []
        self.item_boxes = []
        self.laser_beams = []
        self.special_attacks = []
        self.poison_pools = []
        self.hit_particles = []
        self.current_level = level
        self.current_section = 1
        self.sections_in_level = LEVEL_STRUCTURE[level - 1]['sections']
        self.section_cleared = False
        self.transitioning = False
        self.transition_progress = 0.0
        self.old_surface = None
        self.new_surface = None
        self.start_time = time_module.time()
        self.setup_section()
        self.state = 'playing'

    # ==============================================================
    # 绘制
    # ==============================================================
    def _draw_scene(self, surface):
        """绘制游戏场景（不含HUD，用于过渡截图）"""
        surface.fill(self._bg_color())
        self._draw_ground(surface)
        for p in self.platforms:
            p.draw(surface)
        # 地刺和道具箱
        for spike in self.spikes:
            spike.draw(surface)
        for box in self.item_boxes:
            box.draw(surface)
        for item in self.items:
            item.draw(surface)
        for enemy in self.enemies:
            enemy.draw(surface)
        if self.boss and self.boss.alive:
            self.boss.draw(surface)
        self.player.draw(surface)
        for b in self.bullets:
            b.draw(surface)
        for m in self.melee_attacks:
            m.draw(surface)
        for laser in self.laser_beams:
            laser.draw(surface)
        for sa in self.special_attacks:
            sa.draw(surface)
        for pool in self.poison_pools:
            pool.draw(surface)
        for hp_fx in self.hit_particles:
            hp_fx.draw(surface)

    def draw_playing(self, surface):
        """绘制游戏画面"""
        if self.transitioning:
            self._draw_transition(surface)
            return

        self._draw_scene(surface)
        self._draw_hud(surface)

        # 小关清除提示
        if self.section_cleared and not self._is_boss_section():
            self._draw_arrow_hint(surface)
            from utils import font_medium
            if font_medium:
                t = font_medium.render("敌人已清除！向右前进 →", False, GOLD)
                surface.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 60)))

    def draw_levelup_select(self, surface):
        """绘制升级选择界面 —— 3张卡牌选择"""
        from utils import font_large, font_medium, font_small, font_tiny
        from player import UPGRADE_POOL

        # 背景：绘制游戏画面 + 暗色遮罩
        self._draw_scene(surface)
        self._draw_hud(surface)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        cx = SCREEN_WIDTH // 2
        # 标题
        if font_large:
            shadow = font_large.render("升级！选择一项强化", False, (40, 30, 10))
            surface.blit(shadow, shadow.get_rect(center=(cx + 2, 82)))
            t = font_large.render("升级！选择一项强化", False, GOLD)
            surface.blit(t, t.get_rect(center=(cx, 80)))

        # 卡牌布局
        n = len(self.levelup_options)
        card_w, card_h = 200, 260
        gap = 30
        total_w = n * card_w + (n - 1) * gap
        start_x = cx - total_w // 2

        for i, uid in enumerate(self.levelup_options):
            info = UPGRADE_POOL.get(uid, {})
            card_x = start_x + i * (card_w + gap)
            card_y = 140
            selected = (i == self.levelup_selected)
            cur_lvl = self.player.upgrades.get(uid, 0)
            max_lvl = info.get('max_level', 1)

            # 卡牌背景
            if selected:
                # 选中光晕
                glow_s = pygame.Surface((card_w + 16, card_h + 16), pygame.SRCALPHA)
                pygame.draw.rect(glow_s, (255, 200, 50, 50), (0, 0, card_w + 16, card_h + 16))
                surface.blit(glow_s, (card_x - 8, card_y - 8))
                bg_color = (30, 40, 65)
                border_color = GOLD
            else:
                bg_color = (20, 25, 40)
                border_color = (80, 90, 110)

            pygame.draw.rect(surface, bg_color, (card_x, card_y, card_w, card_h))
            pygame.draw.rect(surface, border_color, (card_x, card_y, card_w, card_h), 2)
            # 卡牌顶部亮线
            pygame.draw.line(surface, (100, 120, 160), (card_x + 2, card_y + 1),
                             (card_x + card_w - 2, card_y + 1))

            # 图标区域
            icon_cx = card_x + card_w // 2
            icon_cy = card_y + 60
            ic = info.get('icon_color', WHITE)
            # 图标光晕
            ig = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(ig, (*ic, 40), (0, 0, 50, 50))
            surface.blit(ig, (icon_cx - 25, icon_cy - 25))
            # 图标圆
            pygame.draw.circle(surface, ic, (icon_cx, icon_cy), 18)
            pygame.draw.circle(surface, (min(ic[0]+60,255), min(ic[1]+60,255), min(ic[2]+60,255)),
                               (icon_cx, icon_cy), 18, 2)
            pygame.draw.circle(surface, WHITE, (icon_cx - 5, icon_cy - 5), 4)

            # 名称
            if font_medium:
                name_t = font_medium.render(info.get('name', uid), False, WHITE)
                surface.blit(name_t, name_t.get_rect(center=(icon_cx, card_y + 105)))

            # 描述
            if font_small:
                desc = info.get('desc', '')
                # 简单折行：每12字一行
                lines = [desc[j:j+12] for j in range(0, len(desc), 12)]
                for li, line in enumerate(lines):
                    dt = font_small.render(line, False, (180, 190, 210))
                    surface.blit(dt, dt.get_rect(center=(icon_cx, card_y + 140 + li * 22)))

            # 等级指示器
            if max_lvl > 1 and font_tiny:
                lvl_text = f"Lv {cur_lvl}/{max_lvl}"
                lt = font_tiny.render(lvl_text, False, YELLOW if selected else GRAY)
                surface.blit(lt, lt.get_rect(center=(icon_cx, card_y + 200)))
                # 等级点
                dot_y = card_y + 218
                dot_total_w = max_lvl * 12
                dot_sx = icon_cx - dot_total_w // 2
                for d in range(max_lvl):
                    dc = GOLD if d < cur_lvl else (60, 65, 80)
                    # 下一级高亮
                    if d == cur_lvl:
                        dc = (180, 180, 50)
                    pygame.draw.rect(surface, dc, (dot_sx + d * 12, dot_y, 8, 8))
                    pygame.draw.rect(surface, (100, 110, 130), (dot_sx + d * 12, dot_y, 8, 8), 1)
            elif max_lvl == 1:
                if font_tiny:
                    tag = "已解锁" if cur_lvl > 0 else "未解锁"
                    tc = LIGHT_GREEN if cur_lvl > 0 else (150, 150, 160)
                    surface.blit(font_tiny.render(tag, False, tc),
                                 font_tiny.render(tag, False, tc).get_rect(center=(icon_cx, card_y + 210)))

            # 选中标记
            if selected:
                pygame.draw.polygon(surface, GOLD,
                                    [(icon_cx - 8, card_y + card_h - 20),
                                     (icon_cx, card_y + card_h - 10),
                                     (icon_cx + 8, card_y + card_h - 20)])

        # 操作提示
        if font_small:
            hint = font_small.render("A/D 或 左/右 切换│ Enter 确认", False, (160, 170, 190))
            surface.blit(hint, hint.get_rect(center=(cx, 430)))

    def draw_start(self, surface):
        """绘制开始界面 —— 精美像素风"""
        from utils import font_large, font_medium, font_small

        surface.fill(BG_START)

        # 背景装饰 —— 城市天际线
        for (dx, dh) in self.start_deco:
            # 建筑主体
            pygame.draw.rect(surface, (25, 28, 55), (dx, SCREEN_HEIGHT - dh - 30, 12, dh))
            # 窗户
            for wy in range(SCREEN_HEIGHT - dh - 28, SCREEN_HEIGHT - 32, 8):
                if (dx + wy) % 16 < 8:
                    pygame.draw.rect(surface, (60, 70, 100), (dx + 3, wy, 3, 3))
                    pygame.draw.rect(surface, (80, 90, 120), (dx + 7, wy, 3, 3))
            # 建筑顶部高光
            pygame.draw.line(surface, (40, 45, 75), (dx, SCREEN_HEIGHT - dh - 30),
                             (dx + 11, SCREEN_HEIGHT - dh - 30))
        # 地面线
        pygame.draw.rect(surface, (30, 35, 60), (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
        pygame.draw.line(surface, (50, 55, 85), (0, SCREEN_HEIGHT - 30), (SCREEN_WIDTH, SCREEN_HEIGHT - 30))

        # 标题 —— 带阴影
        if font_large:
            shadow = font_large.render("斯莱马博历险记", False, (30, 20, 10))
            surface.blit(shadow, shadow.get_rect(center=(SCREEN_WIDTH // 2 + 3, 163)))
            t = font_large.render("斯莱马博历险记", False, GOLD)
            surface.blit(t, t.get_rect(center=(SCREEN_WIDTH // 2, 160)))
        if font_medium:
            # 副标题
            t2 = font_medium.render("The Adventures of Slymarbo", False, CYAN)
            surface.blit(t2, t2.get_rect(center=(SCREEN_WIDTH // 2, 210)))
            # 分割线
            line_w = 200
            cx = SCREEN_WIDTH // 2
            pygame.draw.line(surface, (80, 90, 120), (cx - line_w, 245), (cx + line_w, 245))
            pygame.draw.line(surface, (50, 55, 80), (cx - line_w, 246), (cx + line_w, 246))
            # 按钮提示 —— 带开始框
            btn_r = pygame.Rect(cx - 140, 305, 280, 40)
            pygame.draw.rect(surface, (30, 50, 80), btn_r)
            pygame.draw.rect(surface, CYAN, btn_r, 1)
            t3 = font_medium.render("按 ENTER 开始游戏", False, WHITE)
            surface.blit(t3, t3.get_rect(center=btn_r.center))

            t4 = font_medium.render("按 ESC 进入设置", False, GRAY)
            surface.blit(t4, t4.get_rect(center=(cx, 370)))

        if font_small:
            hints = [
                "A/D 移动  空格 跳跃  S 下落  鼠标左键 攻击",
                "1 切换枪  2 切换刀  ESC 暂停"
            ]
            for i, h in enumerate(hints):
                ht = font_small.render(h, False, (140, 150, 170))
                surface.blit(ht, ht.get_rect(center=(SCREEN_WIDTH // 2, 440 + i * 28)))

    def draw_level_select(self, surface):
        """绘制选关界面"""
        import math as _math
        from utils import font_large, font_medium, font_small

        surface.fill((12, 12, 28))
        cx = SCREEN_WIDTH // 2

        # 标题
        if font_large:
            shadow = font_large.render("选择关卡", False, (30, 20, 10))
            surface.blit(shadow, shadow.get_rect(center=(cx + 2, 62)))
            t = font_large.render("选择关卡", False, GOLD)
            surface.blit(t, t.get_rect(center=(cx, 60)))
        if font_medium:
            pygame.draw.line(surface, (60, 60, 90), (cx - 150, 95), (cx + 150, 95))

        # 关卡信息
        level_info = [
            {"name": "第一章", "sub": "恐虐领域", "color": RED, "boss": "恐虐",
             "desc": "血与怒火的试炼场"},
            {"name": "第二章", "sub": "奸奇迷宫", "color": BLUE, "boss": "奸奇",
             "desc": "魔法与阴谋的漩涡"},
            {"name": "第三章", "sub": "色孽深渊", "color": PURPLE, "boss": "色孽",
             "desc": "弹幕与诱惑的狂欢"},
            {"name": "第四章", "sub": "纳垢花园", "color": GREEN, "boss": "纳垢",
             "desc": "腐朽与瘟疫的温床"},
            {"name": "第五章", "sub": "黄金王座", "color": GOLD, "boss": "人类帝皇",
             "desc": "终极的审判之战"},
        ]

        # 5个关卡卡片
        card_w, card_h, gap = 120, 160, 16
        total_w = 5 * card_w + 4 * gap
        start_x = cx - total_w // 2

        for i, info in enumerate(level_info):
            x = start_x + i * (card_w + gap)
            y = 130
            selected = (i == self.level_select_idx)
            c = info["color"]
            dc = tuple(max(0, v - 80) for v in c)
            lc = tuple(min(255, v + 60) for v in c)

            if selected:
                y -= 12
                glow = pygame.Surface((card_w + 16, card_h + 16), pygame.SRCALPHA)
                pulse = int(20 * abs(_math.sin(pygame.time.get_ticks() * 0.004)))
                pygame.draw.rect(glow, (*c, 40 + pulse), (0, 0, card_w + 16, card_h + 16), border_radius=6)
                surface.blit(glow, (x - 8, y - 8))

            bg_c = (40, 44, 65) if selected else (30, 32, 50)
            pygame.draw.rect(surface, bg_c, (x, y, card_w, card_h), border_radius=4)
            pygame.draw.rect(surface, c, (x, y, card_w, 6))
            pygame.draw.rect(surface, lc, (x + 2, y, card_w - 4, 2))

            if font_large:
                num = font_large.render(str(i + 1), False, c if selected else dc)
                surface.blit(num, num.get_rect(center=(x + card_w // 2, y + 38)))
            if font_medium:
                nt = font_medium.render(info["name"], False, WHITE if selected else (140, 140, 155))
                surface.blit(nt, nt.get_rect(center=(x + card_w // 2, y + 70)))
            if font_small:
                st = font_small.render(info["sub"], False, c if selected else (90, 90, 110))
                surface.blit(st, st.get_rect(center=(x + card_w // 2, y + 95)))
                bt = font_small.render("BOSS: " + info["boss"], False, lc if selected else (80, 80, 100))
                surface.blit(bt, bt.get_rect(center=(x + card_w // 2, y + 118)))

            pygame.draw.rect(surface, c if selected else (50, 52, 70),
                             (x, y, card_w, card_h), 2, border_radius=4)
            if selected:
                tx = x + card_w // 2
                ty = y + card_h + 8
                pygame.draw.polygon(surface, c, [(tx - 6, ty), (tx + 6, ty), (tx, ty + 8)])

        # 选中关卡描述
        sel = level_info[self.level_select_idx]
        if font_medium:
            desc_t = font_medium.render(sel["desc"], False, sel["color"])
            surface.blit(desc_t, desc_t.get_rect(center=(cx, 330)))
        if font_small:
            sections = LEVEL_STRUCTURE[self.level_select_idx]['sections']
            detail = f"共 {sections} 小关（{sections - 1} 普通 + 1 BOSS）"
            dt = font_small.render(detail, False, (160, 160, 175))
            surface.blit(dt, dt.get_rect(center=(cx, 360)))

        # 底部提示
        if font_medium:
            pygame.draw.line(surface, (50, 50, 70), (cx - 200, 410), (cx + 200, 410))
            btn_r = pygame.Rect(cx - 130, 430, 260, 36)
            pygame.draw.rect(surface, (25, 45, 70), btn_r, border_radius=3)
            pygame.draw.rect(surface, CYAN, btn_r, 1, border_radius=3)
            enter_t = font_medium.render("ENTER 开始  ESC 返回", False, WHITE)
            surface.blit(enter_t, enter_t.get_rect(center=btn_r.center))
        if font_small:
            nav_t = font_small.render("A / D 或 ← / → 切换关卡", False, (120, 130, 150))
            surface.blit(nav_t, nav_t.get_rect(center=(cx, 490)))

    # ==============================================================
    # 资料库
    # ==============================================================
    @staticmethod
    def _build_codex():
        """构建资料库条目"""
        allies = [
            {
                'name': '斯莱马博',
                'subtitle': 'Slymarbo  ·  战士',
                'color': (60, 140, 60),
                'accent': LIGHT_GREEN,
                'desc': [
                    '银河帝国的超级战士，凭借一身战斗技艺穿梭于战场。',
                    '初始HP: 5  |  移动速度: 4.0',
                    '武装：标准手枪、砍刀',
                    '可升级获得霰弹枪、激光枪、自动护盾等强化。',
                ],
                'draw_func': '_draw_codex_player',
            },
        ]
        enemies = [
            {
                'name': '叛军',
                'subtitle': '基础步兵  ·  地面单位',
                'color': RED,
                'accent': ORANGE,
                'desc': [
                    '被混沌之力腐化的叛变士兵，游荡于战场。',
                    'HP: 随关卡递增  |  速度: 2.0',
                    '行为：水平巡逻，部分个体配备射击能力。',
                    '颜色随所属混沌神阵营变化。',
                ],
                'draw_func': '_draw_codex_enemy',
            },
            {
                'name': '飞行兽',
                'subtitle': '空中猎手  ·  飞行单位',
                'color': (180, 60, 60),
                'accent': PINK,
                'desc': [
                    '拥有翅膀的混沌变异生物，在空中盘旋。',
                    'HP: 随关卡递增  |  浮空高度: 120-320',
                    '行为：正弦波浮动，自动追踪玩家射击。',
                    '无法用近战轻易触及，建议远程击落。',
                ],
                'draw_func': '_draw_codex_flying',
            },
            {
                'name': '炮台',
                'subtitle': '固定火力  ·  炮台单位',
                'color': (100, 100, 120),
                'accent': YELLOW,
                'desc': [
                    '扎根于高台的混沌自动火炮装置。',
                    'HP: 4  |  类型: 固定炮台',
                    '行为：炮管自动瞄准玩家，周期射击。',
                    '无法移动但火力密集，优先清除。',
                ],
                'draw_func': '_draw_codex_turret',
            },
            {
                'name': '勇气与荣耀之神',
                'subtitle': 'Khorne  ·  第一大关Boss',
                'color': RED,
                'accent': ORANGE,
                'desc': [
                    '混沌四神之一，嗜血与战争的化身。',
                    'HP: 30×难度  |  速度: 2.5  |  冲锋: 10',
                    '技能：鲜血冲锋、斩击旋风、血祭标记、',
                    '　　　7发扇形射击（-45°~+45°）',
                ],
                'draw_func': '_draw_codex_redboss',
            },
            {
                'name': '智慧与变化之神',
                'subtitle': 'Tzeentch  ·  第二大关Boss',
                'color': BLUE,
                'accent': CYAN,
                'desc': [
                    '混沌四神之一，变化与诡计的主宰。',
                    'HP: 35×难度  |  灵能护盾: 2层',
                    '技能：空间瞬移、3发扇形追踪、',
                    '　　　12方向全射、护盾自动恢复',
                ],
                'draw_func': '_draw_codex_blueboss',
            },
            {
                'name': '快乐与艺术之神',
                'subtitle': 'Slaanesh  ·  第三大关Boss',
                'color': PURPLE,
                'accent': PINK,
                'desc': [
                    '混沌四神之一，极致感官的追求者。',
                    'HP: 32×难度  |  速度: 3.5（最快）',
                    '技能：8方向弹幕、10连射追踪、',
                    '　　　螺旋弹幕（30帧持续旋转射击）',
                ],
                'draw_func': '_draw_codex_purpleboss',
            },
            {
                'name': '生命与慈爱之神',
                'subtitle': 'Nurgle  ·  第四大关Boss',
                'color': GREEN,
                'accent': LIME,
                'desc': [
                    '混沌四神之一，腐烂与疫病的领主。',
                    'HP: 90×难度（最高）  |  体型: 60×65',
                    '技能：腐朽吐息（毒雾→毒池）、7发毒弹、',
                    '　　　瘟疫仆从召唤（每次2只）',
                ],
                'draw_func': '_draw_codex_greenboss',
            },
            {
                'name': '人类帝皇',
                'subtitle': 'God Emperor  ·  第五大关Boss',
                'color': GOLD,
                'accent': YELLOW,
                'desc': [
                    '人类帝国至高的统治者，黄金王座上的神。',
                    'HP: 60×难度  |  体型: 55×70（最大）',
                    '技能：神圣激光、黄金弹幕、',
                    '　　　帝皇之怒（大范围爆发攻击）',
                ],
                'draw_func': '_draw_codex_goldboss',
            },
        ]
        return {'allies': allies, 'enemies': enemies}

    def _codex_current_list(self):
        """获取当前页签的条目列表"""
        if self.codex_page == 0:
            return self.codex_entries['allies']
        return self.codex_entries['enemies']

    # ---------- 资料库迷你绘图 ----------
    @staticmethod
    def _draw_codex_player(surface, cx, cy):
        """绘制玩家角色迷你图"""
        # 头部 + 红色头巾
        pygame.draw.rect(surface, (180, 30, 30), (cx - 10, cy - 22, 20, 5))
        pygame.draw.rect(surface, (210, 170, 130), (cx - 8, cy - 17, 16, 12))
        pygame.draw.rect(surface, WHITE, (cx - 5, cy - 14, 4, 3))
        pygame.draw.rect(surface, WHITE, (cx + 1, cy - 14, 4, 3))
        pygame.draw.rect(surface, (30, 30, 30), (cx - 4, cy - 13, 2, 2))
        pygame.draw.rect(surface, (30, 30, 30), (cx + 2, cy - 13, 2, 2))
        # 身体
        pygame.draw.rect(surface, (50, 80, 45), (cx - 9, cy - 5, 18, 20))
        pygame.draw.rect(surface, (70, 100, 60), (cx - 6, cy - 3, 12, 14))
        pygame.draw.rect(surface, GOLD, (cx - 5, cy + 8, 10, 3))
        # 手臂
        pygame.draw.rect(surface, (50, 80, 45), (cx - 14, cy - 3, 6, 14))
        pygame.draw.rect(surface, (50, 80, 45), (cx + 8, cy - 3, 6, 14))
        # 腿
        pygame.draw.rect(surface, (40, 65, 35), (cx - 7, cy + 15, 6, 10))
        pygame.draw.rect(surface, (40, 65, 35), (cx + 1, cy + 15, 6, 10))

    @staticmethod
    def _draw_codex_enemy(surface, cx, cy):
        """绘制普通敌人迷你图"""
        pygame.draw.rect(surface, RED, (cx - 8, cy - 12, 16, 24))
        pygame.draw.rect(surface, DARK_RED, (cx - 6, cy - 8, 12, 16))
        pygame.draw.rect(surface, YELLOW, (cx - 4, cy - 6, 3, 3))
        pygame.draw.rect(surface, YELLOW, (cx + 1, cy - 6, 3, 3))
        pygame.draw.rect(surface, DARK_RED, (cx - 5, cy + 12, 4, 8))
        pygame.draw.rect(surface, DARK_RED, (cx + 1, cy + 12, 4, 8))

    @staticmethod
    def _draw_codex_flying(surface, cx, cy):
        """绘制飞行敌人迷你图"""
        pygame.draw.rect(surface, (180, 60, 60), (cx - 7, cy - 6, 14, 14))
        pygame.draw.rect(surface, YELLOW, (cx - 4, cy - 3, 3, 3))
        pygame.draw.rect(surface, YELLOW, (cx + 1, cy - 3, 3, 3))
        # 翅膀
        pygame.draw.polygon(surface, (200, 80, 80),
                            [(cx - 7, cy - 2), (cx - 18, cy - 10), (cx - 12, cy + 4)])
        pygame.draw.polygon(surface, (200, 80, 80),
                            [(cx + 7, cy - 2), (cx + 18, cy - 10), (cx + 12, cy + 4)])

    @staticmethod
    def _draw_codex_turret(surface, cx, cy):
        """绘制炮台迷你图"""
        pygame.draw.rect(surface, (80, 80, 90), (cx - 10, cy + 4, 20, 10))
        pygame.draw.rect(surface, (100, 100, 120), (cx - 8, cy - 6, 16, 14))
        pygame.draw.rect(surface, (60, 60, 70), (cx - 6, cy - 4, 12, 10))
        pygame.draw.rect(surface, YELLOW, (cx - 2, cy - 2, 3, 3))
        pygame.draw.rect(surface, (120, 120, 140), (cx + 4, cy - 2, 12, 4))

    @staticmethod
    def _draw_codex_redboss(surface, cx, cy):
        """绘制恐虐迷你图"""
        pygame.draw.rect(surface, RED, (cx - 12, cy - 18, 24, 28))
        pygame.draw.rect(surface, DARK_RED, (cx - 10, cy - 14, 20, 20))
        # 角
        pygame.draw.rect(surface, (180, 30, 30), (cx - 13, cy - 26, 6, 12))
        pygame.draw.rect(surface, (180, 30, 30), (cx + 7, cy - 26, 6, 12))
        # 眼
        pygame.draw.rect(surface, YELLOW, (cx - 6, cy - 12, 5, 4))
        pygame.draw.rect(surface, YELLOW, (cx + 1, cy - 12, 5, 4))
        pygame.draw.rect(surface, ORANGE, (cx - 8, cy + 2, 16, 6))
        # 腿
        pygame.draw.rect(surface, DARK_RED, (cx - 8, cy + 10, 6, 10))
        pygame.draw.rect(surface, DARK_RED, (cx + 2, cy + 10, 6, 10))

    @staticmethod
    def _draw_codex_blueboss(surface, cx, cy):
        """绘制奸奇迷你图"""
        pygame.draw.rect(surface, BLUE, (cx - 12, cy - 14, 24, 26))
        pygame.draw.rect(surface, DARK_BLUE, (cx - 10, cy - 10, 20, 18))
        pygame.draw.rect(surface, CYAN, (cx - 3, cy - 4, 6, 6))
        # 触角
        pygame.draw.rect(surface, CYAN, (cx - 8, cy - 22, 4, 12))
        pygame.draw.rect(surface, CYAN, (cx - 1, cy - 24, 4, 14))
        pygame.draw.rect(surface, CYAN, (cx + 6, cy - 22, 4, 12))
        # 眼
        pygame.draw.rect(surface, CYAN, (cx - 6, cy - 8, 4, 4))
        pygame.draw.rect(surface, CYAN, (cx + 2, cy - 8, 4, 4))
        # 裙摆
        pygame.draw.rect(surface, DARK_BLUE, (cx - 10, cy + 12, 20, 8))

    @staticmethod
    def _draw_codex_purpleboss(surface, cx, cy):
        """绘制色孽迷你图"""
        pygame.draw.rect(surface, PURPLE, (cx - 10, cy - 14, 20, 26))
        pygame.draw.rect(surface, DARK_PURPLE, (cx - 8, cy - 10, 16, 18))
        pygame.draw.rect(surface, PINK, (cx - 3, cy - 4, 6, 6))
        # 头饰
        pygame.draw.rect(surface, PURPLE, (cx - 8, cy - 20, 16, 10))
        pygame.draw.polygon(surface, PINK, [(cx, cy - 28), (cx - 4, cy - 20), (cx + 4, cy - 20)])
        # 眼
        pygame.draw.rect(surface, PINK, (cx - 5, cy - 16, 4, 3))
        pygame.draw.rect(surface, PINK, (cx + 1, cy - 16, 4, 3))
        # 腿
        pygame.draw.rect(surface, DARK_PURPLE, (cx - 6, cy + 12, 5, 10))
        pygame.draw.rect(surface, DARK_PURPLE, (cx + 1, cy + 12, 5, 10))

    @staticmethod
    def _draw_codex_greenboss(surface, cx, cy):
        """绘制纳垢迷你图"""
        # 大体型
        pygame.draw.rect(surface, GREEN, (cx - 16, cy - 16, 32, 30))
        pygame.draw.rect(surface, DARK_GREEN, (cx - 14, cy - 12, 28, 22))
        pygame.draw.rect(surface, LIME, (cx - 4, cy - 6, 8, 8))
        # 头
        pygame.draw.rect(surface, GREEN, (cx - 10, cy - 24, 20, 12))
        pygame.draw.rect(surface, YELLOW, (cx - 6, cy - 20, 4, 4))
        pygame.draw.rect(surface, YELLOW, (cx + 2, cy - 20, 4, 4))
        # 腿（粗）
        pygame.draw.rect(surface, DARK_GREEN, (cx - 12, cy + 14, 10, 10))
        pygame.draw.rect(surface, DARK_GREEN, (cx + 2, cy + 14, 10, 10))

    @staticmethod
    def _draw_codex_goldboss(surface, cx, cy):
        """绘制帝皇迷你图"""
        # 最大体型
        pygame.draw.rect(surface, GOLD, (cx - 14, cy - 16, 28, 32))
        pygame.draw.rect(surface, (180, 140, 30), (cx - 12, cy - 12, 24, 24))
        pygame.draw.rect(surface, YELLOW, (cx - 4, cy - 6, 8, 8))
        # 光环 / 王冠
        pygame.draw.rect(surface, GOLD, (cx - 12, cy - 26, 24, 12))
        for i in range(5):
            px = cx - 10 + i * 5
            pygame.draw.rect(surface, YELLOW, (px, cy - 32, 3, 8))
        # 眼
        pygame.draw.rect(surface, WHITE, (cx - 5, cy - 22, 4, 3))
        pygame.draw.rect(surface, WHITE, (cx + 1, cy - 22, 4, 3))
        # 腿
        pygame.draw.rect(surface, (180, 140, 30), (cx - 10, cy + 16, 8, 10))
        pygame.draw.rect(surface, (180, 140, 30), (cx + 2, cy + 16, 8, 10))

    def draw_codex(self, surface):
        """绘制资料库列表页"""
        import math as _math
        from utils import font_large, font_medium, font_small, font_tiny

        surface.fill((20, 18, 28))
        cx = SCREEN_WIDTH // 2

        # 标题
        if font_large:
            shadow = font_large.render("资 料 库", False, (15, 15, 25))
            surface.blit(shadow, shadow.get_rect(center=(cx + 2, 42)))
            t = font_large.render("资 料 库", False, WHITE)
            surface.blit(t, t.get_rect(center=(cx, 40)))
        pygame.draw.line(surface, (60, 55, 80), (cx - 200, 65), (cx + 200, 65))

        # 页签
        tabs = ['角 色', '敌 人']
        if font_medium:
            for i, tab in enumerate(tabs):
                tx = 300 + i * 200
                sel = (i == self.codex_page)
                col = GOLD if sel else (100, 100, 120)
                tt = font_medium.render(tab, False, col)
                tr = tt.get_rect(center=(tx, 90))
                if sel:
                    pygame.draw.line(surface, GOLD, (tr.left, tr.bottom + 2),
                                     (tr.right, tr.bottom + 2), 2)
                surface.blit(tt, tr)

        # 条目列表
        entries = self._codex_current_list()
        start_y = 125
        row_h = 68
        max_visible = 7

        # 滚动
        scroll = max(0, self.codex_idx - max_visible + 1)
        visible = entries[scroll:scroll + max_visible]

        for vi, entry in enumerate(visible):
            real_idx = scroll + vi
            ey = start_y + vi * row_h
            selected = (real_idx == self.codex_idx)

            # 背景条
            bg_color = (40, 38, 55) if selected else (28, 26, 38)
            pygame.draw.rect(surface, bg_color, (60, ey, SCREEN_WIDTH - 120, row_h - 4))
            if selected:
                pygame.draw.rect(surface, entry.get('accent', GOLD),
                                 (60, ey, SCREEN_WIDTH - 120, row_h - 4), 2)
                # 左侧高亮条
                pygame.draw.rect(surface, entry.get('accent', GOLD), (60, ey, 4, row_h - 4))

            # 迷你头像
            icon_cx = 110
            icon_cy = ey + row_h // 2 - 2
            draw_fn = getattr(self, entry.get('draw_func', ''), None)
            if draw_fn:
                # 绘制到小区域
                icon_bg = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.rect(icon_bg, (30, 28, 42), (0, 0, 50, 50))
                pygame.draw.rect(icon_bg, entry.get('color', WHITE), (0, 0, 50, 50), 1)
                draw_fn(icon_bg, 25, 25)
                surface.blit(icon_bg, (icon_cx - 25, icon_cy - 25))

            # 名称 + 副标题
            if font_medium:
                nt = font_medium.render(entry['name'], False,
                                        entry.get('accent', WHITE) if selected else (200, 200, 210))
                surface.blit(nt, (150, ey + 8))
            if font_tiny:
                st = font_tiny.render(entry.get('subtitle', ''), False, (120, 120, 140))
                surface.blit(st, (150, ey + 36))

        # 底部提示
        if font_small:
            hints = "W/S 选择  |  ENTER 查看详情  |  A/D 切换页签  |  ESC 返回"
            ht = font_small.render(hints, False, (100, 105, 130))
            surface.blit(ht, ht.get_rect(center=(cx, SCREEN_HEIGHT - 30)))

        # 滚动指示
        if font_tiny:
            if scroll > 0:
                at = font_tiny.render("▲", False, (100, 100, 120))
                surface.blit(at, at.get_rect(center=(cx, start_y - 8)))
            if scroll + max_visible < len(entries):
                ab = font_tiny.render("▼", False, (100, 100, 120))
                surface.blit(ab, ab.get_rect(center=(cx, start_y + max_visible * row_h + 4)))

    def draw_codex_detail(self, surface):
        """绘制资料库详情页"""
        import math as _math
        from utils import font_large, font_medium, font_small, font_tiny

        surface.fill((20, 18, 28))
        cx = SCREEN_WIDTH // 2
        entries = self._codex_current_list()
        if self.codex_idx >= len(entries):
            return
        entry = entries[self.codex_idx]

        # ---- 顶部横幅 ----
        accent = entry.get('accent', GOLD)
        banner_h = 120
        banner = pygame.Surface((SCREEN_WIDTH, banner_h), pygame.SRCALPHA)
        banner.fill((*entry.get('color', (60, 60, 80)), 40))
        surface.blit(banner, (0, 0))
        pygame.draw.line(surface, accent, (0, banner_h), (SCREEN_WIDTH, banner_h), 2)

        # 名称
        if font_large:
            shadow = font_large.render(entry['name'], False, (10, 10, 15))
            surface.blit(shadow, shadow.get_rect(center=(cx + 2, 42)))
            nt = font_large.render(entry['name'], False, WHITE)
            surface.blit(nt, nt.get_rect(center=(cx, 40)))

        # 副标题
        if font_medium:
            st = font_medium.render(entry.get('subtitle', ''), False, accent)
            surface.blit(st, st.get_rect(center=(cx, 85)))

        # ---- 大头像区域 ----
        portrait_cx = 200
        portrait_cy = 280
        # 头像背景框
        pw, ph = 140, 160
        pygame.draw.rect(surface, (30, 28, 42), (portrait_cx - pw // 2, portrait_cy - ph // 2, pw, ph))
        pygame.draw.rect(surface, accent, (portrait_cx - pw // 2, portrait_cy - ph // 2, pw, ph), 2)
        # 角标
        pygame.draw.rect(surface, accent,
                         (portrait_cx - pw // 2, portrait_cy - ph // 2, pw, 3))

        draw_fn = getattr(self, entry.get('draw_func', ''), None)
        if draw_fn:
            # 绘制放大版（2x）
            temp = pygame.Surface((80, 80), pygame.SRCALPHA)
            draw_fn(temp, 40, 40)
            scaled = pygame.transform.scale(temp, (160, 160))
            surface.blit(scaled, (portrait_cx - 80, portrait_cy - 80))

        # ---- 右侧信息面板 ----
        info_x = 320
        info_y = 160

        # 信息框背景
        info_w = SCREEN_WIDTH - info_x - 60
        info_h = 260
        pygame.draw.rect(surface, (30, 28, 42), (info_x, info_y, info_w, info_h))
        pygame.draw.rect(surface, (50, 48, 65), (info_x, info_y, info_w, info_h), 1)
        # 标题栏
        pygame.draw.rect(surface, (*accent, 60) if len(accent) == 3 else accent,
                         (info_x, info_y, info_w, 28))
        if font_small:
            ht = font_small.render("─ 详 细 资 料 ─", False, accent)
            surface.blit(ht, ht.get_rect(center=(info_x + info_w // 2, info_y + 14)))

        # 描述文字
        desc = entry.get('desc', [])
        if font_medium:
            for i, line in enumerate(desc):
                lt = font_medium.render(line, False, (200, 200, 210))
                surface.blit(lt, (info_x + 20, info_y + 42 + i * 36))

        # ---- 底部装饰线 ----
        deco_y = 460
        pygame.draw.line(surface, (50, 48, 65), (60, deco_y), (SCREEN_WIDTH - 60, deco_y))

        # ---- 底部提示 ----
        if font_small:
            bt = font_small.render("按 ESC 返回列表", False, (100, 105, 130))
            surface.blit(bt, bt.get_rect(center=(cx, SCREEN_HEIGHT - 30)))

    def draw_settings(self, surface):
        """绘制设置界面 —— 精美版"""
        from utils import font_large, font_medium, font_small

        surface.fill(BG_SETTINGS)
        # 装饰线
        cx = SCREEN_WIDTH // 2
        pygame.draw.line(surface, (60, 60, 80), (cx - 180, 155), (cx + 180, 155))

        if font_large:
            shadow = font_large.render("设 置", False, (20, 20, 30))
            surface.blit(shadow, shadow.get_rect(center=(cx + 2, 102)))
            t = font_large.render("设 置", False, WHITE)
            surface.blit(t, t.get_rect(center=(cx, 100)))

        if font_medium:
            surface.blit(font_medium.render("游戏难度:", False, WHITE), (180, 245))
            for i, d in enumerate(self.difficulty_options):
                x = 400 + i * 110
                selected = (i == self.difficulty_index)
                color = GOLD if selected else (120, 120, 140)
                dt = font_medium.render(f" {d} ", False, color)
                r = dt.get_rect(center=(x, 255))
                if selected:
                    # 选中框 + 背景
                    bg = r.inflate(10, 8)
                    pygame.draw.rect(surface, (40, 50, 70), bg)
                    pygame.draw.rect(surface, GOLD, bg, 2)
                surface.blit(dt, r)

        if font_small:
            ht = font_small.render("<- -> 方向键切换难度", False, (140, 150, 170))
            surface.blit(ht, ht.get_rect(center=(cx, 320)))

        if font_medium:
            ct = font_medium.render("按 C 打开资料库", False, CYAN)
            surface.blit(ct, ct.get_rect(center=(cx, 390)))

        if font_medium:
            bt = font_medium.render("按 ESC 返回", False, GRAY)
            surface.blit(bt, bt.get_rect(center=(cx, 460)))

    def draw_paused(self, surface):
        """绘制暂停界面 —— 模糊遮罩+精美面板"""
        from utils import font_large, font_medium

        self.draw_playing(surface)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # 中央面板
        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
        panel = pygame.Rect(cx - 180, cy - 120, 360, 240)
        pygame.draw.rect(surface, (15, 20, 35, 220), panel)
        pygame.draw.rect(surface, (80, 100, 150), panel, 2)
        pygame.draw.line(surface, (100, 130, 180), (panel.x + 2, panel.y), (panel.right - 2, panel.y))

        if font_large:
            t = font_large.render("游戏暂停", False, WHITE)
            surface.blit(t, t.get_rect(center=(cx, cy - 80)))
        if font_medium:
            opts = [("按 ESC 继续游戏", (180, 200, 220)),
                    ("按 S 进入设置", (140, 160, 180)),
                    ("按 Q 退出游戏", (140, 140, 150))]
            for i, (o, c) in enumerate(opts):
                ot = font_medium.render(o, False, c)
                surface.blit(ot, ot.get_rect(center=(cx, cy - 10 + i * 45)))

    def draw_level_complete(self, surface):
        """绘制大关完成界面 —— 精美版"""
        from utils import font_large, font_medium

        surface.fill((10, 20, 35))
        cx = SCREEN_WIDTH // 2

        # 装饰星星
        import random as _r
        for i in range(30):
            sx = (i * 137 + 50) % SCREEN_WIDTH
            sy = (i * 89 + 20) % (SCREEN_HEIGHT // 2)
            brightness = 100 + (i * 37) % 135
            pygame.draw.rect(surface, (brightness, brightness, min(255, brightness + 20)), (sx, sy, 2, 2))

        # 金色分割线
        pygame.draw.line(surface, (180, 150, 50), (cx - 150, 145), (cx + 150, 145))

        if font_large:
            shadow = font_large.render(f"大关 {self.current_level} 通过！", False, (40, 30, 10))
            surface.blit(shadow, shadow.get_rect(center=(cx + 2, 102)))
            t = font_large.render(f"大关 {self.current_level} 通过！", False, GOLD)
            surface.blit(t, t.get_rect(center=(cx, 100)))
        if font_medium:
            stats = [
                (f"击杀数: {self.player.kills}", WHITE),
                (f"经验值: {self.player.xp}", (180, 220, 180)),
                (f"当前等级: {self.player.level}", YELLOW),
                (f"大关进度: {self.current_level}/{TOTAL_LEVELS}", (150, 200, 255)),
            ]
            for i, (s, c) in enumerate(stats):
                st = font_medium.render(s, False, c)
                surface.blit(st, st.get_rect(center=(cx, 210 + i * 42)))

            # 按钮提示
            btn_r = pygame.Rect(cx - 160, 415, 320, 40)
            pygame.draw.rect(surface, (30, 45, 70), btn_r)
            pygame.draw.rect(surface, GOLD, btn_r, 1)
            next_text = f"按 ENTER 进入大关 {self.current_level + 1}"
            t1 = font_medium.render(next_text, False, GOLD)
            surface.blit(t1, t1.get_rect(center=btn_r.center))
            t2 = font_medium.render("按 Q 退出游戏", False, GRAY)
            surface.blit(t2, t2.get_rect(center=(cx, 480)))

    def draw_gameover(self, surface):
        """绘制游戏结束界面 —— 精美版"""
        from utils import font_large, font_medium

        surface.fill((30, 10, 10))
        cx = SCREEN_WIDTH // 2

        # 血色氛围光
        vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(vignette, (80, 0, 0, 30), (50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100))
        surface.blit(vignette, (0, 0))

        # 红色分割线
        pygame.draw.line(surface, (150, 30, 30), (cx - 120, 170), (cx + 120, 170))

        if font_large:
            shadow = font_large.render("游戏结束！", False, (60, 5, 5))
            surface.blit(shadow, shadow.get_rect(center=(cx + 2, 122)))
            t = font_large.render("游戏结束！", False, RED)
            surface.blit(t, t.get_rect(center=(cx, 120)))
        if font_medium:
            stats = [
                (f"击杀数: {self.player.kills}", (200, 180, 180)),
                (f"经验值: {self.player.xp}", (180, 200, 180)),
                (f"最终等级: {self.player.level}", YELLOW),
                (f"到达: 大关{self.current_level} 小关{self.current_section}", (150, 180, 220))
            ]
            for i, (s, c) in enumerate(stats):
                st = font_medium.render(s, False, c)
                surface.blit(st, st.get_rect(center=(cx, 220 + i * 42)))

            btn_r = pygame.Rect(cx - 140, 435, 280, 38)
            pygame.draw.rect(surface, (50, 20, 20), btn_r)
            pygame.draw.rect(surface, (200, 60, 60), btn_r, 1)
            t1 = font_medium.render("按 ENTER 重新开始", False, GOLD)
            surface.blit(t1, t1.get_rect(center=btn_r.center))
            t2 = font_medium.render("按 Q 退出游戏", False, GRAY)
            surface.blit(t2, t2.get_rect(center=(cx, 500)))

    def draw_victory(self, surface):
        """绘制胜利界面 —— 精美版"""
        from utils import font_large, font_medium

        surface.fill((10, 10, 30))
        cx = SCREEN_WIDTH // 2

        # 金色光晕
        glow = pygame.Surface((400, 120), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 200, 50, 25), (0, 0, 400, 120))
        surface.blit(glow, (cx - 200, 25))

        # 装饰星星
        for i in range(50):
            sx = (i * 137 + 50) % SCREEN_WIDTH
            sy = (i * 89 + 20) % SCREEN_HEIGHT
            brightness = 120 + (i * 47) % 135
            sz = 1 + (i % 3)
            pygame.draw.rect(surface, (brightness, brightness, min(255, brightness + 30)), (sx, sy, sz, sz))

        # 金色分割线
        pygame.draw.line(surface, (200, 170, 60), (cx - 160, 130), (cx + 160, 130))

        if font_large:
            shadow = font_large.render("通关成功！", False, (40, 35, 10))
            surface.blit(shadow, shadow.get_rect(center=(cx + 2, 82)))
            t = font_large.render("通关成功！", False, GOLD)
            surface.blit(t, t.get_rect(center=(cx, 80)))
        if font_medium:
            mins = int(self.total_time) // 60
            secs = int(self.total_time) % 60
            stats = [
                (f"击杀数: {self.player.kills}", WHITE),
                (f"经验值: {self.player.xp}", (180, 220, 180)),
                (f"最终等级: {self.player.level}", YELLOW),
                (f"总用时: {mins}分{secs}秒", (150, 200, 255))
            ]
            for i, (s, c) in enumerate(stats):
                st = font_medium.render(s, False, c)
                surface.blit(st, st.get_rect(center=(cx, 190 + i * 45)))

            btn_r = pygame.Rect(cx - 140, 435, 280, 38)
            pygame.draw.rect(surface, (30, 35, 60), btn_r)
            pygame.draw.rect(surface, GOLD, btn_r, 1)
            t1 = font_medium.render("按 ENTER 重新开始", False, GOLD)
            surface.blit(t1, t1.get_rect(center=btn_r.center))
            t2 = font_medium.render("按 Q 退出游戏", False, GRAY)
            surface.blit(t2, t2.get_rect(center=(cx, 500)))

    # ==============================================================
    # 重置
    # ==============================================================
    def reset_game(self):
        """重置游戏"""
        self.player = Player()
        self.bullets = []
        self.melee_attacks = []
        self.enemies = []
        self.boss = None
        self.items = []
        self.spikes = []
        self.item_boxes = []
        self.laser_beams = []
        self.special_attacks = []
        self.poison_pools = []
        self.hit_particles = []
        self.current_level = 1
        self.current_section = 1
        self.sections_in_level = LEVEL_STRUCTURE[0]['sections']
        self.section_cleared = False
        self.transitioning = False
        self.transition_progress = 0.0
        self.old_surface = None
        self.new_surface = None
        self.start_time = time_module.time()
        self.setup_section()
