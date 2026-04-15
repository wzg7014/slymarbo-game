"""
游戏对象模块 - 平台、子弹、近战攻击、道具
"""
import pygame
import math
import random
from constants import *
from utils import font_tiny

# ============================================================
# 平台类
# ============================================================
class Platform:
    def __init__(self, x, y, width, height=12):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, surface):
        r = self.rect
        # 平台主体 —— 石砖纹理
        pygame.draw.rect(surface, (90, 65, 40), r)  # 基底色
        # 顶部草坪层
        pygame.draw.rect(surface, (45, 110, 45), (r.x, r.y, r.width, 3))
        pygame.draw.rect(surface, (65, 140, 55), (r.x, r.y, r.width, 1))  # 草尖高光
        # 砖块纹理 —— 交错排列
        brick_w, brick_h = 14, 4
        for row in range(2):
            by = r.y + 3 + row * (brick_h + 1)
            offset = 7 if row % 2 else 0
            for bx in range(r.x + offset, r.x + r.width - 2, brick_w + 2):
                bw = min(brick_w, r.x + r.width - bx - 1)
                if bw < 4:
                    continue
                pygame.draw.rect(surface, (110, 78, 45), (bx, by, bw, brick_h))
                # 砖块高光（顶边）
                pygame.draw.line(surface, (130, 98, 60), (bx, by), (bx + bw - 1, by))
                # 砖块暗部（底边）
                pygame.draw.line(surface, (70, 50, 28), (bx, by + brick_h - 1), (bx + bw - 1, by + brick_h - 1))
        # 底部阴影
        pygame.draw.line(surface, (50, 35, 15), (r.x, r.y + r.height - 1), (r.x + r.width - 1, r.y + r.height - 1))
        # 左右边缘
        pygame.draw.line(surface, (70, 50, 28), (r.x, r.y), (r.x, r.y + r.height - 1))
        pygame.draw.line(surface, (70, 50, 28), (r.x + r.width - 1, r.y), (r.x + r.width - 1, r.y + r.height - 1))


# ============================================================
# 子弹类
# ============================================================
class Bullet:
    def __init__(self, x, y, dx, dy, damage=1, color=YELLOW, owner='player', speed=7):
        self.x = float(x)
        self.y = float(y)
        self.damage = damage
        self.color = color
        self.owner = owner
        self.speed = speed
        self.size = 5 if owner == 'player' else 4
        self.alive = True
        self.piercing = False   # 穿透属性（激光枪）
        self.hit_set = set()    # 穿透子弹已命中目标
        mag = math.sqrt(dx * dx + dy * dy)
        if mag > 0:
            self.dx = (dx / mag) * speed
            self.dy = (dy / mag) * speed
        else:
            self.dx = speed
            self.dy = 0

    def update(self):
        self.x += self.dx
        self.y += self.dy
        if (self.x < -20 or self.x > SCREEN_WIDTH + 20 or
                self.y < -20 or self.y > SCREEN_HEIGHT + 20):
            self.alive = False

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        s = self.size
        if self.owner == 'player':
            # 玩家子弹 —— 带尾焰的能量弹
            # 尾焰（运动反方向）
            mag = math.sqrt(self.dx ** 2 + self.dy ** 2)
            if mag > 0:
                tx = ix - int(self.dx / mag * 6)
                ty = iy - int(self.dy / mag * 6)
                trail_s = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.line(trail_s, (*self.color, 80), (8, 8),
                                 (8 + tx - ix, 8 + ty - iy), 3)
                surface.blit(trail_s, (ix - 8, iy - 8))
            # 外层光晕
            glow = pygame.Surface((s * 3, s * 3), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*self.color, 50), (0, 0, s * 3, s * 3))
            surface.blit(glow, (ix - s * 3 // 2, iy - s * 3 // 2))
            # 弹体
            pygame.draw.rect(surface, self.color, (ix - s // 2, iy - s // 2, s, s))
            # 亮芯
            pygame.draw.rect(surface, WHITE, (ix - 1, iy - 1, 3, 3))
        else:
            # 敌人子弹 —— 红色危险弹
            glow = pygame.Surface((s * 3, s * 3), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*self.color, 40), (0, 0, s * 3, s * 3))
            surface.blit(glow, (ix - s * 3 // 2, iy - s * 3 // 2))
            pygame.draw.rect(surface, self.color, (ix - s // 2, iy - s // 2, s, s))
            if s >= 4:
                pygame.draw.rect(surface, (255, 200, 180), (ix - 1, iy - 1, 2, 2))

    def get_rect(self):
        s = self.size
        return pygame.Rect(int(self.x) - s // 2, int(self.y) - s // 2, s, s)


# ============================================================
# 近战攻击类
# ============================================================
class MeleeAttack:
    def __init__(self, x, y, width, height, damage, facing_right):
        self.rect = pygame.Rect(x, y, width, height)
        self.damage = damage
        self.max_timer = 14
        self.timer = self.max_timer
        self.alive = True
        self.facing_right = facing_right
        self.color = CYAN
        self.hit_enemies = set()
        self.hit_bullets = set()  # 已消除的子弹

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.alive = False

    def draw(self, surface):
        progress = 1.0 - (self.timer / self.max_timer)  # 0→1
        fade = self.timer / self.max_timer               # 1→0

        rx, ry = self.rect.x, self.rect.y
        rw, rh = self.rect.width, self.rect.height
        cx = rx + rw // 2   # 斩击弧心 X
        cy = ry              # 弧心 Y（顶部）
        radius = rh          # 弧半径

        # 弧形角度范围：从上向下挥 (由 start_angle 到 end_angle)
        if self.facing_right:
            arc_start = -80    # 从右上方
            arc_end = 80       # 到右下方
            arc_cx = rx + 2
        else:
            arc_start = 260    # 从左上方
            arc_end = 100      # 到左下方
            arc_cx = rx + rw - 2

        current_angle = arc_start + (arc_end - arc_start) * progress

        # ---- 弧形刀光拖尾 (多层半透明弧线) ----
        trail_steps = max(2, int(progress * 12))
        for i in range(trail_steps):
            t = i / max(trail_steps, 1)
            a = math.radians(arc_start + (current_angle - arc_start) * t)
            a_next = math.radians(arc_start + (current_angle - arc_start) * min(t + 1.0 / trail_steps, 1.0))

            # 外弧点
            x1 = arc_cx + int(math.cos(a) * radius)
            y1 = cy + rh // 2 + int(math.sin(a) * radius)
            x2 = arc_cx + int(math.cos(a_next) * radius)
            y2 = cy + rh // 2 + int(math.sin(a_next) * radius)

            # 内弧点 (短半径)
            inner_r = radius * 0.45
            x1i = arc_cx + int(math.cos(a) * inner_r)
            y1i = cy + rh // 2 + int(math.sin(a) * inner_r)
            x2i = arc_cx + int(math.cos(a_next) * inner_r)
            y2i = cy + rh // 2 + int(math.sin(a_next) * inner_r)

            trail_alpha = int(180 * fade * (0.3 + 0.7 * t))

            # 绘制梯形刀光片段
            pts = [(x1i, y1i), (x1, y1), (x2, y2), (x2i, y2i)]
            seg_surf = pygame.Surface((rw + 40, rh + 40), pygame.SRCALPHA)
            offset_x = max(0, rx - 20)
            offset_y = max(0, ry - 20)
            shifted = [(px - offset_x, py - offset_y) for px, py in pts]
            try:
                pygame.draw.polygon(seg_surf, (*self.color, trail_alpha // 2), shifted)
                pygame.draw.aalines(seg_surf, (*WHITE, trail_alpha), False,
                                    [(x1 - offset_x, y1 - offset_y), (x2 - offset_x, y2 - offset_y)])
            except (ValueError, TypeError):
                pass
            surface.blit(seg_surf, (offset_x, offset_y))

        # ---- 刀锋前端 (当前位置的亮弧线) ----
        if self.timer > 1:
            ca = math.radians(current_angle)
            tip_x = arc_cx + int(math.cos(ca) * radius)
            tip_y = cy + rh // 2 + int(math.sin(ca) * radius)
            tip_xi = arc_cx + int(math.cos(ca) * inner_r)
            tip_yi = cy + rh // 2 + int(math.sin(ca) * inner_r)
            # 粗亮线
            pygame.draw.line(surface, WHITE, (tip_xi, tip_yi), (tip_x, tip_y), 3)
            pygame.draw.line(surface, self.color, (tip_xi, tip_yi), (tip_x, tip_y), 1)
            # 刀尖火花
            spark = max(2, int(4 * fade))
            pygame.draw.rect(surface, WHITE,
                             (tip_x - spark // 2, tip_y - spark // 2, spark, spark))


# ============================================================
# 激光类 —— 从玩家位置射出一条直线激光，对线上所有敌人造成伤害
# ============================================================
class LaserBeam:
    def __init__(self, x, y, dx, dy, damage, max_range=1200):
        self.start_x = float(x)
        self.start_y = float(y)
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.max_range = max_range
        # 计算终点
        self.end_x = self.start_x + dx * max_range
        self.end_y = self.start_y + dy * max_range
        # 限制在屏幕范围内
        self._clip_to_screen()
        self.timer = 12          # 激光持续帧数
        self.max_timer = 12
        self.alive = True
        self.hit_enemies = set()  # 已命中的敌人
        self.width = 6            # 碰撞宽度

    def _clip_to_screen(self):
        """Clip终点到屏幕边缘"""
        # 沿射线方向找最先碰到的屏幕边界
        t_min = self.max_range
        if self.dx > 0:
            t = (SCREEN_WIDTH + 20 - self.start_x) / self.dx
            t_min = min(t_min, t)
        elif self.dx < 0:
            t = (-20 - self.start_x) / self.dx
            t_min = min(t_min, t)
        if self.dy > 0:
            t = (SCREEN_HEIGHT + 20 - self.start_y) / self.dy
            t_min = min(t_min, t)
        elif self.dy < 0:
            t = (-20 - self.start_y) / self.dy
            t_min = min(t_min, t)
        t_min = max(0, t_min)
        self.end_x = self.start_x + self.dx * t_min
        self.end_y = self.start_y + self.dy * t_min

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.alive = False

    def get_line_rect(self):
        """Return bounding rect for broad-phase collision"""
        x1, y1 = int(self.start_x), int(self.start_y)
        x2, y2 = int(self.end_x), int(self.end_y)
        lx = min(x1, x2) - self.width
        ly = min(y1, y2) - self.width
        rw = abs(x2 - x1) + self.width * 2
        rh = abs(y2 - y1) + self.width * 2
        return pygame.Rect(lx, ly, rw, rh)

    def hits_rect(self, rect):
        """Check if laser line intersects a rect (line-AABB test)"""
        # 简化：将rect扩张width像素，检测点到线段距离
        cx = rect.centerx
        cy = rect.centery
        # 投影点到线段
        lx = self.end_x - self.start_x
        ly = self.end_y - self.start_y
        l2 = lx * lx + ly * ly
        if l2 < 1:
            return False
        t = max(0, min(1, ((cx - self.start_x) * lx + (cy - self.start_y) * ly) / l2))
        px = self.start_x + t * lx
        py = self.start_y + t * ly
        # 检测投影点是否在扩张后的rect内
        half_w = rect.width / 2 + self.width
        half_h = rect.height / 2 + self.width
        return abs(px - cx) <= half_w and abs(py - cy) <= half_h

    def draw(self, surface):
        fade = self.timer / self.max_timer  # 1→0
        ix1, iy1 = int(self.start_x), int(self.start_y)
        ix2, iy2 = int(self.end_x), int(self.end_y)

        # 外层光晕（宽带半透明）
        glow_w = int(16 * fade)
        if glow_w > 2:
            gs = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(gs, (0, 200, 255, int(30 * fade)), (ix1, iy1), (ix2, iy2), glow_w)
            surface.blit(gs, (0, 0))

        # 中层激光（亮青色）
        mid_w = max(2, int(6 * fade))
        pygame.draw.line(surface, (50, 220, 255), (ix1, iy1), (ix2, iy2), mid_w)

        # 核心亮线（白色）
        core_w = max(1, int(3 * fade))
        pygame.draw.line(surface, WHITE, (ix1, iy1), (ix2, iy2), core_w)

        # 射出点火花
        if self.timer > 5:
            spark = int(5 * fade)
            pygame.draw.circle(surface, WHITE, (ix1, iy1), spark)
            pygame.draw.circle(surface, CYAN, (ix1, iy1), max(1, spark - 1))

        # 末端击中火花
        if self.timer > 3:
            spark2 = int(4 * fade)
            pygame.draw.circle(surface, (100, 220, 255), (ix2, iy2), spark2)
            pygame.draw.circle(surface, WHITE, (ix2, iy2), max(1, spark2 - 1))


# ============================================================
# 道具类 —— 支持 health / shield / power_up
# ============================================================
class Item:
    ITEM_INFO = {
        'health':   {'color': LIGHT_GREEN, 'name': '血包'},
        'shield':   {'color': (100, 180, 255), 'name': '护盾'},
        'power_up': {'color': (255, 80, 80), 'name': '增伤'},
    }

    def __init__(self, x, y, item_type='health'):
        self.x = float(x)
        self.y = float(y)
        self.item_type = item_type
        self.size = 14
        self.alive = True
        self.show_name_timer = 90
        self.vy = 0.0
        self.on_ground = False
        info = self.ITEM_INFO.get(item_type, self.ITEM_INFO['health'])
        self.color = info['color']
        self.name = info['name']

    def update(self, ground_y, platforms):
        if not self.on_ground:
            self.vy += 0.5
            self.y += self.vy
            if self.y + self.size >= ground_y:
                self.y = ground_y - self.size
                self.on_ground = True
                self.vy = 0
            for p in platforms:
                if (self.vy > 0 and
                        self.y + self.size >= p.rect.y and
                        self.y + self.size <= p.rect.y + 15 and
                        self.x + self.size > p.rect.x and
                        self.x < p.rect.x + p.rect.width):
                    self.y = p.rect.y - self.size
                    self.on_ground = True
                    self.vy = 0
        if self.show_name_timer > 0:
            self.show_name_timer -= 1

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        # 浮动光晕
        glow = pygame.Surface((22, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (*self.color, 35), (0, 0, 22, 22))
        surface.blit(glow, (ix - 4, iy - 4))

        if self.item_type == 'health':
            # 精致红十字血包
            pygame.draw.rect(surface, (220, 220, 220), (ix, iy, 14, 14))  # 底色
            pygame.draw.rect(surface, (200, 40, 40), (ix + 1, iy + 1, 12, 12))  # 红底
            # 十字
            pygame.draw.rect(surface, WHITE, (ix + 5, iy + 2, 4, 10))
            pygame.draw.rect(surface, WHITE, (ix + 2, iy + 5, 10, 4))
            # 十字高光
            pygame.draw.rect(surface, (255, 230, 230), (ix + 5, iy + 2, 4, 1))
            pygame.draw.rect(surface, (255, 230, 230), (ix + 2, iy + 5, 1, 4))
            # 边框
            pygame.draw.rect(surface, WHITE, (ix, iy, 14, 14), 1)
            # 角落高光
            pygame.draw.rect(surface, (255, 255, 255), (ix + 1, iy + 1, 2, 1))

        elif self.item_type == 'shield':
            # 精致蓝色盾牌
            pygame.draw.rect(surface, (200, 220, 240), (ix, iy, 14, 14))
            pygame.draw.rect(surface, self.color, (ix + 1, iy + 1, 12, 12))
            # 盾牌形状
            pts = [(ix + 7, iy + 2), (ix + 12, iy + 5),
                   (ix + 7, iy + 12), (ix + 2, iy + 5)]
            pygame.draw.polygon(surface, (180, 215, 255), pts)
            # 盾牌高光
            pygame.draw.polygon(surface, (220, 240, 255),
                                [(ix + 7, iy + 2), (ix + 9, iy + 4),
                                 (ix + 7, iy + 8), (ix + 4, iy + 4)])
            pygame.draw.polygon(surface, WHITE, pts, 1)
            # 中心标记
            pygame.draw.rect(surface, WHITE, (ix + 6, iy + 5, 2, 4))
            pygame.draw.rect(surface, WHITE, (ix, iy, 14, 14), 1)

        elif self.item_type == 'power_up':
            # 精致闪电增伤
            pygame.draw.rect(surface, (60, 10, 10), (ix, iy, 14, 14))
            pygame.draw.rect(surface, self.color, (ix + 1, iy + 1, 12, 12))
            # 闪电
            pts = [(ix + 8, iy + 2), (ix + 4, iy + 7),
                   (ix + 7, iy + 7), (ix + 5, iy + 12),
                   (ix + 10, iy + 6), (ix + 7, iy + 6)]
            pygame.draw.polygon(surface, YELLOW, pts)
            pygame.draw.polygon(surface, (255, 255, 200), pts, 1)  # 闪电边缘光
            # 内部亮线
            pygame.draw.line(surface, WHITE, (ix + 7, iy + 3), (ix + 6, iy + 6))
            pygame.draw.rect(surface, (255, 120, 120), (ix, iy, 14, 14), 1)

        if self.show_name_timer > 0 and font_tiny:
            # 名称带半透明背景
            text = font_tiny.render(self.name, False, WHITE)
            tw = text.get_width()
            bg = pygame.Surface((tw + 4, 14), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 100))
            surface.blit(bg, (ix - 4, iy - 18))
            surface.blit(text, (ix - 2, iy - 16))

    def get_rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)


# ============================================================
# 地刺类 —— 放置在地面或平台上，踩到掉血
# ============================================================
class Spike:
    def __init__(self, x, y, width=30):
        self.x = x
        self.y = y
        self.width = width
        self.height = 10
        self.rect = pygame.Rect(x, y, width, self.height)
        self.damage_cooldown = 0
        self.color = (180, 180, 180)

    def update(self):
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

    def draw(self, surface):
        spike_count = self.width // 10
        # 底座
        pygame.draw.rect(surface, (100, 100, 110), (self.x, self.y + self.height - 3, self.width, 3))
        pygame.draw.line(surface, (130, 130, 140), (self.x, self.y + self.height - 3),
                         (self.x + self.width, self.y + self.height - 3))
        for i in range(spike_count):
            bx = self.x + i * 10
            pts = [(bx, self.y + self.height - 2),
                   (bx + 5, self.y),
                   (bx + 10, self.y + self.height - 2)]
            # 尖刺暗面（右半）
            dark_pts = [(bx + 5, self.y), (bx + 10, self.y + self.height - 2),
                        (bx + 5, self.y + self.height - 2)]
            pygame.draw.polygon(surface, (140, 140, 150), pts)  # 亮面
            pygame.draw.polygon(surface, (100, 100, 110), dark_pts)  # 暗面
            # 尖端高光
            pygame.draw.line(surface, (240, 240, 255), (bx + 5, self.y), (bx + 5, self.y + 3))
            # 边缘线
            pygame.draw.polygon(surface, (180, 180, 195), pts, 1)
        # 危险警示 —— 尖刺处微红光
        if self.damage_cooldown <= 0:
            warn = pygame.Surface((self.width + 4, self.height + 4), pygame.SRCALPHA)
            pygame.draw.ellipse(warn, (255, 60, 60, 20), (0, 0, self.width + 4, self.height + 4))
            surface.blit(warn, (self.x - 2, self.y - 2))

    def check_damage(self, player_rect):
        """检测玩家是否踩到地刺"""
        if self.damage_cooldown > 0:
            return False
        if player_rect.colliderect(self.rect):
            if player_rect.bottom >= self.y and player_rect.bottom <= self.y + self.height + 8:
                self.damage_cooldown = 40
                return True
        return False


# ============================================================
# 道具箱类 —— 可被攻击破坏，掉落随机道具
# ============================================================
class ItemBox:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 22
        self.height = 22
        self.hp = 2
        self.alive = True
        self.flash_timer = 0

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def take_damage(self, damage=1):
        self.hp -= damage
        self.flash_timer = 6
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def update(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surface):
        if not self.alive:
            return
        x, y = self.x, self.y
        w, h = self.width, self.height
        flash = self.flash_timer > 0 and self.flash_timer % 2 == 0

        # 木箱主体
        body_color = WHITE if flash else (170, 120, 55)
        pygame.draw.rect(surface, body_color, (x, y, w, h))

        if not flash:
            # 木纹横线
            for ly in range(y + 4, y + h - 2, 5):
                pygame.draw.line(surface, (145, 100, 42), (x + 2, ly), (x + w - 2, ly))
            # 木板竖纹（中间分割）
            pygame.draw.line(surface, (130, 88, 35), (x + w // 2, y + 1), (x + w // 2, y + h - 1))
            # 顶部高光
            pygame.draw.line(surface, (210, 170, 90), (x + 1, y + 1), (x + w - 2, y + 1))
            # 左侧高光
            pygame.draw.line(surface, (195, 155, 75), (x + 1, y + 1), (x + 1, y + h - 2))
            # 右侧暗部
            pygame.draw.line(surface, (110, 70, 25), (x + w - 1, y + 1), (x + w - 1, y + h - 1))
            # 底部暗部
            pygame.draw.line(surface, (100, 65, 22), (x + 1, y + h - 1), (x + w - 1, y + h - 1))

        # 金属边框
        pygame.draw.rect(surface, (100, 75, 25), (x, y, w, h), 2)

        # 四角金属铆钉
        for cx, cy in [(x + 3, y + 3), (x + w - 4, y + 3),
                        (x + 3, y + h - 4), (x + w - 4, y + h - 4)]:
            pygame.draw.rect(surface, (160, 150, 130), (cx, cy, 2, 2))

        # 中心锁扣
        pygame.draw.rect(surface, GOLD, (x + w // 2 - 3, y + h // 2 - 3, 6, 6))
        pygame.draw.rect(surface, (255, 220, 100), (x + w // 2 - 2, y + h // 2 - 2, 4, 4))
        pygame.draw.rect(surface, (180, 140, 30), (x + w // 2 - 3, y + h // 2 - 3, 6, 6), 1)
        # 锁孔
        pygame.draw.rect(surface, (80, 55, 15), (x + w // 2 - 1, y + h // 2, 2, 2))


# ============================================================
# 斩击旋风 (恐虐技能)
# ============================================================
class SpinAttack:
    """以Boss为中心的圆形AOE旋转斩"""
    def __init__(self, cx, cy, damage=2, radius=80, duration=20):
        self.cx = cx
        self.cy = cy
        self.damage = damage
        self.radius = radius
        self.timer = duration
        self.max_timer = duration
        self.alive = True
        self.angle = 0.0
        self.hit_player = False

    def update(self):
        self.timer -= 1
        self.angle += 0.3
        if self.timer <= 0:
            self.alive = False

    def hits_rect(self, rect):
        closest_x = max(rect.x, min(self.cx, rect.x + rect.width))
        closest_y = max(rect.y, min(self.cy, rect.y + rect.height))
        dx = self.cx - closest_x
        dy = self.cy - closest_y
        return (dx * dx + dy * dy) <= self.radius * self.radius

    def draw(self, surface):
        cx, cy = int(self.cx), int(self.cy)
        progress = 1.0 - self.timer / self.max_timer
        r = int(self.radius * (0.5 + 0.5 * progress))
        glow = pygame.Surface((r * 2 + 20, r * 2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 40, 20, 30), (r + 10, r + 10), r + 8)
        surface.blit(glow, (cx - r - 10, cy - r - 10))
        for i in range(4):
            a = self.angle + i * math.pi / 2
            x1 = cx + int(math.cos(a) * r * 0.3)
            y1 = cy + int(math.sin(a) * r * 0.3)
            x2 = cx + int(math.cos(a) * r)
            y2 = cy + int(math.sin(a) * r)
            pygame.draw.line(surface, (255, 80, 40), (x1, y1), (x2, y2), 3)
            pygame.draw.line(surface, (255, 200, 100), (x1, y1), (x2, y2), 1)
        pygame.draw.circle(surface, (255, 60, 20), (cx, cy), 8)
        pygame.draw.circle(surface, (255, 180, 60), (cx, cy), 4)


# ============================================================
# 血祭标记 / 地面之手 (恐虐技能)
# ============================================================
class GroundHand:
    """在目标位置延迟后从地面冒出红色巨手"""
    def __init__(self, target_x, ground_y, damage=2, warn_duration=30, attack_duration=25):
        self.x = target_x
        self.ground_y = ground_y
        self.damage = damage
        self.warn_duration = warn_duration
        self.attack_duration = attack_duration
        self.timer = 0
        self.alive = True
        self.hit_player = False
        self.width = 30
        self.height = 50

    @property
    def phase(self):
        if self.timer < self.warn_duration:
            return 'warn'
        return 'attack'

    @property
    def attack_progress(self):
        if self.phase == 'warn':
            return 0
        elapsed = self.timer - self.warn_duration
        return min(1.0, elapsed / 10.0)

    def update(self):
        self.timer += 1
        total = self.warn_duration + self.attack_duration
        if self.timer >= total:
            self.alive = False

    def get_rect(self):
        if self.phase == 'attack' and self.attack_progress >= 0.8:
            hand_y = self.ground_y - int(self.height * self.attack_progress)
            return pygame.Rect(int(self.x) - self.width // 2, hand_y, self.width, self.height)
        return None

    def draw(self, surface):
        x = int(self.x)
        gy = self.ground_y
        if self.phase == 'warn':
            alpha = 80 + int(60 * abs(math.sin(self.timer * 0.3)))
            mark = pygame.Surface((40, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(mark, (255, 30, 20, alpha), (0, 0, 40, 12))
            surface.blit(mark, (x - 20, gy - 6))
            if self.timer > self.warn_duration * 0.6:
                pygame.draw.line(surface, (180, 20, 10), (x - 5, gy - 2), (x + 5, gy + 2), 2)
                pygame.draw.line(surface, (180, 20, 10), (x + 3, gy - 3), (x - 3, gy + 1), 1)
        else:
            prog = self.attack_progress
            h = int(self.height * prog)
            if h < 4:
                return
            hand_y = gy - h
            hw = self.width
            pygame.draw.rect(surface, (160, 25, 20), (x - hw // 2 + 4, hand_y + 15, hw - 8, h - 15))
            pygame.draw.rect(surface, (120, 15, 10), (x - hw // 2 + 6, hand_y + 18, hw - 12, h - 20))
            pygame.draw.rect(surface, (200, 35, 25), (x - hw // 2, hand_y, hw, 18))
            pygame.draw.rect(surface, (160, 25, 15), (x - hw // 2 + 2, hand_y + 2, hw - 4, 14))
            for i in range(3):
                fx = x - 8 + i * 8
                pygame.draw.rect(surface, (220, 40, 30), (fx, hand_y - 6, 5, 8))
                pygame.draw.rect(surface, (255, 80, 50), (fx + 1, hand_y - 6, 3, 3))
            pygame.draw.ellipse(surface, (100, 15, 10), (x - 18, gy - 5, 36, 10))
            pygame.draw.ellipse(surface, (60, 8, 5), (x - 14, gy - 3, 28, 6))


# ============================================================
# 腐朽吐息 / 毒雾 (纳垢技能)
# ============================================================
class PoisonCloud:
    """向前喷射的毒雾区域"""
    def __init__(self, x, y, direction, ground_y, damage=1, duration=35):
        self.x = x
        self.y = y
        self.direction = direction
        self.ground_y = ground_y
        self.damage = damage
        self.timer = duration
        self.max_timer = duration
        self.alive = True
        self.width = 220
        self.height = 120
        self.hit_timer = 0

    def update(self):
        self.timer -= 1
        self.hit_timer = max(0, self.hit_timer - 1)
        self.x += self.direction * 2.5
        if self.timer <= 0:
            self.alive = False

    def get_rect(self):
        if self.direction > 0:
            return pygame.Rect(int(self.x), int(self.y) - self.height // 2, self.width, self.height)
        else:
            return pygame.Rect(int(self.x) - self.width, int(self.y) - self.height // 2, self.width, self.height)

    def can_hit(self):
        if self.hit_timer <= 0:
            self.hit_timer = 15
            return True
        return False

    def draw(self, surface):
        rect = self.get_rect()
        progress = self.timer / self.max_timer
        base_alpha = int(60 * progress)
        cloud = pygame.Surface((rect.width + 20, rect.height + 20), pygame.SRCALPHA)
        for i in range(5):
            cx = 10 + random.randint(0, rect.width - 10)
            cy = 10 + random.randint(0, rect.height - 10)
            r = random.randint(15, 30)
            a = max(10, base_alpha + random.randint(-15, 15))
            pygame.draw.circle(cloud, (40, 180, 30, a), (cx, cy), r)
        for i in range(3):
            cx = 10 + random.randint(10, max(11, rect.width - 20))
            cy = 10 + random.randint(5, max(6, rect.height - 10))
            r = random.randint(6, 12)
            pygame.draw.circle(cloud, (100, 255, 60, max(10, base_alpha - 10)), (cx, cy), r)
        surface.blit(cloud, (rect.x - 10, rect.y - 10))


# ============================================================
# 毒池 (纳垢技能 - 持续伤害区域)
# ============================================================
class PoisonPool:
    """地面上的持续伤害毒池"""
    def __init__(self, x, ground_y, width=80, duration=180):
        self.x = x
        self.ground_y = ground_y
        self.width = width
        self.height = 10
        self.timer = duration
        self.max_timer = duration
        self.alive = True
        self.hit_timer = 0
        self.damage = 1
        self.bubble_timer = 0

    def update(self):
        self.timer -= 1
        self.hit_timer = max(0, self.hit_timer - 1)
        self.bubble_timer += 1
        if self.timer <= 0:
            self.alive = False

    def get_rect(self):
        return pygame.Rect(int(self.x) - self.width // 2, self.ground_y - self.height,
                           self.width, self.height + 4)

    def can_hit(self):
        if self.hit_timer <= 0:
            self.hit_timer = 30
            return True
        return False

    def draw(self, surface):
        x = int(self.x) - self.width // 2
        gy = self.ground_y
        progress = self.timer / self.max_timer
        alpha = int(120 * progress)
        pool = pygame.Surface((self.width + 10, 16), pygame.SRCALPHA)
        pygame.draw.ellipse(pool, (30, 160, 20, alpha), (0, 2, self.width + 10, 12))
        pygame.draw.ellipse(pool, (60, 200, 40, max(10, alpha - 30)), (5, 4, self.width, 8))
        pygame.draw.ellipse(pool, (100, 255, 60, max(10, alpha // 2)), (15, 5, self.width - 20, 4))
        surface.blit(pool, (x - 5, gy - 10))
        if self.bubble_timer % 20 < 10 and progress > 0.2:
            bx = x + random.randint(5, max(6, self.width - 5))
            pygame.draw.circle(surface, (80, 220, 50), (bx, gy - 8), 2)


# ============================================================
# 受击粒子特效
# ============================================================
class HitParticle:
    """敌人被击中时飞溅的粒子"""
    def __init__(self, x, y, color, count=6):
        self.particles = []
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(1.5, 4.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 1.5  # 略微向上偏移
            size = random.randint(2, 4)
            # 颜色加亮
            r = min(255, color[0] + random.randint(40, 100))
            g = min(255, color[1] + random.randint(40, 100))
            b = min(255, color[2] + random.randint(40, 100))
            life = random.randint(8, 16)
            self.particles.append([x, y, vx, vy, size, (r, g, b), life, life])
        self.alive = True

    def update(self):
        alive_any = False
        for p in self.particles:
            p[0] += p[2]       # x += vx
            p[1] += p[3]       # y += vy
            p[3] += 0.15       # 重力
            p[2] *= 0.95       # 摩擦
            p[6] -= 1          # life -= 1
            if p[6] > 0:
                alive_any = True
        self.alive = alive_any

    def draw(self, surface):
        for p in self.particles:
            if p[6] <= 0:
                continue
            progress = p[6] / p[7]  # 剩余生命比例
            alpha = int(255 * progress)
            size = max(1, int(p[4] * progress))
            x, y = int(p[0]), int(p[1])
            # 核心亮点
            ps = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            col = p[5]
            pygame.draw.rect(ps, (*col, alpha), (1, 1, size * 2, size * 2))
            # 中心高亮
            if size >= 2:
                pygame.draw.rect(ps, (255, 255, 255, min(255, alpha + 30)),
                                 (size // 2 + 1, size // 2 + 1, size, size))
            surface.blit(ps, (x - size - 1, y - size - 1))
