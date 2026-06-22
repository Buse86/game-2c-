import sys

try:
    import pygame
except ImportError:
    print("=" * 60)
    print("ОШИБКА: Библиотека Pygame не найдена!")
    print("Установите: pip install pygame")
    print("=" * 60)
    sys.exit(1)

from src.game import GameApp

if __name__ == "__main__":
    app = GameApp()
    app.run()