import math
import random
import pygame


WIDTH, HEIGHT = 960, 540
PADDLE_WIDTH, PADDLE_HEIGHT = 18, 120
BALL_SIZE = 14
PADDLE_SPEED = 500
BALL_SPEED = 430
WINNING_SCORE = 7


class Paddle:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = color
        self.speed = PADDLE_SPEED

    def move(self, direction, dt):
        self.rect.y += direction * self.speed * dt
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y))

    def move_towards(self, target_y, dt):
        if self.rect.centery < target_y:
            self.move(1, dt)
        elif self.rect.centery > target_y:
            self.move(-1, dt)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)


class Ball:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.velocity = pygame.Vector2()

    def reset(self, direction):
        self.rect.center = (WIDTH // 2, HEIGHT // 2)
        angle = random.uniform(-0.85, 0.85)
        x_speed = direction * BALL_SPEED * math.cos(angle)
        y_speed = BALL_SPEED * math.sin(angle)
        self.velocity = pygame.Vector2(x_speed, y_speed)

    def update(self, dt, left_paddle, right_paddle):
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt

        if self.rect.top <= 0:
            self.rect.top = 0
            self.velocity.y *= -1
        elif self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.velocity.y *= -1

        for paddle in (left_paddle, right_paddle):
            if self.rect.colliderect(paddle.rect):
                self.rect.x = min(self.rect.x, paddle.rect.x - self.rect.width) if self.velocity.x > 0 else max(self.rect.x, paddle.rect.right)
                self.velocity.x *= -1.05

                offset = (self.rect.centery - paddle.rect.centery) / (paddle.rect.height / 2)
                self.velocity.y = offset * 260

                current_speed = self.velocity.length()
                if current_speed < 430:
                    self.velocity.scale_to_length(430)
                if current_speed > 940:
                    self.velocity.scale_to_length(940)

    def draw(self, surface):
        pygame.draw.ellipse(surface, (255, 255, 255), self.rect)


class GameModel:
    def __init__(self, mode):
        self.mode = mode
        self.left_paddle = Paddle(40, HEIGHT // 2 - PADDLE_HEIGHT // 2, (255, 255, 255))
        self.right_paddle = Paddle(WIDTH - 40 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, (255, 255, 255))
        self.ball = Ball()
        self.left_score = 0
        self.right_score = 0
        self.game_over = False
        self.reset_ball()

    def reset_ball(self):
        direction = random.choice([-1, 1])
        self.ball.reset(direction)

    def score_point(self, player_index):
        if player_index == 0:
            self.left_score += 1
            self.reset_ball(1)
        else:
            self.right_score += 1
            self.reset_ball(-1)

        if self.left_score >= WINNING_SCORE or self.right_score >= WINNING_SCORE:
            self.game_over = True

    def update(self, dt, keys):
        if self.game_over:
            return

        if self.mode == "single":
            if keys[pygame.K_w]:
                self.left_paddle.move(-1, dt)
            if keys[pygame.K_s]:
                self.left_paddle.move(1, dt)
            self.right_paddle.move_towards(self.ball.rect.centery, dt)
        else:
            if keys[pygame.K_w]:
                self.left_paddle.move(-1, dt)
            if keys[pygame.K_s]:
                self.left_paddle.move(1, dt)
            if keys[pygame.K_UP]:
                self.right_paddle.move(-1, dt)
            if keys[pygame.K_DOWN]:
                self.right_paddle.move(1, dt)

        self.ball.update(dt, self.left_paddle, self.right_paddle)

        if self.ball.rect.left <= 0:
            self.score_point(1)
        elif self.ball.rect.right >= WIDTH:
            self.score_point(0)

    def draw(self, surface):
        surface.fill((10, 10, 20))

        for y in range(0, HEIGHT, 20):
            pygame.draw.rect(surface, (255, 255, 255, 90), pygame.Rect(WIDTH // 2 - 2, y, 4, 12))

        self.left_paddle.draw(surface)
        self.right_paddle.draw(surface)
        self.ball.draw(surface)

        font = pygame.font.SysFont("arial", 48, bold=True)
        left_text = font.render(str(self.left_score), True, (255, 255, 255))
        right_text = font.render(str(self.right_score), True, (255, 255, 255))
        surface.blit(left_text, (WIDTH // 2 - 80, 24))
        surface.blit(right_text, (WIDTH // 2 + 40, 24))

        if self.game_over:
            winner_text = "Player 1 Wins" if self.left_score >= WINNING_SCORE else "Player 2 Wins"
            if self.mode == "single":
                winner_text = "You Win" if self.left_score >= WINNING_SCORE else "CPU Wins"
            message = font.render(winner_text, True, (255, 255, 255))
            surface.blit(message, (WIDTH // 2 - message.get_width() // 2, HEIGHT // 2 - 40))


class GameView:
    def __init__(self, surface):
        self.surface = surface

    def draw_menu(self):
        self.surface.fill((10, 10, 20))
        font = pygame.font.SysFont("arial", 64, bold=True)
        title = font.render("PONG", True, (255, 255, 255))
        self.surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        small_font = pygame.font.SysFont("arial", 28)
        options = small_font.render("Press 1 for 1 Player  |  Press 2 for 2 Players", True, (220, 220, 220))
        self.surface.blit(options, (WIDTH // 2 - options.get_width() // 2, 240))

        help_text = small_font.render("Player 1: W / S   |   Player 2: Arrow Keys", True, (180, 180, 180))
        self.surface.blit(help_text, (WIDTH // 2 - help_text.get_width() // 2, 290))

    def draw(self, model):
        if model is None:
            self.draw_menu()
        else:
            model.draw(self.surface)


class GameController:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pong")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.view = GameView(self.screen)
        self.model = None
        self.mode = None
        self.running = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.model is None:
                    if event.key == pygame.K_1:
                        self.mode = "single"
                        self.model = GameModel(self.mode)
                    elif event.key == pygame.K_2:
                        self.mode = "two-player"
                        self.model = GameModel(self.mode)
                elif self.model.game_over and event.key == pygame.K_r:
                    self.model = GameModel(self.mode)

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            keys = pygame.key.get_pressed()

            self.handle_events()

            if self.model is not None:
                self.model.update(dt, keys)

            self.view.draw(self.model)
            pygame.display.flip()

        pygame.quit()


def main():
    game = GameController()
    game.run()


if __name__ == "__main__":
    main()
