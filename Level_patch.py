"""
Run this once to patch level.py for the new boss fireball/meteor sprites.
Place this file next to level.py and run: python level_patch.py
"""
import re

with open('level.py', 'r') as f:
    src = f.read()

# ── PATCH 1: add "angle":0 to fireball spawn dict ─────────────────────
old_fb_spawn = '''                self.fireballs.append({
                    "x": self.boss.rect.centerx,
                    "y": self.boss.rect.centery,
                    "vx": vx,
                    "vy": vy
                })'''
new_fb_spawn = '''                self.fireballs.append({
                    "x": self.boss.rect.centerx,
                    "y": self.boss.rect.centery,
                    "vx": vx,
                    "vy": vy,
                    "angle": 0
                })'''
src = src.replace(old_fb_spawn, new_fb_spawn)

# ── PATCH 2: update fireball angle each frame ─────────────────────────
old_fb_update = '''            for fb in list(self.fireballs):
                fb["x"] += fb["vx"]
                fb["y"] += fb["vy"]'''
new_fb_update = '''            for fb in list(self.fireballs):
                fb["x"] += fb["vx"]
                fb["y"] += fb["vy"]
                fb["angle"] = (fb.get("angle", 0) + 8) % 360'''
src = src.replace(old_fb_update, new_fb_update)

# ── PATCH 3: replace raw fireball draw with sprite ────────────────────
old_fb_draw = '''        # Fireballs
        if self.level_id == 5:
            for fb in self.fireballs:
                pygame.draw.circle(
                    screen,
                    (255, 80, 20),
                    (int(fb["x"] - cam_x), int(fb["y"] - cam_y)),
                    6
                )'''
new_fb_draw = '''        # Fireballs — sprite-based
        if self.level_id == 5:
            from boss_terminal import TerminalBoss
            for fb in self.fireballs:
                TerminalBoss.draw_fireball(screen, fb, cam_x, cam_y)'''
src = src.replace(old_fb_draw, new_fb_draw)

# ── PATCH 4: replace raw meteor draw with sprite ──────────────────────
old_meteor_draw = '''        # Meteors
        if self.level_id == 5:
            for m in self.meteors:
                if m["warn_timer"] > 0:
                    pygame.draw.circle(
                        screen,
                        (255, 50, 50),
                        (int(m["x"] - cam_x), int(self.world_h - cam_y)),
                        25, 3
                    )
                else:
                    pygame.draw.rect(
                        screen,
                        (255, 120, 0),
                        (m["x"] - cam_x - 10, m["y"] - cam_y, 20, 40)
                    )'''
new_meteor_draw = '''        # Meteors — sprite-based
        if self.level_id == 5:
            from boss_terminal import TerminalBoss
            for m in self.meteors:
                TerminalBoss.draw_meteor(screen, m, cam_x, cam_y, self.world_h)'''
src = src.replace(old_meteor_draw, new_meteor_draw)

with open('level.py', 'w') as f:
    f.write(src)
print("level.py patched successfully!")
print("Changes made:")
print("  1. Fireball spawn now includes 'angle' key for rotation")
print("  2. Fireball angle updates each frame (spinning effect)")
print("  3. Fireball draw → TerminalBoss.draw_fireball() sprite")
print("  4. Meteor draw  → TerminalBoss.draw_meteor() sprite")