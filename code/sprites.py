import pygame
from settings import *
from random import choice, randint


class Upgrade(pygame.sprite.Sprite):
    def __init__(self, pos, upgrade_type, groups):
        super().__init__(groups)
        self.upgrade_type = upgrade_type
        self.image = pygame.image.load(f'../graphics/upgrades/{upgrade_type}.png').convert_alpha()
        self.rect = self.image.get_rect(midtop=pos)

        self.pos = pygame.math.Vector2(self.rect.topleft)
        self.speed = 300

    def update(self, dt):
        self.pos.y += self.speed * dt
        self.rect.y = round(self.pos.y)

        if self.rect.top > WINDOW_HEIGHT + 100:
            self.kill()


class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, groups, frames):
        super().__init__(groups)
        self.frames = frames
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(midbottom=pos)
        self.animation_timer = 0

        self.pos = pygame.math.Vector2(self.rect.topleft)
        self.speed = 300

    def update(self, dt):

        self.animation_timer += 1
        if self.animation_timer >= dt:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]

        self.pos.y -= self.speed * dt
        self.rect.y = round(self.pos.y)

        if self.rect.bottom <= -100:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, groups, surfacemaker):
        super().__init__(groups)

        # setup
        self.display_surface = pygame.display.get_surface()
        self.surfacemaker = surfacemaker
        self.image = surfacemaker.get_surf('player', (WINDOW_WIDTH // 10, WINDOW_HEIGHT // 20))

        # position
        self.rect = self.image.get_rect(midbottom=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 20))
        self.old_rect = self.rect.copy()
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(self.rect.topleft)
        self.speed = 300

        self.hearts = 3

        # laser
        self.laser_amount = 2
        self.laser_surf = pygame.image.load('../graphics/other/laser.png').convert_alpha()
        self.laser_rects = []

    def input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            self.direction.x = 1
        elif keys[pygame.K_LEFT]:
            self.direction.x = -1
        else:
            self.direction.x = 0

    def screen_constraint(self):
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH
            self.pos.x = self.rect.x
        if self.rect.left < 0:
            self.rect.left = 0
            self.pos.x = self.rect.x

    def upgrade(self, upgrade_type):
        if upgrade_type == 'speed':
            self.speed += 50
        if upgrade_type == 'heart':
            self.hearts += 1

        if upgrade_type == 'size':
            new_width = self.rect.width * 1.1
            self.image = self.surfacemaker.get_surf('player', (new_width, self.rect.height))
            self.rect = self.image.get_rect(center=self.rect.center)
            self.pos.x = self.rect.x

        if upgrade_type == 'laser':
            self.laser_amount += 1

    def display_lasers(self):
        self.laser_rects = []
        if self.laser_amount > 0:
            divider_length = self.rect.width / (self.laser_amount + 1)
            for i in range(self.laser_amount):
                x = self.rect.left + divider_length * (i + 1)
                laser_rect = self.laser_surf.get_rect(midbottom=(x, self.rect.top))
                self.laser_rects.append(laser_rect)

            for laser_rect in self.laser_rects:
                self.display_surface.blit(self.laser_surf, laser_rect)

    def update(self, dt):
        self.old_rect = self.rect.copy()
        self.input()
        self.pos.x += self.direction.x * self.speed * dt
        self.rect.x = round(self.pos.x)
        self.screen_constraint()
        self.display_lasers()

    def change_theme(self):
        self.image = self.surfacemaker.get_surf('player', (self.rect.width, self.rect.height))


class Ball(pygame.sprite.Sprite):
    def __init__(self, groups, player, blocks):
        super().__init__(groups)

        # Collision objects
        self.player = player
        self.blocks = blocks

        # Graphics setup
        self.image = pygame.image.load('../graphics/other/ball.png').convert_alpha()

        # Position setup
        self.rect = self.image.get_rect(midbottom=player.rect.midtop)
        self.old_rect = self.rect.copy()
        self.pos = pygame.math.Vector2(self.rect.topleft)
        self.direction = pygame.math.Vector2((choice((1, -1)), -1))

        # Initial speed
        self.base_speed = 300  # This will be the base speed, which will scale with level
        self.speed = self.base_speed

        # Active state
        self.active = False

        # Sounds
        self.impact_sound = pygame.mixer.Sound('../sounds/impact.wav')
        self.impact_sound.set_volume(0.1)

        self.fail_sound = pygame.mixer.Sound('../sounds/fail.wav')
        self.fail_sound.set_volume(0.1)

    def scale_speed_based_on_level(self, level):
        # Increase the ball speed as the level increases (e.g., 10% increase per level)
        self.speed = self.base_speed + (level - 1) * 30  # Example: Increases by 30 per level

    def window_collision(self, direction):
        if direction == 'horizontal':
            if self.rect.left < 0:
                self.rect.left = 0
                self.pos.x = self.rect.x
                self.direction.x *= -1

            if self.rect.right > WINDOW_WIDTH:
                self.rect.right = WINDOW_WIDTH
                self.pos.x = self.rect.x
                self.direction.x *= -1

        if direction == 'vertical':
            if self.rect.top < 0:
                self.rect.top = 0
                self.pos.y = self.rect.y
                self.direction.y *= -1

            if self.rect.bottom > WINDOW_HEIGHT:
                self.active = False
                self.direction.y = -1
                self.player.hearts -= 1
                self.fail_sound.play()

    def collision(self, direction):
        # Find overlapping objects
        overlap_sprites = pygame.sprite.spritecollide(self, self.blocks, False)
        if self.rect.colliderect(self.player.rect):
            overlap_sprites.append(self.player)

        if overlap_sprites:
            if direction == 'horizontal':
                for sprite in overlap_sprites:
                    if self.rect.right >= sprite.rect.left and self.old_rect.right <= sprite.old_rect.left:
                        self.rect.right = sprite.rect.left - 1
                        self.pos.x = self.rect.x
                        self.direction.x *= -1
                        self.impact_sound.play()

                    if self.rect.left <= sprite.rect.right and self.old_rect.left >= sprite.old_rect.right:
                        self.rect.left = sprite.rect.right + 1
                        self.pos.x = self.rect.x
                        self.direction.x *= -1
                        self.impact_sound.play()

                    if getattr(sprite, 'health', None):
                        sprite.get_damage(1)

            if direction == 'vertical':
                for sprite in overlap_sprites:
                    if self.rect.bottom >= sprite.rect.top and self.old_rect.bottom <= sprite.old_rect.top:
                        self.rect.bottom = sprite.rect.top - 1
                        self.pos.y = self.rect.y
                        self.direction.y *= -1
                        self.impact_sound.play()

                    if self.rect.top <= sprite.rect.bottom and self.old_rect.top >= sprite.old_rect.bottom:
                        self.rect.top = sprite.rect.bottom + 1
                        self.pos.y = self.rect.y
                        self.direction.y *= -1
                        self.impact_sound.play()

                    if getattr(sprite, 'health', None):
                        sprite.get_damage(1)

    def update(self, dt):
        if self.active:

            if self.direction.magnitude() != 0:
                self.direction = self.direction.normalize()

            # Create old rect
            self.old_rect = self.rect.copy()

            # Horizontal movement + collision
            self.pos.x += self.direction.x * self.speed * dt
            self.rect.x = round(self.pos.x)
            self.collision('horizontal')
            self.window_collision('horizontal')

            # Vertical movement + collision
            self.pos.y += self.direction.y * self.speed * dt
            self.rect.y = round(self.pos.y)
            self.collision('vertical')
            self.window_collision('vertical')

        else:
            self.rect.midbottom = self.player.rect.midtop
            self.pos = pygame.math.Vector2(self.rect.topleft)


class Block(pygame.sprite.Sprite):
    def __init__(self, block_type, pos, groups, surfacemaker, create_upgrade):
        super().__init__(groups)
        self.surfacemaker = surfacemaker

        self.block_type = block_type

        self.image = self.surfacemaker.get_surf(COLOR_LEGEND[block_type], (BLOCK_WIDTH, BLOCK_HEIGHT))
        self.rect = self.image.get_rect(topleft=pos)
        self.old_rect = self.rect.copy()

        # damage information
        self.health = int(block_type)

        # upgrade
        self.create_upgrade = create_upgrade

    def change_theme(self, theme):
        self.surfacemaker.change_surf(theme)
        self.image = self.surfacemaker.get_surf(COLOR_LEGEND[self.block_type], (BLOCK_WIDTH, BLOCK_HEIGHT))

    def get_damage(self, amount):
        self.health -= amount

        if self.health > 0:
            self.image = self.surfacemaker.get_surf(COLOR_LEGEND[str(self.health)], (BLOCK_WIDTH, BLOCK_HEIGHT))
        else:
            if randint(0, 10) < 9:
                self.create_upgrade(self.rect.center)
            self.kill()