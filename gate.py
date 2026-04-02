# gate.py
import pygame


class Gate:
    def __init__(self, x, y, world_height, frames, width=16, speed=6):

        self.rect = pygame.Rect(x, y, width, world_height - y)
        self.world_height = world_height
        self.start_y = y
        self.floor_y = y + (world_height - y)
        self.visual_y = y

        self.frames = frames
        self.state = "closed"   # closed | opening | open
        self.speed = speed

        # ⭐ Animation
        self.anim_index = 0
        self.anim_timer = 0
        self.anim_speed = 10   # smaller = faster

    # =========================
    # UPDATE
    # =========================
    def update(self):

        # --- Opening physics ---
        if self.state == "opening":
            self.rect.y -= self.speed
            self.rect.height -= self.speed

            # --- Animate opening ---
            self.anim_timer += 1

            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0

                if self.anim_index < len(self.frames) - 1:
                    self.anim_index += 1

            if self.rect.height <= 0:
                self.state = "open"

    # =========================
    # TRIGGER
    # =========================
    def open(self):
        if self.state == "closed":
            self.state = "opening"
            self.anim_index = 0

    # =========================
    # RESET
    # =========================
    def reset(self):
        self.rect.y = self.start_y
        self.rect.height = self.world_height - self.start_y
        self.state = "closed"
        self.anim_index = 0

    # =========================
    # DRAW
    # =========================
    def draw(self, screen, cam_x, cam_y):

        # ✔ Closed gate → show first frame (locked look)
        if self.state == "closed":
            frame = self.frames[0]

        # ✔ Opening animation
        elif self.state == "opening":
            frame = self.frames[self.anim_index]

        # ✔ Fully open
        else:
            frame = self.frames[-1]

        sprite_x = self.rect.x - cam_x - (frame.get_width() - self.rect.width)//2
        sprite_y = self.visual_y - cam_y

        screen.blit(frame, (sprite_x, sprite_y))