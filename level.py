# level.py
import pygame, csv, math
from config import *
from enemy import Enemy
import player
import random
from gate import Gate
from trap import SpikeTrap, BreakableBridge, JumpPad, RotatingSaw
from config import LEVEL_ENEMY_HP
from checkpoint import Checkpoint
from flying_enemy import FlyingEnemy
from trap import FakeSawPlatform
from boss_terminal import TerminalBoss


LEVEL_BRIDGES = {
    1: [
        (52, 22, "instant", 0),
        (56, 22, "safe",   0),
        (60, 22, "normal",   30),
    ],
    2: [
        (47, 20, "normal", 24),
        (54, 18, "instant",   0),
        (59, 22, "safe",   0),
        (129, 21, "instant", 0),
        (133, 18, "normal", 24),
        (139, 21, "safe", 0),
        (144, 25, "normal", 24),
        (148, 17, "safe", 0),
        (152, 24, "instant", 0),
    ],
    3: [
        (27, 22, "instant", 0),
        (31, 25, "instant", 0),
        (67, 22, "chain", 26),
        (74, 22, "chain", 24),
        (81, 22, "chain", 26),
        (119, 27, "normal", 24),
        (126, 25, "safe", 0),
        (215, 22, "chain", 28),
        (221, 22, "chain", 28),
        (227, 22, "chain", 28),
        (232, 22, "chain", 28),
    ],
    4: [
        (219, 15, "instant", 0),
        (229, 15, "instant", 0),
        (240, 15, "instant", 0),
        (250, 15, "instant", 0),
        (260, 15, "instant", 0),
        (270, 15, "instant", 0),
    ]
}

LEVEL_LAYOUTS = {
    1: {
        "enemy_left": 74, "enemy_right": 86, "enemy_y": 24,
        "gate_x": 88, "gate_y": 20, "behavior": "passive"
    },
    2: {
        "enemy_left": 82, "enemy_right": 103, "enemy_y": 19,
        "behavior": "passive", "gate_x": 173, "gate_y": 18
    },
    3: {
        "enemies": [
            {"left": 38, "right": 49, "y": 26, "behavior": "passive"},
            {"left": 94, "right": 112, "y": 24, "behavior": "shooter"},
        ],
        "flying_enemies": [{"x": 190, "y": 20, "range": 200}],
        "gate_x": 248, "gate_y": 20
    },
    4: {
        "flying_enemies": [
            {"x": 145, "y": 16, "range": 200},
            {"x": 170, "y": 20, "range": 200},
            {"x": 291, "y": 15, "range": 200}
        ],
        "gate_x": 318, "gate_y": 20
    },
    5: {
        "enemies": [
            {"left": 40, "right": 80, "y": 94, "behavior": "shooter"},
            {"left": 15, "right": 30, "y": 72, "behavior": "shooter"},
            {"left": 35, "right": 55, "y": 72, "behavior": "shooter"},
            {"left": 60, "right": 80, "y": 72, "behavior": "shooter"},
        ],
        "flying_enemies": [
            {"x": 20, "y": 55, "range": 200},
            {"x": 50, "y": 55, "range": 200},
            {"x": 70, "y": 55, "range": 200},
        ],
        "gate_x": 357, "gate_y": 20
    }
}


# ── PRE-BAKED FIREBALL / METEOR / WARNING SPRITES ─────────────────────
def _make_fireball_surf():
    size = 20
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    for r, col in [
        (10, (255,  60,   0,  60)),
        ( 8, (255, 100,   0, 120)),
        ( 6, (255, 140,  20, 200)),
        ( 4, (255, 200,  60, 255)),
        ( 2, (255, 240, 200, 255)),
    ]:
        pygame.draw.circle(surf, col, (cx, cy), r)
    return surf

def _make_meteor_surf():
    """
    Pixel-art style meteor matching reference:
    - Bright orange/yellow flame core at bottom
    - Flame body widens then narrows going up
    - Dark smoke wisps curling at the top
    - Rocky debris embedded in the flame
    """
    w, h = 36, 72
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2

    # ── SMOKE (top) — dark translucent wisps ─────────────────────────
    smoke_data = [
        # (x_offset, y, w, h, alpha)
        ( 2,  0, 10, 10,  60),
        (-4,  4, 12, 10,  50),
        ( 5,  6,  8,  8,  45),
        (-2,  8, 14, 10,  55),
        ( 3, 12,  9,  8,  40),
        (-3, 14, 11,  9,  50),
        ( 1, 18, 13, 10,  60),
    ]
    for ox, sy, sw, sh, sa in smoke_data:
        smoke_col = (40, 25, 15, sa)
        pygame.draw.ellipse(surf, smoke_col, (cx + ox - sw//2, sy, sw, sh))

    # ── FLAME BODY — layered from outside in ─────────────────────────
    # Each layer: (y_top, height, half_width, color)
    flame_layers = [
        # outer dark orange — widest
        (20, 14, 13, (180,  55,  0, 200)),
        (26, 12, 12, (200,  70,  0, 220)),
        (30, 16, 11, (220,  85,  0, 230)),
        # mid orange
        (22, 18, 10, (240, 110,  0, 240)),
        (28, 16,  9, (250, 130,  0, 245)),
        # bright inner core
        (30, 18,  7, (255, 160,  0, 255)),
        (32, 16,  5, (255, 200,  30, 255)),
        (35, 12,  4, (255, 230,  80, 255)),
        # hottest white-yellow center
        (38,  8,  3, (255, 250, 160, 255)),
        (40,  6,  2, (255, 255, 220, 255)),
    ]
    for fy, fh, fw, fc in flame_layers:
        pygame.draw.ellipse(surf, fc, (cx - fw, fy, fw*2, fh))

    # ── FLAME TIPS — tongue shapes going upward ───────────────────────
    tip_data = [
        # (cx_offset, y_top, width, height, color)
        ( 0, 16, 6, 12, (220,  80,  0, 180)),
        (-5, 18, 4,  9, (200,  60,  0, 160)),
        ( 6, 20, 4,  8, (200,  65,  0, 155)),
        ( 2, 14, 3,  8, (240, 100,  0, 170)),
        (-3, 22, 3,  6, (180,  50,  0, 140)),
    ]
    for ox, ty, tw, th, tc in tip_data:
        pygame.draw.ellipse(surf, tc, (cx + ox - tw//2, ty, tw, th))

    # ── ROCKY CORE — small dark rock embedded at flame base ───────────
    ry = 42
    rw, rh = 18, 14
    pygame.draw.ellipse(surf, ( 45,  28,  12, 255), (cx-rw//2,   ry,   rw,   rh  ))
    pygame.draw.ellipse(surf, ( 70,  45,  20, 255), (cx-rw//2+1, ry+1, rw-2, rh-3))
    # rock lit by flame above
    pygame.draw.ellipse(surf, (200, 100,  30, 180), (cx-4,       ry,   8,    4   ))
    # glowing cracks
    pygame.draw.line(surf, (255, 150, 0, 220), (cx-3, ry+3), (cx+3, ry+8), 1)
    pygame.draw.line(surf, (255, 120, 0, 180), (cx+2, ry+2), (cx-1, ry+9), 1)
    # ember sparks off the rock
    for sx, sy in [(cx-5, ry-2), (cx+6, ry-3), (cx+4, ry+1)]:
        pygame.draw.circle(surf, (255, 220, 80, 255), (sx, sy), 1)

    # ── BRIGHT GLOW HALO at base ──────────────────────────────────────
    for gr, ga in [(22,25),(18,40),(14,60),(10,80)]:
        pygame.draw.circle(surf, (255, 120, 0, ga), (cx, 48), gr)

    return surf
def _make_warning_surf():
    size = 72
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    mid  = size // 2

    # outer glow fill
    pygame.draw.circle(surf, (255,  50,  0,  35), (mid, mid), mid)
    # concentric rings
    pygame.draw.circle(surf, (255,  80,  0,  90), (mid, mid), mid-2,  3)
    pygame.draw.circle(surf, (255, 130,  0, 150), (mid, mid), mid-8,  2)
    pygame.draw.circle(surf, (255, 200,  0, 220), (mid, mid), mid-16, 1)

    # dotted crosshair arms
    for angle_deg in (0, 90, 180, 270):
        rad = angle_deg * 3.14159 / 180
        for dist in range(8, mid-2, 5):
            dx = int(dist * (1 if angle_deg == 0 else -1 if angle_deg == 180 else 0))
            dy = int(dist * (1 if angle_deg == 90 else -1 if angle_deg == 270 else 0))
            if angle_deg in (0, 180):
                px = mid + (dist if angle_deg == 0 else -dist)
                py = mid
            else:
                px = mid
                py = mid + (dist if angle_deg == 90 else -dist)
            pygame.draw.circle(surf, (255, 180, 0, 200), (px, py), 1)

    # bright center dot
    pygame.draw.circle(surf, (255, 230, 80, 255), (mid, mid), 3)
    pygame.draw.circle(surf, (255, 255, 200, 255), (mid, mid), 1)
    return surf

_FIREBALL_SURF   = None
_METEOR_SURF     = None
_WARNING_SURF    = None
_METEOR_FRAMES   = None   # animated frames from spritesheet
_METEOR_ANIM_IDX = 0.0    # shared animation index

def _load_meteor_frames():
    """
    Sheet: 256x48px, single row of 8 frames each 32x48px.
    Scaled 2x to 64x96 so it's clearly visible in-game.
    """
    try:
        sheet  = pygame.image.load("assets/effects/fire_spritesheet.png").convert_alpha()
        sw, sh = sheet.get_size()
        cols   = 8
        fw     = sw // cols  # 32
        fh     = sh          # 48
        frames = []
        for col in range(cols):
            frame = sheet.subsurface((col * fw, 0, fw, fh))
            frame = pygame.transform.scale(frame, (fw * 2, fh * 2))  # 64x96
            frames.append(frame)
        return frames
    except Exception:
        return None   # fallback to procedural if file missing


def _init_attack_surfs():
    global _FIREBALL_SURF, _METEOR_SURF, _WARNING_SURF, _METEOR_FRAMES, _METEOR_ANIM_IDX
    if _FIREBALL_SURF is None:
        _FIREBALL_SURF    = _make_fireball_surf()
        _METEOR_SURF      = _make_meteor_surf()     # procedural fallback
        _WARNING_SURF     = _make_warning_surf()
        _METEOR_FRAMES    = _load_meteor_frames()   # animated frames (None if asset missing)
        _METEOR_ANIM_IDX  = 0.0


class Level:
    def __init__(self, map_path, spike_imgs, bridge_imgs, rules=None, boss_sprites=None, gate_frames=None):
        _init_attack_surfs()   # ensure sprites are ready

        self.map_path    = map_path
        self.spike_imgs  = spike_imgs
        self.bridge_imgs = bridge_imgs

        self.active_checkpoint_index = -1
        self.rules       = rules or {}
        self.enemy_count = self.rules.get("enemy_count", 0)

        self.tiles, self.solids = self.load_map(map_path)
        self.world_w = max(r.right  for r in self.solids)
        self.world_h = max(r.bottom for r in self.solids)

        self.chain_active          = False
        self.commit_zone           = None
        self._commit_entered       = False
        self.boss_sprites          = boss_sprites

        self.commit_fade_alpha     = 180
        self.commit_fade_speed     = 6
        self.commit_wall_alpha     = 0
        self.commit_wall_active    = False
        self.commit_wall_fade_done = False

        self.jump_pads    = []
        self.rotating_saws = []
        self.fake_saws    = []
        self.fireballs    = []
        self.meteors      = []
        self.death_wall_active = False

        def _s(path, vol=1.0):
            try:
                s = pygame.mixer.Sound(path); s.set_volume(vol); return s
            except Exception:
                return None

        self.commit_sound       = _s("assets/sfx/traps/commit_lock.wav", 0.6)
        self.warning_sound      = _s("assets/sfx/traps/warning.wav",     0.7)
        self.sfx_checkpoint     = _s("assets/sfx/traps/checkpoint.wav",  0.7)
        self.sfx_fireball       = _s("assets/sfx/boss/fireball.wav",     0.5)
        self.sfx_meteor         = _s("assets/sfx/boss/meteor.wav",       0.8)
        self.sfx_gate           = _s("assets/sfx/ui/gate.wav",           0.7)
        self._gate_sound_played = False

        self.checkpoints      = []
        self.active_checkpoint = None
        self.gate_frames      = gate_frames
        self.shake_timer      = 0
        self.shake_intensity  = 0

        self.enemies       = []
        self.flying_enemies = []
        self.all_enemies   = []

        level_id      = int(self.map_path.split("level")[1].split("_")[0])
        self.level_id = level_id

        # ---------- BOSS ----------
        if level_id == 5 and self.boss_sprites:
            self.boss = TerminalBoss(40 * TILE_SIZE, 5 * TILE_SIZE, self.boss_sprites)
            self.boss.vulnerable = True
        else:
            self.boss = None

        # ---------- SPIKES ----------
        if level_id == 1:
            self.spikes = [SpikeTrap(26, 15, spike_imgs, delay=18, mode="one_shot")]

        elif level_id == 2:
            self.spikes = [
                SpikeTrap(22, 14, spike_imgs, delay=10, mode="timed"),
                # SpikeTrap(31, 11, spike_imgs, delay=10, mode="always"),
                # SpikeTrap(34, 16, spike_imgs, delay=10, mode="always"),
                # SpikeTrap(41, 13, spike_imgs, delay=10, mode="always"),
                # SpikeTrap(68, 22, spike_imgs, delay=10, mode="always"),
                # SpikeTrap(74, 20, spike_imgs, delay=10, mode="always"),
                SpikeTrap(106, 23, spike_imgs, delay=10, mode="timed"),
                SpikeTrap(107, 23, spike_imgs, delay=10, mode="timed"),
                # SpikeTrap(112, 20, spike_imgs, delay=10, mode="always"),
                SpikeTrap(119, 21, spike_imgs, delay=10, mode="always"),
                SpikeTrap(122, 18, spike_imgs, delay=10, mode="always"),
                SpikeTrap(158, 24, spike_imgs, delay=10, mode="always"),
            ]

        elif level_id == 3:
            self.spikes = [
                SpikeTrap(9, 21, spike_imgs, delay=10, mode="always"),
                SpikeTrap(10, 21, spike_imgs, delay=10, mode="always"),
                SpikeTrap(20, 16, spike_imgs, delay=10, mode="always"),
                SpikeTrap(21, 16, spike_imgs, delay=10, mode="always"),
                SpikeTrap(22, 16, spike_imgs, delay=10, mode="always"),
                SpikeTrap(36, 25, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(37, 25, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(88, 23, spike_imgs, delay=10, mode="always"),
                SpikeTrap(89, 23, spike_imgs, delay=10, mode="always"),
                SpikeTrap(131, 25, spike_imgs, delay=10, mode="always"),
                SpikeTrap(132, 25, spike_imgs, delay=10, mode="always"),
                SpikeTrap(159, 24, spike_imgs, delay=10, mode="always"),
                SpikeTrap(160, 24, spike_imgs, delay=10, mode="always"),
                SpikeTrap(171, 22, spike_imgs, delay=10, mode="always"),
                SpikeTrap(172, 22, spike_imgs, delay=10, mode="always"),
                SpikeTrap(173, 22, spike_imgs, delay=10, mode="always"),
                SpikeTrap(174, 19, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(175, 19, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(176, 19, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(187, 19, spike_imgs, delay=10, mode="always"),
                SpikeTrap(195, 23, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(200, 21, spike_imgs, delay=10, mode="always"),
                SpikeTrap(209, 21, spike_imgs, delay=10, mode="always"),
                SpikeTrap(242, 23, spike_imgs, delay=18, mode="one_shot"),
            ]

        elif level_id == 4:
            self.checkpoints = [
                Checkpoint(100 * TILE_SIZE, 16 * TILE_SIZE),
                Checkpoint(209 * TILE_SIZE, 13 * TILE_SIZE)
            ]
            self.reverse_zone = pygame.Rect(100*TILE_SIZE, 0, 120*TILE_SIZE, self.world_h)
            self.normal_zone  = pygame.Rect(220*TILE_SIZE, 0, 100*TILE_SIZE, self.world_h)
            self.spikes = [
                SpikeTrap(22, 24, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(23, 24, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(24, 24, spike_imgs, delay=10, mode="always"),
                SpikeTrap(25, 24, spike_imgs, delay=10, mode="always"),
                SpikeTrap(26, 24, spike_imgs, delay=10, mode="always"),
                SpikeTrap(27, 24, spike_imgs, delay=10, mode="always"),
                SpikeTrap(54, 14, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(54, 23, spike_imgs, delay=10, mode="always"),
                SpikeTrap(136, 23, spike_imgs, delay=10, mode="always"),
                SpikeTrap(159, 23, spike_imgs, delay=10, mode="always"),
                SpikeTrap(175, 23, spike_imgs, delay=10, mode="always"),
                SpikeTrap(187, 16, spike_imgs, delay=10, mode="always"),
                SpikeTrap(188, 16, spike_imgs, delay=10, mode="always"),
                SpikeTrap(189, 16, spike_imgs, delay=10, mode="always"),
                SpikeTrap(194, 18, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(195, 18, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(196, 18, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(202, 16, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(203, 16, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(204, 16, spike_imgs, delay=10, mode="always"),
                SpikeTrap(219, 14, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(229, 14, spike_imgs, delay=0, mode="visual"),
                SpikeTrap(240, 14, spike_imgs, delay=10, mode="always"),
                SpikeTrap(250, 14, spike_imgs, delay=10, mode="always"),
                SpikeTrap(260, 14, spike_imgs, delay=10, mode="always"),
                SpikeTrap(270, 14, spike_imgs, delay=10, mode="always"),
                SpikeTrap(283, 25, spike_imgs, delay=10, mode="always"),
                SpikeTrap(299, 23, spike_imgs, delay=10, mode="always"),
                SpikeTrap(309, 23, spike_imgs, delay=10, mode="always"),
            ]
            pad_imgs = [
                pygame.image.load("assets/6 Traps/jump_pads/jump_pad1.png").convert_alpha(),
                pygame.image.load("assets/6 Traps/jump_pads/jump_pad2.png").convert_alpha(),
                pygame.image.load("assets/6 Traps/jump_pads/jump_pad3.png").convert_alpha()
            ]
            self.jump_pads = [
                JumpPad(17, 25, pad_imgs, boost_power=20),
                JumpPad(86, 28, pad_imgs, boost_power=20),
                JumpPad(179, 23, pad_imgs, boost_power=20)
            ]
            saw_img = pygame.image.load("assets/6 Traps/saw/saw1.png").convert_alpha()
            self.rotating_saws = [
                RotatingSaw(22, 14, saw_img, move_type="blink", delay=120),
                RotatingSaw(24, 14, saw_img, move_type="blink", delay=120),
                RotatingSaw(26, 14, saw_img, move_type="blink", delay=120),
                RotatingSaw(41, 20, saw_img, move_type="vertical", range_px=140, speed=5),
                RotatingSaw(64, 13, saw_img, visual_only=True),
                RotatingSaw(68, 13, saw_img, visual_only=True),
                RotatingSaw(72, 13, saw_img),
                RotatingSaw(76, 13, saw_img),
                RotatingSaw(80, 13, saw_img),
                RotatingSaw(84, 13, saw_img),
                RotatingSaw(84, 11, saw_img),
                RotatingSaw(84,  9, saw_img),
                RotatingSaw(84,  7, saw_img),
                RotatingSaw(64, 28, saw_img),
                RotatingSaw(68, 28, saw_img, visual_only=True),
                RotatingSaw(72, 28, saw_img, visual_only=True),
                RotatingSaw(76, 28, saw_img, visual_only=True),
                RotatingSaw(80, 28, saw_img, visual_only=True),
                RotatingSaw(84, 28, saw_img, visual_only=True),
                RotatingSaw(84, 26, saw_img, visual_only=True),
                RotatingSaw(84, 24, saw_img, visual_only=True),
                RotatingSaw(84, 22, saw_img, visual_only=True),
                RotatingSaw(122, 14, saw_img, move_type="horizontal", range_px=120, speed=3),
                RotatingSaw(215, 24, saw_img, activate_on_touch=True),
                RotatingSaw(225, 24, saw_img, activate_on_touch=True),
            ]
            fake_img = pygame.image.load("assets/6 Traps/saw/saw1.png").convert_alpha()
            self.fake_saws = [
                FakeSawPlatform(235, 23, fake_img),
                FakeSawPlatform(245, 23, fake_img),
                FakeSawPlatform(255, 23, fake_img),
                FakeSawPlatform(265, 23, fake_img),
            ]

        elif level_id == 5:
            self.spikes = [
                SpikeTrap(23, 94, spike_imgs, delay=10, mode="always"),
                SpikeTrap(24, 94, spike_imgs, delay=0,  mode="visual"),
                SpikeTrap(25, 94, spike_imgs, delay=0,  mode="visual"),
                SpikeTrap(29, 94, spike_imgs, delay=0,  mode="always"),
                SpikeTrap(30, 94, spike_imgs, delay=0,  mode="always"),
                SpikeTrap(31, 94, spike_imgs, delay=0,  mode="always"),
                SpikeTrap(2, 75, spike_imgs, delay=0, mode="always", direction="down"),
                SpikeTrap(3, 75, spike_imgs, delay=0, mode="always", direction="down"),
                SpikeTrap(4, 75, spike_imgs, delay=0, mode="always", direction="down"),
                SpikeTrap(5, 75, spike_imgs, delay=0, mode="always", direction="down"),
                SpikeTrap(7, 64, spike_imgs, delay=0, mode="always", direction="down"),
                SpikeTrap(8, 64, spike_imgs, delay=0, mode="always", direction="down"),
                SpikeTrap(7, 42, spike_imgs, delay=0, mode="always", direction="down"),
                SpikeTrap(8, 42, spike_imgs, delay=0, mode="always", direction="down"),
            ]
            for x in range(2, 81):
                self.spikes.append(SpikeTrap(x, 86, spike_imgs, mode="visual", direction="down"))
            for i in range(2, 88):
                self.spikes.append(SpikeTrap(i, 97, spike_imgs, mode="always", direction="up"))

            saw_img = pygame.image.load("assets/6 Traps/saw/saw1.png").convert_alpha()
            self.rotating_saws = [
                RotatingSaw(50, 80, saw_img, move_type="horizontal", range_px=160, speed=4),
                RotatingSaw(30, 80, saw_img, move_type="horizontal", range_px=160, speed=4),
                RotatingSaw(27, 52, saw_img, move_type="vertical",   range_px=140, speed=4),
                RotatingSaw(58, 52, saw_img, move_type="vertical",   range_px=140, speed=4),
                RotatingSaw(45, 21, saw_img, move_type="horizontal", range_px=580, speed=4),
                RotatingSaw(20, 29, saw_img),
                RotatingSaw(41, 29, saw_img),
                RotatingSaw(61, 29, saw_img, visual_only=True),
                RotatingSaw(80, 29, saw_img),
            ]
            pad_imgs = [
                pygame.image.load("assets/6 Traps/jump_pads/jump_pad1.png").convert_alpha(),
                pygame.image.load("assets/6 Traps/jump_pads/jump_pad2.png").convert_alpha(),
                pygame.image.load("assets/6 Traps/jump_pads/jump_pad3.png").convert_alpha()
            ]
            self.jump_pads = [
                JumpPad(82, 93, pad_imgs, boost_power=20),
                JumpPad( 7, 82, pad_imgs, boost_power=22),
                JumpPad(84, 71, pad_imgs, boost_power=20),
                JumpPad( 7, 60, pad_imgs, boost_power=22),
                JumpPad( 3, 50, pad_imgs, boost_power=20),
                JumpPad(19, 38, pad_imgs, boost_power=20),
                JumpPad(40, 38, pad_imgs, boost_power=20),
                JumpPad(60, 38, pad_imgs, boost_power=20),
                JumpPad(79, 38, pad_imgs, boost_power=20),
                JumpPad(29, 27, pad_imgs, boost_power=20),
                JumpPad(50, 27, pad_imgs, boost_power=20),
                JumpPad(69, 27, pad_imgs, boost_power=20),
            ]

        else:
            self.spikes = []

        # ---------- COMMIT ZONE (level 3) ----------
        if level_id == 3:
            self.commit_zone = pygame.Rect(52*TILE_SIZE, 0, 2*TILE_SIZE, 40*TILE_SIZE)
            self.checkpoints = [Checkpoint(149*TILE_SIZE, 19*TILE_SIZE)]

        # ---------- LEVEL 5 SYSTEMS ----------
        if level_id == 5:
            self.arena_trigger = pygame.Rect(0, 0, self.world_w, 15*TILE_SIZE)

            real_gate_x, real_gate_y =  3*TILE_SIZE, 13*TILE_SIZE
            fake_gate_x, fake_gate_y = 84*TILE_SIZE, 13*TILE_SIZE

            self.real_gate = Gate(real_gate_x, real_gate_y, self.world_h, self.gate_frames)
            self.fake_gate = Gate(fake_gate_x, fake_gate_y, self.world_h, self.gate_frames)

            for g in (self.real_gate, self.fake_gate):
                g.rect.width, g.rect.height = 48, 64
            self.real_gate.rect.topleft = (real_gate_x, real_gate_y)
            self.fake_gate.rect.topleft = (fake_gate_x, fake_gate_y)

            self.exit_rect      = pygame.Rect(real_gate_x, real_gate_y, TILE_SIZE*2, TILE_SIZE*4)
            self.fake_exit_rect = pygame.Rect(fake_gate_x, fake_gate_y, TILE_SIZE*2, TILE_SIZE*4)
            self.fake_gate.anim_speed = 2
            self.fake_gate.speed      = 12

            self.meteors         = []
            self.meteor_cooldown = 180
            self.meteor_timer    = 0

            self.arena_locked     = False
            self.boss_active      = False
            self.boss_timer       = 0
            self.boss_duration    = 900
            self.real_gate_ready  = False

            self.death_wall_active = False
            self.death_wall_y      = self.world_h + 100
            self.death_wall_speed  = 1

            self.fireballs        = []
            self.fireball_cooldown = 120
            self.fireball_timer   = 0

            self.checkpoints = [
                Checkpoint( 77*TILE_SIZE, 59*TILE_SIZE),
                Checkpoint( 50*TILE_SIZE, 37*TILE_SIZE),
                Checkpoint(200*TILE_SIZE, 12*TILE_SIZE),
                Checkpoint(240*TILE_SIZE,  5*TILE_SIZE),
            ]

        # ---------- LAYOUT / ENEMIES ----------
        layout     = LEVEL_LAYOUTS[level_id]
        self.layout = layout

        if "flying_enemies" in layout:
            for f in layout["flying_enemies"]:
                sx, sy    = f["x"]*TILE_SIZE, f["y"]*TILE_SIZE
                range_px  = f.get("range", 150)
                hp        = f.get("hp", 10)
                enemy     = FlyingEnemy(sx, sy, sx-range_px, sx+range_px, hp)
                self.flying_enemies.append(enemy)
                self.all_enemies.append(enemy)

        self.bridges = []
        for tx, ty, mode, delay in LEVEL_BRIDGES.get(level_id, []):
            self.bridges.append(BreakableBridge(tx, ty, bridge_imgs, mode=mode, delay=delay))
        for i in range(len(self.bridges)-1):
            if self.bridges[i].mode == "chain" and self.bridges[i+1].mode == "chain":
                self.bridges[i].next_bridge = self.bridges[i+1]

        self.traps   = self.spikes + self.bridges
        enemy_hp     = LEVEL_ENEMY_HP.get(level_id, ENEMY_HP)

        if "enemies" in layout:
            for ed in layout["enemies"]:
                lx = ed["left"]*TILE_SIZE; rx = ed["right"]*TILE_SIZE
                y  = ed["y"]*TILE_SIZE - 32
                e  = Enemy(lx, y, lx, rx, enemy_hp, ed.get("behavior","passive"), level_id)
                self.enemies.append(e); self.all_enemies.append(e)
        elif all(k in layout for k in ("enemy_left","enemy_right","enemy_y")):
            lx = layout["enemy_left"]*TILE_SIZE; rx = layout["enemy_right"]*TILE_SIZE
            y  = layout["enemy_y"]*TILE_SIZE - 32
            for i in range(self.enemy_count):
                e = Enemy(lx+i*40, y, lx, rx, enemy_hp, "passive", level_id)
                self.enemies.append(e); self.all_enemies.append(e)

        self.gate_x = layout["gate_x"]*TILE_SIZE
        self.gate_y = layout.get("gate_y", 0)*TILE_SIZE

        if self.enemies:
            fe = self.enemies[0]
            self.enemy_trigger = pygame.Rect(fe.left-6*TILE_SIZE, fe.rect.y-2*TILE_SIZE,
                                             10*TILE_SIZE, 4*TILE_SIZE)
        else:
            self.enemy_trigger = None

    # ------------------------------------------------------------------
    def load_map(self, path):
        tiles, solids = [], []
        with open(path, encoding="utf-8") as f:
            for y, row in enumerate(csv.reader(f)):
                for x, t in enumerate(row):
                    t = int(t)
                    if t >= 0:
                        r = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        tiles.append((t, r))
                        if t in GROUND_TILES:
                            solids.append(r)
        return tiles, solids

    # ------------------------------------------------------------------
    def trigger_chain(self):
        if self.chain_active:
            return
        self.chain_active          = True
        self.commit_wall_active    = True
        self.commit_wall_alpha     = 0
        self.commit_wall_fade_done = False
        self.commit_pulse_timer    = 10
        if hasattr(self, "commit_sound") and self.commit_sound:
            self.commit_sound.play()
        self.spawn_flying_enemy = True
        self.commit_wall = pygame.Rect(self.commit_zone.right, self.commit_zone.top,
                                       TILE_SIZE, self.commit_zone.height)

    # ------------------------------------------------------------------
    def update(self, player):

        if self.level_id == 5 and not self.boss_active:
            if player.rect.colliderect(self.arena_trigger):
                self.death_wall_active = True
                self.boss_active       = True
                self.boss_timer        = self.boss_duration
                self.shake_timer       = 60
                self.shake_intensity   = 8
                if hasattr(self, "warning_sound") and self.warning_sound:
                    self.warning_sound.play()

        if self.level_id == 5 and self.boss_active and not self.real_gate_ready:
            if self.boss_timer > 0:
                self.boss_timer -= 1
            else:
                self.real_gate_ready = True
                if self.sfx_gate and not self._gate_sound_played:
                    self.sfx_gate.play()
                    self._gate_sound_played = True

        if self.level_id == 5:
            self.real_gate.update()
            self.fake_gate.update()
            if self.real_gate_ready:
                self.real_gate.open(); self.fake_gate.open()
            if self.real_gate.state == "open" and player.rect.colliderect(self.exit_rect):
                return "level_complete"
            if self.fake_gate.state == "open" and player.rect.colliderect(self.fake_exit_rect):
                return "player_dead"

        if self.commit_zone and not self.chain_active:
            if player.rect.colliderect(self.commit_zone) and not self._commit_entered:
                self._commit_entered = True
                self.trigger_chain()

        for i, cp in enumerate(self.checkpoints):
            if not cp.active and player.rect.colliderect(cp.rect):
                cp.active              = True
                self.active_checkpoint = cp
                self.active_checkpoint_index = i
                if self.sfx_checkpoint: self.sfx_checkpoint.play()
                if self.level_id == 4:
                    player.reverse_controls = (i == 0)

        if self.chain_active and hasattr(self, "commit_wall"):
            if player.rect.colliderect(self.commit_wall):
                player.rect.left = self.commit_wall.right

        if hasattr(self, "commit_pulse_timer") and self.commit_pulse_timer > 0:
            self.commit_pulse_timer -= 1

        if self.boss and self.boss_active:
            self.boss.update(player, self.solids)

        for enemy in self.flying_enemies:
            if not enemy.alive:
                continue
            px = player.rect.centerx
            enemy.state = "attack" if enemy.left_bound <= px <= enemy.right_bound else "idle"
            enemy.update(player)
            if self.level_id == 5 and enemy.rect.bottom > 60*TILE_SIZE:
                enemy.rect.bottom = 60*TILE_SIZE

        # --- BOSS FIREBALL ---
        if self.level_id == 5 and self.boss_active:
            self.fireball_timer -= 1
            if self.fireball_timer <= 0:
                dx = player.rect.centerx - self.boss.rect.centerx
                dy = player.rect.centery - self.boss.rect.centery
                dist = max(1, (dx*dx + dy*dy)**0.5)
                spd  = 6
                self.fireballs.append({
                    "x": float(self.boss.rect.centerx),
                    "y": float(self.boss.rect.centery),
                    "vx": dx/dist*spd,
                    "vy": dy/dist*spd,
                    "angle": 0.0,
                })
                if self.sfx_fireball: self.sfx_fireball.play()
                self.fireball_timer = self.fireball_cooldown

            for fb in list(self.fireballs):
                fb["x"]     += fb["vx"]
                fb["y"]     += fb["vy"]
                fb["angle"]  = (fb.get("angle", 0) + 8) % 360
                fb["angle"]  = (fb["angle"] + 8) % 360   # spin
                if pygame.Rect(fb["x"]-5, fb["y"]-5, 10, 10).colliderect(player.rect):
                    player.take_damage()
                    self.fireballs.remove(fb)

        # --- METEOR ---
        if self.level_id == 5 and self.boss_active:
            self.meteor_timer -= 1
            if self.meteor_timer <= 0:
                self.meteors.append({
                    "x": float(player.rect.centerx),
                    "y": -50.0,
                    "vy": 8,
                    "warn_timer": 60,
                })
                self.meteor_timer = self.meteor_cooldown

            for m in list(self.meteors):
                if m["warn_timer"] > 0:
                    m["warn_timer"] -= 1
                    # play sound exactly when warning ends and meteor starts falling
                    if m["warn_timer"] == 0:
                        if self.sfx_meteor: self.sfx_meteor.play()
                else:
                    m["y"] += m["vy"]
                    # hitbox matches visual size (64x96 sprite, bottom-aligned)
                    hit_rect = pygame.Rect(m["x"] - 28, m["y"] - 80, 56, 80)
                    if hit_rect.colliderect(player.rect):
                        self.meteors.remove(m)
                        return "player_dead"
                    # remove if fallen off screen
                    if m["y"] > self.world_h + 100:
                        self.meteors.remove(m)

        for spike in self.spikes:
            if spike.update(player) == "kill":
                return "player_dead"
        for pad in self.jump_pads:
            pad.update(player)
        for saw in self.rotating_saws:
            if saw.update(player) == "kill":
                return "player_dead"
        for bridge in self.bridges:
            on_bridge = player.rect.colliderect(bridge.rect)
            if bridge.collidable and on_bridge and not bridge.was_on_bridge:
                bridge.on_player_step()
            bridge.was_on_bridge = on_bridge
            bridge.update()

        if self.commit_wall_active and not self.commit_wall_fade_done:
            self.commit_wall_alpha += 8
            if self.commit_wall_alpha >= 160:
                self.commit_wall_alpha     = 160
                self.commit_wall_fade_done = True

        for enemy in self.enemies:
            if not enemy.active:
                # activate when player enters a wide trigger zone
                arect = pygame.Rect(enemy.left - 6*TILE_SIZE, enemy.rect.y - 3*TILE_SIZE,
                                    (enemy.right - enemy.left) + 12*TILE_SIZE, 6*TILE_SIZE)
                if player.rect.colliderect(arect):
                    enemy.active = True
            if enemy.alive and enemy.active:
                enemy.update(player, self.solids)

        if self.level_id == 5 and self.death_wall_active:
            self.death_wall_y -= self.death_wall_speed
            if player.rect.bottom >= self.death_wall_y:
                return "void_death"

        return None

    # ------------------------------------------------------------------
    def reset(self):
        for s in self.spikes:   s.reset()
        for b in self.bridges:  b.reset()

    # ------------------------------------------------------------------
    def draw(self, screen, cam_x, cam_y, tile_img):
        for t, r in self.tiles:
            screen.blit(tile_img(t), (r.x - cam_x, r.y - cam_y))

        for s in self.spikes:         s.draw(screen, cam_x, cam_y)
        for b in self.bridges:        b.draw(screen, cam_x, cam_y)
        for e in self.enemies:        e.draw(screen, cam_x, cam_y)

        if self.commit_zone and self.commit_wall_active:
            wsurf = pygame.Surface((self.commit_wall.w, self.commit_wall.h), pygame.SRCALPHA)
            bc = (170, 175, 180, self.commit_wall_alpha)
            ec = (130, 135, 140, self.commit_wall_alpha)
            wsurf.fill(bc)
            pygame.draw.rect(wsurf, ec, (0, 0, 4, wsurf.get_height()))
            pygame.draw.rect(wsurf, ec, (wsurf.get_width()-4, 0, 4, wsurf.get_height()))
            screen.blit(wsurf, (self.commit_wall.x-cam_x, self.commit_wall.y-cam_y))

        if hasattr(self, "commit_pulse_timer") and self.commit_pulse_timer > 0:
            pa = int(200 * (self.commit_pulse_timer / 10))
            ps = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ps.fill((220, 220, 220, pa))
            screen.blit(ps, (0, 0))

        for cp  in self.checkpoints:    cp.draw(screen, cam_x, cam_y)
        for en  in self.flying_enemies: en.draw(screen, cam_x, cam_y)
        for pad in self.jump_pads:      pad.draw(screen, cam_x, cam_y)
        for saw in self.rotating_saws:  saw.draw(screen, cam_x, cam_y)
        for fk  in self.fake_saws:      fk.draw(screen, cam_x, cam_y)

        if self.boss and self.boss_active:
            self.boss.draw(screen, cam_x, cam_y)

        # ── FIREBALLS — sprite with spin ─────────────────────────────
        if self.level_id == 5:
            for fb in self.fireballs:
                rotated = pygame.transform.rotate(_FIREBALL_SURF, fb["angle"])
                rx = int(fb["x"] - cam_x) - rotated.get_width()  // 2
                ry = int(fb["y"] - cam_y) - rotated.get_height() // 2
                screen.blit(rotated, (rx, ry))

        # ── SURVIVAL TIMER — polished cyber bar ─────────────────────
        if self.level_id == 5 and self.boss_active and not self.real_gate_ready:
            seconds  = max(0, self.boss_timer // 60)
            progress = max(0.0, self.boss_timer / self.boss_duration)

            BAR_W, BAR_H = 220, 18
            bx = WIDTH // 2 - BAR_W // 2
            by = 40

            # dark panel behind everything
            panel = pygame.Surface((BAR_W + 60, BAR_H + 22), pygame.SRCALPHA)
            panel.fill((0, 0, 0, 160))
            screen.blit(panel, (bx - 30, by - 4))

            # filled bar — colour shifts red→orange→yellow as time runs out
            r = 255
            g = max(0, min(255, int(200 * progress)))
            bar_col = (r, g, 0)
            fill_w  = max(0, int(BAR_W * progress))
            if fill_w > 0:
                pygame.draw.rect(screen, bar_col,      (bx, by + 10, fill_w, BAR_H))
                # bright top edge shimmer
                pygame.draw.rect(screen, (255, 255, 200), (bx, by + 10, fill_w, 2))

            # bar outline
            pygame.draw.rect(screen, (180, 180, 180), (bx, by + 10, BAR_W, BAR_H), 1)

            # "SURVIVE" label left, seconds right
            lf  = pygame.font.SysFont("Courier New", 13, bold=True)
            tf  = pygame.font.SysFont("Courier New", 15, bold=True)

            lbl = lf.render("SURVIVE", True, (200, 200, 200))
            sec = tf.render(f"{seconds}s", True, bar_col)

            # shadow
            lbl_s = lf.render("SURVIVE", True, (0, 0, 0))
            sec_s = tf.render(f"{seconds}s", True, (0, 0, 0))
            screen.blit(lbl_s, (bx + 1,         by + 1))
            screen.blit(sec_s, (bx + BAR_W - sec.get_width() + 1, by + 1))
            screen.blit(lbl,   (bx,              by))
            screen.blit(sec,   (bx + BAR_W - sec.get_width(),     by))

            # urgent flash when <= 5 seconds
            if seconds <= 5 and (pygame.time.get_ticks() // 200) % 2 == 0:
                flash = pygame.Surface((BAR_W + 60, BAR_H + 22), pygame.SRCALPHA)
                flash.fill((255, 0, 0, 35))
                screen.blit(flash, (bx - 30, by - 4))

        # ── LEVEL 5 GATES ────────────────────────────────────────────
        if self.level_id == 5:
            self.real_gate.draw(screen, cam_x, cam_y)
            self.fake_gate.draw(screen, cam_x, cam_y)

        # ── METEORS — sprite with warning ring ───────────────────────
        if self.level_id == 5:
            for m in self.meteors:
                if m["warn_timer"] > 0:
                    # pulsing warning on the floor
                    pulse = abs(math.sin(pygame.time.get_ticks() * 0.008))
                    warn  = _WARNING_SURF.copy()
                    warn.set_alpha(int(80 + 120 * pulse))
                    wx = int(m["x"] - cam_x) - warn.get_width()  // 2
                    wy = int(self.world_h - cam_y) - warn.get_height() // 2
                    screen.blit(warn, (wx, wy))
                else:
                    # falling meteor — animated fire sprite if available
                    global _METEOR_ANIM_IDX
                    if _METEOR_FRAMES:
                        _METEOR_ANIM_IDX = (_METEOR_ANIM_IDX + 0.35) % len(_METEOR_FRAMES)
                        frame = _METEOR_FRAMES[int(_METEOR_ANIM_IDX)]
                        mx = int(m["x"] - cam_x) - frame.get_width()  // 2
                        my = int(m["y"] - cam_y) - frame.get_height() + 16
                        screen.blit(frame, (mx, my))
                    else:
                        # procedural fallback
                        mx = int(m["x"] - cam_x) - _METEOR_SURF.get_width() // 2
                        my = int(m["y"] - cam_y)
                        screen.blit(_METEOR_SURF, (mx, my))
                    # ground glow as it gets close
                    dist = self.world_h - m["y"]
                    if dist < 200:
                        ga = max(0, min(255, int(200 * (1 - dist/200))))
                        glow = pygame.Surface((40, 12), pygame.SRCALPHA)
                        pygame.draw.ellipse(glow, (255, 100, 0, ga), (0, 0, 40, 12))
                        screen.blit(glow, (mx - 8, int(self.world_h - cam_y) - 6))

        # ── DEATH WALL ───────────────────────────────────────────────
        if self.level_id == 5 and self.death_wall_active:
            wall_y = int(self.death_wall_y - cam_y)
            wall_h = max(0, HEIGHT - wall_y + self.world_h)

            # main body: deep crimson fill
            pygame.draw.rect(screen, (80, 0, 0),
                             (0, wall_y, self.world_w, wall_h))

            # pulsing glow overlay
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.004))
            glow_alpha = int(60 + 80 * pulse)
            glow_surf = pygame.Surface((self.world_w, wall_h), pygame.SRCALPHA)
            glow_surf.fill((180, 0, 0, glow_alpha))
            screen.blit(glow_surf, (0, wall_y))

            # bright hot leading edge
            edge_alpha = int(180 + 75 * pulse)
            edge_surf = pygame.Surface((self.world_w, 6), pygame.SRCALPHA)
            edge_surf.fill((255, 60, 60, edge_alpha))
            screen.blit(edge_surf, (0, wall_y))

            # softer glow halo just above the edge
            for offset, alpha in [(8, 80), (16, 50), (28, 25)]:
                halo = pygame.Surface((self.world_w, offset), pygame.SRCALPHA)
                halo.fill((255, 30, 30, int(alpha * pulse + alpha * 0.4)))

                screen.blit(halo, (0, wall_y - offset))
