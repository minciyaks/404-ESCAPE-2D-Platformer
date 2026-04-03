import random
import pygame
import sys

from config import *
from player import Player
from level import Level
from gate import Gate

pygame.init()

# =========================
# WINDOW
# =========================
WIN_W, WIN_H = 1280, 720
window       = pygame.display.set_mode((WIN_W, WIN_H))
screen       = pygame.Surface((WIDTH, HEIGHT))

def flip():
    pygame.transform.scale(screen, (WIN_W, WIN_H), window)
    pygame.display.flip()

pygame.display.set_caption("404 Escape")
clock = pygame.time.Clock()

# --- MENU ASSETS & STATE ---
menu_bg = None
try:
    menu_bg = pygame.transform.scale(
        pygame.image.load("assets/menu/mainmenu_bg.png").convert(),
        (WIDTH, HEIGHT)
    )
except:
    try:
        menu_bg = pygame.transform.scale(
            pygame.image.load("assets/menu/background.png").convert(),
            (WIDTH, HEIGHT)
        )
    except:
        menu_bg = None

# ── UI SOUND EFFECTS ──────────────────────────────────────────────────
def _ui_sfx(path, vol=1.0):
    try:
        s = pygame.mixer.Sound(path); s.set_volume(vol); return s
    except Exception:
        return None

sfx_button    = _ui_sfx("assets/sfx/ui/button.wav",    0.6)
sfx_scrolling = _ui_sfx("assets/sfx/ui/scrolling.wav", 0.5)
sfx_victory   = _ui_sfx("assets/sfx/ui/victory.wav",   0.8)
sfx_keyboard  = _ui_sfx("assets/sfx/ui/keyboard.wav",  0.4)
sfx_main_menu = _ui_sfx("assets/sfx/ui/main_menu.wav", 0.7)
sfx_gate      = _ui_sfx("assets/sfx/ui/gate.wav",      0.8)
sfx_back      = _ui_sfx("assets/sfx/ui/back.wav",      0.6)

# ── MUSIC ─────────────────────────────────────────────────────────────
def _play_music(path, volume=0.35, loops=-1):
    """Load and play a music track, silently ignore if file missing."""
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops)
    except Exception:
        pass

def _stop_music():
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


# ── UI SOUND EFFECTS ─────────────────────────────────────────────────
# Pre-build scanline surface
scanline_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for y in range(0, HEIGHT, 2):
    pygame.draw.line(scanline_surf, (0, 0, 0, 60), (0, y), (WIDTH, y))

# Glitch timer for title
menu_glitch_timer  = 0
menu_glitch_offset = 0
menu_frame         = 0

# ---------------- GAME STATES ----------------
GAME_INTRO        = "intro"
GAME_MENU         = "menu"
GAME_NAME         = "name"
GAME_HOWTO        = "howto"
GAME_PLAY         = "play"
GAME_VICTORY      = "victory"
GAME_DEAD         = "dead"
GAME_END          = "end"
GAME_LEVEL_SELECT = "level_select"
GAME_PAUSE        = "pause"

ending_alpha = 0
ending_phase         = 0   # 0=quote  1=credits
ending_credits_alpha = 0

game_state  = GAME_INTRO
death_timer = 0

cam_x = 0.0
cam_y = 0.0

death_cam_x   = 0.0
respawning    = False
skip_draw     = False
fade_timer    = 0
shutdown_transition = False
shutdown_alpha      = 0
name_locked   = False

current_level = 1
MAX_LEVELS    = 5

unlocked_level = 1

menu_options = ["Start Game", "Level Select", "How to Play", "Quit"]
menu_index   = 0
player_name  = ""

pause_options = ["Resume", "Restart Level", "Level Select", "Quit to Menu"]
pause_index   = 0

# Scroll state for How To Play
howto_scroll = 0

LEVEL_NAMES = {
    1: "Awakening",
    2: "Pressure",
    3: "Chaos",
    4: "Descent",
    5: "Terminal"
}

INTRO_SCENES = [
    ("assets/intro/intro1.png", "Another day. Another shift. The world outside is gray."),
    ("assets/intro/intro2.png", "It didn't arrive by mail. It wasn't a console. It was a file that shouldn't have been there."),
    ("assets/intro/intro3.png", "The code didn't just change the screen... it changed me."),
    ("assets/intro/intro4.png", "Wait—no! Is this... inside the screen?! Something just pulled me in!")
]

intro_imgs  = [pygame.transform.scale(pygame.image.load(i).convert(), (WIDTH, HEIGHT))
               for i, _ in INTRO_SCENES]
intro_font  = pygame.font.SysFont(None, 38)
hint_font   = pygame.font.SysFont(None, 24)
intro_index = 0
intro_alpha = 0

# =========================
# LOAD ASSETS
# =========================
LEVEL_TILESETS = {
    1: "assets/7 Levels/Tiled/Tileset.png",
    2: "assets/7 Levels/Tiled/Tileset.png",
    3: "assets/7 Levels/Tiled/Tileset.png",
    4: "assets/7 Levels/Tiled/Tileset.png",
    5: "assets/7 Levels/Tiled/GUI.png"
}


def tile_image(t):
    return tileset.subsurface(
        (t % COLS * TILE_SIZE,
         t // COLS * TILE_SIZE,
         TILE_SIZE, TILE_SIZE)
    )


spike_images = {
    "idle":    pygame.image.load("assets/6 Traps/spike/idle.png").convert_alpha(),
    "popping": pygame.image.load("assets/6 Traps/spike/popping.png").convert_alpha(),
    "active":  pygame.image.load("assets/6 Traps/spike/active.png").convert_alpha(),
    "used":    pygame.image.load("assets/6 Traps/spike/used.png").convert_alpha(),
}

bridge_images = {
    "idle":   pygame.image.load("assets/6 Traps/bridge/idle.png").convert_alpha(),
    "active": pygame.image.load("assets/6 Traps/bridge/active.png").convert_alpha(),
    "break":  pygame.image.load("assets/6 Traps/bridge/break.png").convert_alpha(),
}

gate_frames = [
    pygame.image.load(f"assets/gate/gate_{i}.png").convert_alpha()
    for i in range(6)
]


def load_strip(path, w, h):
    sheet = pygame.image.load(path).convert_alpha()
    return [sheet.subsurface((i * w, 0, w, h))
            for i in range(sheet.get_width() // w)]


boss_sprites = {
    "idle": load_strip("assets/4 Enemies/BOSS/Idle.png", 32, 32),
    "run":  load_strip("assets/4 Enemies/BOSS/Run.png",  32, 32),
    "hit":  load_strip("assets/4 Enemies/BOSS/Hit.png",  32, 32),
    "jump": load_strip("assets/4 Enemies/BOSS/Jump.png", 32, 32),
    "fall": load_strip("assets/4 Enemies/BOSS/Fall.png", 32, 32),
}
for k, v in boss_sprites.items():
    print(k, len(v))

# ── HEART SPRITE SHEET ─────────────────────────────────────────────
# frame_007 = full red heart  |  frame_002 = empty dark heart
# Pre-baked at HUD display size (20px) — never scaled per frame.
_HEART_DISPLAY = 20
_heart_full  = pygame.transform.scale(
    pygame.image.load("assets/hud/hp1.png").convert_alpha(),
    (_HEART_DISPLAY, _HEART_DISPLAY)
)
_heart_empty = pygame.transform.scale(
    pygame.image.load("assets/hud/hp2.png").convert_alpha(),
    (_HEART_DISPLAY, _HEART_DISPLAY)
)
# Pre-baked dark overlay — applied over bg every frame (no per-frame alloc)
_bg_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_bg_overlay.fill((0, 0, 0, 50))

# Pre-baked dark overlay — applied over bg every frame, no per-frame alloc
_bg_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
_bg_overlay.fill((0, 0, 0, 50))

# draw_hud surface cache — avoids re-allocating per frame
_hud_card_cache = {}   # key: (w,h) → Surface

level_bg     = None
ending_image = pygame.transform.scale(
    pygame.image.load("assets/ending/home.jpg").convert(),
    (WIDTH, HEIGHT)
)

LEVEL_RULES = {
    1: {"spike_delay": 18, "bridge_break": False, "enemy_count": 1, "flying_enemy": False},
    2: {"spike_delay": 10, "bridge_break": True,  "enemy_count": 1, "flying_enemy": False},
    3: {"spike_delay": 6,  "bridge_break": True,  "enemy_count": 1, "flying_enemy": True},
    4: {"spike_delay": 6,  "bridge_break": True,  "enemy_count": 0, "flying_enemy": True},
    5: {"spike_delay": 6,  "enemy_count": 1,      "flying_enemy": False},
}


def load_level(level_id, silent=False):
    global level, player, gate, cam_x, cam_y, level_bg, tileset, COLS
    # ── start correct music track for this level ──────────────────────
    # silent=True is used for the very first load at startup so the
    # intro music (started just before the main loop) is never interrupted.
    if not silent:
        if level_id in (1, 2):
            _play_music("assets/sfx/music/level1_2.wav", volume=0.35)
        elif level_id in (3, 4):
            _play_music("assets/sfx/music/level3_4.wav", volume=0.35)
        elif level_id == 5:
            _play_music("assets/sfx/music/level5.wav",   volume=0.40)

    map_path     = f"maps/level{level_id}_ground.csv"
    tileset_path = LEVEL_TILESETS[level_id]
    tileset      = pygame.image.load(tileset_path).convert_alpha()
    COLS         = tileset.get_width() // TILE_SIZE

    rules  = LEVEL_RULES.get(level_id, {})
    level  = Level(map_path, spike_images, bridge_images, rules, boss_sprites, gate_frames)
    player = Player(level.solids)

    # ── per-level HP ──────────────────────────────────────────────────
    # LEVEL_PLAYER_HP in config.py is the single place to tune difficulty.
    # max_hp drives both the HUD heart count and respawn restoration.
    player_max_hp    = LEVEL_PLAYER_HP.get(level_id, PLAYER_MAX_HP)
    player.max_hp    = player_max_hp
    player.hp        = player_max_hp
    # ─────────────────────────────────────────────────────────────────

    if level_id == 5:
        player.rect.topleft = (2 * TILE_SIZE, 94 * TILE_SIZE)
        player.spawn        = player.rect.topleft

    player.reverse_controls = rules.get("reverse_controls", False)
    gate = Gate(level.gate_x, level.gate_y, level.world_h, gate_frames)

    bg_path  = LEVEL_BACKGROUNDS[level_id]
    level_bg = pygame.transform.scale(
        pygame.image.load(bg_path).convert(), (WIDTH, HEIGHT)
    )

    cam_x = float(max(0, min(
        player.rect.centerx - WIDTH // 2,
        level.world_w - WIDTH
    )))
    cam_y = float(max(0, min(
        player.rect.centery - HEIGHT // 2,
        level.world_h - HEIGHT
    )))

    print(f"Loaded Level {level_id} rules:", rules,
          f" | player HP: {player_max_hp}/{player_max_hp}")


load_level(current_level, silent=True)   # assets only — intro music starts below


# =========================
# HUD / HELPERS
# =========================
def _draw_esc_pause_badge(screen):
    """ESC | PAUSE badge pinned to bottom-right corner."""
    import pygame as _pg
    PAD     = 10
    H       = 22
    kf      = _pg.font.SysFont("Courier New", 13, bold=True)
    vf      = _pg.font.SysFont("Courier New", 13)

    esc_surf  = kf.render("ESC",   True, (220, 220, 220))
    sep_surf  = vf.render("|",     True, (100, 120, 130))
    pau_surf  = vf.render("PAUSE", True, (180, 190, 200))

    inner_pad = 6
    div_gap   = 5
    total_w   = inner_pad + esc_surf.get_width() + div_gap + sep_surf.get_width() + div_gap + pau_surf.get_width() + inner_pad
    bx = WIDTH  - PAD - total_w
    by = HEIGHT - PAD - H

    # dark panel
    panel = _pg.Surface((total_w, H), _pg.SRCALPHA)
    panel.fill((10, 12, 16, 210))
    screen.blit(panel, (bx, by))
    # border
    _pg.draw.rect(screen, (60, 75, 85), (bx, by, total_w, H), 1)
    # top bright edge
    _pg.draw.line(screen, (80, 100, 115), (bx, by), (bx + total_w, by), 1)

    # blit text pieces
    ty = by + (H - esc_surf.get_height()) // 2
    cx = bx + inner_pad
    screen.blit(esc_surf,  (cx, ty));                           cx += esc_surf.get_width()  + div_gap
    screen.blit(sep_surf,  (cx, ty));                           cx += sep_surf.get_width()  + div_gap
    screen.blit(pau_surf,  (cx, ty))


def draw_hud(screen, player, name):
    PAD        = 10
    HEART_SIZE = 22
    HEART_GAP  = 5
    NUM_HEARTS = HUD_HEARTS   # always 5, every level

    h_full  = pygame.transform.scale(_heart_full,  (HEART_SIZE, HEART_SIZE))
    h_empty = pygame.transform.scale(_heart_empty, (HEART_SIZE, HEART_SIZE))

    # Anchor row to top-right corner
    total_w = NUM_HEARTS * HEART_SIZE + (NUM_HEARTS - 1) * HEART_GAP
    start_x = WIDTH - PAD - total_w

    # How many HP points equal one full heart for this level.
    max_hp       = getattr(player, "max_hp", PLAYER_MAX_HP)
    hp_per_heart = max_hp / NUM_HEARTS
    current_hp   = max(0, player.hp)

    # Hearts drawn left to right, but drain RIGHT TO LEFT.
    # i=0 is leftmost (last to empty), i=4 rightmost (first to empty).
    # slot maps display index to HP bucket: slot 0 = rightmost HP bucket.
    for i in range(NUM_HEARTS):
        slot     = NUM_HEARTS - 1 - i          # 0 = rightmost bucket
        high_val = max_hp - slot * hp_per_heart
        low_val  = max_hp - (slot + 1) * hp_per_heart
        fill     = (current_hp - low_val) / hp_per_heart
        fill     = max(0.0, min(1.0, fill))

        x = start_x + i * (HEART_SIZE + HEART_GAP)

        if fill <= 0:
            screen.blit(h_empty, (x, PAD))
        elif fill >= 1:
            screen.blit(h_full, (x, PAD))
        else:
            screen.blit(h_empty, (x, PAD))
            filled_w  = max(1, int(HEART_SIZE * fill))
            clip_surf = h_full.subsurface((0, 0, filled_w, HEART_SIZE))
            screen.blit(clip_surf, (x, PAD))

    # ESC | PAUSE badge pinned bottom-right
    _draw_esc_pause_badge(screen)

def draw_text_box_centered(text, font, color, center_x, y, max_width, alpha, line_spacing=6):
    words, lines, current = text.split(" "), [], ""
    for word in words:
        test = current + word + " "
        if font.size(test)[0] <= max_width:
            current = test
        else:
            lines.append(current)
            current = word + " "
    lines.append(current)

    total_h = sum(font.size(l)[1] + line_spacing for l in lines)
    start_y = y - total_h // 2
    for i, line in enumerate(lines):
        surf = font.render(line, True, color).convert_alpha()
        surf.set_alpha(alpha)
        screen.blit(surf, (center_x - surf.get_width() // 2,
                           start_y + i * (surf.get_height() + line_spacing)))


def draw_intro():
    global intro_alpha
    screen.blit(intro_imgs[intro_index], (0, 0))
    ov = pygame.Surface((WIDTH, HEIGHT)); ov.set_alpha(140); ov.fill((0, 0, 0))
    screen.blit(ov, (0, 0))
    intro_alpha = min(255, intro_alpha + 4)
    draw_text_box_centered(INTRO_SCENES[intro_index][1], intro_font,
                           (230, 230, 230), WIDTH // 2, HEIGHT - 140,
                           WIDTH - 160, intro_alpha)
    if intro_alpha > 120:
        h = hint_font.render("Press ENTER", True, (180, 180, 180)).convert_alpha()
        h.set_alpha(min(255, intro_alpha + 40))
        screen.blit(h, (WIDTH // 2 - h.get_width() // 2, HEIGHT - 60))


def draw_ending():
    global ending_alpha, ending_credits_alpha

    tx = WIDTH // 2

    # ── background image always visible ──────────────────────────────
    screen.blit(ending_image, (0, 0))

    # warm dark gradient — heavier at bottom for text readability
    grad = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for row in range(HEIGHT):
        t   = row / HEIGHT
        alp = int(10 + t * 160)
        pygame.draw.line(grad, (8, 5, 1, alp), (0, row), (WIDTH, row))
    screen.blit(grad, (0, 0))

    # ── PHASE 0 — quote fades in at bottom ───────────────────────────
    if ending_phase == 0:
        ending_alpha = min(255, ending_alpha + 2)

        # quote text — sits just above the bottom third
        qf    = pygame.font.SysFont("Courier New", 26, bold=True)
        quote = "You made it out.  The system is off."
        # shadow
        qs = qf.render(quote, True, (0, 0, 0))
        qs.set_alpha(ending_alpha)
        screen.blit(qs, (tx - qs.get_width()//2 + 2, HEIGHT - 80 + 2))
        # warm gold text
        qt = qf.render(quote, True, (255, 230, 110))
        qt.set_alpha(ending_alpha)
        screen.blit(qt, (tx - qt.get_width()//2, HEIGHT - 80))

        # hint — appears after quote is visible
        if ending_alpha > 180:
            import math
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.002))
            ha  = min(255, int((ending_alpha - 180) * 4 * (0.55 + 0.45 * pulse)))
            hf  = pygame.font.SysFont("Courier New", 15)
            h   = hf.render("Press  ENTER  to continue", True, (200, 195, 180))
            h.set_alpha(ha)
            screen.blit(h, (tx - h.get_width()//2, HEIGHT - 30))

    # ── PHASE 1 — credits card fades in ──────────────────────────────
    elif ending_phase == 1:
        ending_credits_alpha = min(255, ending_credits_alpha + 3)
        ca = ending_credits_alpha

        # ── credits card ─────────────────────────────────────────────
        # YOU can customise the lines below — add your own name, links etc.
        CREDITS = [
            ("404 ESCAPE",          "",                             True,  (255, 210, 60),      None),

            ("",                    "",                             False, None,                None),

            ("Created by",          "Minciya KS",                   False, (160, 180, 160),     (220, 215, 200)),
            ("Role",                "Solo Developer",               False, (160, 180, 160),     (220, 215, 200)),

            ("",                    "",                             False, None,                None),

            ("Map Design",          "Tiled Map Editor",             False, (160, 180, 160),     (220, 215, 200)),
            ("Assets",              "Craftpix.net, itch.io",        False, (160, 180, 160),     (220, 215, 200)),

            ("",                    "",                             False, None,                None),

            ("Music",               "Zakiro",                       False, (160, 180, 160),     (220, 215, 200)),
            ("SFX",                 "Various Free Sources",         False, (160, 180, 160),     (220, 215, 200)),

            ("",                    "",                             False, None,                None),

            ("Special Thanks",      "opengameart.org",              False, (160, 180, 160),     (220, 215, 200)),
        ]

        # measure card height
        tf  = pygame.font.SysFont("Courier New", 20, bold=True)
        cf  = pygame.font.SysFont("Courier New", 15)
        ROW_H   = cf.get_linesize() + 5
        TITLE_H = tf.get_linesize() + 8
        CARD_PAD = 20

        total_h = CARD_PAD
        for _, _, bold, lc, _ in CREDITS:
            if lc is None:
                total_h += 8   # spacer
            elif bold:
                total_h += TITLE_H
            else:
                total_h += ROW_H
        total_h += CARD_PAD

        CARD_W = 480
        cx = tx - CARD_W // 2
        cy = HEIGHT // 2 - total_h // 2 + 20   # slightly below center

        # card bg
        card = pygame.Surface((CARD_W, total_h), pygame.SRCALPHA)
        card.fill((6, 4, 1, 210))
        card.set_alpha(ca)
        screen.blit(card, (cx, cy))

        # gold border lines top + bottom
        for border_y in (cy, cy + total_h - 2):
            bs = pygame.Surface((CARD_W, 2), pygame.SRCALPHA)
            bs.fill((255, 205, 50, ca))
            screen.blit(bs, (cx, border_y))

        # left accent bar
        ab = pygame.Surface((3, total_h), pygame.SRCALPHA)
        ab.fill((255, 205, 50, ca))
        screen.blit(ab, (cx, cy))

        # right accent bar
        screen.blit(ab, (cx + CARD_W - 3, cy))

        # render rows
        ry = cy + CARD_PAD
        for label, value, bold, lc, vc in CREDITS:
            if lc is None:
                ry += 8
                continue
            if bold:
                ts = tf.render(label, True, lc)
                ts.set_alpha(ca)
                screen.blit(ts, (tx - ts.get_width()//2, ry))
                # thin divider under title
                div = pygame.Surface((CARD_W - 60, 1), pygame.SRCALPHA)
                div.fill((255, 205, 50, min(ca, 100)))
                screen.blit(div, (cx + 30, ry + tf.get_linesize() + 2))
                ry += TITLE_H
            else:
                ls = cf.render(label, True, lc)
                ls.set_alpha(ca)
                screen.blit(ls, (cx + 20, ry))
                if value:
                    vs = cf.render(value, True, vc)
                    vs.set_alpha(ca)
                    screen.blit(vs, (cx + CARD_W - vs.get_width() - 20, ry))
                ry += ROW_H

        # ENTER hint
        if ca > 180:
            import math
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.002))
            ha  = min(255, int((ca - 180) * 4 * (0.55 + 0.45 * pulse)))
            hf  = pygame.font.SysFont("Courier New", 15)
            h   = hf.render("Press  ENTER  to exit", True, (190, 185, 170))
            h.set_alpha(ha)
            screen.blit(h, (tx - h.get_width()//2, HEIGHT - 30))


def draw_bezier(surface, color, p0, p1, p2, p3, width=2, steps=40):
    points = []
    for step in range(steps + 1):
        t  = step / steps
        mt = 1 - t
        x  = mt**3*p0[0] + 3*mt**2*t*p1[0] + 3*mt*t**2*p2[0] + t**3*p3[0]
        y  = mt**3*p0[1] + 3*mt**2*t*p1[1] + 3*mt*t**2*p2[1] + t**3*p3[1]
        points.append((int(x), int(y)))
    if len(points) > 1:
        pygame.draw.lines(surface, color, False, points, width)


def draw_node(surface, cx, cy, r, unlocked, label_num, label_name, nf, lnf, pf, frame):
    nw, nh = 90, 70
    nx, ny = cx - nw//2, cy - nh//2

    if unlocked:
        body = pygame.Surface((nw, nh), pygame.SRCALPHA)
        body.fill((0, 18, 28, 230))
        surface.blit(body, (nx, ny))
        pygame.draw.rect(surface, (0, 200, 240), (nx, ny, nw, nh), 2)
        screen_rect = pygame.Rect(nx+6, ny+6, nw-12, nh-20)
        pygame.draw.rect(surface, (0, 30, 40), screen_rect)
        pygame.draw.rect(surface, (0, 120, 150), screen_rect, 1)
        num = nf.render(str(label_num), True, (0, 255, 200))
        surface.blit(num, (cx - num.get_width()//2, ny + 8))
        pygame.draw.rect(surface, (0, 140, 170), (cx - 8, ny + nh, 16, 6))
        pygame.draw.rect(surface, (0, 140, 170), (cx - 18, ny + nh + 5, 36, 4))
        name = lnf.render(label_name.upper(), True, (0, 200, 180))
        surface.blit(name, (cx - name.get_width()//2, ny + nh + 14))
        hint = pf.render(f"[ {label_num} ]", True, (0, 160, 140))
        surface.blit(hint, (cx - hint.get_width()//2, ny + nh + 28))
        if (frame // 30) % 2 == 0:
            pygame.draw.circle(surface, (0, 255, 150), (nx + nw - 8, ny + 8), 4)
        else:
            pygame.draw.circle(surface, (0, 80, 60), (nx + nw - 8, ny + 8), 4)
    else:
        body = pygame.Surface((nw, nh), pygame.SRCALPHA)
        body.fill((8, 8, 12, 200))
        surface.blit(body, (nx, ny))
        pygame.draw.rect(surface, (50, 20, 20), (nx, ny, nw, nh), 1)
        screen_rect = pygame.Rect(nx+6, ny+6, nw-12, nh-20)
        pygame.draw.rect(surface, (15, 5, 5), screen_rect)
        lkf = pygame.font.SysFont("Courier New", 22, bold=True)
        lk  = lkf.render("##", True, (70, 20, 20))
        surface.blit(lk, (cx - lk.get_width()//2, ny + 10))
        pygame.draw.rect(surface, (40, 20, 20), (cx - 8, ny + nh, 16, 6))
        pygame.draw.rect(surface, (40, 20, 20), (cx - 18, ny + nh + 5, 36, 4))
        name = lnf.render(label_name.upper(), True, (50, 25, 25))
        surface.blit(name, (cx - name.get_width()//2, ny + nh + 14))
        locked_txt = pf.render("LOCKED", True, (70, 25, 25))
        surface.blit(locked_txt, (cx - locked_txt.get_width()//2, ny + nh + 28))


def draw_level_select():
    global menu_frame
    draw_cyber_bg()
    tx = WIDTH // 2

    tf  = pygame.font.SysFont("Courier New", 44, bold=True)
    ts  = tf.render("SELECT LEVEL", True, (0, 60, 90))
    tt  = tf.render("SELECT LEVEL", True, (0, 220, 255))
    screen.blit(ts, (tx - ts.get_width()//2 + 3, 53))
    screen.blit(tt, (tx - tt.get_width()//2,     50))
    sf  = pygame.font.SysFont("Courier New", 15)
    sub = sf.render("// NETWORK MAP — CHOOSE YOUR ENTRY NODE //", True, (0, 130, 100))
    screen.blit(sub, (tx - sub.get_width()//2, 100))
    pygame.draw.line(screen, (0, 100, 130), (tx - 240, 120), (tx + 240, 120), 1)

    node_y_pattern = [310, 240, 310, 240, 310]
    spacing   = 130
    total_w   = (MAX_LEVELS - 1) * spacing
    start_x   = tx - total_w // 2
    positions = [(start_x + i * spacing, node_y_pattern[i]) for i in range(MAX_LEVELS)]

    nf  = pygame.font.SysFont("Courier New", 28, bold=True)
    lnf = pygame.font.SysFont("Courier New", 12, bold=True)
    pf  = pygame.font.SysFont("Courier New", 12)

    for i in range(MAX_LEVELS - 1):
        ax, ay = positions[i]
        bx, by = positions[i + 1]
        unlocked_conn = (i + 1) < unlocked_level
        mid_x = (ax + bx) // 2
        if ay < by:
            cp1 = (ax + 40, ay + 40)
            cp2 = (bx - 40, by - 20)
        else:
            cp1 = (ax + 40, ay - 20)
            cp2 = (bx - 40, by + 40)

        if unlocked_conn:
            draw_bezier(screen, (0, 100, 130), (ax, ay), cp1, cp2, (bx, by), width=2)
            draw_bezier(screen, (0, 200, 220), (ax, ay), cp1, cp2, (bx, by), width=1)
            t   = ((menu_frame * 2 + i * 30) % 100) / 100
            mt  = 1 - t
            px  = int(mt**3*ax + 3*mt**2*t*cp1[0] + 3*mt*t**2*cp2[0] + t**3*bx)
            py  = int(mt**3*ay + 3*mt**2*t*cp1[1] + 3*mt*t**2*cp2[1] + t**3*by)
            pygame.draw.circle(screen, (0, 255, 200), (px, py), 4)
            pygame.draw.circle(screen, (0, 255, 200), (px, py), 7, 1)
        else:
            draw_bezier(screen, (30, 15, 15), (ax, ay), cp1, cp2, (bx, by), width=1)

    for i in range(MAX_LEVELS):
        cx, cy   = positions[i]
        unlocked = (i + 1) <= unlocked_level
        lname    = LEVEL_NAMES.get(i + 1, "")
        draw_node(screen, cx, cy, 36, unlocked, i + 1, lname, nf, lnf, pf, menu_frame)

    hf = pygame.font.SysFont("Courier New", 16)
    h  = hf.render("1 - 5  to select   |   ESC  to return", True, (50, 70, 80))
    screen.blit(h, (tx - h.get_width()//2, HEIGHT - 36))
    draw_cyber_scanlines()


def draw_pause():
    global menu_frame
    menu_frame += 1

    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 180))
    screen.blit(ov, (0, 0))

    bar = pygame.Surface((4, HEIGHT), pygame.SRCALPHA)
    bar.fill((0, 220, 255, 80))
    screen.blit(bar, (0, 0))
    screen.blit(bar, (WIDTH - 4, 0))

    for cx, cy, dx, dy in [(8,8,1,1),(WIDTH-8,8,-1,1),(8,HEIGHT-8,1,-1),(WIDTH-8,HEIGHT-8,-1,-1)]:
        pygame.draw.line(screen, (0, 100, 120), (cx, cy), (cx+dx*20, cy), 1)
        pygame.draw.line(screen, (0, 100, 120), (cx, cy), (cx, cy+dy*20), 1)

    tx = WIDTH // 2

    tf = pygame.font.SysFont("Courier New", 52, bold=True)
    ts = tf.render("// PAUSED //", True, (0, 60, 90))
    tt = tf.render("// PAUSED //", True, (0, 220, 255))
    screen.blit(ts, (tx - ts.get_width()//2 + 3, 113))
    screen.blit(tt, (tx - tt.get_width()//2,     110))

    sep_y = 110 + tf.size("X")[1] + 12
    pygame.draw.line(screen, (0, 180, 220), (tx - 160, sep_y), (tx + 160, sep_y), 1)

    opt_font     = pygame.font.SysFont("Courier New", 30, bold=True)
    opt_font_dim = pygame.font.SysFont("Courier New", 30)
    opt_spacing  = 54
    start_y      = sep_y + 30

    for i, opt in enumerate(pause_options):
        selected = (i == pause_index)
        oy = start_y + i * opt_spacing

        if selected:
            panel_w, panel_h = 280, 44
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((0, 220, 255, 30))
            screen.blit(panel, (tx - panel_w//2, oy - 6))
            pygame.draw.line(screen, (0, 220, 255),
                             (tx - panel_w//2, oy - 6),
                             (tx - panel_w//2, oy + panel_h - 6), 2)
            pygame.draw.line(screen, (0, 220, 255),
                             (tx + panel_w//2, oy - 6),
                             (tx + panel_w//2, oy + panel_h - 6), 2)
            if (menu_frame // 20) % 2 == 0:
                cur = opt_font.render(">", True, (0, 255, 180))
                screen.blit(cur, (tx - panel_w//2 + 8, oy))
            txt = opt_font.render(opt, True, (0, 220, 255))
        else:
            txt = opt_font_dim.render(opt, True, (160, 170, 180))

        screen.blit(txt, (tx - txt.get_width()//2, oy))

    hf = pygame.font.SysFont("Courier New", 16)
    h  = hf.render("ENTER to select  |  ARROWS to navigate", True, (60, 80, 90))
    screen.blit(h, (tx - h.get_width()//2, HEIGHT - 36))

    screen.blit(scanline_surf, (0, 0))


# =========================
# SHARED UI HELPERS
# =========================
def draw_cyber_bg():
    for row in range(HEIGHT):
        t = row / HEIGHT
        pygame.draw.line(screen, (int(t*5), int(5+t*8), int(20+t*10)), (0, row), (WIDTH, row))
    bar = pygame.Surface((4, HEIGHT), pygame.SRCALPHA)
    bar.fill((0, 220, 255, 80))
    screen.blit(bar, (0, 0))
    screen.blit(bar, (WIDTH - 4, 0))
    for cx, cy, dx, dy in [(8,8,1,1),(WIDTH-8,8,-1,1),(8,HEIGHT-8,1,-1),(WIDTH-8,HEIGHT-8,-1,-1)]:
        pygame.draw.line(screen, (0, 100, 120), (cx, cy), (cx+dx*20, cy), 1)
        pygame.draw.line(screen, (0, 100, 120), (cx, cy), (cx, cy+dy*20), 1)


def draw_cyber_panel(x, y, w, h):
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((0, 20, 30, 160))
    screen.blit(panel, (x, y))
    pygame.draw.rect(screen, (0, 180, 220), (x, y, w, h), 1)


def draw_cyber_title(text, y, font_size=48):
    font = pygame.font.SysFont("Courier New", font_size, bold=True)
    tx = WIDTH // 2
    s = font.render(text, True, (0, 60, 90))
    screen.blit(s, (tx - s.get_width()//2 + 3, y + 3))
    t = font.render(text, True, (0, 220, 255))
    screen.blit(t, (tx - t.get_width()//2, y))
    sep_y = y + t.get_height() + 8
    pygame.draw.line(screen, (0, 180, 220), (tx-160, sep_y), (tx+160, sep_y), 1)
    return sep_y + 16


def draw_cyber_scanlines():
    screen.blit(scanline_surf, (0, 0))


# =========================
# MENU DRAW
# =========================
def draw_menu():
    global menu_glitch_timer, menu_glitch_offset, menu_frame
    menu_frame += 1

    if menu_bg:
        screen.blit(menu_bg, (0, 0))
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 140))
        screen.blit(ov, (0, 0))
    else:
        for row in range(HEIGHT):
            t = row / HEIGHT
            r = int(0   + t * 5)
            g = int(5   + t * 8)
            b = int(20  + t * 10)
            pygame.draw.line(screen, (r, g, b), (0, row), (WIDTH, row))

    bar_surf = pygame.Surface((4, HEIGHT), pygame.SRCALPHA)
    bar_surf.fill((0, 220, 255, 80))
    screen.blit(bar_surf, (0, 0))
    screen.blit(bar_surf, (WIDTH - 4, 0))

    if menu_frame % 180 == 0:
        menu_glitch_timer  = 6
        menu_glitch_offset = random.randint(4, 12)

    if menu_glitch_timer > 0:
        menu_glitch_timer -= 1
    else:
        menu_glitch_offset = 0

    title_font = pygame.font.SysFont("Courier New", 64, bold=True)
    title_text = "404 ESCAPE"
    glow_col   = (0, 200, 255)
    shadow_col = (0, 80, 120)
    tx = WIDTH // 2
    ty = 80

    for offset in [4, 3, 2]:
        s = title_font.render(title_text, True, shadow_col)
        screen.blit(s, (tx - s.get_width() // 2 + offset, ty + offset))

    if menu_glitch_offset > 0:
        glitch_r = title_font.render(title_text, True, (255, 30, 80))
        screen.blit(glitch_r, (tx - glitch_r.get_width() // 2 + menu_glitch_offset, ty - 2))
        glitch_b = title_font.render(title_text, True, (0, 255, 200))
        screen.blit(glitch_b, (tx - glitch_b.get_width() // 2 - menu_glitch_offset, ty + 2))

    title_surf = title_font.render(title_text, True, glow_col)
    screen.blit(title_surf, (tx - title_surf.get_width() // 2, ty))

    sub_font = pygame.font.SysFont("Courier New", 18)
    sub      = sub_font.render("// SYSTEM BREACH DETECTED //", True, (0, 255, 180))
    screen.blit(sub, (tx - sub.get_width() // 2, ty + 72))

    sep_y = ty + 100
    pygame.draw.line(screen, (0, 220, 255), (WIDTH // 2 - 160, sep_y),
                     (WIDTH // 2 + 160, sep_y), 1)

    opt_font      = pygame.font.SysFont("Courier New", 30, bold=True)
    opt_font_dim  = pygame.font.SysFont("Courier New", 30)
    opt_spacing   = 54
    lock_extra    = 28

    oy_positions = []
    cur_y = sep_y + 30
    for opt in menu_options:
        oy_positions.append(cur_y)
        locked = (opt == "Level Select" and unlocked_level == 1)
        cur_y += opt_spacing + (lock_extra if locked else 0)

    for i, opt in enumerate(menu_options):
        locked   = (opt == "Level Select" and unlocked_level == 1)
        selected = (i == menu_index) and not locked
        oy       = oy_positions[i]

        if locked:
            txt = opt_font_dim.render(opt, True, (60, 60, 70))
            screen.blit(txt, (tx - txt.get_width() // 2, oy))
            lock = opt_font_dim.render("[LOCKED]", True, (80, 40, 40))
            screen.blit(lock, (tx - lock.get_width() // 2, oy + 26))
            continue

        if selected:
            panel_w, panel_h = 280, 44
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((0, 220, 255, 30))
            screen.blit(panel, (tx - panel_w // 2, oy - 6))
            pygame.draw.line(screen, (0, 220, 255),
                             (tx - panel_w // 2, oy - 6),
                             (tx - panel_w // 2, oy + panel_h - 6), 2)
            pygame.draw.line(screen, (0, 220, 255),
                             (tx + panel_w // 2, oy - 6),
                             (tx + panel_w // 2, oy + panel_h - 6), 2)
            if (menu_frame // 20) % 2 == 0:
                cur = opt_font.render(">", True, (0, 255, 180))
                screen.blit(cur, (tx - panel_w // 2 + 8, oy))
            txt = opt_font.render(opt, True, (0, 220, 255))
        else:
            txt = opt_font.render(opt, True, (160, 170, 180))

        screen.blit(txt, (tx - txt.get_width() // 2, oy))

    hint_f = pygame.font.SysFont("Courier New", 16)
    hint   = hint_f.render("ENTER to select  |  ARROWS to navigate", True, (60, 80, 90))
    screen.blit(hint, (tx - hint.get_width() // 2, HEIGHT - 36))

    corner_col = (0, 100, 120)
    for cx, cy, dx, dy in [(8,8,1,1),(WIDTH-8,8,-1,1),(8,HEIGHT-8,1,-1),(WIDTH-8,HEIGHT-8,-1,-1)]:
        pygame.draw.line(screen, corner_col, (cx, cy), (cx + dx*20, cy), 1)
        pygame.draw.line(screen, corner_col, (cx, cy), (cx, cy + dy*20), 1)

    screen.blit(scanline_surf, (0, 0))


# =========================
# HOW TO PLAY DRAW
# =========================
def draw_howto():
    global howto_scroll

    draw_cyber_bg()
    tx = WIDTH // 2

    # ── TITLE (fixed at top) ─────────────────────────────────────────
    title_bottom_y = draw_cyber_title("HOW TO PLAY", 30, 44)

    kf = pygame.font.SysFont("Courier New", 17, bold=True)
    vf = pygame.font.SysFont("Courier New", 16)
    sf = pygame.font.SysFont("Courier New", 13)

    # ── KEY BADGES (fixed row, below title) ──────────────────────────
    # Each entry: (primary_key, alt_key, label)
    # badge_data: (primary_key, alt_key_text, label)
    badge_data = [
        ("A",     "LEFT",   "Left"),
        ("D",     "RIGHT",  "Right"),
        ("SPACE", "UP",     "Jump"),
        ("J",     "",       "Attack"),
        ("ESC",   "",       "Pause"),
    ]

    BADGE_PAD = 18
    BADGE_GAP = 10
    BADGE_H   = 72
    badge_y   = title_bottom_y + 8

    kf2  = pygame.font.SysFont("Courier New", 15, bold=True)  # primary key
    af2  = pygame.font.SysFont("Courier New", 12, bold=True)  # alt key
    div2 = pygame.font.SysFont("Courier New", 12)             # divider
    lf2  = pygame.font.SysFont("Courier New", 13)             # label

    def get_badge_w(pk, ak):
        if ak:
            w = kf2.size(pk)[0] + div2.size(" / ")[0] + af2.size(ak)[0]
        else:
            w = kf2.size(pk)[0]
        return max(w, lf2.size("Attack")[0]) + BADGE_PAD * 2

    badge_widths  = [get_badge_w(pk, ak) for pk, ak, _ in badge_data]
    total_badge_w = sum(badge_widths) + BADGE_GAP * (len(badge_data) - 1)
    bx = tx - total_badge_w // 2

    for i, (pkey, akey, lbl) in enumerate(badge_data):
        bw = badge_widths[i]
        cx = bx + bw // 2

        # box
        pygame.draw.rect(screen, (0, 18, 30),   (bx, badge_y, bw, BADGE_H))
        pygame.draw.rect(screen, (0, 180, 220), (bx, badge_y, bw, BADGE_H), 2)
        pygame.draw.line(screen, (0, 220, 255), (bx, badge_y), (bx + bw, badge_y), 2)

        # key row
        ky = badge_y + 12
        if akey:
            pk_s  = kf2.render(pkey,  True, (0, 220, 255))
            div_s = div2.render(" / ", True, (0, 100, 120))
            ak_s  = af2.render(akey,  True, (0, 190, 170))
            row_w = pk_s.get_width() + div_s.get_width() + ak_s.get_width()
            rx    = cx - row_w // 2
            screen.blit(pk_s,  (rx, ky))
            screen.blit(div_s, (rx + pk_s.get_width(), ky + 2))
            screen.blit(ak_s,  (rx + pk_s.get_width() + div_s.get_width(), ky + 1))
        else:
            pk_s = kf2.render(pkey, True, (0, 220, 255))
            screen.blit(pk_s, (cx - pk_s.get_width() // 2, ky))

        # divider
        pygame.draw.line(screen, (0, 80, 100),
                         (bx + 8, badge_y + 44), (bx + bw - 8, badge_y + 44), 1)

        # label
        lt = lf2.render(lbl, True, (0, 150, 140))
        screen.blit(lt, (cx - lt.get_width() // 2, badge_y + 50))

        bx += bw + BADGE_GAP

    sep_y = badge_y + BADGE_H + 14
    pygame.draw.line(screen, (0, 70, 90), (50, sep_y), (WIDTH - 50, sep_y), 1)

    # ── SCROLLABLE OBJECTIVE ROWS ─────────────────────────────────────
    HINT_H        = 36
    SCROLL_TOP    = sep_y + 10
    SCROLL_BOTTOM = HEIGHT - HINT_H
    SCROLL_H      = SCROLL_BOTTOM - SCROLL_TOP

    OBJ_PANEL_W  = WIDTH - 110
    OBJ_LEFT     = 55
    ROW_GAP      = 8
    INNER_PAD_X  = 14
    INNER_PAD_Y  = 10

    objectives = [
        ("ELIMINATE ENEMIES", "Hunt down every enemy on the level. Only then will the exit gate unlock."),
        ("REACH THE GATE",    "Find the open gate and step through it to breach the next system."),
        ("USE CHECKPOINTS",   "Touch glowing checkpoints to set your respawn point. Don't skip them."),
        ("AVOID TRAPS",       "Spikes, rotating saws and crumbling bridges will kill on contact."),
        ("SURVIVE THE ARENA", "Some levels lock you in. Outlast the threat timer to open the gate."),
        ("REVERSE CONTROLS",  "Certain zones flip your controls. Stay sharp and adapt quickly."),
    ]

    def wrap_text(font, text, max_w):
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    line_h     = vf.get_linesize()
    title_lh   = kf.get_linesize()
    max_text_w = OBJ_PANEL_W - INNER_PAD_X * 2 - 6   # 6 = accent bar width

    # Pre-compute rows
    rows = []
    for t_txt, b_txt in objectives:
        blines = wrap_text(vf, b_txt, max_text_w)
        rh = INNER_PAD_Y + title_lh + 4 + len(blines) * line_h + INNER_PAD_Y
        rows.append((t_txt, blines, rh))

    total_content_h = sum(rh for _, _, rh in rows) + ROW_GAP * (len(rows) - 1)
    max_scroll      = max(0, total_content_h - SCROLL_H)
    scroll_y        = max(0, min(howto_scroll, max_scroll))
    howto_scroll    = scroll_y   # keep clamped

    # Render all rows onto an off-screen surface, blit a viewport slice
    content_surf = pygame.Surface((WIDTH, max(total_content_h, 1)), pygame.SRCALPHA)
    ry = 0
    for t_txt, blines, rh in rows:
        # panel background
        rp = pygame.Surface((OBJ_PANEL_W, rh), pygame.SRCALPHA)
        rp.fill((0, 14, 20, 210))
        content_surf.blit(rp, (OBJ_LEFT, ry))
        pygame.draw.rect(content_surf, (0, 55, 75), (OBJ_LEFT, ry, OBJ_PANEL_W, rh), 1)
        # left accent bar
        pygame.draw.rect(content_surf, (0, 200, 180), (OBJ_LEFT, ry, 3, rh))
        # title
        tt = kf.render(f"> {t_txt}", True, (0, 210, 190))
        content_surf.blit(tt, (OBJ_LEFT + INNER_PAD_X, ry + INNER_PAD_Y))
        # body lines
        by = ry + INNER_PAD_Y + title_lh + 4
        for bline in blines:
            bt = vf.render(bline, True, (90, 150, 160))
            content_surf.blit(bt, (OBJ_LEFT + INNER_PAD_X, by))
            by += line_h
        ry += rh + ROW_GAP

    # Blit only the visible viewport slice
    screen.blit(content_surf, (0, SCROLL_TOP), (0, scroll_y, WIDTH, SCROLL_H))

    # Top & bottom fade masks for clean clipping
    FADE_H = 20
    for is_top in (True, False):
        fsurf = pygame.Surface((WIDTH, FADE_H), pygame.SRCALPHA)
        for i in range(FADE_H):
            a = int(180 * (1 - i / FADE_H)) if is_top else int(180 * (i / FADE_H))
            pygame.draw.line(fsurf, (0, 0, 0, a), (0, i), (WIDTH, i))
        screen.blit(fsurf, (0, SCROLL_TOP if is_top else SCROLL_BOTTOM - FADE_H))

    # Scrollbar (only if content overflows)
    if total_content_h > SCROLL_H:
        SB_X    = WIDTH - 12
        SB_W    = 5
        track_h = SCROLL_H
        thumb_h = max(28, int(track_h * SCROLL_H / total_content_h))
        thumb_pct = scroll_y / max_scroll if max_scroll > 0 else 0
        thumb_y   = SCROLL_TOP + int(thumb_pct * (track_h - thumb_h))
        pygame.draw.rect(screen, (0, 25, 35),   (SB_X, SCROLL_TOP, SB_W, track_h))
        pygame.draw.rect(screen, (0, 180, 220), (SB_X, thumb_y,    SB_W, thumb_h))
        pygame.draw.rect(screen, (0, 220, 255), (SB_X, thumb_y,    SB_W, thumb_h), 1)

    # ── HINT BAR (pinned to bottom, never overlaps content) ──────────
    hbar = pygame.Surface((WIDTH, HINT_H), pygame.SRCALPHA)
    hbar.fill((0, 8, 14, 230))
    screen.blit(hbar, (0, SCROLL_BOTTOM))
    pygame.draw.line(screen, (0, 70, 90), (0, SCROLL_BOTTOM), (WIDTH, SCROLL_BOTTOM), 1)

    hf = pygame.font.SysFont("Courier New", 15)
    scroll_hint = "UP / DOWN  to scroll     |     " if total_content_h > SCROLL_H else ""
    hint_str    = scroll_hint + "ESC  to return"
    h = hf.render(hint_str, True, (60, 120, 140))
    screen.blit(h, (tx - h.get_width() // 2,
                    SCROLL_BOTTOM + (HINT_H - h.get_height()) // 2))

    draw_cyber_scanlines()


# =========================
# MAIN LOOP
# =========================
_play_music("assets/sfx/music/intro.wav", volume=0.25)
running = True
while running:
    clock.tick(FPS)

    keys = pygame.key.get_pressed()

    if shutdown_transition:
        shutdown_alpha += 3
        if shutdown_alpha >= 255:
            pygame.quit()
            sys.exit()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_state == GAME_INTRO:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                intro_index += 1
                intro_alpha  = 0
                if intro_index >= len(INTRO_SCENES):
                    _stop_music()
                    if sfx_main_menu: sfx_main_menu.play()
                    game_state = GAME_MENU

        elif game_state == GAME_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    current_level = 1; load_level(1); game_state = GAME_PLAY
                elif event.key == pygame.K_2:
                    current_level = 2; load_level(2); game_state = GAME_PLAY
                elif event.key == pygame.K_3:
                    current_level = 3; load_level(3); game_state = GAME_PLAY
                elif event.key == pygame.K_4:
                    current_level = 4; load_level(4); game_state = GAME_PLAY
                elif event.key == pygame.K_5:
                    current_level = 5; load_level(5); game_state = GAME_PLAY
                elif event.key == pygame.K_UP:
                    menu_index = (menu_index - 1) % len(menu_options)
                    if sfx_scrolling: sfx_scrolling.play()
                elif event.key == pygame.K_DOWN:
                    menu_index = (menu_index + 1) % len(menu_options)
                    if sfx_scrolling: sfx_scrolling.play()
                elif event.key == pygame.K_RETURN:
                    if sfx_button: sfx_button.play()
                    choice = menu_options[menu_index]
                    if choice == "Start Game":
                        current_level = 1
                        if not player_name.strip():
                            name_locked = False; game_state = GAME_NAME
                        else:
                            load_level(current_level); game_state = GAME_PLAY
                    elif choice == "Level Select":
                        game_state = GAME_LEVEL_SELECT
                    elif choice == "How to Play":
                        howto_scroll = 0
                        game_state   = GAME_HOWTO
                    elif choice == "Quit":
                        running = False

        elif game_state == GAME_LEVEL_SELECT:
            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_5:
                    chosen = event.key - pygame.K_0
                    if chosen <= unlocked_level:
                        if sfx_button: sfx_button.play()
                        current_level = chosen; load_level(current_level); game_state = GAME_PLAY
                elif event.key == pygame.K_ESCAPE:
                    if sfx_back: sfx_back.play()
                    game_state = GAME_MENU

        elif game_state == GAME_NAME:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and player_name.strip():
                    if sfx_button: sfx_button.play()
                    name_locked = True; load_level(current_level); game_state = GAME_PLAY
                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif not name_locked and len(player_name) < 12 and event.unicode.isalpha():
                    player_name += event.unicode
                    if sfx_keyboard: sfx_keyboard.play()

        elif game_state == GAME_HOWTO:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if sfx_back: sfx_back.play()
                    howto_scroll = 0
                    game_state   = GAME_MENU
                elif event.key == pygame.K_DOWN:
                    howto_scroll += 40
                    if sfx_scrolling: sfx_scrolling.play()
                elif event.key == pygame.K_UP:
                    howto_scroll = max(0, howto_scroll - 40)
                    if sfx_scrolling: sfx_scrolling.play()
            elif event.type == pygame.MOUSEWHEEL:
                howto_scroll = max(0, howto_scroll - event.y * 40)

        elif game_state == GAME_PLAY:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if sfx_back: sfx_back.play()
                game_state = GAME_PAUSE

        elif game_state == GAME_PAUSE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    pause_index = (pause_index - 1) % len(pause_options)
                    if sfx_scrolling: sfx_scrolling.play()
                elif event.key == pygame.K_DOWN:
                    pause_index = (pause_index + 1) % len(pause_options)
                    if sfx_scrolling: sfx_scrolling.play()
                elif event.key == pygame.K_RETURN:
                    if sfx_button: sfx_button.play()
                    choice = pause_options[pause_index]
                    if choice == "Resume":
                        game_state = GAME_PLAY
                    elif choice == "Restart Level":
                        load_level(current_level); game_state = GAME_PLAY
                    elif choice == "Level Select":
                        game_state = GAME_LEVEL_SELECT
                    elif choice == "Quit to Menu":
                        _stop_music()
                        game_state = GAME_MENU

        elif game_state == GAME_VICTORY:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if sfx_button: sfx_button.play()
                    if current_level >= unlocked_level:
                        unlocked_level = min(current_level + 1, MAX_LEVELS)
                    if current_level == MAX_LEVELS:
                        ending_alpha = 0; ending_phase = 0; ending_credits_alpha = 0; game_state = GAME_END
                    else:
                        current_level += 1; load_level(current_level); game_state = GAME_PLAY
                elif event.key == pygame.K_r:
                    if sfx_button: sfx_button.play()
                    load_level(current_level); game_state = GAME_PLAY
                elif event.key == pygame.K_ESCAPE:
                    if sfx_back: sfx_back.play()
                    game_state = GAME_LEVEL_SELECT

        elif game_state == GAME_END:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if sfx_button: sfx_button.play()
                if ending_phase == 0 and ending_alpha >= 200:
                    ending_phase         = 1
                    ending_credits_alpha = 0
                elif ending_phase == 1 and ending_credits_alpha >= 200:
                    shutdown_transition = True

    # =========================
    # NON-GAMEPLAY SCREENS
    # =========================
    if game_state == GAME_INTRO:
        draw_intro(); flip(); continue

    if game_state == GAME_MENU:
        draw_menu(); flip(); continue

    if game_state == GAME_NAME:
        draw_cyber_bg()
        import math as _m
        t_ms = pygame.time.get_ticks()
        tx   = WIDTH // 2

        # title
        content_y = draw_cyber_title("IDENTIFY YOURSELF", 72, 44)

        # decorative divider with diamonds
        div_y = content_y + 12
        pygame.draw.line(screen, (0, 140, 180), (tx - 220, div_y), (tx + 220, div_y), 1)
        for dx in [-220, 220]:
            sign = 1 if dx < 0 else -1
            ox = tx + dx
            pygame.draw.polygon(screen, (0, 200, 255),
                [(ox, div_y), (ox + sign*8, div_y-4),
                 (ox + sign*16, div_y), (ox + sign*8, div_y+4)])

        # input box
        panel_w, panel_h = 420, 56
        px = tx - panel_w // 2
        py = content_y + 90

        # pulsing glow behind box
        pulse      = abs(_m.sin(t_ms * 0.003))
        glow_alpha = int(50 + 70 * pulse)
        glow_surf  = pygame.Surface((panel_w + 16, panel_h + 16), pygame.SRCALPHA)
        glow_surf.fill((0, 160, 255, glow_alpha))
        screen.blit(glow_surf, (px - 8, py - 8))

        draw_cyber_panel(px, py, panel_w, panel_h)

        # typed text + blinking pipe cursor
        inf    = pygame.font.SysFont("Courier New", 28, bold=True)
        cursor = "|" if (t_ms // 530) % 2 == 0 else " "
        nt = inf.render(player_name + cursor, True, (0, 255, 180))
        screen.blit(nt, (tx - nt.get_width() // 2, py + 14))

        # char counter
        cf  = pygame.font.SysFont("Courier New", 14)
        cco = (0, 210, 150) if len(player_name) > 0 else (50, 90, 110)
        cc  = cf.render(f"{len(player_name)}/12", True, cco)
        screen.blit(cc, (px + panel_w - cc.get_width() - 8, py + panel_h + 5))

        # progress bar of 12 small blocks
        dot_y   = py + panel_h + 6
        dot_gap = 16
        dot_x0  = tx - (12 * dot_gap) // 2 + 4
        for di in range(12):
            filled = di < len(player_name)
            col    = (0, 220, 160) if filled else (25, 55, 65)
            pygame.draw.rect(screen, col, (dot_x0 + di * dot_gap, dot_y, 11, 4),
                             0 if filled else 1)

        # hint
        hf       = pygame.font.SysFont("Courier New", 17)
        hint_txt = "[ ENTER ]  confirm" if player_name.strip() else "type your handle..."
        hint_col = (0, 220, 160) if player_name.strip() else (45, 75, 85)
        h        = hf.render(hint_txt, True, hint_col)
        screen.blit(h, (tx - h.get_width() // 2, py + panel_h + 28))

        # corner brackets
        bc  = (0, 150, 195)
        bx1, by1 = px - 18, py - 18
        bx2, by2 = px + panel_w + 18, py + panel_h + 18
        sz  = 14
        for bx, by, sx, sy in [(bx1,by1,1,1),(bx2,by1,-1,1),(bx1,by2,1,-1),(bx2,by2,-1,-1)]:
            pygame.draw.line(screen, bc, (bx, by), (bx + sx*sz, by), 2)
            pygame.draw.line(screen, bc, (bx, by), (bx, by + sy*sz), 2)

        # bottom status line
        sf  = pygame.font.SysFont("Courier New", 13)
        stx = sf.render("// SYSTEM AWAITING IDENTIFICATION //", True, (20, 55, 75))
        screen.blit(stx, (tx - stx.get_width() // 2, HEIGHT - 55))

        draw_cyber_scanlines()
        flip(); continue

    if game_state == GAME_LEVEL_SELECT:
        draw_level_select(); flip(); continue

    if game_state == GAME_HOWTO:
        draw_howto(); flip(); continue

    if game_state == GAME_PAUSE:
        draw_pause(); flip(); continue

    if game_state == GAME_VICTORY:
        draw_cyber_bg()
        tx = WIDTH // 2
        lf = pygame.font.SysFont("Courier New", 16)
        lname = LEVEL_NAMES.get(current_level, "")
        ln = lf.render(f"// LEVEL {current_level} : {lname.upper()} //", True, (0, 180, 140))
        screen.blit(ln, (tx - ln.get_width()//2, 100))
        draw_cyber_title("ACCESS GRANTED", 130, 52)
        pf = pygame.font.SysFont("Courier New", 24)
        msg = pf.render(f"WELL DONE, {player_name.upper()}", True, (160, 210, 220))
        screen.blit(msg, (tx - msg.get_width()//2, 240))
        draw_cyber_panel(tx - 200, 290, 400, 120)
        af = pygame.font.SysFont("Courier New", 20, bold=True)
        actions = [
            ("ENTER", "Next Level"),
            ("R",     "Retry"),
            ("ESC",   "Level Select"),
        ]
        for i, (key, desc) in enumerate(actions):
            ky = 304 + i * 32
            kt = af.render(f"[ {key} ]", True, (0, 220, 255))
            dt = af.render(desc, True, (140, 170, 180))
            screen.blit(kt, (tx - 170, ky))
            screen.blit(dt, (tx - 50,  ky))
        draw_cyber_scanlines()
        flip(); continue

    if game_state == GAME_END:
        draw_ending()
        if shutdown_transition:
            ov = pygame.Surface((WIDTH, HEIGHT)); ov.fill((0, 0, 0))
            ov.set_alpha(shutdown_alpha); screen.blit(ov, (0, 0))
        flip(); continue

    # =========================
    # GAMEPLAY UPDATE
    # =========================
    result = None

    if game_state == GAME_PLAY:

        if player.state == "dead":
            game_state  = GAME_DEAD
            death_timer = DEATH_DELAY
            death_cam_x = cam_x

        if player.state == "alive" and player.rect.centery > level.world_h:
            player.hp = 0
            player.die()
            game_state  = GAME_DEAD
            death_timer = DEATH_DELAY
            death_cam_x = cam_x

        if game_state == GAME_DEAD:
            pass
        else:
            player.handle_input(keys)
            fake_rects    = [f.rect for f in getattr(level, "fake_saws", [])]
            all_platforms = level.solids + fake_rects
            player.update(all_platforms, level.bridges, gate)

            result = level.update(player)

            if result == "level_complete":
                pygame.mixer.stop()
                _stop_music()
                if hasattr(level, "warning_sound"):
                    level.warning_sound.stop()
                if current_level == 5:
                    ending_alpha = 0
                    ending_phase = 0
                    ending_credits_alpha = 0
                    _play_music("assets/sfx/music/ending.wav", volume=0.40)
                    game_state = GAME_END
                else:
                    _stop_music()
                    if sfx_victory: sfx_victory.play()
                    game_state = GAME_VICTORY
                flip(); continue

            if result == "void_death" and current_level == 5:
                pygame.mixer.stop()
                load_level(current_level)
                flip(); continue

            if result == "player_dead":
                player.hp = 0    
                player.die()
                game_state  = GAME_DEAD
                death_timer = DEATH_DELAY
                death_cam_x = cam_x

            if player.atk:
                hitbox = player.attack_rect()
                for en in level.enemies:
                    if en.alive and hitbox.colliderect(en.rect) and not player.atk_hit:
                        en.take_damage(); player.atk_hit = True
                for fe in getattr(level, "flying_enemies", []):
                    if fe.alive and hitbox.colliderect(fe.rect) and not player.atk_hit:
                        fe.take_damage(); player.atk_hit = True

        # Gate logic
        if level.level_id == 5:
            gc = all(not e.alive for e in level.enemies)
            fc = all(not f.alive for f in getattr(level, "flying_enemies", []))
            if gc and fc and result == "boss_finished":
                gate.open()
        else:
            if getattr(level, "boss", None):
                if level.boss.hp <= 0:
                    gate.open()
            else:
                gc = all(not e.alive for e in level.enemies)
                fc = all(not f.alive for f in getattr(level, "flying_enemies", []))
                if gc and fc:
                    if not getattr(gate, '_sound_played', False):
                        if sfx_gate: sfx_gate.play()
                        gate._sound_played = True
                    gate.open()

        gate.update()
        if result == "boss_finished":
            gate.open()

        if gate.state == "open" and player.rect.centerx > gate.rect.centerx:
            player.visible = False
            _stop_music()
            if sfx_victory: sfx_victory.play()
            game_state     = GAME_VICTORY
            flip(); continue

    elif game_state == GAME_DEAD:
        death_timer -= 1
        if death_timer <= 0:
            level.reset()
            gate.reset()

            if current_level in (3, 4, 5) and level.active_checkpoint:
                player.respawn(level.active_checkpoint.rect.topleft)
                if current_level == 4:
                    player.reverse_controls = (level.active_checkpoint_index == 0)
            else:
                player.respawn()

            cam_x = float(max(0, min(
                player.rect.centerx - WIDTH // 2,
                level.world_w - WIDTH
            )))
            fade_timer = 5
            game_state = GAME_PLAY

    # =========================
    # CAMERA
    # =========================
    if game_state == GAME_DEAD:
        cam_x = death_cam_x
    else:
        target_x = float(player.rect.centerx - WIDTH // 2)
        cam_x   += (target_x - cam_x) * 0.2

    if level.level_id == 5:
        target_y = float(player.rect.centery - HEIGHT // 2)
        cam_y   += (target_y - cam_y) * 0.2
    else:
        cam_y = 0.0

    cam_x = max(0.0, min(cam_x, float(level.world_w - WIDTH)))
    cam_y = max(0.0, min(cam_y, float(level.world_h - HEIGHT)))

    # =========================
    # CAMERA SHAKE
    # =========================
    shake_x = shake_y = 0
    if level.level_id == 5 and level.shake_timer > 0:
        level.shake_timer -= 1
        shake_x = random.randint(-level.shake_intensity, level.shake_intensity)
        shake_y = random.randint(-level.shake_intensity, level.shake_intensity)

    draw_cam_x = int(cam_x) + shake_x
    draw_cam_y = int(cam_y) + shake_y

    # =========================
    # DRAW
    # =========================
    screen.blit(level_bg, (0, 0))
    # subtle dark overlay to reduce bg brightness & improve readability
    _bg_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    _bg_overlay.fill((0, 0, 0, 55))
    screen.blit(_bg_overlay, (0, 0))
    level.draw(screen, draw_cam_x, draw_cam_y, tile_image)
    gate.draw(screen,   draw_cam_x, draw_cam_y)
    player.draw(screen, draw_cam_x, draw_cam_y)

    draw_hud(screen, player, player_name)

    if fade_timer > 0:
        fade = pygame.Surface((WIDTH, HEIGHT))
        fade.fill((0, 0, 0)); fade.set_alpha(255)
        screen.blit(fade, (0, 0))
        fade_timer -= 1

    respawning = False

    if shutdown_transition:
        ov = pygame.Surface((WIDTH, HEIGHT))
        ov.fill((0, 0, 0)); ov.set_alpha(shutdown_alpha)
        screen.blit(ov, (0, 0))

    flip()

pygame.quit()
sys.exit()
