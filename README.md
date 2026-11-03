# PyPong

A simple 2D Pong game built with Python and `pygame-ce`.

## Disclaimer
All code in this repository was made with generative AI for a lab in Dalhousie University's Software Development course CSCI2134.

## Features
- One-player mode vs CPU
- Local two-player mode on one keyboard
- Score tracking and win condition
- Single-player survival high score based on seconds without conceding a point
- Unlockable paddle skins based on survival performance
- Paddle color selection from the main menu

## Installation

```bash
pip install -r requirements.txt
```

## Run

```bash
python pong_game.py
```

## Controls
- Main menu: `Left` / `Right` to change paddle color
- Start single-player: `1`
- Start two-player: `2`
- Single-player: `W` / `S` to move, CPU controls right paddle
- Two-player: `W` / `S` for left player, `Up` / `Down` for right player
- Restart match: `R`
- Quit: `Esc`

## Skin unlocks
Unlocked paddle colors are tied to survival time in one-player mode:
- Classic White: unlocked by default
- Sky Blue: 15 seconds
- Coral Red: 30 seconds
- Lime Green: 60 seconds
- Gold: 90 seconds

The chosen color is saved automatically in `paddle_progress.json`.
