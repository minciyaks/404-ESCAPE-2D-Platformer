# checkpoint.py
import pygame


class Checkpoint:
    def __init__(self, x, y, w=32, h=32):
        self.rect = pygame.Rect(x, y, w, h)
        self.active = False

    def draw(self, screen, cam_x, cam_y):
        color = (0, 200, 0) if self.active else (120, 120, 120)
        pygame.draw.rect(
            screen,
            color,
            (self.rect.x - cam_x, self.rect.y - cam_y, self.rect.w, self.rect.h),
            2
        )
