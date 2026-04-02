# flying_enemy.py
import pygame
from config import *


def _sfx(path, vol=1.0):
    try:
        s = pygame.mixer.Sound(path); s.set_volume(vol); return s
    except Exception:
        return None

_sfx_flying_death = None

def _init_flying_sounds():
    global _sfx_flying_death
    if _sfx_flying_death is None:
        _sfx_flying_death = _sfx("assets/sfx/enemy/death.wav", 0.8)


class FlyingEnemy:
    def __init__(self, x, y, left_bound, right_bound, hp):
        _init_flying_sounds()

        self.rect = pygame.Rect(x, y, 32, 32)

        self.left_bound  = left_bound
        self.right_bound = right_bound

        self.hp     = hp
        self.max_hp = hp
        self.alive  = True

        self.state        = "idle"
        self.moving_right = True

        self.attack_timer = 0

        self.speed_idle   = 1
        self.speed_attack = 3

        # --- SPRITES ---
        self.fly_frames = []
        for i in range(1, 7):
            img = pygame.image.load(f"assets/flying_enemy/fly/fly{i}.png").convert_alpha()
            img = pygame.transform.scale(img, (32, 32))
            self.fly_frames.append(img)

        self.hit_frame = pygame.transform.scale(
            pygame.image.load("assets/flying_enemy/hit.png").convert_alpha(),
            (32, 32)
        )

        self.anim_index = 0.0
        self.anim_speed = 0.12
        self.hit_timer  = 0
        self.face       = 1

    # ------------------------------------------------------------------
    def update(self, player):
        if not self.alive:
            return

        if self.hit_timer > 0:
            self.hit_timer -= 1

        if self.state == "idle":
            self.idle_patrol()
        elif self.state == "attack":
            self.attack_player(player)

        self.anim_index += self.anim_speed
        if self.anim_index >= len(self.fly_frames):
            self.anim_index = 0.0

        if self.rect.colliderect(player.rect):
            player.take_damage()

    # ------------------------------------------------------------------
    def idle_patrol(self):
        if self.moving_right:
            self.rect.x += self.speed_idle
            self.face    = 1
        else:
            self.rect.x -= self.speed_idle
            self.face    = -1

        if self.rect.left <= self.left_bound:
            self.rect.left = self.left_bound
            self.moving_right = True
        elif self.rect.right >= self.right_bound:
            self.rect.right = self.right_bound
            self.moving_right = False

    # ------------------------------------------------------------------
    def _move_toward(self, current, target, speed):
        diff = target - current
        if abs(diff) <= speed:
            return target
        return current + speed * (1 if diff > 0 else -1)

    def attack_player(self, player):
        self.attack_timer += 1

        if player.rect.centerx < self.rect.centerx:
            self.face = -1
        else:
            self.face = 1

        if self.attack_timer % 120 < 20:
            self.rect.x = self._move_toward(self.rect.x, player.rect.centerx, self.speed_attack * 2)
            self.rect.y = self._move_toward(self.rect.y, player.rect.centery, self.speed_attack * 2)
        else:
            desired_x_offset = 80
            desired_y_offset = -20

            if self.rect.centerx < player.rect.centerx:
                target_x = player.rect.centerx - desired_x_offset
            else:
                target_x = player.rect.centerx + desired_x_offset

            target_y = player.rect.centery + desired_y_offset

            self.rect.x = self._move_toward(self.rect.x, target_x, self.speed_attack)
            self.rect.y = self._move_toward(self.rect.y, target_y, self.speed_attack)

        if self.rect.left < self.left_bound:
            self.rect.left = self.left_bound
        if self.rect.right > self.right_bound:
            self.rect.right = self.right_bound

    # ------------------------------------------------------------------
    def take_damage(self):
        self.hp -= 1
        self.hit_timer = 8
        if self.hp <= 0:
            self.alive = False
            if _sfx_flying_death: _sfx_flying_death.play()

    # ------------------------------------------------------------------
    def draw(self, screen, cam_x, cam_y):
        if not self.alive:
            return

        ix = int(cam_x)
        iy = int(cam_y)

        if self.hit_timer > 0:
            img = self.hit_frame.copy()
        else:
            img = self.fly_frames[int(self.anim_index)].copy()

        if self.face == 1:
            img = pygame.transform.flip(img, True, False)

        screen.blit(img, (self.rect.x - ix, self.rect.y - iy))

        hp_ratio = self.hp / self.max_hp
        bar_x = self.rect.x - ix
        bar_y = self.rect.y - iy - 6
        pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, 32, 4))
        pygame.draw.rect(screen, (0, 200, 0),  (bar_x, bar_y, int(32 * hp_ratio), 4))