"""
玩家模块 - 鼠标瞄准射击 + WASD/方向键 移动
"""
import pygame
import math
import random
from constants import *
from objects import Bullet, MeleeAttack, LaserBeam
from utils import play_sound

# ============================================================
# 升级项池定义
# ============================================================
UPGRADE_POOL = {
    'bullet_damage': {'name': '子弹威力+', 'desc': '子弹伤害+1', 'max_level': 3,
                      'icon_color': ORANGE},
    'max_hp_up':     {'name': '生命上限+', 'desc': '最大HP+1，回夁1HP', 'max_level': 5,
                      'icon_color': LIGHT_GREEN},
    'shotgun':       {'name': '霸弹枪', 'desc': '解锁武器：一次发射5颗5散子弹', 'max_level': 1,
                      'icon_color': YELLOW},
    'laser':         {'name': '激光枪', 'desc': '解锁武器：穿透子弹，命中不消失', 'max_level': 1,
                      'icon_color': CYAN},
    'melee_reflect': {'name': '近战反弹', 'desc': '挥刀反弹敌人子弹而非消除', 'max_level': 1,
                      'icon_color': LIGHT_BLUE},
    'trap_immune':   {'name': '陷阱免疫', 'desc': '地刺不再造成伤害', 'max_level': 1,
                      'icon_color': GRAY},
    'kill_heal':     {'name': '击杀回血', 'desc': '击杀敌人+15%概率回1HP', 'max_level': 4,
                      'icon_color': RED},
    'auto_shield':   {'name': '自动护盾', 'desc': '每隔一段时间自动获得1层护盾', 'max_level': 3,
                      'icon_color': LIGHT_BLUE},
}


class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = 80.0
        self.y = 400.0
        self.width = 24
        self.height = 36
        self.vx = 0.0
        self.vy = 0.0
        self.speed = 4.0
        self.jump_power = -11.0
        self.on_ground = False
        self.facing_right = True
        self.max_hp = 5
        self.hp = self.max_hp
        self.kills = 0
        self.xp = 0
        self.level = 1
        self.weapon = 'gun'
        self.shoot_cooldown = 0
        self.melee_cooldown = 0
        self.bullet_speed = 7.0
        self.bullet_damage = 1
        self.sword_damage = 2
        self.sword_range = 55
        self.invincible = 0
        self.levelup_timer = 0
        self.swing_timer = 0
        self.shield = 0
        self.power_up_timer = 0
        self.power_up_mult = 1.5
        # ---- 升级选择系统 ----
        self.upgrades = {}           # 已选升级及等级
        self.pending_levelup = False # 是否有待选升级
        self.kill_heal_chance = 0.0  # 击杀回血概率
        self.trap_immune = False     # 陷阱免疫
        self.melee_reflect = False   # 近战反弹
        self.auto_shield_interval = 0  # 自动护盾间隔帧数 (0=未解锁)
        self.auto_shield_timer = 0     # 自动护盾计时器
        self.has_shotgun = False
        self.has_laser = False
        self.laser_fire_timer = 0  # 激光发射动画计时

    def update(self, ground_y, platforms, right_limit=None):
        """更新玩家状态 —— 内部直接读取键盘状态，不依赖外部传参
        right_limit: 玩家x坐标最大值，None时为 SCREEN_WIDTH - self.width
        """
        if right_limit is None:
            right_limit = SCREEN_WIDTH - self.width

        # ---- 直接从 pygame 获取当前帧按键快照 ----
        keys = pygame.key.get_pressed()

        # ---- 水平移动：A / D 键 ----
        self.vx = 0.0
        if keys[pygame.K_a]:
            self.vx = -self.speed
        if keys[pygame.K_d]:
            self.vx = self.speed

        # ---- 朝向跟随鼠标光标 ----
        mouse_x, _ = pygame.mouse.get_pos()
        center_x = self.x + self.width / 2
        if mouse_x > center_x:
            self.facing_right = True
        elif mouse_x < center_x:
            self.facing_right = False

        # 是否按下 S 穿过平台
        dropping = keys[pygame.K_s]

        # ---- 应用重力 ----
        self.vy += 0.6

        # ---- 更新位置 ----
        self.x += self.vx
        self.x = max(0, min(right_limit, self.x))
        self.y += self.vy
        self.on_ground = False

        # 地面碰撞
        if self.y + self.height >= ground_y:
            self.y = ground_y - self.height
            self.vy = 0
            self.on_ground = True

        # 平台碰撞
        if not dropping:
            for p in platforms:
                if (self.vy >= 0 and
                        self.y + self.height >= p.rect.y and
                        self.y + self.height <= p.rect.y + 14 and
                        self.x + self.width > p.rect.x + 4 and
                        self.x < p.rect.x + p.rect.width - 4):
                    self.y = p.rect.y - self.height
                    self.vy = 0
                    self.on_ground = True

        # ---- 更新冷却计时器 ----
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.levelup_timer > 0:
            self.levelup_timer -= 1
        if self.swing_timer > 0:
            self.swing_timer -= 1
        if self.laser_fire_timer > 0:
            self.laser_fire_timer -= 1
        if self.power_up_timer > 0:
            self.power_up_timer -= 1
        # 自动护盾计时
        if self.auto_shield_interval > 0:
            self.auto_shield_timer += 1
            if self.auto_shield_timer >= self.auto_shield_interval:
                self.auto_shield_timer = 0
                if self.shield < 5:
                    self.shield += 1

    def jump(self):
        """跳跃"""
        if self.on_ground:
            self.vy = self.jump_power
            self.on_ground = False

    def shoot(self, mouse_x, mouse_y):
        """射击/攻击 —— 子弹朝鼠标光标方向飞"""
        from utils import snd_shoot, snd_melee

        cx = self.x + self.width / 2
        cy = self.y + self.height / 3

        if self.weapon == 'gun' and self.shoot_cooldown <= 0:
            self.shoot_cooldown = 12
            dx = mouse_x - cx
            dy = mouse_y - cy
            mag = math.sqrt(dx * dx + dy * dy)
            if mag < 1:
                dx = 1 if self.facing_right else -1
                dy = 0
            else:
                dx /= mag
                dy /= mag
            play_sound(snd_shoot)
            return Bullet(cx, cy, dx, dy, self._calc_bullet_damage(), YELLOW,
                          'player', self.bullet_speed)

        elif self.weapon == 'shotgun' and self.has_shotgun and self.shoot_cooldown <= 0:
            self.shoot_cooldown = 22
            dx = mouse_x - cx
            dy = mouse_y - cy
            mag = math.sqrt(dx * dx + dy * dy)
            if mag < 1:
                dx = 1 if self.facing_right else -1
                dy = 0
            else:
                dx /= mag
                dy /= mag
            base_angle = math.atan2(dy, dx)
            play_sound(snd_shoot)
            bullets = []
            for i in range(5):
                spread = (i - 2) * 0.15  # -0.30 ~ +0.30 rad
                a = base_angle + spread
                bdx = math.cos(a)
                bdy = math.sin(a)
                bullets.append(Bullet(cx, cy, bdx, bdy, self._calc_bullet_damage(),
                                      ORANGE, 'player', self.bullet_speed * 0.9))
            return bullets

        elif self.weapon == 'laser' and self.has_laser and self.shoot_cooldown <= 0:
            self.shoot_cooldown = 25
            dx = mouse_x - cx
            dy = mouse_y - cy
            mag = math.sqrt(dx * dx + dy * dy)
            if mag < 1:
                dx = 1 if self.facing_right else -1
                dy = 0
            else:
                dx /= mag
                dy /= mag
            play_sound(snd_shoot)
            self.laser_fire_timer = 8  # 激光发射动画计时
            return LaserBeam(cx, cy, dx, dy, self._calc_bullet_damage() + 1)

        elif self.weapon == 'sword' and self.melee_cooldown <= 0:
            self.melee_cooldown = 20
            self.swing_timer = 14  # 挥刀动画持续帧数
            if self.facing_right:
                ax = self.x + self.width
            else:
                ax = self.x - self.sword_range
            ay = self.y - 10
            play_sound(snd_melee)
            return MeleeAttack(int(ax), int(ay), self.sword_range, self.height + 20,
                               self._calc_sword_damage(), self.facing_right)

        return None

    def _calc_bullet_damage(self):
        """计算子弹伤害（含增伤buff）"""
        d = self.bullet_damage
        if self.power_up_timer > 0:
            d = int(d * self.power_up_mult)
        return max(1, d)

    def _calc_sword_damage(self):
        """计算近战伤害（含增伤buff）"""
        d = self.sword_damage
        if self.power_up_timer > 0:
            d = int(d * self.power_up_mult)
        return max(1, d)

    def take_damage(self, damage):
        """受到伤害"""
        from utils import snd_hit
        if self.invincible > 0:
            return False
        # 护盾挡伤害
        if self.shield > 0:
            self.shield -= 1
            self.invincible = 30
            return False
        self.hp -= damage
        self.invincible = 60
        play_sound(snd_hit)
        if self.hp <= 0:
            self.hp = 0
            return True
        return False

    def gain_xp(self, amount):
        """获得经验值"""
        from utils import snd_levelup
        self.xp += amount
        new_level = self.xp // 100 + 1
        if new_level > self.level:
            self.level = new_level
            self.levelup_timer = 60
            self.pending_levelup = True
            play_sound(snd_levelup)

    def get_upgrade_options(self):
        """从池中随机抽3个可用升级（未满级的）"""
        available = []
        for uid, info in UPGRADE_POOL.items():
            cur = self.upgrades.get(uid, 0)
            if cur < info['max_level']:
                available.append(uid)
        if len(available) <= 3:
            return available
        return random.sample(available, 3)

    def apply_upgrade(self, upgrade_id):
        """应用选择的升级"""
        cur = self.upgrades.get(upgrade_id, 0)
        self.upgrades[upgrade_id] = cur + 1
        self.pending_levelup = False

        if upgrade_id == 'bullet_damage':
            self.bullet_damage += 1
        elif upgrade_id == 'max_hp_up':
            self.max_hp += 1
            self.hp = min(self.hp + 1, self.max_hp)
        elif upgrade_id == 'shotgun':
            self.has_shotgun = True
        elif upgrade_id == 'laser':
            self.has_laser = True
        elif upgrade_id == 'melee_reflect':
            self.melee_reflect = True
        elif upgrade_id == 'trap_immune':
            self.trap_immune = True
        elif upgrade_id == 'kill_heal':
            self.kill_heal_chance = min(0.60, self.kill_heal_chance + 0.15)
        elif upgrade_id == 'auto_shield':
            lvl = self.upgrades['auto_shield']
            intervals = {1: 900, 2: 720, 3: 600}  # 15s/12s/10s
            self.auto_shield_interval = intervals.get(lvl, 600)
            self.auto_shield_timer = 0

    def heal(self, amount):
        """恢复生命值"""
        self.hp = min(self.hp + amount, self.max_hp)

    def draw(self, surface):
        """绘制玩家 —— 精致像素风战士"""
        if self.invincible > 0 and (self.invincible // 3) % 2 == 0:
            return
        x, y = int(self.x), int(self.y)

        # ---- 头发 + 头巾 ----
        pygame.draw.rect(surface, (180, 50, 50), (x + 5, y - 3, 14, 3))   # 红色头巾
        pygame.draw.rect(surface, (140, 35, 35), (x + 5, y - 1, 14, 1))   # 头巾暗部
        pygame.draw.rect(surface, BROWN, (x + 6, y - 5, 12, 4))           # 头发
        pygame.draw.rect(surface, (100, 60, 30), (x + 7, y - 5, 4, 2))    # 头发高光

        # ---- 头部 ----
        pygame.draw.rect(surface, SKIN, (x + 6, y + 0, 12, 11))           # 脸
        pygame.draw.rect(surface, (220, 175, 130), (x + 6, y + 8, 12, 3)) # 下巴阴影
        # 眼睛（带眼白和瞳孔）
        if self.facing_right:
            pygame.draw.rect(surface, WHITE, (x + 13, y + 3, 4, 3))
            pygame.draw.rect(surface, (30, 30, 80), (x + 15, y + 3, 2, 3))
            pygame.draw.rect(surface, WHITE, (x + 16, y + 3, 1, 1))  # 眼光
        else:
            pygame.draw.rect(surface, WHITE, (x + 7, y + 3, 4, 3))
            pygame.draw.rect(surface, (30, 30, 80), (x + 7, y + 3, 2, 3))
            pygame.draw.rect(surface, WHITE, (x + 7, y + 3, 1, 1))

        # ---- 身体 (迷彩军装) ----
        pygame.draw.rect(surface, (60, 85, 60), (x + 4, y + 11, 16, 13))    # 军绿主色
        pygame.draw.rect(surface, (45, 70, 45), (x + 6, y + 13, 5, 4))      # 迷彩暗斑
        pygame.draw.rect(surface, (45, 70, 45), (x + 13, y + 15, 4, 3))     # 迷彩暗斑
        pygame.draw.rect(surface, (75, 100, 70), (x + 9, y + 11, 6, 3))     # 胸口亮斑
        # 肩甲
        pygame.draw.rect(surface, (80, 80, 90), (x + 2, y + 11, 4, 4))
        pygame.draw.rect(surface, (100, 100, 110), (x + 2, y + 11, 4, 2))  # 肩甲高光
        pygame.draw.rect(surface, (80, 80, 90), (x + 18, y + 11, 4, 4))
        pygame.draw.rect(surface, (100, 100, 110), (x + 18, y + 11, 4, 2))
        # 腰带
        pygame.draw.rect(surface, (90, 70, 40), (x + 4, y + 22, 16, 2))
        pygame.draw.rect(surface, GOLD, (x + 10, y + 22, 4, 2))            # 腰带扣

        # ---- 手臂 & 武器 ----
        swinging = self.swing_timer > 0
        if swinging:
            swing_progress = 1.0 - (self.swing_timer / 14.0)
            angle_start = -70
            angle_end = 130
            angle = math.radians(angle_start + (angle_end - angle_start) * swing_progress)
            if self.facing_right:
                shoulder_x = x + 20
                shoulder_y = y + 12
                pygame.draw.rect(surface, SKIN, (x + 0, y + 14, 5, 4))
                hand_x = shoulder_x + int(math.cos(angle) * 6)
                hand_y = shoulder_y + int(math.sin(angle) * 6)
                pygame.draw.rect(surface, SKIN, (hand_x - 2, hand_y - 2, 5, 4))
                hilt_x = hand_x + int(math.cos(angle) * 2)
                hilt_y = hand_y + int(math.sin(angle) * 2)
                pygame.draw.line(surface, (100, 80, 50), (hilt_x, hilt_y),
                                 (hilt_x + int(math.cos(angle + 1.57) * 4),
                                  hilt_y + int(math.sin(angle + 1.57) * 4)), 2)
                pygame.draw.rect(surface, DARK_GRAY, (hilt_x - 1, hilt_y - 1, 3, 3))
                blade_len = 16
                tip_x = hilt_x + int(math.cos(angle) * blade_len)
                tip_y = hilt_y + int(math.sin(angle) * blade_len)
                pygame.draw.line(surface, (200, 210, 220), (hilt_x, hilt_y), (tip_x, tip_y), 3)
                pygame.draw.line(surface, CYAN, (hilt_x, hilt_y), (tip_x, tip_y), 1)
                pygame.draw.rect(surface, WHITE, (tip_x - 1, tip_y - 1, 2, 2))
            else:
                shoulder_x = x + 4
                shoulder_y = y + 12
                pygame.draw.rect(surface, SKIN, (x + 19, y + 14, 5, 4))
                hand_x = shoulder_x - int(math.cos(angle) * 6)
                hand_y = shoulder_y + int(math.sin(angle) * 6)
                pygame.draw.rect(surface, SKIN, (hand_x - 2, hand_y - 2, 5, 4))
                hilt_x = hand_x - int(math.cos(angle) * 2)
                hilt_y = hand_y + int(math.sin(angle) * 2)
                pygame.draw.line(surface, (100, 80, 50), (hilt_x, hilt_y),
                                 (hilt_x - int(math.cos(angle + 1.57) * 4),
                                  hilt_y + int(math.sin(angle + 1.57) * 4)), 2)
                pygame.draw.rect(surface, DARK_GRAY, (hilt_x - 1, hilt_y - 1, 3, 3))
                blade_len = 16
                tip_x = hilt_x - int(math.cos(angle) * blade_len)
                tip_y = hilt_y + int(math.sin(angle) * blade_len)
                pygame.draw.line(surface, (200, 210, 220), (hilt_x, hilt_y), (tip_x, tip_y), 3)
                pygame.draw.line(surface, CYAN, (hilt_x, hilt_y), (tip_x, tip_y), 1)
                pygame.draw.rect(surface, WHITE, (tip_x - 1, tip_y - 1, 2, 2))
        else:
            # 正常手臂
            pygame.draw.rect(surface, SKIN, (x + 0, y + 12, 5, 4))
            pygame.draw.rect(surface, SKIN, (x + 19, y + 12, 5, 4))
            if self.weapon == 'gun':
                if self.facing_right:
                    # 枪械细节
                    pygame.draw.rect(surface, (70, 70, 75), (x + 23, y + 11, 10, 4))  # 枪身
                    pygame.draw.rect(surface, (90, 90, 95), (x + 23, y + 11, 10, 1))  # 高光
                    pygame.draw.rect(surface, (50, 50, 55), (x + 31, y + 12, 3, 2))   # 枪口
                    pygame.draw.rect(surface, ORANGE, (x + 33, y + 12, 1, 1))         # 火星
                else:
                    pygame.draw.rect(surface, (70, 70, 75), (x - 9, y + 11, 10, 4))
                    pygame.draw.rect(surface, (90, 90, 95), (x - 9, y + 11, 10, 1))
                    pygame.draw.rect(surface, (50, 50, 55), (x - 10, y + 12, 3, 2))
                    pygame.draw.rect(surface, ORANGE, (x - 10, y + 12, 1, 1))
            elif self.weapon == 'shotgun':
                # 霞弹枪 —— 短粗双管
                if self.facing_right:
                    pygame.draw.rect(surface, (60, 58, 55), (x + 23, y + 10, 12, 6))  # 枪身（粗）
                    pygame.draw.rect(surface, (80, 78, 72), (x + 23, y + 10, 12, 1))  # 高光
                    # 双管口
                    pygame.draw.rect(surface, (40, 40, 42), (x + 33, y + 10, 3, 2))   # 上管
                    pygame.draw.rect(surface, (40, 40, 42), (x + 33, y + 13, 3, 2))   # 下管
                    pygame.draw.rect(surface, (90, 85, 75), (x + 33, y + 12, 3, 1))   # 中间分割
                    # 枪托
                    pygame.draw.rect(surface, (100, 75, 45), (x + 22, y + 14, 3, 4))  # 木质枪托
                    pygame.draw.rect(surface, (120, 90, 55), (x + 22, y + 14, 3, 1))  # 枪托高光
                    # 发射火花
                    if self.shoot_cooldown > 16:
                        pygame.draw.rect(surface, YELLOW, (x + 35, y + 10, 2, 2))
                        pygame.draw.rect(surface, ORANGE, (x + 35, y + 13, 2, 2))
                else:
                    pygame.draw.rect(surface, (60, 58, 55), (x - 11, y + 10, 12, 6))
                    pygame.draw.rect(surface, (80, 78, 72), (x - 11, y + 10, 12, 1))
                    pygame.draw.rect(surface, (40, 40, 42), (x - 12, y + 10, 3, 2))
                    pygame.draw.rect(surface, (40, 40, 42), (x - 12, y + 13, 3, 2))
                    pygame.draw.rect(surface, (90, 85, 75), (x - 12, y + 12, 3, 1))
                    pygame.draw.rect(surface, (100, 75, 45), (x - 1, y + 14, 3, 4))
                    pygame.draw.rect(surface, (120, 90, 55), (x - 1, y + 14, 3, 1))
                    if self.shoot_cooldown > 16:
                        pygame.draw.rect(surface, YELLOW, (x - 13, y + 10, 2, 2))
                        pygame.draw.rect(surface, ORANGE, (x - 13, y + 13, 2, 2))
            elif self.weapon == 'laser':
                # 激光枪 —— 细长科技枪管 + 发光核心
                firing = self.laser_fire_timer > 0
                if self.facing_right:
                    pygame.draw.rect(surface, (50, 70, 90), (x + 23, y + 11, 14, 3))   # 枪管（深蓝）
                    pygame.draw.rect(surface, (70, 100, 130), (x + 23, y + 11, 14, 1)) # 枪管高光
                    pygame.draw.rect(surface, (30, 50, 70), (x + 35, y + 11, 3, 3))    # 枪口
                    # 能量核心（发光）
                    core_c = WHITE if firing else CYAN
                    pygame.draw.rect(surface, core_c, (x + 28, y + 11, 3, 3))
                    # 发射时枪口光效
                    if firing:
                        gs = pygame.Surface((12, 12), pygame.SRCALPHA)
                        pygame.draw.ellipse(gs, (0, 220, 255, 120), (0, 0, 12, 12))
                        surface.blit(gs, (x + 34, y + 6))
                        pygame.draw.rect(surface, WHITE, (x + 37, y + 11, 2, 2))
                else:
                    pygame.draw.rect(surface, (50, 70, 90), (x - 13, y + 11, 14, 3))
                    pygame.draw.rect(surface, (70, 100, 130), (x - 13, y + 11, 14, 1))
                    pygame.draw.rect(surface, (30, 50, 70), (x - 14, y + 11, 3, 3))
                    core_c = WHITE if firing else CYAN
                    pygame.draw.rect(surface, core_c, (x - 7, y + 11, 3, 3))
                    if firing:
                        gs = pygame.Surface((12, 12), pygame.SRCALPHA)
                        pygame.draw.ellipse(gs, (0, 220, 255, 120), (0, 0, 12, 12))
                        surface.blit(gs, (x - 18, y + 6))
                        pygame.draw.rect(surface, WHITE, (x - 15, y + 11, 2, 2))
            else:
                if self.facing_right:
                    pygame.draw.rect(surface, (100, 80, 50), (x + 23, y + 11, 2, 5))
                    pygame.draw.rect(surface, (80, 80, 90), (x + 22, y + 10, 4, 2))
                    pygame.draw.line(surface, (200, 210, 220), (x + 24, y + 10), (x + 28, y + 0), 2)
                    pygame.draw.line(surface, CYAN, (x + 24, y + 10), (x + 28, y + 0), 1)
                    pygame.draw.rect(surface, WHITE, (x + 27, y - 1, 2, 2))
                else:
                    pygame.draw.rect(surface, (100, 80, 50), (x - 1, y + 11, 2, 5))
                    pygame.draw.rect(surface, (80, 80, 90), (x - 2, y + 10, 4, 2))
                    pygame.draw.line(surface, (200, 210, 220), (x, y + 10), (x - 4, y + 0), 2)
                    pygame.draw.line(surface, CYAN, (x, y + 10), (x - 4, y + 0), 1)
                    pygame.draw.rect(surface, WHITE, (x - 5, y - 1, 2, 2))

        # ---- 说 ----
        pygame.draw.rect(surface, (50, 70, 50), (x + 5, y + 24, 6, 10))     # 左腿
        pygame.draw.rect(surface, (50, 70, 50), (x + 13, y + 24, 6, 10))    # 右腿
        pygame.draw.rect(surface, (40, 58, 40), (x + 5, y + 24, 6, 2))      # 腿部暗纹
        pygame.draw.rect(surface, (40, 58, 40), (x + 13, y + 24, 6, 2))
        # 战斗靴
        pygame.draw.rect(surface, (55, 45, 30), (x + 3, y + 33, 9, 3))      # 左靴
        pygame.draw.rect(surface, (70, 58, 40), (x + 3, y + 33, 9, 1))      # 靴面高光
        pygame.draw.rect(surface, (55, 45, 30), (x + 12, y + 33, 9, 3))     # 右靴
        pygame.draw.rect(surface, (70, 58, 40), (x + 12, y + 33, 9, 1))

        # ---- Buff 视觉效果 ----
        if self.shield > 0:
            shield_surf = pygame.Surface((self.width + 12, self.height + 12), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surf, (80, 160, 255, 45),
                                (0, 0, self.width + 12, self.height + 12))
            pygame.draw.ellipse(shield_surf, (140, 200, 255, 100),
                                (0, 0, self.width + 12, self.height + 12), 2)
            pygame.draw.ellipse(shield_surf, (200, 230, 255, 60),
                                (2, 2, self.width + 8, self.height + 8), 1)
            surface.blit(shield_surf, (x - 6, y - 6))
        if self.power_up_timer > 0:
            glow_surf = pygame.Surface((self.width + 8, self.height + 8), pygame.SRCALPHA)
            glow_alpha = 35 + int(25 * math.sin(self.power_up_timer * 0.25))
            pygame.draw.ellipse(glow_surf, (255, 50, 30, max(0, glow_alpha)),
                                (0, 0, self.width + 8, self.height + 8))
            surface.blit(glow_surf, (x - 4, y - 4))

    def get_rect(self):
        """获取碰撞矩形"""
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)
