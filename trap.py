# trap.py
import pygame
from config import *


def _s(path, vol=1.0):
    try:
        s = pygame.mixer.Sound(path); s.set_volume(vol); return s
    except Exception:
        return None

# Module-level sounds loaded once
_sfx_spike    = None
_sfx_bridge   = None
_sfx_jumppad  = None

def _init_trap_sounds():
    global _sfx_spike, _sfx_bridge, _sfx_jumppad
    if _sfx_spike is None:
        _sfx_spike   = _s("assets/sfx/traps/spike.wav",    0.6)
        _sfx_bridge  = _s("assets/sfx/traps/bridge.wav",   0.6)
        _sfx_jumppad = _s("assets/sfx/traps/jump_pad.wav", 0.7)


class SpikeTrap:
    def __init__(self, tx, ty, images, delay=18, mode="timed", direction="up"):
        _init_trap_sounds()
        self.images = images
        self.delay = delay
        self.direction = direction
        self.mode = mode
        self.state = "active" if mode == "always" else "idle"
        self.timer = 0
        self.used = False
        self.danger = False
        self.visual_only = (mode == "visual")

        if direction == "up":
            y = (ty + 1) * TILE_SIZE - images["active"].get_height()
        else:
            y = ty * TILE_SIZE

        self.rect = pygame.Rect(
            tx * TILE_SIZE,
            y,
            images["active"].get_width(),
            images["active"].get_height()
        )

        self.trigger = pygame.Rect(tx*TILE_SIZE, ty*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        if self.mode == "visual":
            self.state = "active"
            self.active = False

    def update(self, player):
        if self.used:
            return None
        if self.visual_only:
            return None
        if self.mode == "always":
            if self.rect.colliderect(player.rect):
                if _sfx_spike: _sfx_spike.play()
                return "kill"
            return None

        if self.direction == "up":
            trigger_zone = pygame.Rect(
                player.rect.x + 4, player.rect.bottom,
                player.rect.width - 8, 2
            )
        else:
            trigger_zone = pygame.Rect(
                player.rect.x + 4, player.rect.top - 2,
                player.rect.width - 8, 2
            )

        if self.state == "idle" and trigger_zone.colliderect(self.trigger):
            self.state = "popping"
            self.timer = 0

        if self.state == "popping":
            self.timer += 1
            if self.timer >= self.delay // 2:
                self.danger = True
            if self.timer >= self.delay:
                self.state = "active"

        if (self.state == "active" or self.danger) and self.rect.colliderect(player.rect):
            if self.mode == "one_shot":
                self.used = True
            if _sfx_spike: _sfx_spike.play()
            return "kill"

        return None

    def reset(self):
        self.timer  = 0
        self.danger = False   # ← always clear danger on reset
        if self.mode == "visual":
            self.state  = "active"
            self.active = False
            return
        if self.mode == "always":
            self.state  = "active"
            self.active = True
        elif self.mode == "one_shot":
            self.state  = "idle"
            self.active = False
            self.used   = False
        else:                  # timed
            self.state  = "idle"
            self.active = False

    def draw(self, screen, cam_x, cam_y):
        if self.used:
            return
        img = self.images[self.state]
        if self.direction == "down":
            img = pygame.transform.flip(img, False, True)
            y = self.rect.y - cam_y
        else:
            y = self.rect.bottom - img.get_height() - cam_y
        screen.blit(img, (self.rect.x - cam_x, y))


class BreakableBridge:
    def __init__(self, tx, ty, images, mode="safe", delay=30):
        _init_trap_sounds()
        self.images = images
        self.mode = mode
        self.delay = delay
        self.state = "idle"
        self.timer = 0
        self.collidable = True
        self.triggered = False
        self.chain = False
        self.next_bridge = None
        self.was_on_bridge = False
        self._break_sound_played = False

        self.rect = pygame.Rect(
            tx * TILE_SIZE,
            ty * TILE_SIZE - images["idle"].get_height(),
            images["idle"].get_width(),
            images["idle"].get_height()
        )

    def on_player_step(self, triggered_by_chain=False):
        if triggered_by_chain and self.mode != "chain":
            return
        if self.mode == "safe":
            return
        if self.triggered:
            return
        self.triggered = True
        if self.mode == "instant":
            self.state = "break"
            self.collidable = False
            if not self._break_sound_played:
                if _sfx_bridge: _sfx_bridge.play()
                self._break_sound_played = True
        else:
            self.state = "warning"
            self.timer = 0

    def update(self):
        if self.state == "warning":
            self.timer += 1
            if self.timer >= self.delay:
                self.state = "break"
                self.collidable = False
                if not self._break_sound_played:
                    if _sfx_bridge: _sfx_bridge.play()
                    self._break_sound_played = True
                if self.mode == "chain" and self.next_bridge:
                    self.next_bridge.on_player_step(triggered_by_chain=True)

    def reset(self):
        self.timer = 0
        self.collidable = True
        self.triggered = False
        self.state = "idle"
        self.was_on_bridge = False
        self._break_sound_played = False

    def draw(self, screen, cam_x, cam_y):
        if hasattr(self, "visual_only") and self.visual_only:
            img = self.images["active"]
            screen.blit(img, (self.rect.x - cam_x, self.rect.y - cam_y))
            return
        img = (
            self.images["active"]
            if self.state == "warning"
            else self.images[self.state]
        )
        screen.blit(img, (self.rect.x - cam_x, self.rect.y - cam_y))


class JumpPad:
    def __init__(self, tx, ty, images, boost_power=18):
        _init_trap_sounds()
        self.images = images
        self.boost_power = boost_power
        self.rect = pygame.Rect(tx * TILE_SIZE, ty * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.state = "idle"
        self.frame = 0
        self.anim_speed = 0.5
        self.active_timer = 0

    def update(self, player):
        if (
            self.state == "idle"
            and player.rect.colliderect(self.rect)
            and player.vy > 0
        ):
            player.vy = -self.boost_power
            self.state = "active"
            self.frame = 0
            self.active_timer = 12
            if _sfx_jumppad: _sfx_jumppad.play()

        if self.state == "active":
            self.frame += self.anim_speed
            if self.frame >= len(self.images):
                self.frame = len(self.images) - 1
            self.active_timer -= 1
            if self.active_timer <= 0:
                self.state = "idle"
                self.frame = 0

    def draw(self, screen, cam_x, cam_y):
        img = self.images[int(self.frame)]
        screen.blit(img, (
            self.rect.x - cam_x,
            self.rect.bottom - img.get_height() - cam_y
        ))


class RotatingSaw:
    def __init__(self, tx, ty, image,
                 move_type="static", range_px=120, speed=2,
                 delay=0, visual_only=False, activate_on_touch=False):
        self.base_image = image
        self.image = image
        self.angle = 0
        self.pos_x = tx * TILE_SIZE
        self.pos_y = ty * TILE_SIZE
        self.start_x = self.pos_x
        self.start_y = self.pos_y
        self.rect = self.base_image.get_rect(topleft=(self.pos_x, self.pos_y))
        self.move_type = move_type
        self.range = range_px
        self.speed = speed
        self.delay = delay
        self.visual_only = visual_only
        self.activate_on_touch = activate_on_touch
        self.dir = 1
        self.timer = 0
        self.visible = True
        self.active = not activate_on_touch

    def update(self, player):
        if self.activate_on_touch and not self.active:
            if self.rect.colliderect(player.rect):
                self.active = True
        if self.active:
            self.angle = (self.angle + 6) % 360
            self.image = pygame.transform.rotate(self.base_image, self.angle)
        if self.active:
            if self.move_type == "vertical":
                self.pos_y += self.speed * self.dir
                if abs(self.pos_y - self.start_y) > self.range:
                    self.dir *= -1
            elif self.move_type == "horizontal":
                self.pos_x += self.speed * self.dir
                if abs(self.pos_x - self.start_x) > self.range:
                    self.dir *= -1
            elif self.move_type == "blink":
                self.timer += 1
                if self.timer >= self.delay:
                    self.visible = not self.visible
                    self.timer = 0
        self.rect = self.image.get_rect(center=(int(self.pos_x), int(self.pos_y)))
        if self.active and not self.visual_only and self.visible:
            if self.rect.colliderect(player.rect):
                return "kill"
        return None

    def draw(self, screen, cam_x, cam_y):
        if self.visible:
            screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))


class FakeSawPlatform:
    def __init__(self, tx, ty, image):
        self.image = image
        self.rect = pygame.Rect(
            tx * TILE_SIZE, ty * TILE_SIZE,
            image.get_width(), image.get_height()
        )

    def update(self, player):
        return None

    def draw(self, screen, cam_x, cam_y):
        screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))