# boss_terminal.py
import pygame
import math
from config import *


def _make_fireball_surf():
    """Procedural fireball sprite — glowing orange orb with inner core."""
    size = 20
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    # outer glow
    for r, col in [(10, (255, 60, 0, 60)),
                   (8,  (255, 100, 0, 120)),
                   (6,  (255, 140, 20, 200)),
                   (4,  (255, 200, 60, 255)),
                   (2,  (255, 240, 200, 255))]:
        pygame.draw.circle(surf, col, (cx, cy), r)
    return surf


def _make_meteor_surf():
    """Procedural meteor sprite — rocky chunk with fire trail."""
    w, h = 24, 36
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # fire trail (top, fades out)
    for i, col in enumerate([(255, 80, 0, 40), (255, 120, 0, 80),
                               (255, 160, 0, 130), (255, 200, 50, 180)]):
        trail_h = 20 - i * 4
        pygame.draw.ellipse(surf, col, (w//2 - 5 + i, i*3, 10 - i*2, trail_h))
    # rocky body (bottom)
    rock_y = 14
    rock_col  = (120, 80, 50, 255)
    rock_edge = (80, 50, 30, 255)
    pygame.draw.ellipse(surf, rock_col,  (2,  rock_y, w-4, h-rock_y-2))
    pygame.draw.ellipse(surf, rock_edge, (2,  rock_y, w-4, h-rock_y-2), 2)
    # hot cracks
    pygame.draw.line(surf, (255, 120, 0, 200), (8, rock_y+4), (14, rock_y+10), 1)
    pygame.draw.line(surf, (255, 120, 0, 200), (14, rock_y+2), (10, rock_y+12), 1)
    return surf


def _make_warning_surf():
    """Procedural meteor warning indicator — red pulsing ring on the ground."""
    size = 60
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 50, 50, 80),  (size//2, size//2), size//2)
    pygame.draw.circle(surf, (255, 50, 50, 180), (size//2, size//2), size//2, 2)
    # crosshair lines
    mid = size // 2
    pygame.draw.line(surf, (255, 80, 80, 150), (mid-8, mid), (mid+8, mid), 1)
    pygame.draw.line(surf, (255, 80, 80, 150), (mid, mid-8), (mid, mid+8), 1)
    return surf


# Pre-bake the sprites once at module load
FIREBALL_SURF = _make_fireball_surf()
METEOR_SURF   = _make_meteor_surf()
WARNING_SURF  = _make_warning_surf()


class TerminalBoss:
    def __init__(self, x, y, sprites):
        self.rect = pygame.Rect(x, y, 48, 48)

        self.vy = 0
        self.on_ground = False

        # Scale up boss sprites from 32x32 → 48x48 to match rect
        self.sprites = {}
        for state, frames in sprites.items():
            self.sprites[state] = [
                pygame.transform.scale(f, (48, 48)) for f in frames
            ]

        self.anim_state = "idle"
        self.frame      = 0
        self.anim_speed = 0.2

        self.hp          = 25
        self.vulnerable  = True

        self.dir   = 1     # 1 = facing right, -1 = facing left
        self.speed = 2

        self.attack_timer    = 0
        self.attack_cooldown = 240

        # Sprite naturally faces RIGHT in the sheet
        # dir == -1 → player is to the left → flip sprite to face left
        self.sprite_faces_right = True

    # ------------------------------------------------------------------
    def update(self, player, solids):

        # ── face the player ───────────────────────────────────────────
        if player.rect.centerx < self.rect.centerx:
            self.dir = -1   # player is left → face left
        else:
            self.dir = 1    # player is right → face right

        # ── animation ────────────────────────────────────────────────
        self.anim_state = "idle"
        self.frame += self.anim_speed
        frames = self.sprites[self.anim_state]
        if self.frame >= len(frames):
            self.frame = 0

        # ── hover ────────────────────────────────────────────────────
        if not hasattr(self, "base_y"):
            self.base_y = self.rect.y
        offset = int(5 * math.sin(pygame.time.get_ticks() * 0.005))
        self.rect.y = self.base_y + offset

    # ------------------------------------------------------------------
    def take_damage(self):
        if self.vulnerable:
            self.hp -= 1

    # ------------------------------------------------------------------
    def draw(self, screen, cam_x, cam_y):
        img = self.sprites[self.anim_state][int(self.frame)]

        # Flip when facing left (dir == -1)
        if self.dir == 1:
            img = pygame.transform.flip(img, True, False)

        screen.blit(img, (self.rect.x - cam_x, self.rect.y - cam_y))

    # ------------------------------------------------------------------
    @staticmethod
    def draw_fireball(screen, fb, cam_x, cam_y):
        """Draw a single fireball dict {"x", "y"} with sprite."""
        x = int(fb["x"] - cam_x) - FIREBALL_SURF.get_width() // 2
        y = int(fb["y"] - cam_y) - FIREBALL_SURF.get_height() // 2
        # rotate slightly each frame for spin effect
        angle = (fb.get("angle", 0))
        rotated = pygame.transform.rotate(FIREBALL_SURF, angle)
        rx = int(fb["x"] - cam_x) - rotated.get_width() // 2
        ry = int(fb["y"] - cam_y) - rotated.get_height() // 2
        screen.blit(rotated, (rx, ry))

    @staticmethod
    def draw_meteor(screen, m, cam_x, cam_y, world_h):
        """Draw a single meteor dict {"x","y","warn_timer"} with sprite."""
        if m["warn_timer"] > 0:
            # Pulsing warning indicator on the floor
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.008))
            alpha = int(80 + 120 * pulse)
            warn  = WARNING_SURF.copy()
            warn.set_alpha(alpha)
            wx = int(m["x"] - cam_x) - warn.get_width() // 2
            wy = int(world_h - cam_y) - warn.get_height() // 2
            screen.blit(warn, (wx, wy))
            # Dashed vertical line from warning to top
            dash_x = int(m["x"] - cam_x)
            for dy in range(0, int(world_h - cam_y), 12):
                pygame.draw.line(screen, (255, 60, 60, 80),
                                 (dash_x, dy), (dash_x, dy + 6), 1)
        else:
            # Falling meteor sprite
            mx = int(m["x"] - cam_x) - METEOR_SURF.get_width() // 2
            my = int(m["y"] - cam_y)
            screen.blit(METEOR_SURF, (mx, my))
            # Glow ring at impact point when close to ground
            dist_to_ground = world_h - m["y"]
            if dist_to_ground < 200:
                glow_alpha = int(200 * (1 - dist_to_ground / 200))
                glow = pygame.Surface((40, 12), pygame.SRCALPHA)
                pygame.draw.ellipse(glow, (255, 100, 0, glow_alpha), (0, 0, 40, 12))
                screen.blit(glow, (mx - 8, int(world_h - cam_y) - 6))