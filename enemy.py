# enemy.py
import pygame
from config import *


def load_passive_anims(base_path):
    anim = {}
    img = pygame.image.load(f"{base_path}/idle/idle.png").convert_alpha()
    anim["idle"] = pygame.transform.scale(img, (32, 32))
    anim["run"] = []
    for i in range(1, 13):
        img = pygame.image.load(f"{base_path}/run/run{i}.png").convert_alpha()
        anim["run"].append(pygame.transform.scale(img, (32, 32)))
    img = pygame.image.load(f"{base_path}/hit/hit.png").convert_alpha()
    anim["hit"] = pygame.transform.scale(img, (32, 32))
    return anim


def load_shooter_anims(base_path, walk_count=12, attack_count=7):
    anim = {}
    img = pygame.image.load(f"{base_path}/idle/idle.png").convert_alpha()
    anim["idle"] = pygame.transform.scale(img, (32, 32))
    anim["walk"] = []
    for i in range(1, walk_count + 1):
        img = pygame.image.load(f"{base_path}/walk/walk{i}.png").convert_alpha()
        anim["walk"].append(pygame.transform.scale(img, (32, 32)))
    anim["attack"] = []
    for i in range(1, attack_count + 1):
        img = pygame.image.load(f"{base_path}/attack/attack{i}.png").convert_alpha()
        anim["attack"].append(pygame.transform.scale(img, (32, 32)))
    img = pygame.image.load(f"{base_path}/hit/hit.png").convert_alpha()
    anim["hit"] = pygame.transform.scale(img, (32, 32))
    img = pygame.image.load(f"{base_path}/bullet/cannonball1.png").convert_alpha()
    anim["bullet"] = img
    return anim


PASSIVE_PATHS = {
    1: "assets/enemy/level1",
    2: "assets/enemy/level2",
    3: "assets/enemy/level3",
}

SHOOTER_PATHS = {
    3: "assets/enemy/canon",
    5: "assets/enemy/canon",
}


def _sfx(path, vol=1.0):
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(vol)
        return s
    except Exception:
        return None

# Module-level shared sounds (loaded once)
_sfx_canon       = None
_sfx_enemy_death = None

def _init_enemy_sounds():
    global _sfx_canon, _sfx_enemy_death
    if _sfx_canon is None:
        _sfx_canon       = _sfx("assets/sfx/enemy/canon.wav",  0.5)
        _sfx_enemy_death = _sfx("assets/sfx/enemy/death.wav",  0.8)


class Enemy:
    def __init__(self, x, y, left, right, hp, behavior="passive", level_id=1):
        _init_enemy_sounds()

        self.rect  = pygame.Rect(x, y, 32, 32)
        self.left  = left
        self.right = right
        self.dir   = 1

        self.behavior       = behavior
        self.touch_cooldown = 0

        self.alive  = True
        self.active = False

        self.state  = "patrol"
        self.hp     = hp
        self.max_hp = hp

        self.cooldown    = 0
        self.projectiles = []
        self.hit_timer   = 0

        self.level_id = level_id

        if behavior == "passive":
            path = PASSIVE_PATHS.get(level_id)
            self.anims = load_passive_anims(path) if path else None
        elif behavior == "shooter":
            path = SHOOTER_PATHS.get(level_id)
            self.anims = load_shooter_anims(path) if path else None
        else:
            self.anims = None

        self.walk_index   = 0.0
        self.attack_index = 0.0
        self.anim_speed   = 0.15
        self.face         = 1

        self.is_attacking = False

        FACES_LEFT = {1: False, 2: False, 3: True, 5: True}
        self.sprite_faces_left = FACES_LEFT.get(level_id, False)

    # ------------------------------------------------------------------
    def update(self, player, solids):
        if not self.alive or not self.active:
            return

        if self.hit_timer > 0:
            self.hit_timer -= 1

        # ---------- SHOOTER LOGIC ----------
        if self.behavior == "shooter":
            detect_range = 180
            dx_signed = player.rect.centerx - self.rect.centerx
            self.face = 1 if dx_signed > 0 else -1
            dx_abs = abs(dx_signed)

            if dx_abs < detect_range and self.cooldown == 0:
                speed = 6 * self.face
                if self.anims and "bullet" in self.anims:
                    bw = self.anims["bullet"].get_width()
                    bh = self.anims["bullet"].get_height()
                else:
                    bw, bh = 10, 10

                bx = self.rect.right if self.face == 1 else self.rect.left - bw
                bullet_rect = pygame.Rect(bx, self.rect.centery - bh // 2, bw, bh)
                self.projectiles.append({"rect": bullet_rect, "speed": speed})
                self.cooldown     = ENEMY_COOLDOWN
                self.is_attacking = True
                self.attack_index = 0.0
                if _sfx_canon: _sfx_canon.play()

        # ---------- PATROL ----------
        if self.state == "patrol":
            self.rect.x += ENEMY_SPEED * self.dir

            if self.behavior == "passive":
                self.face = 1 if self.dir > 0 else -1

            for s in solids:
                if self.rect.colliderect(s):
                    if self.dir > 0:
                        self.rect.right = s.left
                        self.dir = -1
                    else:
                        self.rect.left = s.right
                        self.dir = 1
                    break

            if self.rect.left <= self.left:
                self.rect.left = self.left
                self.dir = 1
            elif self.rect.right >= self.right:
                self.rect.right = self.right
                self.dir = -1

        # ---------- GRAVITY ----------
        self.rect.y += GRAVITY * 4
        for s in solids:
            if self.rect.colliderect(s) and self.rect.bottom <= s.bottom:
                self.rect.bottom = s.top

        # ---------- ANIMATION ----------
        if self.anims:
            if self.behavior == "passive":
                self.walk_index += self.anim_speed
                if self.walk_index >= len(self.anims["run"]):
                    self.walk_index = 0.0
            elif self.behavior == "shooter":
                if self.is_attacking:
                    self.attack_index += self.anim_speed
                    if self.attack_index >= len(self.anims["attack"]):
                        self.attack_index = 0.0
                        self.is_attacking = False
                else:
                    self.walk_index += self.anim_speed
                    if self.walk_index >= len(self.anims["walk"]):
                        self.walk_index = 0.0

        # ---------- BULLETS ----------
        new_bullets = []
        for b in self.projectiles:
            b["rect"].x += b["speed"]
            if b["rect"].colliderect(player.rect):
                player.take_damage()
                continue
            if abs(b["rect"].x - self.rect.x) > 500:
                continue
            new_bullets.append(b)
        self.projectiles = new_bullets

        if self.cooldown > 0:
            self.cooldown -= 1

        # ---------- PASSIVE CONTACT DAMAGE ----------
        if self.behavior == "passive":
            if self.touch_cooldown > 0:
                self.touch_cooldown -= 1
            if self.rect.colliderect(player.rect) and self.touch_cooldown == 0:
                player.take_damage()
                self.touch_cooldown = 30

    # ------------------------------------------------------------------
    def take_damage(self):
        if not self.active:
            return
        self.hp -= 1
        self.hit_timer = 8
        if self.hp <= 0:
            self.alive = False
            if _sfx_enemy_death: _sfx_enemy_death.play()

    # ------------------------------------------------------------------
    def _get_frame(self):
        if not self.anims:
            return None
        if self.hit_timer > 0:
            return self.anims["hit"]
        if not self.active:
            return self.anims["idle"]
        if self.behavior == "passive":
            return self.anims["run"][int(self.walk_index)]
        if self.behavior == "shooter":
            if self.is_attacking:
                return self.anims["attack"][int(self.attack_index)]
            return self.anims["walk"][int(self.walk_index)]
        return self.anims.get("idle")

    # ------------------------------------------------------------------
    def draw(self, screen, cam_x, cam_y):
        if not self.alive:
            return

        ix = int(cam_x)
        iy = int(cam_y)
        x  = self.rect.x - ix
        y  = self.rect.y - iy

        frame = self._get_frame()
        if frame:
            img = frame.copy()
            should_flip = (self.sprite_faces_left and self.face == 1) or \
                          (not self.sprite_faces_left and self.face == -1)
            if should_flip:
                img = pygame.transform.flip(img, True, False)
            screen.blit(img, (x, y))
        else:
            pygame.draw.rect(screen, (200, 50, 50), (x, y, 32, 32))

        # HP bar
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(screen, (40, 40, 40), (x, y - 6, 32, 4))
        pygame.draw.rect(screen, (0, 200, 0),  (x, y - 6, int(32 * hp_ratio), 4))

        # Bullets
        for b in self.projectiles:
            bx = b["rect"].x - ix
            by = b["rect"].y - iy
            if self.anims and "bullet" in self.anims:
                screen.blit(self.anims["bullet"], (bx, by))
            else:
                pygame.draw.rect(screen, (255, 200, 50),
                                 (bx, by, b["rect"].w, b["rect"].h))