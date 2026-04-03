import pygame
from config import *


def load_slash_frames():
    frames = []
    for i in range(1, 7):
        img = pygame.image.load(f"assets/slash/slash{i}.png").convert_alpha()
        img = pygame.transform.scale(img, (48, 48))
        frames.append(img)
    return frames


class Player:
    def __init__(self, solids):
        spawn = min(solids, key=lambda r: (r.x, -r.y))
        self.rect = pygame.Rect(0, 0, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.rect.midbottom = spawn.midtop
        self.spawn = self.rect.topleft
        self.reverse_controls = False

        self.sprite = pygame.transform.scale(
            pygame.image.load("assets/player/idle/idle1.png").convert_alpha(),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        )

        self.run_frames = []
        for i in range(1, 13):
            img = pygame.image.load(f"assets/player/run/run{i}.png").convert_alpha()
            self.run_frames.append(pygame.transform.scale(img, (PLAYER_WIDTH, PLAYER_HEIGHT)))

        self.jump_frame = pygame.transform.scale(
            pygame.image.load("assets/player/jump/jump1.png").convert_alpha(),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        )
        self.fall_frame = pygame.transform.scale(
            pygame.image.load("assets/player/fall/fall1.png").convert_alpha(),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        )

        self.hit_image = pygame.transform.scale(
            pygame.image.load("assets/player/hit/white.png").convert_alpha(),
            (PLAYER_WIDTH, PLAYER_HEIGHT)
        )

        self._sprite_flip      = pygame.transform.flip(self.sprite,     True, False)
        self._jump_flip        = pygame.transform.flip(self.jump_frame, True, False)
        self._fall_flip        = pygame.transform.flip(self.fall_frame, True, False)
        self._hit_flip         = pygame.transform.flip(self.hit_image,  True, False)
        self._run_frames_flip  = [pygame.transform.flip(f, True, False) for f in self.run_frames]

        # ── Idle animation frames ──────────────────────────────────────
        self.idle_frames = []
        for i in range(1, 12):
            try:
                img = pygame.image.load(f"assets/player/idle/idle{i}.png").convert_alpha()
                self.idle_frames.append(pygame.transform.scale(img, (PLAYER_WIDTH, PLAYER_HEIGHT)))
            except Exception:
                break
        if not self.idle_frames:
            self.idle_frames = [self.sprite]   # fallback to single sprite
        self._idle_frames_flip = [pygame.transform.flip(f, True, False) for f in self.idle_frames]
        self.idle_index   = 0.0
        self.idle_speed   = 0.12

        self.run_index    = 0.0
        self.run_speed    = 0.18
        self.hit_timer    = 0
        self.is_moving    = False

        self.grounded_frames = 0
        self.COYOTE_FRAMES   = 5

        self.slash_frames     = load_slash_frames()
        self._slash_flipped   = [pygame.transform.flip(f, True, False) for f in self.slash_frames]
        self.slash_frame      = 0
        self.slash_anim_speed = 0.5
        self.slash_active     = False

        # ── SOUND EFFECTS ─────────────────────────────────────────────
        def _sfx(path, vol=1.0):
            try:
                s = pygame.mixer.Sound(path)
                s.set_volume(vol)
                return s
            except Exception:
                return None

        self.sfx_jump        = _sfx("assets/sfx/player/jump.wav",  0.6)
        self.sfx_sword       = _sfx("assets/sfx/player/sword.wav", 0.7)
        self.sfx_hit         = _sfx("assets/sfx/player/hit.wav",   0.8)
        self.sfx_death       = _sfx("assets/sfx/player/death.wav", 0.9)
        self.sfx_run         = _sfx("assets/sfx/player/run.wav",   0.3)
        self._run_snd_timer  = 14   # start full so run sfx doesn't fire on frame 1

        self.vx = 0
        self.vy = 0
        self.face = 1
        self.on_ground = False

        # max_hp is set by load_level() in main.py after construction.
        # We default to PLAYER_MAX_HP here so the player is never uninitialised.
        self.max_hp = PLAYER_MAX_HP
        self.hp     = PLAYER_MAX_HP
        self.state  = "alive"
        self.visible = True

        self.inv   = False
        self.inv_t = 0

        self.atk     = False
        self.atk_t   = 0
        self.atk_hit = False

        self.frozen_pos = None

    def handle_input(self, keys):
        if self.state != "alive":
            return

        self.vx        = 0
        self.is_moving = False

        left_key  = pygame.K_a
        right_key = pygame.K_d

        if self.reverse_controls:
            left_key, right_key = right_key, left_key

        if keys[left_key] or keys[pygame.K_LEFT]:
            self.vx        = -PLAYER_SPEED
            self.face      = -1
            self.is_moving = True
        if keys[right_key] or keys[pygame.K_RIGHT]:
            self.vx        = PLAYER_SPEED
            self.face      = 1
            self.is_moving = True

        if (keys[pygame.K_SPACE] or keys[pygame.K_UP]) and self.on_ground:
            self.vy              = -PLAYER_JUMP
            self.on_ground       = False
            self.grounded_frames = 0
            if self.sfx_jump: self.sfx_jump.play()

        if keys[pygame.K_j] and not self.atk:
            self.atk          = True
            self.atk_t        = ATTACK_TIME
            self.atk_hit      = False
            self.slash_active = True
            self.slash_frame  = 0
            if self.sfx_sword: self.sfx_sword.play()

    def update(self, solids, bridges, gate):
        if self.state == "dead":
            self.rect.topleft = self.frozen_pos
            return

        if self.atk:
            self.atk_t -= 1
            if self.atk_t <= 0:
                self.atk     = False
                self.atk_hit = False

        if self.inv:
            self.inv_t -= 1
            if self.inv_t <= 0:
                self.inv = False

        if self.slash_active:
            self.slash_frame += self.slash_anim_speed
            if self.slash_frame >= len(self.slash_frames):
                self.slash_active = False
                self.slash_frame  = 0

        if self.hit_timer > 0:
            self.hit_timer -= 1

        self.vy += GRAVITY
        self.vy  = min(self.vy, 20)

        self.rect.x += self.vx
        for s in solids:
            if self.rect.colliderect(s):
                if self.vx > 0:
                    self.rect.right = s.left
                elif self.vx < 0:
                    self.rect.left = s.right

        if gate and gate.state == "closed":
            if self.rect.colliderect(gate.rect):
                self.rect.right = gate.rect.left

        self.rect.y   += self.vy
        self.on_ground = False

        for s in solids:
            if self.rect.colliderect(s):
                if self.vy > 0:
                    self.rect.bottom = s.top
                    self.vy          = 0
                    self.on_ground   = True
                elif self.vy < 0:
                    self.rect.top = s.bottom
                    self.vy       = 0

        for bridge in bridges:
            if not bridge.collidable:
                continue
            if self.vy > 0 and self.rect.colliderect(bridge.rect):
                if self.rect.bottom - self.vy <= bridge.rect.top + 4:
                    self.rect.bottom = bridge.rect.top
                    self.vy          = 0
                    self.on_ground   = True
                    bridge.on_player_step()

        if self.on_ground:
            self.grounded_frames = self.COYOTE_FRAMES
        else:
            self.grounded_frames = max(0, self.grounded_frames - 1)

        # ── animation + run sound ─────────────────────────────────────
        if self.is_moving and self.grounded_frames > 0:
            self.run_index += self.run_speed
            if self.run_index >= len(self.run_frames):
                self.run_index = 0.0
            self.idle_index = 0.0
            # footstep sound every 14 frames
            self._run_snd_timer -= 1
            if self._run_snd_timer <= 0:
                if self.sfx_run: self.sfx_run.play()
                self._run_snd_timer = 14
        else:
            self.run_index = 0.0
            if self.on_ground:
                self.idle_index = (self.idle_index + self.idle_speed) % len(self.idle_frames)

    def attack_rect(self):
        if self.face == 1:
            return pygame.Rect(self.rect.right,     self.rect.y + 10, 35, 40)
        return     pygame.Rect(self.rect.left - 35, self.rect.y + 10, 35, 40)

    def die(self):
        if self.state == "dead":
            return
        if self.sfx_death: self.sfx_death.play()
        self.state      = "dead"
        self.vx         = 0
        self.vy         = 0
        self.frozen_pos = self.rect.topleft

    def take_damage(self):
        if self.inv or self.state != "alive":
            return
        if self.sfx_hit: self.sfx_hit.play()
        self.hp   -= 1
        self.inv   = True
        self.inv_t = INV_TIME
        self.hit_timer = 10
        self.vx = -5 * self.face
        self.vy = -5
        if self.hp <= 0:
            self.die()

    def respawn(self, pos=None):
        self.rect.topleft    = pos if pos else self.spawn
        self.vx              = 0
        self.vy              = 0
        self.hp              = self.max_hp   # ← restore to level's own max, not global
        self.inv             = False
        self.state           = "alive"
        self.frozen_pos      = None
        self.visible         = True
        self.is_moving       = False
        self.run_index       = 0.0
        self.idle_index      = 0.0
        self.grounded_frames = 0

    def draw(self, screen, cam_x, cam_y):
        if not self.visible:
            return

        ix = int(cam_x)
        iy = int(cam_y)

        if self.state == "dead":
            img = self.sprite if self.face == 1 else self._sprite_flip
            img = img.copy()
            img.set_alpha(80)
            screen.blit(img, (self.frozen_pos[0] - ix, self.frozen_pos[1] - iy))
            return

        is_grounded = self.grounded_frames > 0
        right       = (self.face == 1)

        if self.hit_timer > 0:
            base = self.hit_image   if right else self._hit_flip
        elif not is_grounded:
            if self.vy < 0:
                base = self.jump_frame if right else self._jump_flip
            else:
                base = self.fall_frame if right else self._fall_flip
        elif self.is_moving:
            idx  = int(self.run_index)
            base = self.run_frames[idx] if right else self._run_frames_flip[idx]
        else:
            idx  = int(self.idle_index) % len(self.idle_frames)
            base = self.idle_frames[idx] if right else self._idle_frames_flip[idx]

        if self.inv:
            img = base.copy()
            img.set_alpha(120)
            screen.blit(img, (self.rect.x - ix, self.rect.y - iy))
        else:
            screen.blit(base, (self.rect.x - ix, self.rect.y - iy))

        if self.slash_active and self.atk:
            fi = int(self.slash_frame)
            slash_img = self.slash_frames[fi] if right else self._slash_flipped[fi]
            sx = (self.rect.centerx + 13
                  if right
                  else self.rect.centerx - slash_img.get_width() - 13)
            sy = self.rect.centery - slash_img.get_height() // 2
            screen.blit(slash_img, (sx - ix, sy - iy))
