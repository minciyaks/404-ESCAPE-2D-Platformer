# config.py
import pygame

# config.py
# ---------------- WINDOW ----------------
WIDTH, HEIGHT = 800, 600
FPS = 60

# ---------backgorund on each level--------
LEVEL_BACKGROUNDS = {
    1: "assets/7 Levels/Tiled/Backgrounds/bg1.png",
    2:  "assets/7 Levels/Tiled/Backgrounds/bg2.png",
    3: "assets/7 Levels/Tiled/Backgrounds/bg3.png",
    4: "assets/7 Levels/Tiled/Backgrounds/bg4.png",
    5: "assets/7 Levels/Tiled/Backgrounds/bg5.png",
}

LEVEL_ENEMY_HP = {
    1: 10,   # Awakening – tutorial enemy
    2: 12,   # Pressure – forces commitment
    3: 18,   # Chaos – dangerous if ignored
    4: 20,   # Descent – overwhelming numbers
    5: 22,   # Terminal – the final boss
}

# ---------------- TILE / WORLD ----------------
TILE_SIZE = 16
GRAVITY = 0.8

# ---------------- GAME STATES ----------------
GAME_PLAY = "play"
GAME_DEAD = "dead"

# ---------------- PLAYER ----------------
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 32
PLAYER_SPEED = 5
PLAYER_JUMP = 12

PLAYER_MAX_HP = 6
ATTACK_TIME = 10
INV_TIME = 45
DEATH_DELAY = 40

# ---------------- SPIKE ----------------
SPIKE_POP_DELAY = 18
SPIKE_DANGER_START = 6

# ---------------- BRIDGE ----------------
BRIDGE_WARNING_TIME = 8

# ---------------- ENEMY ----------------
ENEMY_HP = 3
ENEMY_SPEED = 2
ENEMY_ATTACK_WINDUP = 12
ENEMY_ATTACK_HIT_FRAME = 6
ENEMY_COOLDOWN = 30

# ---------------- MAP ----------------
GROUND_TILES = {
    0,1,2,6, 7,8, 70, 71,72, 134,135,136,137,138,140,141,142,
      76,77,78, 128, 129, 130, 156,157,158, 12, 13, 14, 31, 47,
        172, 173, 174, 79, 95, 111, 66,67,68, 81, 83, 96, 97, 98, 21, 23, 36, 37, 42, 43, 44
}
# 76,77, 78 , 13,12, 14currently placeholder of breakable bridge

# ---------------- HUD ----------------
HEART_SIZE = 20
HEART_GAP = 6
HEART_COLOR = (220, 40, 40)
HEART_BG = (60, 60, 60)
