"""
敌人和BOSS模块
"""
import pygame
import random
import math
from src.constants import *
from src.objects import Bullet, SpinAttack, GroundHand, PoisonCloud, PoisonPool
from src.utils import play_sound, snd_boss_hit, snd_kill, font_tiny


# ============================================================
# 敌人类
# ============================================================
class Enemy:
    def __init__(self, x, y, hp=3, can_shoot=False, speed=2.0, color=RED):
        self.x = float(x)
        self.y = float(y)
        self.width = 22
        self.height = 30
        self.hp = hp
        self.max_hp = hp
        self.can_shoot = can_shoot
        self.speed = speed
        self.color = color
        self.alive = True
        self.direction = random.choice([-1, 1])
        self.shoot_timer = random.randint(60, 130)
        self.move_range = 140
        self.start_x = x
        self.vy = 0.0
        self.on_ground = False
        self.flash_timer = 0

    def update(self, ground_y, platforms, player_x=0, player_y=0):
        self.flash_timer = max(0, self.flash_timer - 1)
        self.x += self.speed * self.direction
        if abs(self.x - self.start_x) > self.move_range:
            self.direction *= -1
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))

        self.vy += 0.6
        self.y += self.vy
        self.on_ground = False
        if self.y + self.height >= ground_y:
            self.y = ground_y - self.height
            self.vy = 0
            self.on_ground = True
        for p in platforms:
            if (self.vy >= 0 and
                    self.y + self.height >= p.rect.y and
                    self.y + self.height <= p.rect.y + 14 and
                    self.x + self.width > p.rect.x and
                    self.x < p.rect.x + p.rect.width):
                self.y = p.rect.y - self.height
                self.vy = 0
                self.on_ground = True

        bullet = None
        if self.can_shoot:
            self.shoot_timer -= 1
            if self.shoot_timer <= 0:
                self.shoot_timer = random.randint(80, 150)
                dx = -1 if player_x < self.x else 1
                cx = self.x + self.width / 2
                cy = self.y + self.height / 3
                bullet = Bullet(cx, cy, dx, 0, 1, LIGHT_RED, 'enemy', 4)
        return bullet

    def take_damage(self, damage):
        self.hp -= damage
        self.flash_timer = 6
        play_sound(snd_boss_hit)
        if self.hp <= 0:
            self.alive = False
            play_sound(snd_kill)
            return True
        return False

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        c = self.color
        # 受击闪白
        if self.flash_timer > 0 and self.flash_timer % 2 == 0:
            c = (255, 255, 255)
        dc = tuple(max(0, v - 60) for v in c)
        lc = tuple(min(255, v + 40) for v in c)
        # 头盔
        pygame.draw.rect(surface, dc, (x + 3, y - 2, 16, 4))         # 盔檐
        pygame.draw.rect(surface, c, (x + 4, y, 14, 10))             # 头
        pygame.draw.rect(surface, lc, (x + 5, y, 12, 2))             # 盔面高光
        # 眼睛（发光）
        pygame.draw.rect(surface, (255, 240, 100), (x + 6, y + 3, 4, 3))
        pygame.draw.rect(surface, (255, 240, 100), (x + 12, y + 3, 4, 3))
        pygame.draw.rect(surface, (180, 50, 20), (x + 7, y + 4, 2, 2))
        pygame.draw.rect(surface, (180, 50, 20), (x + 13, y + 4, 2, 2))
        # 身体装甲
        pygame.draw.rect(surface, c, (x + 2, y + 10, 18, 12))
        pygame.draw.rect(surface, dc, (x + 4, y + 12, 14, 8))
        pygame.draw.rect(surface, lc, (x + 6, y + 10, 10, 2))       # 胸口高光
        pygame.draw.rect(surface, dc, (x + 9, y + 14, 4, 4))         # 核心暗块
        # 手臂
        pygame.draw.rect(surface, dc, (x - 1, y + 12, 4, 6))
        pygame.draw.rect(surface, dc, (x + 19, y + 12, 4, 6))
        # 腿
        pygame.draw.rect(surface, dc, (x + 3, y + 22, 7, 8))
        pygame.draw.rect(surface, dc, (x + 12, y + 22, 7, 8))
        pygame.draw.rect(surface, c, (x + 3, y + 22, 7, 2))         # 腿高光
        pygame.draw.rect(surface, c, (x + 12, y + 22, 7, 2))
        # 血条
        bar_w = 24
        bar_h = 3
        bx = x - 1
        by = y - 10
        pygame.draw.rect(surface, (40, 40, 40), (bx, by, bar_w, bar_h))
        hw = max(0, int(bar_w * self.hp / self.max_hp))
        hc = c if self.hp > self.max_hp * 0.3 else (255, 80, 60)
        pygame.draw.rect(surface, hc, (bx, by, hw, bar_h))
        pygame.draw.rect(surface, (100, 100, 100), (bx, by, bar_w, bar_h), 1)

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)


# ============================================================
# 飞行敌人类
# ============================================================
class FlyingEnemy:
    """飞在空中的敌人 —— 不受重力，正弦波上下浮动，朝玩家射击"""
    def __init__(self, x, y, hp=2, speed=1.5, color=RED, bullet_color=ORANGE):
        self.x = float(x)
        self.y = float(y)
        self.base_y = float(y)       # 浮动中心Y
        self.width = 20
        self.height = 20
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.color = color
        self.bullet_color = bullet_color
        self.alive = True
        self.direction = random.choice([-1, 1])
        self.move_range = 180
        self.start_x = x
        self.shoot_timer = random.randint(70, 140)
        self.float_timer = random.uniform(0, math.pi * 2)  # 浮动相位
        self.float_amp = 30.0       # 浮动幅度
        self.float_speed = 0.04     # 浮动速度
        self.wing_timer = 0         # 翅膀动画
        self.flash_timer = 0

    def update(self, ground_y, platforms, player_x=0, player_y=0):
        self.flash_timer = max(0, self.flash_timer - 1)
        # 水平移动
        self.x += self.speed * self.direction
        if abs(self.x - self.start_x) > self.move_range:
            self.direction *= -1
        self.x = max(10, min(SCREEN_WIDTH - self.width - 10, self.x))

        # 正弦浮动（不受重力）
        self.float_timer += self.float_speed
        self.y = self.base_y + math.sin(self.float_timer) * self.float_amp

        self.wing_timer += 1

        # 射击
        bullet = None
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = random.randint(80, 150)
            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            dx = player_x - cx
            dy = player_y - cy
            mag = math.sqrt(dx * dx + dy * dy) or 1
            bullet = Bullet(cx, cy, dx / mag, dy / mag, 1, self.bullet_color, 'enemy', 3.5)
        return bullet

    def take_damage(self, damage):
        self.hp -= damage
        self.flash_timer = 6
        play_sound(snd_boss_hit)
        if self.hp <= 0:
            self.alive = False
            play_sound(snd_kill)
            return True
        return False

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        c = self.color
        if self.flash_timer > 0 and self.flash_timer % 2 == 0:
            c = (255, 255, 255)
        dc = tuple(max(0, v - 60) for v in c)
        lc = tuple(min(255, v + 50) for v in c)
        # 身体光罩
        glow = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*c, 35), (0, 0, 24, 24))
        surface.blit(glow, (x - 2, y - 2))
        # 身体（圆润）
        pygame.draw.rect(surface, c, (x + 3, y + 3, 14, 14))
        pygame.draw.rect(surface, dc, (x + 5, y + 5, 10, 10))
        pygame.draw.rect(surface, lc, (x + 5, y + 3, 10, 3))       # 顶部高光
        # 眼睛（发光红眼）
        pygame.draw.rect(surface, (255, 200, 80), (x + 5, y + 6, 3, 3))
        pygame.draw.rect(surface, (255, 200, 80), (x + 12, y + 6, 3, 3))
        pygame.draw.rect(surface, (200, 40, 20), (x + 6, y + 7, 2, 2))
        pygame.draw.rect(surface, (200, 40, 20), (x + 13, y + 7, 2, 2))
        # 翅膀（扇动 + 羽毛细节）
        wing_offset = 3 if (self.wing_timer // 8) % 2 == 0 else -3
        # 左翅
        pygame.draw.rect(surface, c, (x - 6, y + 3 + wing_offset, 8, 10))
        pygame.draw.rect(surface, lc, (x - 6, y + 3 + wing_offset, 8, 2))
        pygame.draw.rect(surface, dc, (x - 4, y + 7 + wing_offset, 4, 4))
        pygame.draw.rect(surface, lc, (x - 6, y + 3 + wing_offset, 2, 6))  # 翅尖
        # 右翅
        pygame.draw.rect(surface, c, (x + 18, y + 3 + wing_offset, 8, 10))
        pygame.draw.rect(surface, lc, (x + 18, y + 3 + wing_offset, 8, 2))
        pygame.draw.rect(surface, dc, (x + 20, y + 7 + wing_offset, 4, 4))
        pygame.draw.rect(surface, lc, (x + 24, y + 3 + wing_offset, 2, 6))
        # 血条
        bar_w = 22
        bar_h = 3
        bx = x - 1
        by = y - 8
        pygame.draw.rect(surface, (40, 40, 40), (bx, by, bar_w, bar_h))
        hw = max(0, int(bar_w * self.hp / self.max_hp))
        pygame.draw.rect(surface, c, (bx, by, hw, bar_h))
        pygame.draw.rect(surface, (100, 100, 100), (bx, by, bar_w, bar_h), 1)

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)


# ============================================================
# 炮台敌人类
# ============================================================
class TurretEnemy:
    """固定在平台上的炮台 —— 不移动，瞄准玩家方向射击"""
    def __init__(self, x, y, hp=4, color=RED, bullet_color=ORANGE):
        self.x = float(x)
        self.y = float(y)
        self.width = 24
        self.height = 22
        self.hp = hp
        self.max_hp = hp
        self.color = color
        self.bullet_color = bullet_color
        self.alive = True
        self.shoot_timer = random.randint(50, 100)
        self.shoot_interval = (55, 110)   # 射击间隔范围
        self.barrel_angle = 0.0           # 炮管朝向角度 (弧度)
        self.vy = 0.0
        self.on_ground = False
        self.flash_timer = 0

    def update(self, ground_y, platforms, player_x=0, player_y=0):
        self.flash_timer = max(0, self.flash_timer - 1)
        # 重力 (掉到平台/地面上)
        self.vy += 0.6
        self.y += self.vy
        self.on_ground = False
        if self.y + self.height >= ground_y:
            self.y = ground_y - self.height
            self.vy = 0
            self.on_ground = True
        for p in platforms:
            if (self.vy >= 0 and
                    self.y + self.height >= p.rect.y and
                    self.y + self.height <= p.rect.y + 14 and
                    self.x + self.width > p.rect.x and
                    self.x < p.rect.x + p.rect.width):
                self.y = p.rect.y - self.height
                self.vy = 0
                self.on_ground = True

        # 炮管瞄准玩家
        cx = self.x + self.width / 2
        cy = self.y + self.height / 3
        dx = player_x - cx
        dy = player_y - cy
        self.barrel_angle = math.atan2(dy, dx)

        # 射击
        bullet = None
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = random.randint(*self.shoot_interval)
            mag = math.sqrt(dx * dx + dy * dy) or 1
            bullet = Bullet(cx, cy, dx / mag, dy / mag, 1, self.bullet_color, 'enemy', 4)
        return bullet

    def take_damage(self, damage):
        self.hp -= damage
        self.flash_timer = 6
        play_sound(snd_boss_hit)
        if self.hp <= 0:
            self.alive = False
            play_sound(snd_kill)
            return True
        return False

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        c = self.color
        if self.flash_timer > 0 and self.flash_timer % 2 == 0:
            c = (255, 255, 255)
        dc = tuple(max(0, v - 60) for v in c)
        lc = tuple(min(255, v + 40) for v in c)
        # 底座（金属感）
        pygame.draw.rect(surface, (50, 50, 55), (x + 1, y + 14, 22, 8))
        pygame.draw.rect(surface, (75, 75, 80), (x + 1, y + 14, 22, 2))     # 底座高光
        pygame.draw.rect(surface, (40, 40, 45), (x + 4, y + 17, 16, 4))     # 底座暗部
        # 铆钉
        pygame.draw.rect(surface, (120, 120, 130), (x + 3, y + 15, 2, 2))
        pygame.draw.rect(surface, (120, 120, 130), (x + 19, y + 15, 2, 2))
        # 炮身（主体）
        pygame.draw.rect(surface, c, (x + 3, y + 1, 18, 14))
        pygame.draw.rect(surface, dc, (x + 5, y + 3, 14, 10))
        pygame.draw.rect(surface, lc, (x + 5, y + 1, 14, 3))               # 顶部高光
        # 装甲纹路
        pygame.draw.rect(surface, dc, (x + 10, y + 6, 4, 6))
        # 炮管（朝向玩家）
        cx = x + self.width // 2
        cy = y + self.height // 3
        bx = cx + int(math.cos(self.barrel_angle) * 16)
        by = cy + int(math.sin(self.barrel_angle) * 16)
        pygame.draw.line(surface, (50, 50, 55), (cx, cy), (bx, by), 5)     # 炮管外壳
        pygame.draw.line(surface, (80, 80, 85), (cx, cy), (bx, by), 3)     # 炮管内管
        pygame.draw.line(surface, c, (cx, cy), (bx, by), 1)                 # 炮管亮线
        # 炮口火星
        pygame.draw.rect(surface, ORANGE, (bx - 1, by - 1, 3, 3))
        # 眼睛（发光）
        pygame.draw.rect(surface, (255, 220, 80), (x + 7, y + 5, 4, 3))
        pygame.draw.rect(surface, (255, 220, 80), (x + 13, y + 5, 4, 3))
        pygame.draw.rect(surface, WHITE, (x + 8, y + 6, 2, 1))
        pygame.draw.rect(surface, WHITE, (x + 14, y + 6, 2, 1))
        # 血条
        bar_w = 26
        bar_h = 3
        bx_bar = x - 1
        by_bar = y - 8
        pygame.draw.rect(surface, (40, 40, 40), (bx_bar, by_bar, bar_w, bar_h))
        hw = max(0, int(bar_w * self.hp / self.max_hp))
        pygame.draw.rect(surface, c, (bx_bar, by_bar, hw, bar_h))
        pygame.draw.rect(surface, (100, 100, 100), (bx_bar, by_bar, bar_w, bar_h), 1)

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)


# ============================================================
# BOSS 基类
# ============================================================
class Boss:
    def __init__(self, x, y, hp, color, name):
        self.x = float(x)
        self.y = float(y)
        self.width = 50
        self.height = 60
        self.hp = hp
        self.max_hp = hp
        self.color = color
        self.name = name
        self.alive = True
        self.direction = -1
        self.speed = 1.5
        self.attack_timer = 80
        self.vy = 0.0
        self.on_ground = False
        self.flash_timer = 0

    def base_update(self, ground_y, platforms):
        self.flash_timer = max(0, self.flash_timer - 1)
        self.vy += 0.6
        self.y += self.vy
        self.on_ground = False
        if self.y + self.height >= ground_y:
            self.y = ground_y - self.height
            self.vy = 0
            self.on_ground = True
        for p in platforms:
            if (self.vy >= 0 and
                    self.y + self.height >= p.rect.y and
                    self.y + self.height <= p.rect.y + 14 and
                    self.x + self.width > p.rect.x and
                    self.x < p.rect.x + p.rect.width):
                self.y = p.rect.y - self.height
                self.vy = 0
                self.on_ground = True
        self.x = max(0, min(SCREEN_WIDTH - self.width, self.x))

    def take_damage(self, damage):
        self.hp -= damage
        self.flash_timer = 6
        play_sound(snd_boss_hit)
        if self.hp <= 0:
            self.alive = False
            play_sound(snd_kill)
            return True
        return False

    def draw_health_bar(self, surface):
        x, y = int(self.x), int(self.y)
        bar_w = self.width + 20
        bar_h = 7
        bx = x - 10
        by = y - 20
        # 背景框
        pygame.draw.rect(surface, (20, 20, 25), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
        pygame.draw.rect(surface, (50, 50, 55), (bx, by, bar_w, bar_h))
        # 血量
        hw = max(0, int(bar_w * self.hp / self.max_hp))
        hc = self.color if self.hp > self.max_hp * 0.3 else (255, 70, 50)
        pygame.draw.rect(surface, hc, (bx, by, hw, bar_h))
        # 血量高光
        lc = tuple(min(255, v + 60) for v in (hc if isinstance(hc, tuple) else self.color))
        pygame.draw.rect(surface, lc, (bx, by, hw, 2))
        # 边框
        pygame.draw.rect(surface, (140, 140, 140), (bx, by, bar_w, bar_h), 1)
        # 名字
        if font_tiny:
            text = font_tiny.render(self.name, False, self.color)
            surface.blit(text, (bx, by - 16))

    def _draw_hit_flash(self, surface):
        """Boss受击闪白叠加层"""
        if self.flash_timer > 0 and self.flash_timer % 2 == 0:
            flash = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 140))
            surface.blit(flash, (int(self.x) - 5, int(self.y) - 5))

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)


# ============================================================
# BOSS 1: 红色（恐虐 - Khorne）
# ============================================================
class RedBoss(Boss):
    def __init__(self, x, y, difficulty):
        hp = int(30 * difficulty['boss_hp_mult'])
        super().__init__(x, y, hp, RED, "恐虐")
        self.speed = 2.5
        self.charge_timer = 0
        self.charging = False
        self.charge_speed = 10
        self.spin_cooldown = 0
        self.ground_hand_cooldown = 0

    def update(self, ground_y, platforms, player_x, player_y):
        self.base_update(ground_y, platforms)
        bullets = []
        specials = []
        self.attack_timer -= 1
        self.spin_cooldown = max(0, self.spin_cooldown - 1)
        self.ground_hand_cooldown = max(0, self.ground_hand_cooldown - 1)

        if self.charging:
            self.x += self.charge_speed * self.direction
            self.charge_timer -= 1
            if self.charge_timer <= 0:
                self.charging = False
                self.attack_timer = 40
        else:
            self.x += self.speed * self.direction
            if self.x <= 40 or self.x >= SCREEN_WIDTH - self.width - 40:
                self.direction *= -1

            if self.attack_timer <= 0:
                # ====================== 【修改 1】攻击变为 四选二 ======================
                actions = ['charge', 'spin', 'ground_hand', 'shoot']
                selected = random.sample(actions, 2)  # 随机选2个不同技能

                for action in selected:
                    if action == 'charge':
                        # 鲜血冲锋
                        self.charging = True
                        self.charge_timer = 35
                        self.direction = 1 if player_x > self.x else -1
                    elif action == 'spin' and self.spin_cooldown == 0:
                        # 斩击旋风
                        cx = self.x + self.width / 2
                        cy = self.y + self.height / 2
                        specials.append(SpinAttack(cx, cy, damage=2, radius=80, duration=22))
                        self.spin_cooldown = 90
                    elif action == 'ground_hand' and self.ground_hand_cooldown == 0:
                        # ==========================
                        # 一次召唤两只血手（无报错版）
                        # ==========================
                        specials.append(GroundHand(player_x - 80, ground_y, damage=2))
                        specials.append(GroundHand(player_x + 80, ground_y, damage=2))
                        self.ground_hand_cooldown = 100
                    elif action == 'shoot':
                        # ====================== 【修改 2】子弹数量大幅增加 ======================
                        cx = self.x + self.width / 2
                        cy = self.y + self.height / 3
                        # 从 3发 → 7发 大范围扩散射击
                        for angle in [-45, -30, -15, 0, 15, 30, 45]:
                            rad = math.radians(angle)
                            d = 1 if player_x > self.x else -1
                            dx_val = math.cos(rad) * d
                            dy_val = math.sin(rad)
                            bullets.append(Bullet(cx, cy, dx_val, dy_val, 1, ORANGE, 'enemy', 5))
                # ==========================================================================
                self.attack_timer = random.randint(45, 75)
        return bullets, specials

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        # 火焰光罩
        aura = pygame.Surface((60, 70), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (255, 60, 20, 25), (0, 0, 60, 70))
        surface.blit(aura, (x - 5, y - 5))
        # 身体装甲
        pygame.draw.rect(surface, RED, (x + 5, y + 15, 40, 30))
        pygame.draw.rect(surface, DARK_RED, (x + 8, y + 18, 34, 24))
        pygame.draw.rect(surface, (180, 40, 40), (x + 12, y + 20, 26, 18))  # 胸甲亮部
        pygame.draw.rect(surface, DARK_RED, (x + 18, y + 22, 14, 12))        # 胸口核心
        pygame.draw.rect(surface, ORANGE, (x + 22, y + 25, 6, 6))            # 燃烧核心
        # 头部 + 角
        pygame.draw.rect(surface, RED, (x + 12, y + 2, 26, 16))
        pygame.draw.rect(surface, DARK_RED, (x + 14, y + 4, 22, 12))         # 脸部阴影
        pygame.draw.rect(surface, (180, 30, 30), (x + 7, y - 10, 7, 16))     # 左角
        pygame.draw.rect(surface, (200, 40, 30), (x + 8, y - 10, 4, 4))      # 角尖高光
        pygame.draw.rect(surface, (180, 30, 30), (x + 36, y - 10, 7, 16))    # 右角
        pygame.draw.rect(surface, (200, 40, 30), (x + 37, y - 10, 4, 4))
        # 眼睛（燃烧之眼）
        pygame.draw.rect(surface, YELLOW, (x + 17, y + 6, 6, 5))
        pygame.draw.rect(surface, YELLOW, (x + 27, y + 6, 6, 5))
        pygame.draw.rect(surface, (255, 100, 30), (x + 18, y + 7, 4, 3))     # 眵孔
        pygame.draw.rect(surface, (255, 100, 30), (x + 28, y + 7, 4, 3))
        pygame.draw.rect(surface, WHITE, (x + 19, y + 7, 1, 1))              # 眼光
        pygame.draw.rect(surface, WHITE, (x + 29, y + 7, 1, 1))
        # 手臂
        pygame.draw.rect(surface, RED, (x - 2, y + 18, 10, 20))
        pygame.draw.rect(surface, DARK_RED, (x, y + 20, 6, 16))
        pygame.draw.rect(surface, RED, (x + 42, y + 18, 10, 20))
        pygame.draw.rect(surface, DARK_RED, (x + 44, y + 20, 6, 16))
        # 腿
        pygame.draw.rect(surface, DARK_RED, (x + 10, y + 45, 12, 15))
        pygame.draw.rect(surface, (120, 25, 25), (x + 10, y + 45, 12, 3))    # 腿高光
        pygame.draw.rect(surface, DARK_RED, (x + 28, y + 45, 12, 15))
        pygame.draw.rect(surface, (120, 25, 25), (x + 28, y + 45, 12, 3))
        # 冲锋拖尾
        if self.charging:
            for i in range(4):
                ax = x - (10 + i * 8) * self.direction
                alpha = 180 - i * 40
                cs = pygame.Surface((5, 12), pygame.SRCALPHA)
                cs.fill((255, 100, 40, max(0, alpha)))
                surface.blit(cs, (ax, y + 20))
        self._draw_hit_flash(surface)
        self.draw_health_bar(surface)


# ============================================================
# BOSS 2: 蓝色（奸奇 - Tzeentch）
# ============================================================
class BlueBoss(Boss):
    def __init__(self, x, y, difficulty):
        hp = int(35 * difficulty['boss_hp_mult'])
        super().__init__(x, y, hp, BLUE, "奸奇")
        self.teleport_timer = 120
        self.width = 48
        self.height = 58
        self.psy_shield = 2
        self.psy_shield_max = 2
        self.psy_shield_cd = 0
        self.psy_shield_cd_max = 240

    def take_damage(self, damage):
        """灵能护盾：护盾存在时伤害减半"""
        if self.psy_shield > 0:
            self.psy_shield -= 1
            damage = max(1, (damage + 1) // 2)
            if self.psy_shield <= 0:
                self.psy_shield_cd = self.psy_shield_cd_max
        self.hp -= damage
        self.flash_timer = 6
        play_sound(snd_boss_hit)
        if self.hp <= 0:
            self.alive = False
            play_sound(snd_kill)
            return True
        return False

    def update(self, ground_y, platforms, player_x, player_y):
        self.base_update(ground_y, platforms)
        bullets = []
        self.attack_timer -= 1
        self.teleport_timer -= 1

        # 护盾恢复
        if self.psy_shield <= 0:
            self.psy_shield_cd -= 1
            if self.psy_shield_cd <= 0:
                self.psy_shield = self.psy_shield_max

        if self.teleport_timer <= 0:
            self.x = random.randint(50, SCREEN_WIDTH - self.width - 50)
            self.y = random.randint(100, ground_y - self.height - 50)
            self.vy = 0
            self.teleport_timer = random.randint(80, 140)

        self.x += self.speed * self.direction
        if self.x <= 30 or self.x >= SCREEN_WIDTH - self.width - 30:
            self.direction *= -1

        if self.attack_timer <= 0:
            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            action = random.choice(['track', 'multi'])
            if action == 'track':
                # 3发扇形追踪
                dx = player_x - cx
                dy = player_y - cy
                base_angle = math.atan2(dy, dx)
                for offset in [-0.2, 0, 0.2]:
                    a = base_angle + offset
                    bullets.append(Bullet(cx, cy, math.cos(a), math.sin(a), 1, CYAN, 'enemy', 3.5))
            else:
                # 12方向全射
                for angle in range(0, 360, 30):
                    rad = math.radians(angle)
                    bullets.append(Bullet(cx, cy, math.cos(rad), math.sin(rad), 1, LIGHT_BLUE, 'enemy', 3))
            self.attack_timer = random.randint(40, 75)
        return bullets

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        # 魔法光罩
        aura = pygame.Surface((58, 68), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (50, 100, 255, 20), (0, 0, 58, 68))
        surface.blit(aura, (x - 5, y - 5))
        # 身体
        pygame.draw.rect(surface, BLUE, (x + 6, y + 12, 36, 34))
        pygame.draw.rect(surface, DARK_BLUE, (x + 10, y + 16, 28, 26))
        pygame.draw.rect(surface, (70, 120, 240), (x + 14, y + 12, 20, 4))    # 胸口高光
        pygame.draw.rect(surface, CYAN, (x + 18, y + 22, 12, 8))              # 魔法核心
        pygame.draw.rect(surface, (100, 200, 255), (x + 21, y + 24, 6, 4))    # 核心亮部
        # 头部
        pygame.draw.rect(surface, BLUE, (x + 12, y, 24, 16))
        pygame.draw.rect(surface, DARK_BLUE, (x + 14, y + 2, 20, 12))
        # 触角（发光）
        pygame.draw.rect(surface, CYAN, (x + 14, y - 8, 5, 12))
        pygame.draw.rect(surface, (140, 220, 255), (x + 15, y - 8, 3, 3))     # 触角尖端发光
        pygame.draw.rect(surface, CYAN, (x + 22, y - 10, 5, 14))
        pygame.draw.rect(surface, (140, 220, 255), (x + 23, y - 10, 3, 3))
        pygame.draw.rect(surface, CYAN, (x + 30, y - 8, 5, 12))
        pygame.draw.rect(surface, (140, 220, 255), (x + 31, y - 8, 3, 3))
        # 眼睛（魔法之眼）
        pygame.draw.rect(surface, CYAN, (x + 17, y + 5, 5, 5))
        pygame.draw.rect(surface, WHITE, (x + 18, y + 6, 3, 3))
        pygame.draw.rect(surface, CYAN, (x + 26, y + 5, 5, 5))
        pygame.draw.rect(surface, WHITE, (x + 27, y + 6, 3, 3))
        # 手臂（魔法触手）
        pygame.draw.rect(surface, LIGHT_BLUE, (x, y + 16, 8, 6))
        pygame.draw.rect(surface, BLUE, (x + 1, y + 22, 6, 8))
        pygame.draw.rect(surface, LIGHT_BLUE, (x + 40, y + 16, 8, 6))
        pygame.draw.rect(surface, BLUE, (x + 41, y + 22, 6, 8))
        # 裙摆/腿
        pygame.draw.rect(surface, DARK_BLUE, (x + 8, y + 46, 32, 12))
        pygame.draw.rect(surface, (40, 55, 130), (x + 8, y + 46, 32, 3))      # 裙摆高光
        # 灵能护盾
        if self.psy_shield > 0:
            shield_s = pygame.Surface((self.width + 16, self.height + 16), pygame.SRCALPHA)
            alpha = 50 + self.psy_shield * 25
            pygame.draw.ellipse(shield_s, (80, 160, 255, alpha),
                                (0, 0, self.width + 16, self.height + 16))
            pygame.draw.ellipse(shield_s, (140, 200, 255, alpha + 20),
                                (4, 4, self.width + 8, self.height + 8), 2)
            surface.blit(shield_s, (x - 8, y - 8))
        self._draw_hit_flash(surface)
        self.draw_health_bar(surface)


# ============================================================
# BOSS 3: 紫色（色孽 - Slaanesh）
# ============================================================
class PurpleBoss(Boss):
    def __init__(self, x, y, difficulty):
        hp = int(32 * difficulty['boss_hp_mult'])
        super().__init__(x, y, hp, PURPLE, "色孽")
        self.speed = 3.5
        self.burst_count = 0
        self.burst_timer = 0
        self.width = 44
        self.height = 58
        self.spiral_timer = 0
        self.spiral_angle = 0.0

    def update(self, ground_y, platforms, player_x, player_y):
        self.base_update(ground_y, platforms)
        bullets = []
        self.attack_timer -= 1

        self.x += self.speed * self.direction
        if self.x <= 30 or self.x >= SCREEN_WIDTH - self.width - 30:
            self.direction *= -1

        # 螺旋弹幕
        if self.spiral_timer > 0:
            self.spiral_timer -= 1
            if self.spiral_timer % 2 == 0:
                cx = self.x + self.width / 2
                cy = self.y + self.height / 2
                self.spiral_angle += 0.35
                bullets.append(Bullet(cx, cy, math.cos(self.spiral_angle),
                                      math.sin(self.spiral_angle), 1, PINK, 'enemy', 3.5))
            return bullets

        # 连射
        if self.burst_count > 0:
            self.burst_timer -= 1
            if self.burst_timer <= 0:
                cx = self.x + self.width / 2
                cy = self.y + self.height / 3
                dx = player_x - cx
                dy = player_y - cy
                mag = math.sqrt(dx * dx + dy * dy) or 1
                bullets.append(Bullet(cx, cy, dx / mag, dy / mag, 1, PINK, 'enemy', 5))
                self.burst_count -= 1
                self.burst_timer = 4

        if self.attack_timer <= 0 and self.burst_count == 0:
            action = random.choice(['cross', 'burst', 'spiral'])
            cx = self.x + self.width / 2
            cy = self.y + self.height / 2
            if action == 'cross':
                # 8方向弹幕
                for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                    rad = math.radians(angle)
                    bullets.append(Bullet(cx, cy, math.cos(rad), math.sin(rad), 1, PURPLE, 'enemy', 4))
            elif action == 'burst':
                # 10连射
                self.burst_count = 10
                self.burst_timer = 0
            elif action == 'spiral':
                # 螺旋弹幕
                self.spiral_timer = 30
                self.spiral_angle = 0.0
            self.attack_timer = random.randint(20, 45)
        return bullets

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        # 光罩
        aura = pygame.Surface((54, 68), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (180, 50, 220, 20), (0, 0, 54, 68))
        surface.blit(aura, (x - 5, y - 5))
        # 身体
        pygame.draw.rect(surface, PURPLE, (x + 10, y + 10, 24, 34))
        pygame.draw.rect(surface, DARK_PURPLE, (x + 13, y + 14, 18, 26))
        pygame.draw.rect(surface, (200, 70, 240), (x + 15, y + 10, 14, 4))    # 胸口高光
        pygame.draw.rect(surface, PINK, (x + 17, y + 20, 10, 8))              # 核心
        pygame.draw.rect(surface, (255, 180, 220), (x + 19, y + 22, 6, 4))    # 核心亮
        # 头部
        pygame.draw.rect(surface, PURPLE, (x + 13, y, 18, 13))
        pygame.draw.rect(surface, DARK_PURPLE, (x + 15, y + 2, 14, 9))
        # 角
        pygame.draw.rect(surface, PINK, (x + 9, y - 7, 4, 11))
        pygame.draw.rect(surface, (255, 180, 220), (x + 10, y - 7, 2, 3))
        pygame.draw.rect(surface, PINK, (x + 31, y - 7, 4, 11))
        pygame.draw.rect(surface, (255, 180, 220), (x + 32, y - 7, 2, 3))
        # 眼睛
        pygame.draw.rect(surface, PINK, (x + 17, y + 3, 4, 4))
        pygame.draw.rect(surface, WHITE, (x + 18, y + 4, 2, 2))
        pygame.draw.rect(surface, PINK, (x + 25, y + 3, 4, 4))
        pygame.draw.rect(surface, WHITE, (x + 26, y + 4, 2, 2))
        # 手臂（利爪）
        pygame.draw.rect(surface, PINK, (x + 2, y + 12, 10, 5))
        pygame.draw.rect(surface, PURPLE, (x + 1, y + 17, 4, 8))
        pygame.draw.rect(surface, PINK, (x + 32, y + 12, 10, 5))
        pygame.draw.rect(surface, PURPLE, (x + 39, y + 17, 4, 8))
        # 腿
        pygame.draw.rect(surface, DARK_PURPLE, (x + 12, y + 44, 8, 14))
        pygame.draw.rect(surface, (100, 25, 120), (x + 12, y + 44, 8, 3))
        pygame.draw.rect(surface, DARK_PURPLE, (x + 24, y + 44, 8, 14))
        pygame.draw.rect(surface, (100, 25, 120), (x + 24, y + 44, 8, 3))
        self._draw_hit_flash(surface)
        self.draw_health_bar(surface)


# ============================================================
# BOSS 4: 绿色（纳垢 - Nurgle）
# ============================================================
class GreenBoss(Boss):
    def __init__(self, x, y, difficulty):
        hp = int(90 * difficulty['boss_hp_mult'])
        super().__init__(x, y, hp, GREEN, "纳垢")
        self.width = 60
        self.height = 65
        self.speed = 1.0
        self.summon_timer = 150
        self.breath_cooldown = 0

    def update(self, ground_y, platforms, player_x, player_y):
        self.base_update(ground_y, platforms)
        bullets = []
        summons = []
        specials = []
        self.attack_timer -= 1
        self.summon_timer -= 1
        self.breath_cooldown = max(0, self.breath_cooldown - 1)

        self.x += self.speed * self.direction
        if self.x <= 30 or self.x >= SCREEN_WIDTH - self.width - 30:
            self.direction *= -1

        if self.attack_timer <= 0:
            action = random.choice(['shoot', 'breath', 'shoot'])
            cx = self.x + self.width / 2
            cy = self.y + self.height / 3
            if action == 'breath' and self.breath_cooldown == 0:
                # 腐朽吐息
                d = 1 if player_x > self.x else -1
                specials.append(PoisonCloud(cx, cy, d, ground_y, damage=1, duration=35))
                self.breath_cooldown = 120
            else:
                # 毒弹
                for _ in range(7):
                    dx = player_x - cx + random.randint(-60, 60)
                    dy = player_y - cy + random.randint(-40, 40)
                    mag = math.sqrt(dx * dx + dy * dy) or 1
                    bullets.append(Bullet(cx, cy, dx / mag, dy / mag, 1, LIME, 'enemy', 2.5))
            self.attack_timer = random.randint(50, 90)

        # 瘟疫仆从召唤 - 每次召唤2只
        if self.summon_timer <= 0:
            self.summon_timer = random.randint(120, 200)
            for _ in range(2):
                sx = random.choice([random.randint(50, 120), random.randint(SCREEN_WIDTH - 140, SCREEN_WIDTH - 60)])
                s = Enemy(sx, ground_y - 60, hp=2, can_shoot=False, speed=1.5, color=DARK_GREEN)
                summons.append(s)
        return bullets, summons, specials

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        # 毒气光罩
        aura = pygame.Surface((70, 75), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (50, 200, 50, 18), (0, 0, 70, 75))
        surface.blit(aura, (x - 5, y - 5))
        # 巨大身体
        pygame.draw.rect(surface, GREEN, (x + 5, y + 12, 50, 40))
        pygame.draw.rect(surface, DARK_GREEN, (x + 10, y + 16, 40, 32))
        pygame.draw.rect(surface, (70, 220, 70), (x + 15, y + 12, 30, 5))     # 胸口高光
        pygame.draw.rect(surface, LIME, (x + 20, y + 24, 20, 16))
        pygame.draw.rect(surface, (120, 255, 80), (x + 23, y + 27, 14, 10))   # 胖肚子亮部
        # 脑袋 + 角
        pygame.draw.rect(surface, GREEN, (x + 17, y, 26, 16))
        pygame.draw.rect(surface, DARK_GREEN, (x + 20, y + 3, 20, 10))
        pygame.draw.rect(surface, DARK_GREEN, (x + 14, y - 7, 7, 11))
        pygame.draw.rect(surface, (40, 140, 40), (x + 15, y - 7, 4, 3))       # 角尖
        pygame.draw.rect(surface, DARK_GREEN, (x + 40, y - 7, 7, 11))
        pygame.draw.rect(surface, (40, 140, 40), (x + 41, y - 7, 4, 3))
        # 独眼
        pygame.draw.rect(surface, YELLOW, (x + 25, y + 4, 10, 8))
        pygame.draw.rect(surface, (30, 30, 10), (x + 28, y + 5, 4, 6))        # 眵孔
        pygame.draw.rect(surface, WHITE, (x + 28, y + 5, 2, 2))               # 眼光
        # 手臂
        pygame.draw.rect(surface, GREEN, (x - 2, y + 18, 10, 24))
        pygame.draw.rect(surface, DARK_GREEN, (x, y + 20, 6, 20))
        pygame.draw.rect(surface, GREEN, (x + 52, y + 18, 10, 24))
        pygame.draw.rect(surface, DARK_GREEN, (x + 54, y + 20, 6, 20))
        # 腿
        pygame.draw.rect(surface, DARK_GREEN, (x + 12, y + 52, 14, 13))
        pygame.draw.rect(surface, (25, 100, 25), (x + 12, y + 52, 14, 3))
        pygame.draw.rect(surface, DARK_GREEN, (x + 34, y + 52, 14, 13))
        pygame.draw.rect(surface, (25, 100, 25), (x + 34, y + 52, 14, 3))
        self._draw_hit_flash(surface)
        self.draw_health_bar(surface)


# ============================================================
# BOSS 5: 金色（人类帝皇 - Emperor）
# ============================================================
class GoldBoss(Boss):
    def __init__(self, x, y, difficulty):
        hp = int(60 * difficulty['boss_hp_mult'])
        super().__init__(x, y, hp, GOLD, "人类帝皇")
        self.width = 55
        self.height = 70
        self.speed = 2.0
        self.laser_timer = 0
        self.laser_active = False
        self.laser_y = 0

    def update(self, ground_y, platforms, player_x, player_y):
        self.base_update(ground_y, platforms)
        bullets = []
        self.attack_timer -= 1

        self.x += self.speed * self.direction
        if self.x <= 30 or self.x >= SCREEN_WIDTH - self.width - 30:
            self.direction *= -1

        if self.laser_active:
            self.laser_timer -= 1
            if self.laser_timer <= 0:
                self.laser_active = False

        if self.attack_timer <= 0:
            action = random.choice(['barrage', 'laser', 'explosion', 'barrage'])
            cx = self.x + self.width / 2
            cy = self.y + self.height / 3

            if action == 'barrage':
                for angle in range(0, 360, 30):
                    rad = math.radians(angle)
                    bullets.append(Bullet(cx, cy, math.cos(rad), math.sin(rad), 1, GOLD, 'enemy', 3.5))
            elif action == 'laser':
                self.laser_active = True
                self.laser_timer = 35
                self.laser_y = player_y + 18
            elif action == 'explosion':
                for angle in range(0, 360, 20):
                    rad = math.radians(angle)
                    bullets.append(Bullet(cx, cy, math.cos(rad), math.sin(rad), 2, ORANGE, 'enemy', 2))
                for angle in range(10, 360, 25):
                    rad = math.radians(angle)
                    bullets.append(Bullet(cx, cy, math.cos(rad), math.sin(rad), 1, YELLOW, 'enemy', 4))
            self.attack_timer = random.randint(35, 65)
        return bullets

    def draw(self, surface):
        x, y = int(self.x), int(self.y)
        # 神圣光罩
        aura = pygame.Surface((65, 80), pygame.SRCALPHA)
        pygame.draw.ellipse(aura, (255, 200, 50, 22), (0, 0, 65, 80))
        surface.blit(aura, (x - 5, y - 5))
        # 身体装甲
        pygame.draw.rect(surface, GOLD, (x + 8, y + 18, 39, 34))
        pygame.draw.rect(surface, (200, 160, 40), (x + 12, y + 22, 31, 26))
        pygame.draw.rect(surface, (255, 220, 80), (x + 16, y + 18, 23, 5))    # 胸口高光
        # 帝国之鹰图标
        pygame.draw.rect(surface, (180, 40, 40), (x + 20, y + 28, 15, 12))
        pygame.draw.rect(surface, GOLD, (x + 22, y + 30, 11, 8))
        pygame.draw.rect(surface, WHITE, (x + 25, y + 32, 5, 4))              # 鹰形
        # 手臂
        pygame.draw.rect(surface, GOLD, (x - 2, y + 16, 13, 16))
        pygame.draw.rect(surface, (200, 160, 40), (x, y + 18, 9, 12))
        pygame.draw.rect(surface, GOLD, (x + 44, y + 16, 13, 16))
        pygame.draw.rect(surface, (200, 160, 40), (x + 46, y + 18, 9, 12))
        # 头部（皇冠）
        pygame.draw.rect(surface, SKIN, (x + 15, y + 4, 25, 16))
        pygame.draw.rect(surface, (210, 170, 120), (x + 17, y + 12, 21, 6))   # 下巴阴影
        pygame.draw.rect(surface, GOLD, (x + 12, y - 3, 31, 9))
        pygame.draw.rect(surface, (255, 220, 80), (x + 14, y - 3, 27, 3))     # 冠高光
        pygame.draw.rect(surface, GOLD, (x + 14, y - 12, 6, 13))
        pygame.draw.rect(surface, (255, 220, 80), (x + 15, y - 12, 3, 3))
        pygame.draw.rect(surface, GOLD, (x + 24, y - 15, 7, 16))
        pygame.draw.rect(surface, (255, 220, 80), (x + 25, y - 15, 4, 3))
        pygame.draw.rect(surface, GOLD, (x + 35, y - 12, 6, 13))
        pygame.draw.rect(surface, (255, 220, 80), (x + 36, y - 12, 3, 3))
        # 眼睛（威严之眼）
        pygame.draw.rect(surface, WHITE, (x + 20, y + 8, 5, 5))
        pygame.draw.rect(surface, GOLD, (x + 21, y + 9, 3, 3))
        pygame.draw.rect(surface, WHITE, (x + 30, y + 8, 5, 5))
        pygame.draw.rect(surface, GOLD, (x + 31, y + 9, 3, 3))
        # 腿
        pygame.draw.rect(surface, GOLD, (x + 14, y + 52, 12, 18))
        pygame.draw.rect(surface, (200, 160, 40), (x + 16, y + 54, 8, 14))
        pygame.draw.rect(surface, GOLD, (x + 29, y + 52, 12, 18))
        pygame.draw.rect(surface, (200, 160, 40), (x + 31, y + 54, 8, 14))
        # 激光
        if self.laser_active:
            ly = int(self.laser_y)
            # 激光光罩
            glow = pygame.Surface((SCREEN_WIDTH, 24), pygame.SRCALPHA)
            pygame.draw.rect(glow, (255, 230, 100, 40), (0, 0, SCREEN_WIDTH, 24))
            surface.blit(glow, (0, ly - 12))
            # 激光主体
            s = pygame.Surface((SCREEN_WIDTH, 14), pygame.SRCALPHA)
            s.fill((255, 220, 50, 160))
            surface.blit(s, (0, ly - 7))
            pygame.draw.rect(surface, (255, 240, 150), (0, ly - 3, SCREEN_WIDTH, 6))
            pygame.draw.rect(surface, WHITE, (0, ly - 1, SCREEN_WIDTH, 2))
        self._draw_hit_flash(surface)
        self.draw_health_bar(surface)

    def check_laser_hit(self, player_rect):
        if self.laser_active:
            laser_rect = pygame.Rect(0, int(self.laser_y) - 6, SCREEN_WIDTH, 12)
            return laser_rect.colliderect(player_rect)
        return False
