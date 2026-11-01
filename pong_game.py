"""Pong game implementation using pygame-ce.

This file follows a simple Model-View-Controller (MVC) structure:
- Model: stores game state and rules
- View: draws the menu and game screen
- Controller: handles events and coordinates the game loop

A junior developer can read this file top-to-bottom to understand how a basic
2D game is structured in Python.
"""

import math
import random
import pygame


# --- Screen dimensions ---
# These values define the playable area of the game window.
WIDTH, HEIGHT = 960, 540

# --- Paddle and ball dimensions ---
PADDLE_WIDTH, PADDLE_HEIGHT = 18, 120
BALL_SIZE = 14

# --- Movement settings ---
# These speeds are in pixels per second.
PADDLE_SPEED = 500
BALL_SPEED = 430

# --- Match settings ---
WINNING_SCORE = 7


class Paddle:
    """Represents one of the two paddles in the game.

    The paddle has a rectangle position, a color, and a movement speed.
    It can move up/down or track a target Y position.
    """

    def __init__(self, x, y, color):
        # pygame.Rect stores the paddle position and size.
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = color
        self.speed = PADDLE_SPEED

    def move(self, direction, dt):
        """Move the paddle vertically.

        direction is either -1 (up) or 1 (down), and dt is the time step.
        """
        self.rect.y += direction * self.speed * dt

        # Keep the paddle on screen by clamping its position.
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y))

    def move_towards(self, target_y, dt):
        """Smoothly move the CPU paddle toward the ball.

        This is used for the single-player mode so the right paddle behaves like
        a simple computer opponent.
        """
        if self.rect.centery < target_y:
            self.move(1, dt)
        elif self.rect.centery > target_y:
            self.move(-1, dt)

    def draw(self, surface):
        """Draw the paddle on a given pygame surface."""
        pygame.draw.rect(surface, self.color, self.rect)


class Ball:
    """Represents the ball that bounces around the court."""

    def __init__(self):
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.velocity = pygame.Vector2()

    def reset(self, direction):
        """Place the ball in the center and launch it left or right.

        direction is either -1 or 1. It tells the ball which direction to move
        after the reset.
        """
        self.rect.center = (WIDTH // 2, HEIGHT // 2)

        # Random angle gives the serve a bit of variety.
        angle = random.uniform(-0.85, 0.85)
        x_speed = direction * BALL_SPEED * math.cos(angle)
        y_speed = BALL_SPEED * math.sin(angle)
        self.velocity = pygame.Vector2(x_speed, y_speed)

    def update(self, dt, left_paddle, right_paddle):
        """Update ball movement and handle collisions with walls/paddles."""
        # Move the ball by a small amount each frame.
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt

        # Top wall collision.
        if self.rect.top <= 0:
            self.rect.top = 0
            self.velocity.y *= -1
        # Bottom wall collision.
        elif self.rect.bottom >= HEIGHT:
            self.rect.bottom = HEIGHT
            self.velocity.y *= -1

        # Paddle collisions.
        for paddle in (left_paddle, right_paddle):
            if self.rect.colliderect(paddle.rect):
                # Ensure the ball does not stick inside the paddle after impact.
                if self.velocity.x > 0:
                    self.rect.x = min(self.rect.x, paddle.rect.x - self.rect.width)
                else:
                    self.rect.x = max(self.rect.x, paddle.rect.right)

                # Reverse horizontal direction and add some vertical control.
                self.velocity.x *= -1.05

                offset = (self.rect.centery - paddle.rect.centery) / (paddle.rect.height / 2)
                self.velocity.y = offset * 260

                # Keep the ball speed in a reasonable range.
                current_speed = self.velocity.length()
                if current_speed < 430:
                    self.velocity.scale_to_length(430)
                if current_speed > 940:
                    self.velocity.scale_to_length(940)

    def draw(self, surface):
        """Draw the ball on the screen."""
        pygame.draw.ellipse(surface, (255, 255, 255), self.rect)


class GameModel:
    """Stores the game state and rules for the match.

    The model is responsible for the current world state: paddles, ball, and
    score. It does not know anything about drawing or input handling.
    """

    def __init__(self, mode):
        self.mode = mode

        # Left paddle is always controlled by the player on the left side.
        self.left_paddle = Paddle(40, HEIGHT // 2 - PADDLE_HEIGHT // 2, (255, 255, 255))

        # Right paddle is controlled by either the second local player or the CPU.
        self.right_paddle = Paddle(WIDTH - 40 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, (255, 255, 255))

        self.ball = Ball()
        self.left_score = 0
        self.right_score = 0
        self.game_over = False

        # Start the match with a random serve direction.
        self.reset_ball()

    def reset_ball(self):
        """Serve the ball in a random direction."""
        direction = random.choice([-1, 1])
        self.ball.reset(direction)

    def score_point(self, player_index):
        """Award a point to the given player and reset the ball."""
        if player_index == 0:
            self.left_score += 1
            self.reset_ball(1)
        else:
            self.right_score += 1
            self.reset_ball(-1)

        if self.left_score >= WINNING_SCORE or self.right_score >= WINNING_SCORE:
            self.game_over = True

    def update(self, dt, keys):
        """Advance the game by one frame.

        dt: time elapsed since the last frame, in seconds.
        keys: current keyboard state from pygame.key.get_pressed().
        """
        if self.game_over:
            return

        # Handle paddle controls.
        if self.mode == "single":
            # Player 1 controls the left paddle.
            if keys[pygame.K_w]:
                self.left_paddle.move(-1, dt)
            if keys[pygame.K_s]:
                self.left_paddle.move(1, dt)

            # Simple CPU opponent tracks the ball's vertical position.
            self.right_paddle.move_towards(self.ball.rect.centery, dt)
        else:
            # Two-player mode: both paddles are controlled by players.
            if keys[pygame.K_w]:
                self.left_paddle.move(-1, dt)
            if keys[pygame.K_s]:
                self.left_paddle.move(1, dt)
            if keys[pygame.K_UP]:
                self.right_paddle.move(-1, dt)
            if keys[pygame.K_DOWN]:
                self.right_paddle.move(1, dt)

        # Update the ball and check for collisions.
        self.ball.update(dt, self.left_paddle, self.right_paddle)

        # If the ball crosses either side, a point is scored.
        if self.ball.rect.left <= 0:
            self.score_point(1)
        elif self.ball.rect.right >= WIDTH:
            self.score_point(0)

    def draw(self, surface):
        """Render the game scene to the screen."""
        # Fill the screen with a dark background color.
        surface.fill((10, 10, 20))

        # Draw the center line to visually separate the halves.
        for y in range(0, HEIGHT, 20):
            pygame.draw.rect(surface, (255, 255, 255, 90), pygame.Rect(WIDTH // 2 - 2, y, 4, 12))

        # Draw paddles and the ball.
        self.left_paddle.draw(surface)
        self.right_paddle.draw(surface)
        self.ball.draw(surface)

        # Score display.
        font = pygame.font.SysFont("arial", 48, bold=True)
        left_text = font.render(str(self.left_score), True, (255, 255, 255))
        right_text = font.render(str(self.right_score), True, (255, 255, 255))
        surface.blit(left_text, (WIDTH // 2 - 80, 24))
        surface.blit(right_text, (WIDTH // 2 + 40, 24))

        # If a player has reached the winning score, display a winner message.
        if self.game_over:
            winner_text = "Player 1 Wins" if self.left_score >= WINNING_SCORE else "Player 2 Wins"
            if self.mode == "single":
                winner_text = "You Win" if self.left_score >= WINNING_SCORE else "CPU Wins"

            message = font.render(winner_text, True, (255, 255, 255))
            surface.blit(message, (WIDTH // 2 - message.get_width() // 2, HEIGHT // 2 - 40))


class GameView:
    """Responsible for drawing the menu and the active game screen."""

    def __init__(self, surface):
        self.surface = surface

    def draw_menu(self):
        """Draw the start menu so the user can choose a game mode."""
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
        """Render either the menu or the actual game based on the model state."""
        if model is None:
            self.draw_menu()
        else:
            model.draw(self.surface)


class GameController:
    """Handles input events and runs the main game loop.

    This class connects the model and view together. It decides when the game
    should update and when the view should redraw the screen.
    """

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
        """Process all user input and window events for this frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.model is None:
                    # When no match is active, allow the user to choose a game mode.
                    if event.key == pygame.K_1:
                        self.mode = "single"
                        self.model = GameModel(self.mode)
                    elif event.key == pygame.K_2:
                        self.mode = "two-player"
                        self.model = GameModel(self.mode)
                elif self.model.game_over and event.key == pygame.K_r:
                    # Restart the match with the same selected mode.
                    self.model = GameModel(self.mode)

    def run(self):
        """Main game loop: process input, update physics, draw the screen."""
        while self.running:
            # dt is the time difference in seconds between frames.
            dt = self.clock.tick(60) / 1000.0
            keys = pygame.key.get_pressed()

            self.handle_events()

            if self.model is not None:
                self.model.update(dt, keys)

            self.view.draw(self.model)
            pygame.display.flip()

        pygame.quit()


def main():
    """Entry point for the application."""
    game = GameController()
    game.run()


if __name__ == "__main__":
    main()

