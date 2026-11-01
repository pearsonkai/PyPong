"""Pong game implementation using pygame-ce.

This file follows a simple Model-View-Controller (MVC) structure:
- Model: stores game state and rules
- View: draws the menu and game screen
- Controller: handles events and coordinates the game loop

This version includes:
- one-player and two-player modes
- survival-based high score tracking
- unlockable paddle skins
- persistent progress saved to disk
"""

import json
import math
import os
import random
import pygame


# --- Screen dimensions ---
WIDTH, HEIGHT = 960, 540

# --- Paddle and ball dimensions ---
PADDLE_WIDTH, PADDLE_HEIGHT = 18, 120
BALL_SIZE = 14

# --- Movement settings ---
PADDLE_SPEED = 500
BALL_SPEED = 430

# --- Match settings ---
WINNING_SCORE = 7

# --- Paddle skin definitions ---
# Each skin unlocks once the player's best survival time reaches the listed
# number of seconds in single-player mode.
PADDLE_SKINS = [
    {"name": "Classic White", "color": (255, 255, 255), "unlock_seconds": 0},
    {"name": "Sky Blue", "color": (100, 180, 255), "unlock_seconds": 15},
    {"name": "Coral Red", "color": (255, 120, 120), "unlock_seconds": 30},
    {"name": "Lime Green", "color": (120, 255, 120), "unlock_seconds": 60},
    {"name": "Gold", "color": (255, 214, 80), "unlock_seconds": 90},
]


class HighScoreStore:
    """Persist survival progress and unlocked skin choices."""

    def __init__(self, file_path="paddle_progress.json"):
        self.file_path = file_path
        self.best_seconds = 0.0
        self.selected_skin = "Classic White"
        self.unlocked_skins = {"Classic White"}
        self.load()

    def load(self):
        """Load saved progress from disk if available."""
        if not os.path.exists(self.file_path):
            self._refresh_unlocks()
            self.save()
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            self.best_seconds = float(data.get("best_seconds", 0.0))
            self.selected_skin = data.get("selected_skin", "Classic White")
            self.unlocked_skins = set(data.get("unlocked_skins", ["Classic White"]))
        except (json.JSONDecodeError, TypeError, ValueError):
            self.best_seconds = 0.0
            self.selected_skin = "Classic White"
            self.unlocked_skins = {"Classic White"}

        self._refresh_unlocks()

        if self.selected_skin not in self.unlocked_skins:
            self.selected_skin = "Classic White"

        self.save()

    def save(self):
        """Write current progress to the JSON file."""
        payload = {
            "best_seconds": round(self.best_seconds, 2),
            "selected_skin": self.selected_skin,
            "unlocked_skins": sorted(self.unlocked_skins),
        }

        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

    def _refresh_unlocks(self):
        """Unlock all skins whose challenge threshold has been met."""
        for skin in PADDLE_SKINS:
            if self.best_seconds >= skin["unlock_seconds"]:
                self.unlocked_skins.add(skin["name"])

    def record_survival_seconds(self, seconds):
        """Update the best survival time if the new value is better."""
        if seconds <= 0:
            return

        self.best_seconds = max(self.best_seconds, seconds)
        self._refresh_unlocks()
        self.save()

    def get_skin_by_name(self, name):
        """Return the skin dictionary for a given name."""
        for skin in PADDLE_SKINS:
            if skin["name"] == name:
                return skin
        return PADDLE_SKINS[0]

    def get_unlocked_skins(self):
        """Return a list of unlocked skins in the design order."""
        return [skin for skin in PADDLE_SKINS if skin["name"] in self.unlocked_skins]

    def set_selected_skin(self, skin_name):
        """Only allow selection of currently unlocked skins."""
        if skin_name in self.unlocked_skins:
            self.selected_skin = skin_name
            self.save()


class Paddle:
    """Represents one paddle on the screen."""

    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.color = color
        self.speed = PADDLE_SPEED

    def move(self, direction, dt):
        """Move vertically by direction * speed * dt."""
        self.rect.y += direction * self.speed * dt
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y))

    def move_towards(self, target_y, dt):
        """Used for the CPU paddle: chase a target vertical position."""
        if self.rect.centery < target_y:
            self.move(1, dt)
        elif self.rect.centery > target_y:
            self.move(-1, dt)

    def draw(self, surface):
        """Render the paddle on a surface."""
        pygame.draw.rect(surface, self.color, self.rect)


class Ball:
    """Represents the ping-pong ball."""

    def __init__(self):
        self.rect = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.velocity = pygame.Vector2()

    def reset(self, direction):
        """Center the ball and send it in the chosen direction."""
        self.rect.center = (WIDTH // 2, HEIGHT // 2)

        angle = random.uniform(-0.85, 0.85)
        x_speed = direction * BALL_SPEED * math.cos(angle)
        y_speed = BALL_SPEED * math.sin(angle)
        self.velocity = pygame.Vector2(x_speed, y_speed)

    def update(self, dt, left_paddle, right_paddle):
        """Advance the ball and handle wall/paddle collisions."""
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
                if self.velocity.x > 0:
                    self.rect.x = min(self.rect.x, paddle.rect.x - self.rect.width)
                else:
                    self.rect.x = max(self.rect.x, paddle.rect.right)

                self.velocity.x *= -1.05

                offset = (self.rect.centery - paddle.rect.centery) / (paddle.rect.height / 2)
                self.velocity.y = offset * 260

                current_speed = self.velocity.length()
                if current_speed < 430:
                    self.velocity.scale_to_length(430)
                if current_speed > 940:
                    self.velocity.scale_to_length(940)

    def draw(self, surface):
        """Draw the ball to the passed surface."""
        pygame.draw.ellipse(surface, (255, 255, 255), self.rect)


class GameModel:
    """Contains the game state and rules."""

    def __init__(self, mode, selected_skin_name="Classic White", high_score_store=None):
        self.mode = mode
        self.high_score_store = high_score_store
        self.survival_time = 0.0

        if high_score_store is not None:
            selected_color = high_score_store.get_skin_by_name(selected_skin_name)["color"]
        else:
            selected_color = PADDLE_SKINS[0]["color"]

        self.left_paddle = Paddle(40, HEIGHT // 2 - PADDLE_HEIGHT // 2, selected_color)
        self.right_paddle = Paddle(WIDTH - 40 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, (255, 255, 255))
        self.ball = Ball()
        self.left_score = 0
        self.right_score = 0
        self.game_over = False
        self.reset_ball()

    def reset_ball(self):
        """Serve the ball in a random direction."""
        direction = random.choice([-1, 1])
        self.ball.reset(direction)

    def finalize_survival(self):
        """Record the current survival time once the player has either lost or won."""
        if self.mode == "single" and self.high_score_store is not None and self.survival_time > 0:
            self.high_score_store.record_survival_seconds(self.survival_time)
            self.survival_time = 0.0

    def score_point(self, player_index):
        """Award a point and reset after a goal is scored."""
        if self.mode == "single" and player_index == 1:
            self.finalize_survival()

        if player_index == 0:
            self.left_score += 1
            self.reset_ball(1)
        else:
            self.right_score += 1
            self.reset_ball(-1)

        if self.left_score >= WINNING_SCORE or self.right_score >= WINNING_SCORE:
            self.game_over = True
            if self.mode == "single":
                self.finalize_survival()

    def update(self, dt, keys):
        """Advance the game simulation by one frame."""
        if self.game_over:
            return

        if self.mode == "single":
            self.survival_time += dt

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
        """Render the current game state."""
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

        if self.mode == "single":
            survival_font = pygame.font.SysFont("arial", 20)
            survival_text = survival_font.render(f"Survival: {self.survival_time:.1f}s", True, (200, 220, 255))
            surface.blit(survival_text, (24, 16))

        if self.game_over:
            winner_text = "Player 1 Wins" if self.left_score >= WINNING_SCORE else "Player 2 Wins"
            if self.mode == "single":
                winner_text = "You Win" if self.left_score >= WINNING_SCORE else "CPU Wins"

            message = font.render(winner_text, True, (255, 255, 255))
            surface.blit(message, (WIDTH // 2 - message.get_width() // 2, HEIGHT // 2 - 40))


class GameView:
    """Draws the menu and the active game scene."""

    def __init__(self, surface):
        self.surface = surface

    def draw_menu(self, selected_skin_name, high_score_store):
        """Show the main menu with score and skin selection."""
        self.surface.fill((10, 10, 20))

        font = pygame.font.SysFont("arial", 64, bold=True)
        title = font.render("PONG", True, (255, 255, 255))
        self.surface.blit(title, (WIDTH // 2 - title.get_width() // 2, 120))

        small_font = pygame.font.SysFont("arial", 28)
        best_label = small_font.render(f"Best survival: {high_score_store.best_seconds:.1f}s", True, (200, 220, 255))
        self.surface.blit(best_label, (WIDTH // 2 - best_label.get_width() // 2, 200))

        current_skin = high_score_store.get_skin_by_name(selected_skin_name)
        selection_text = small_font.render(f"Selected skin: {selected_skin_name}", True, current_skin["color"])
        self.surface.blit(selection_text, (WIDTH // 2 - selection_text.get_width() // 2, 240))

        directions = small_font.render("Left/Right = change skin  |  1 = 1 Player  |  2 = 2 Players", True, (220, 220, 220))
        self.surface.blit(directions, (WIDTH // 2 - directions.get_width() // 2, 290))

        skin_font = pygame.font.SysFont("arial", 22)
        y = 340
        for skin in PADDLE_SKINS:
            unlocked = skin["name"] in high_score_store.unlocked_skins
            label = f"{skin['name']} - {skin['unlock_seconds']}s" if not unlocked else skin["name"]
            text_color = skin["color"] if unlocked else (100, 100, 100)
            text = skin_font.render(label, True, text_color)

            if skin["name"] == selected_skin_name:
                highlight = pygame.Rect(WIDTH // 2 - 180, y - 4, 360, 28)
                pygame.draw.rect(self.surface, (60, 60, 80), highlight)

            self.surface.blit(text, (WIDTH // 2 - text.get_width() // 2, y))
            y += 32

    def draw(self, model, selected_skin_name, high_score_store):
        """Draw either the menu or the match scene."""
        if model is None:
            self.draw_menu(selected_skin_name, high_score_store)
        else:
            model.draw(self.surface)


class GameController:
    """Coordinates the window, events, and model/view interaction."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Pong")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.view = GameView(self.screen)
        self.model = None
        self.mode = None
        self.running = True
        self.high_score_store = HighScoreStore()
        self.selected_skin_name = self.high_score_store.selected_skin

    def get_unlocked_skin_names(self):
        """Return the unlocked skins in display order."""
        return [skin["name"] for skin in PADDLE_SKINS if skin["name"] in self.high_score_store.unlocked_skins]

    def cycle_skin(self, direction):
        """Move through unlocked skins with left/right arrow keys."""
        unlocked = self.get_unlocked_skin_names()
        if not unlocked:
            return

        current_index = unlocked.index(self.selected_skin_name)
        new_index = (current_index + direction) % len(unlocked)
        self.selected_skin_name = unlocked[new_index]
        self.high_score_store.set_selected_skin(self.selected_skin_name)

    def handle_events(self):
        """Process keyboard and window events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.model is None:
                    if event.key == pygame.K_LEFT:
                        self.cycle_skin(-1)
                    elif event.key == pygame.K_RIGHT:
                        self.cycle_skin(1)
                    elif event.key == pygame.K_1:
                        self.mode = "single"
                        self.model = GameModel(self.mode, self.selected_skin_name, self.high_score_store)
                    elif event.key == pygame.K_2:
                        self.mode = "two-player"
                        self.model = GameModel(self.mode, self.selected_skin_name, self.high_score_store)
                elif self.model.game_over and event.key == pygame.K_r:
                    self.model = GameModel(self.mode, self.selected_skin_name, self.high_score_store)

    def run(self):
        """Main game loop: process input, update, render."""
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            keys = pygame.key.get_pressed()

            self.handle_events()

            if self.model is not None:
                self.model.update(dt, keys)

            self.view.draw(self.model, self.selected_skin_name, self.high_score_store)
            pygame.display.flip()

        pygame.quit()


def main():
    """Entry point for the application."""
    game = GameController()
    game.run()


if __name__ == "__main__":
    main()
