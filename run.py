import sys

try:
    import pygame
except ImportError:
    print("=" * 60)
    print("ОШИБКА: Библиотека Pygame не найдена!")
    print("Пожалуйста, установите её перед запуском: pip install pygame")
    print("=" * 60)
    sys.exit(1)

# Теперь импортируем из пакета src
from src.game import GameApp

if __name__ == "__main__":
    app = GameApp()
    app.run()