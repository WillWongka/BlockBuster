import pygame, sys, time
from settings import *
from sprites import Player, Ball, Block, Upgrade, Projectile
from surfacemaker import SurfaceMaker
from random import choice, randint


class Game:
    def __init__(self):

        # general setup
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Breakout')

        #game mode
        self.game_mode = ["START", "OPTIONS", "QUIT", "PAUSE"]
        self.current_mode = "START"
        self.started = False

        #option choice
        self.setting_options = ["THEME", "VOLUME", "CREDITS", "BACK"]
        self.current_selection = None

        #theme choice
        self.theme_options = ["90s", "80s"]
        self.current_theme = "90s"

        # main background
        self.bg = self.create_bg("8bit_bg")

        #menu UI images
        self.cursor = pygame.image.load('../graphics/cursor/cursor.png').convert_alpha()
        self.start_menu = pygame.image.load('../graphics/background/start_menu.png').convert_alpha()

        #score and level fonts
        self.hs_font = pygame.font.Font('../graphics/font/BungeeTint-Regular.ttf', 32)
        self.score_level_font = pygame.font.Font('../graphics/font/SairaStencilOne-Regular.ttf', 28)

        #game over fonts
        self.game_over_font = pygame.font.Font('../graphics/font/BungeeTint-Regular.ttf', 70)
        self.secondary_font = pygame.font.Font('../graphics/font/SairaStencilOne-Regular.ttf', 40)

        #option background
        self.options_bg = self.create_bg("options_bg")

        #options UI
        self.options_header = pygame.image.load('../graphics/font/text_images/options_header.png').convert_alpha()
        self.option_theme = pygame.image.load('../graphics/font/text_images/theme.png').convert_alpha()
        self.option_volume = pygame.image.load('../graphics/font/text_images/volume.png').convert_alpha()
        self.option_credits = pygame.image.load('../graphics/font/text_images/credits.png').convert_alpha()
        self.theme90s = pygame.image.load('../graphics/font/text_images/theme90s.png').convert_alpha()
        self.theme80s = pygame.image.load('../graphics/font/text_images/theme80s.png').convert_alpha()

        self.back_button = pygame.image.load('../graphics/other/back.png').convert_alpha()
        self.volume_cursor = pygame.image.load('../graphics/cursor/volume_cursor.png').convert_alpha()

        #credits background
        self.credit_bg = self.create_bg("credit_bg")

        # sprite group setup
        self.all_sprites = pygame.sprite.Group()
        self.block_sprites = pygame.sprite.Group()
        self.upgrade_sprites = pygame.sprite.Group()
        self.projectile_sprites = pygame.sprite.Group()

        #highscore tracking
        self.highscore = self.retrieve_highscore()

        #score and level setup
        self.score_value = 0
        self.projectilekills = 0
        self.level = 1

        # graphics and related setup
        self.surfacemaker = SurfaceMaker()
        self.player = Player(self.all_sprites, self.surfacemaker)
        self.stage_setup()
        self.ball = Ball(self.all_sprites, self.player, self.block_sprites)

        self.ball.scale_speed_based_on_level(self.level)

        # hearts
        self.heart_surf = pygame.image.load('../graphics/other/heart.png').convert_alpha()

        #projectile (animated)
        self.projectile_frames = [
            pygame.image.load('../graphics/laser/LaserShot' + f'{i}.png') for i in range(1, 7)
        ]

        # laser setting
        self.can_shoot = True
        self.shoot_time = 0

        # crt UI
        self.crt = CRT()

        #music
        self.laser_sound = pygame.mixer.Sound('../sounds/laser.wav')
        self.laser_sound.set_volume(0.1)

        self.powerup_sound = pygame.mixer.Sound('../sounds/powerup.wav')
        self.powerup_sound.set_volume(0.1)

        self.laserhit_sound = pygame.mixer.Sound('../sounds/laser_hit.wav')
        self.laserhit_sound.set_volume(0.02)

        self.music = pygame.mixer.Sound('../sounds/funmusic.mp3')
        self.music.set_volume(0.1)
        self.music.play(loops=-1)

    # create upgrade items
    def create_upgrade(self, pos):
        upgrade_type = choice(UPGRADES)
        Upgrade(pos, upgrade_type, [self.all_sprites, self.upgrade_sprites])

    # create scaled background
    def create_bg(self, image_name):
        bg_original = pygame.image.load(f'../graphics/background/{image_name}.png').convert()
        scale_factor = WINDOW_HEIGHT / bg_original.get_height()
        scaled_width = bg_original.get_width() * scale_factor
        scaled_height = bg_original.get_height() * scale_factor
        scaled_bg = pygame.transform.scale(bg_original, (scaled_width, scaled_height))
        return scaled_bg

    def level_up_block(self, column):
        col = int(column)
        level_up = self.level - 1
        if level_up + col < 7:
            col = level_up + col
        elif level_up + col >= 7:
            col = 7
        return str(col)

    # block setup for stage
    def stage_setup(self):
        vertical_padding = 0
        # cycle through all rows and columns of BLOCK MAP
        for row_index, row in enumerate(BLOCK_MAP):
            for col_index, col in enumerate(row):
                if col != ' ':
                    if self.level > 1:
                        col = self.level_up_block(col)
                    # find the x and y position for each individual block
                    x = col_index * (BLOCK_WIDTH + GAP_SIZE) + GAP_SIZE // 2
                    y = TOP_OFFSET + vertical_padding + row_index * (BLOCK_HEIGHT + GAP_SIZE) + GAP_SIZE // 2
                    Block(col, (x, y), [self.all_sprites, self.block_sprites], self.surfacemaker, self.create_upgrade)

    # saving highscore to text file
    @staticmethod
    def save_highscore(highscore):
        with open("highscore.txt", "w") as f:
            f.write(str(highscore))

    # retrieving highscore from text file
    @staticmethod
    def retrieve_highscore():
        with open("highscore.txt", "r") as f:
            highscore = f.read()
            return int(highscore)

    # level reset logic
    def reset_level(self):
        self.level += 1
        self.all_sprites.empty()
        self.block_sprites.empty()
        self.upgrade_sprites.empty()
        self.projectile_sprites.empty()
        self.player = Player(self.all_sprites, self.surfacemaker)
        self.stage_setup()
        self.ball = Ball(self.all_sprites, self.player, self.block_sprites)

        self.ball.scale_speed_based_on_level(self.level)

    def check_level_complete(self):
        if not self.block_sprites:
            self.reset_level()

    # displaying player's life
    def display_hearts(self):
        for i in range(self.player.hearts):
            x = 10 + i * (self.heart_surf.get_width() + 2)
            self.display_surface.blit(self.heart_surf, (x, 10))

    # player upgrade logic
    def upgrade_collision(self):
        overlap_sprites = pygame.sprite.spritecollide(self.player, self.upgrade_sprites, True)
        for sprite in overlap_sprites:
            self.player.upgrade(sprite.upgrade_type)
            self.powerup_sound.play()

    # projectile creation
    def create_projectile(self):
        self.laser_sound.play()
        for projectile in self.player.laser_rects:
            Projectile(projectile.midtop - pygame.math.Vector2(0, 30),
                       [self.all_sprites, self.projectile_sprites],
                       self.projectile_frames)

    def laser_timer(self):
        if pygame.time.get_ticks() - self.shoot_time >= 500:
            self.can_shoot = True

    # displaying score, level and highscore
    def score_update(self):
        score = self.score_level_font.render(f"SCORE: {self.score_value}", True, (255, 255, 255))
        level_display = self.score_level_font.render(f"Level: {self.level}", True, (255, 255, 255))
        high_score_display = self.hs_font.render(f"High Score: {self.highscore}", True, (124, 255, 12))

        self.display_surface.blit(score, (WINDOW_WIDTH - score.get_width() - 20, 0))
        self.display_surface.blit(level_display, (20, WINDOW_HEIGHT - level_display.get_height()))
        self.display_surface.blit(high_score_display, (WINDOW_WIDTH // 2 - high_score_display.get_width() // 2, 0))

    # collision detection logic and score tracking
    def projectile_block_collision(self):
        for projectile in self.projectile_sprites:
            overlap_sprites = pygame.sprite.spritecollide(projectile, self.block_sprites, False)
            if overlap_sprites:
                for sprite in overlap_sprites:
                    sprite.get_damage(1)
                    projectile.kill()  # Remove the projectile
                    self.laserhit_sound.play()
                    self.projectilekills += 1
                    self.score_value += 100
                    if self.score_value >= self.highscore:
                        self.highscore = self.score_value

    # UI for volume adjustment
    def display_volume(self, current_surface):
        volume_position = [(950, 320), (990, 320), (1030, 320), (1070, 320), (1100, 320)]
        volume_cursor = Cursor(self.volume_cursor, volume_position)

        while True:
            volume = volume_cursor.handle_input()
            if volume is not None:
                volume *= 0.25
                for sound in [self.music, self.laserhit_sound, self.powerup_sound, self.laser_sound]:
                    sound.set_volume(volume)
                return

            self.display_surface.blit(current_surface, (0, 0))
            pygame.draw.rect(self.display_surface, (255, 117, 0), (950, 320, 160, 32))
            volume_cursor.draw(self.display_surface)
            pygame.display.update()

    # UI for theme adjustment
    def display_theme(self, current_surface):
        theme_position = [(950, 230), (950, 270)]
        theme_cursor = Cursor(self.cursor, theme_position)
        while True:
            theme_selection = theme_cursor.handle_input()
            if theme_selection == 0:
                for block in self.block_sprites:
                    block.change_theme("theme1")
                self.player.change_theme()
                self.current_theme = "90s"
                return
            elif theme_selection == 1:
                for block in self.block_sprites:
                    block.change_theme("theme2")
                self.player.change_theme()
                self.current_theme = "80s"
                return

            self.display_surface.blit(current_surface, (0, 0))
            self.display_surface.blit(self.theme90s, (1050, 220))
            self.display_surface.blit(self.theme80s, (1050, 260))
            theme_cursor.draw(self.display_surface)
            pygame.display.update()

    # frame for team credit
    def display_credits(self):
        back_position = [(50, 50)]
        back_cursor = Cursor(self.cursor, back_position)
        while True:
            back = back_cursor.handle_input()
            if back is not None:
                self.current_mode = "OPTIONS"
                return

            self.display_surface.blit(self.credit_bg, (0, 0))
            back_cursor.draw(self.display_surface)
            pygame.display.update()

    #UI for options
    def display_options(self):
        self.display_surface.blit(self.options_bg, (0, 0))
        self.display_surface.blit(self.options_header, (WINDOW_WIDTH // 2 + 100, WINDOW_HEIGHT // 14))
        self.display_surface.blit(self.option_theme, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4))
        self.display_surface.blit(self.option_volume, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4 + 80))
        self.display_surface.blit(self.option_credits, (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4 + 160))
        self.display_surface.blit(self.back_button, (WINDOW_WIDTH // 24, WINDOW_HEIGHT // 10))
        self.crt.draw()
        pygame.display.flip()

        menu_position = [(610, 250), (610, 330), (610, 410), (55, 115)]

        current_surface = self.display_surface.copy()
        settings_cursor = Cursor(self.cursor, menu_position)

        while self.current_mode != "START":
            selected_option = settings_cursor.handle_input()
            if selected_option is not None:
                self.current_selection = self.setting_options[selected_option]
                if self.current_selection == "VOLUME":
                    self.display_volume(current_surface)
                if self.current_selection == "THEME":
                    self.display_theme(current_surface)
                if self.current_selection == "CREDITS":
                    self.display_credits()
                if self.current_selection == "BACK":
                    self.current_mode = "START"

            self.current_selection = None
            self.display_surface.blit(current_surface, (0, 0))
            settings_cursor.draw(self.display_surface)
            pygame.display.update()

    # UI enhancement for displaying score, level, highscore more clearly
    def overlay(self):
        overlay_height = 40
        overlay = pygame.Surface((WINDOW_WIDTH, overlay_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.display_surface.blit(overlay, (0, 0))

    # UI element
    def dim_background(self):
        dim_surface = pygame.Surface(self.display_surface.get_size())
        dim_surface.set_alpha(128)
        dim_surface.fill((0, 0, 0))
        self.display_surface.blit(dim_surface, (0, 0))

    # UI for the main menu
    def display_menu(self):
        menu_width = self.start_menu.get_width()
        menu_height = self.start_menu.get_height()
        menu_x = (WINDOW_WIDTH - menu_width) // 2
        menu_y = (WINDOW_HEIGHT - menu_height) // 3

        self.display_surface.blit(self.start_menu, (menu_x, menu_y))
        current_surface = self.display_surface.copy()
        menu_positions = [(440, 320), (440, 360), (440, 400)]

        cursor = Cursor(self.cursor, menu_positions)

        while True:
            selected_mode = cursor.handle_input()
            if selected_mode is not None:
                self.current_mode = self.game_mode[selected_mode]
                if self.current_mode == "START":
                    if self.started:
                        self.ball.active = True
                    self.started = True
                return

            self.display_surface.blit(current_surface, (0, 0))
            cursor.draw(self.display_surface)
            self.crt.draw()
            pygame.display.update()

    # game over logic with highscore saving
    def game_over(self):

        # Update high score text file if current score exceeds it
        if self.score_value >= self.highscore:
            self.save_highscore(self.score_value)

        while self.current_mode == "GAME OVER":

            self.display_surface.fill((0, 0, 0))  # Clear the screen with black

            game_over_text = self.game_over_font.render("GAME OVER", True, (255, 0, 0))
            score_text = self.secondary_font.render(f"Final Score: {self.score_value}", True, (255, 255, 255))
            high_score_text = self.secondary_font.render(f"High Score: {self.highscore}", True, (255, 255, 0))
            play_again_text = self.secondary_font.render("Press R to Play Again", True, (255, 255, 255))
            quit_text = self.secondary_font.render("Press Q to Quit", True, (255, 255, 255))
            self.display_surface.blit(game_over_text,
                                      (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2, WINDOW_HEIGHT // 2 - 150))
            self.display_surface.blit(score_text,
                                      (WINDOW_WIDTH // 2 - score_text.get_width() // 2, WINDOW_HEIGHT // 2 - 50))
            self.display_surface.blit(high_score_text,
                                      (WINDOW_WIDTH // 2 - high_score_text.get_width() // 2, WINDOW_HEIGHT // 2 + 50))
            self.display_surface.blit(play_again_text,
                                      (WINDOW_WIDTH // 2 - play_again_text.get_width() // 2, WINDOW_HEIGHT // 2 + 150))
            self.display_surface.blit(quit_text,
                                      (WINDOW_WIDTH // 2 - quit_text.get_width() // 2, WINDOW_HEIGHT // 2 + 200))
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_r:  # Restart the game
                        self.score_value = 0
                        self.projectilekills = 0
                        self.level = 0
                        self.reset_level()
                        self.current_mode = "START"
                    elif event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()

    # main game logic
    def play(self, dt):

        if self.player.hearts > 0 and self.current_mode != "PAUSE":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.ball.active = True
                        if self.can_shoot:
                            self.create_projectile()
                            self.can_shoot = False
                            self.shoot_time = pygame.time.get_ticks()
                    if event.key == pygame.K_RETURN:
                        self.current_mode = "PAUSE"
                        return

            # draw bg
            self.display_surface.blit(self.bg, (0, 0))

            # update the game
            self.all_sprites.update(dt)
            self.upgrade_collision()
            self.laser_timer()
            self.projectile_block_collision()
            self.check_level_complete()

            # draw the frame
            self.all_sprites.draw(self.display_surface)
            self.overlay()
            self.display_hearts()
            self.score_update()

            # crt styling
            self.crt.draw()

            if not self.started:
                self.dim_background()
                self.display_menu()

            pygame.display.update()
        else:
            self.current_mode = "GAME OVER"

    # main loop
    def run(self):
        last_time = time.time()

        while True:
            dt = time.time() - last_time
            if self.current_mode == "START":
                last_time = time.time()
                self.play(dt)
            elif self.current_mode == "GAME OVER":
                self.game_over()
            elif self.current_mode == "OPTIONS":
                self.display_options()
                last_time = time.time()
            elif self.current_mode == "PAUSE":
                self.display_menu()
                last_time = time.time()
            elif self.current_mode == "QUIT":
                pygame.quit()
                sys.exit()


# selection cursor and logic
class Cursor:
    def __init__(self, images, positions):
        self.image = images
        self.positions = positions
        self.current_index = 0

    def move_up(self):
        if self.current_index > 0:
            self.current_index -= 1

    def move_down(self):
        if self.current_index < len(self.positions) - 1:
            self.current_index += 1

    def get_position(self):
        return self.positions[self.current_index]

    def draw(self, surface):
        surface.blit(self.image, self.get_position())

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.move_down()
                elif event.key == pygame.K_UP:
                    self.move_up()
                if event.key == pygame.K_RETURN:
                    return self.current_index


# UI enhancement for retro-vibe
class CRT:
    def __init__(self):
        vignette = pygame.image.load('../graphics/background/tv.png').convert_alpha()
        self.scaled_vignette = pygame.transform.scale(vignette, (WINDOW_WIDTH, WINDOW_HEIGHT))
        self.display_surface = pygame.display.get_surface()
        self.create_crt_lines()

    def create_crt_lines(self):
        line_height = 4
        line_amount = WINDOW_HEIGHT // line_height
        for line in range(line_amount):
            y = line * line_height
            pygame.draw.line(self.scaled_vignette, (20, 20, 20), (0, y), (WINDOW_WIDTH, y), 1)

    def draw(self):
        self.scaled_vignette.set_alpha(randint(60, 75))
        self.display_surface.blit(self.scaled_vignette, (0, 0))


if __name__ == '__main__':
    game = Game()
    game.run()
