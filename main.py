import pygame
import sys
import random
import asyncio

# --- Game Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 400
GROUND_HEIGHT = 50
PLAYER_SIZE = 40
OBSTACLE_WIDTH = 30
OBSTACLE_HEIGHT = 30
YARN_BALL_RADIUS = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (100, 100, 255) # Player color
RED = (255, 0, 0)     # Obstacle color
YELLOW = (255, 255, 0) # Yarn ball color
GREEN = (0, 200, 0)   # Ground color
DARK_BLUE = (50, 50, 150) # Background hills
LIGHT_BLUE_SKY = (173, 216, 230) # Sky background

# Game Physics
GRAVITY = 0.8
JUMP_STRENGTH = -15
GAME_SPEED_INITIAL = 5
GAME_SPEED_INCREMENT = 0.001 # How much speed increases per frame
MAX_GAME_SPEED = 15

# Spawning Frequencies (lower value means more frequent)
OBSTACLE_SPAWN_CHANCE = 0.015 # Chance per frame to spawn an obstacle
COLLECTIBLE_SPAWN_CHANCE = 0.005 # Chance per frame to spawn a collectible

# Score
DISTANCE_SCORE_MULTIPLIER = 0.1
COLLECTIBLE_BONUS = 10

# --- Classes ---

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([PLAYER_SIZE, PLAYER_SIZE])
        self.image.fill(BLUE) # Placeholder for Pixel Paws
        self.rect = self.image.get_rect()
        self.rect.midbottom = (SCREEN_WIDTH // 4, SCREEN_HEIGHT - GROUND_HEIGHT)
        self.vel_y = 0
        self.is_jumping = False
        self.on_ground = True

    def update(self):
        # Apply gravity
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # Keep player on ground
        if self.rect.bottom >= SCREEN_HEIGHT - GROUND_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT - GROUND_HEIGHT
            self.vel_y = 0
            self.is_jumping = False
            self.on_ground = True
        else:
            self.on_ground = False # Player is in the air

    def jump(self):
        if self.on_ground:
            self.vel_y = JUMP_STRENGTH
            self.is_jumping = True
            self.on_ground = False

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, game_speed):
        super().__init__()
        # Randomly choose obstacle type (visual distinction only for now)
        obstacle_type = random.choice(["box", "fishbone"])
        self.image = pygame.Surface([OBSTACLE_WIDTH, OBSTACLE_HEIGHT])
        if obstacle_type == "box":
            self.image.fill(RED) # Cardboard box
        else:
            self.image.fill((200, 100, 0)) # Fishbone pile (brownish red)

        self.rect = self.image.get_rect()
        self.rect.bottomleft = (SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT)
        self.speed = game_speed

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill() # Remove obstacle once it's off-screen

class YarnBall(pygame.sprite.Sprite):
    def __init__(self, game_speed):
        super().__init__()
        self.image = pygame.Surface([YARN_BALL_RADIUS * 2, YARN_BALL_RADIUS * 2], pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (YARN_BALL_RADIUS, YARN_BALL_RADIUS), YARN_BALL_RADIUS)
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT - 5) # Slightly above ground
        self.speed = game_speed

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill() # Remove collectible once it's off-screen

# --- Game Initialization ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pixel Paws: The Endless Leap")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36) # Default font, size 36

# --- Game Variables (for restart functionality) ---
player = None
all_sprites = None
obstacles = None
collectibles = None
game_speed = 0
score = 0
distance_traveled = 0
game_over_state = False

def reset_game():
    global player, all_sprites, obstacles, collectibles, game_speed, score, game_over_state, distance_traveled
    
    player = Player()
    all_sprites = pygame.sprite.Group()
    obstacles = pygame.sprite.Group()
    collectibles = pygame.sprite.Group()

    all_sprites.add(player)

    game_speed = GAME_SPEED_INITIAL
    score = 0
    distance_traveled = 0
    game_over_state = False

async def main():
    global player, all_sprites, obstacles, collectibles, game_speed, score, game_over_state, distance_traveled
    
    reset_game()

    # Background scrolling variables
    bg_x = 0
    bg_speed_multiplier = 0.5 # Parallax effect

    # --- Game Loop ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    if not game_over_state:
                        player.jump()
                    else:
                        reset_game()

        if not game_over_state:
            # --- Update ---
            all_sprites.update()

            # Update game speed
            game_speed += GAME_SPEED_INCREMENT
            game_speed = min(game_speed, MAX_GAME_SPEED) # Cap max speed

            # Scroll background
            bg_x -= game_speed * bg_speed_multiplier
            if bg_x <= -SCREEN_WIDTH:
                bg_x = 0

            # Spawning obstacles
            if random.random() < OBSTACLE_SPAWN_CHANCE:
                new_obstacle = Obstacle(game_speed)
                obstacles.add(new_obstacle)
                all_sprites.add(new_obstacle)

            # Spawning collectibles
            if random.random() < COLLECTIBLE_SPAWN_CHANCE:
                new_yarn_ball = YarnBall(game_speed)
                collectibles.add(new_yarn_ball)
                all_sprites.add(new_yarn_ball)

            # Update obstacles and collectibles to scroll them
            for obs in obstacles:
                obs.speed = game_speed # Ensure obstacles move at current game speed
            for yarn in collectibles:
                yarn.speed = game_speed # Ensure collectibles move at current game speed

            # --- Collision Detection ---

            # Player vs Obstacles
            if pygame.sprite.spritecollide(player, obstacles, False):
                game_over_state = True

            # Player vs Collectibles
            collected_yarn_balls = pygame.sprite.spritecollide(player, collectibles, True) # True removes collected sprite
            for yarn in collected_yarn_balls:
                score += COLLECTIBLE_BONUS

            # Score update (distance)
            distance_traveled += game_speed
            score = int(distance_traveled * DISTANCE_SCORE_MULTIPLIER) + (score % COLLECTIBLE_BONUS if collected_yarn_balls else score)


        # --- Drawing ---
        screen.fill(LIGHT_BLUE_SKY) # Sky background

        # Draw parallax background elements (simple hills)
        pygame.draw.ellipse(screen, DARK_BLUE, (bg_x - 100, SCREEN_HEIGHT - GROUND_HEIGHT - 80, 200, 100))
        pygame.draw.ellipse(screen, DARK_BLUE, (bg_x + 150, SCREEN_HEIGHT - GROUND_HEIGHT - 120, 250, 150))
        pygame.draw.ellipse(screen, DARK_BLUE, (bg_x + 400, SCREEN_HEIGHT - GROUND_HEIGHT - 90, 180, 110))
        pygame.draw.ellipse(screen, DARK_BLUE, (bg_x + 600, SCREEN_HEIGHT - GROUND_HEIGHT - 130, 220, 160))

        # Draw a second set of hills for seamless scrolling
        pygame.draw.ellipse(screen, DARK_BLUE, (bg_x + SCREEN_WIDTH - 100, SCREEN_HEIGHT - GROUND_HEIGHT - 80, 200, 100))
        pygame.draw.ellipse(screen, DARK_BLUE, (bg_x + SCREEN_WIDTH + 150, SCREEN_HEIGHT - GROUND_HEIGHT - 120, 250, 150))
        pygame.draw.ellipse(screen, DARK_BLUE, (bg_x + SCREEN_WIDTH + 400, SCREEN_HEIGHT - GROUND_HEIGHT - 90, 180, 110))
        pygame.draw.ellipse(screen, DARK_BLUE, (bg_x + SCREEN_WIDTH + 600, SCREEN_HEIGHT - GROUND_HEIGHT - 130, 220, 160))


        # Draw the ground
        pygame.draw.rect(screen, GREEN, (0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT))

        all_sprites.draw(screen) # Draw player, obstacles, and collectibles

        # Display score
        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        # Game Over screen
        if game_over_state:
            game_over_text = font.render("Game Over!", True, BLACK)
            restart_text = font.render("Press SPACE to Restart", True, BLACK)
            final_score_text = font.render(f"Final Score: {score}", True, BLACK)

            text_rect_go = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            text_rect_fs = final_score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            text_rect_restart = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))

            screen.blit(game_over_text, text_rect_go)
            screen.blit(final_score_text, text_rect_fs)
            screen.blit(restart_text, text_rect_restart)

        # --- Update Display ---
        pygame.display.flip()

        # --- Frame Rate ---
        clock.tick(60) # Cap the frame rate at 60 FPS
        
        # VERY IMPORTANT FOR PYGBAG
        await asyncio.sleep(0)

asyncio.run(main())
