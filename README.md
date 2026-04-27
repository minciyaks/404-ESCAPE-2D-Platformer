# 404 Escape

> *You didn't open it. It opened you.*

A 2D pixel-art platformer built with **Python + Pygame** where a developer gets pulled inside their own screen and must fight through five corrupted system levels to escape.

---

## Table of Contents

- [Story](#story)
- [Gameplay](#gameplay)
- [Levels](#levels)
- [Controls](#controls)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Credits](#credits)

---

## Story

Another day. Another shift. The world outside is gray.

A mysterious file appears on your desktop — one that shouldn't be there. The moment you open it, the code doesn't just change your screen. It changes *you*. You are pulled inside the machine. The only way out is forward.

---

## Gameplay

404 Escape is a side-scrolling action platformer. Run, jump, and slash your way through five increasingly dangerous levels. Each level is locked behind a gate that only opens once all enemies are defeated. Reach the gate to breach the next system.

- **Attack enemies** to unlock the exit gate
- **Avoid traps** — spikes, rotating saws, crumbling bridges
- **Use checkpoints** to save your progress mid-level
- **Survive special zones** — some levels lock you in and force you to outlast a timer
- **Watch out for the death wall** in the final level — it rises from below and cannot be outrun forever

---

## Levels

| # | Name | Description |
|---|------|-------------|
| 1 | **Awakening** | Tutorial level. Learn the basics. Enemies are slow and forgiving. |
| 2 | **Pressure** | Breakable bridges and tighter spike timing ramp up the challenge. |
| 3 | **Chaos** | Shooter enemies, flying threats, chain bridges, and a commit zone that locks you in. |
| 4 | **Descent** | Reverse controls zone, jump pads, blinking and moving saws. No ground enemies — only flyers. |
| 5 | **Terminal** | The final system. A boss arena locks you in. Survive fireballs, meteor strikes, and a rising death wall. Reach the correct gate to escape — one of them is a trap. |

---

## Controls

| Key | Action |
|-----|--------|
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `Space` / `↑` | Jump |
| `J` | Attack (slash) |
| `ESC` | Pause |
| `Enter` | Confirm / advance |

---

## Features

- **5 handcrafted levels** with unique mechanics per level
- **Cinematic intro** with 4 illustrated story scenes
- **Cyber-themed UI** — glitch title, animated level select network map, scanline overlay
- **Per-level player HP** — visual HUD always shows 5 hearts but each heart absorbs more hits as levels progress
- **Partial heart rendering** — hearts drain proportionally rather than in fixed whole increments
- **Checkpoints** — respawn mid-level in levels 3, 4, and 5
- **Reverse controls zone** in level 4 that flips left/right input
- **Boss arena** in level 5 with:
  - Homing fireballs
  - Meteor strikes with warning indicators
  - Rising crimson death wall with pulsing glow effect
  - Two gates — one real exit, one trap
- **Animated sprites** — idle, run, jump, fall, hit, and slash animations for the player
- **Procedural trap visuals** — fireball, meteor, and warning ring sprites generated in code
- **Full SFX suite** — jump, sword, hit, death, enemies, traps, checkpoints, UI, and music per level
- **Level-specific background music** — intro, levels 1–2, levels 3–4, level 5, and ending tracks
- **Smooth camera** with lerp tracking and screen shake on boss trigger
- **Fake saw platforms** in level 4 that look dangerous but are safe to stand on

---

## Project Structure

```
404-escape/
│
├── main.py               # Game entry point, main loop, UI screens
├── config.py             # All tuneable constants (HP, speed, tile size, etc.)
├── player.py             # Player class — movement, animation, combat, damage
├── level.py              # Level loader, trap/enemy/boss logic, draw pipeline
├── enemy.py              # Ground enemy (passive patrol + cannon shooter)
├── flying_enemy.py       # Flying enemy — idle patrol and dive attack
├── boss_terminal.py      # Level 5 boss — fireball and meteor projectiles
├── trap.py               # SpikeTrap, BreakableBridge, JumpPad, RotatingSaw, FakeSaw
├── gate.py               # Animated exit gate
├── checkpoint.py         # Checkpoint save points
│
├── maps/
│   ├── level1_ground.csv
│   ├── level2_ground.csv
│   ├── level3_ground.csv
│   ├── level4_ground.csv
│   └── level5_ground.csv
│
├── assets/
│   ├── player/           # idle, run, jump, fall, hit sprite frames
│   ├── enemy/            # level1–3 passive, canon shooter sprites
│   ├── flying_enemy/     # fly frames + hit frame
│   ├── 4 Enemies/BOSS/   # boss sprite strips
│   ├── 6 Traps/          # spike, bridge, jump_pad, saw sprites
│   ├── 7 Levels/Tiled/   # tilesets and level backgrounds
│   ├── gate/             # gate animation frames
│   ├── hud/              # hp1.png (full heart), hp2.png (empty heart)
│   ├── slash/            # sword slash animation frames
│   ├── intro/            # intro scene illustrations
│   ├── menu/             # main menu background
│   ├── ending/           # ending screen image
│   ├── effects/          # fire_spritesheet.png for meteor animation
│   └── sfx/
│       ├── player/       # jump, sword, hit, death, run
│       ├── enemy/        # canon, death
│       ├── traps/        # spike, bridge, jump_pad, commit_lock, warning, checkpoint, death_wall
│       ├── boss/         # fireball, meteor
│       ├── ui/           # button, scrolling, victory, keyboard, main_menu, gate, back
│       └── music/        # intro, level1_2, level3_4, level5, ending
```

---

## Installation

### Option 1 (Recommended – works on latest Python)

```bash
# Clone the repository
git clone https://github.com/minciyaks/404-ESCAPE-2D-Platformer.git
cd 404-ESCAPE-2D-Platformer

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install pygame-ce

# Run the game
python main.py
```

---

### Option 2 (Stable alternative)

```bash
# Use Python 3.10 or 3.11

pip install pygame
python main.py
```

---

### Requirements

* Python 3.10+
* Recommended: Python 3.14 with pygame-ce


---

## Configuration

All game constants live in `config.py` and can be freely edited:

```python
# Tune player HP per level — HUD always shows 5 hearts
# hp_per_heart = LEVEL_PLAYER_HP[level] / 5
LEVEL_PLAYER_HP = {
    1:  5,   # 1 hit  per heart
    2: 10,   # 2 hits per heart
    3: 15,   # 3 hits per heart
    4: 20,   # 4 hits per heart
    5: 25,   # 5 hits per heart
}

# Enemy HP per level
LEVEL_ENEMY_HP = {
    1: 10,
    2: 12,
    3: 18,
    4: 20,
    5: 22,
}

# Core physics
GRAVITY      = 0.8
PLAYER_SPEED = 5
PLAYER_JUMP  = 12
```

---

## Credits

| Role | Credit |
|------|--------|
| Created by | Minciya K S |
| Role | Solo Developer |
| Map Design | Tiled Map Editor |
| Assets | Craftpix.net, itch.io |
|Music | Zakiro|
| SFX | Various Free Sources |
| Art | AI Generated |
| Special Thanks | opengameart.org |

---

*404 Escape — the system failed. So did the exit.*
