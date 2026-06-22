"""
Главный класс приложения — создание окна, игровой цикл, музыка.
Использует паттерн «фиксированный шаг физики» (fixed timestep):
логика обновляется 60 раз в секунду, а отрисовка — до 120 FPS.
"""

import pygame
import os
from src import config as cfg
from src.ui.renderer import GameRenderer
from src.ui.input_handler import InputHandler


class GameApp:
    """Главный класс приложения.

    Управляет окном pygame, игровым циклом и переключением
    между меню и игровым процессом.
    """

    def __init__(self):
        # Инициализация pygame и аудио
        pygame.init()
        pygame.mixer.init()

        # Вычисляем сколько клеток помещается в окно
        # (вычитаем высоту HUD-панели снизу)
        cfg.cols = cfg.WIDTH // cfg.GRID_SIZE
        cfg.rows = (cfg.HEIGHT - cfg.HUD_HEIGHT) // cfg.GRID_SIZE

        # Создаём окно с поддержкой изменения размера
        self.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("SOLID Dynamic Tower Defense")

        # Создаём подсистемы отрисовки и ввода
        self.renderer = GameRenderer()       # отвечает за всю отрисовку
        self.input_handler = InputHandler(self)  # обрабатывает мышь и клавиатуру

        # Состояние приложения
        self.manager = None     # GameManager создаётся при старте игры из меню
        self.in_menu = True     # True = показываем меню, False = идёт игра
        self.running = True     # False = выходим из приложения

        self._init_music()
        self._update_buttons()

    def _init_music(self):
        """Загружает и запускает фоновую музыку.
        Файл ищется в папке assets/ рядом с src/.
        Если файла нет — игра работает без музыки."""
        music_path = os.path.join(os.path.dirname(__file__), "..", "assets", "859078__josefpres__piano-loops-210-efect-4-octave-long-loop-120-bpm.wav")
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(cfg.MUSIC_VOLUME)
            pygame.mixer.music.play(-1)  # -1 означает бесконечный повтор

    def _update_buttons(self):
        """Пересчитывает позиции кнопок меню под текущий размер окна.
        Вызывается при запуске и при ресайзе."""
        w, h = self.screen.get_size()
        # Кнопки по центру окна
        self.btn_new = pygame.Rect(w // 2 - 150, 260, 300, 50)
        self.btn_cont = pygame.Rect(w // 2 - 150, 340, 300, 50)
        # Кнопка «В меню» в правом нижнем углу (внутри HUD-панели)
        self.btn_to_menu = pygame.Rect(w - 180, h - 65, 150, 40)

    def resize_window(self, w, h):
        """Обрабатывает событие изменения размера окна.
        Пересчитывает сетку, кнопки и перестраивает карту."""
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        # Минимум 5 клеток по каждой оси, чтобы игра не сломалась
        cfg.cols = max(5, w // cfg.GRID_SIZE)
        cfg.rows = max(5, (h - cfg.HUD_HEIGHT) // cfg.GRID_SIZE)
        self._update_buttons()
        if self.manager:
            self.manager.handle_resize()

    def run(self):
        """Главный игровой цикл.

        Используется паттерн «fixed timestep» (фиксированный шаг):
        - Рендеринг работает с переменным FPS (до 120)
        - Логика обновляется строго 60 раз в секунду (dt = 1/60)
        - accumulator копит реальное время между кадрами
        - Когда накоплено достаточно — делаем один шаг логики

        Это гарантирует одинаковое поведение игры на любом FPS.
        """
        clock = pygame.time.Clock()
        accumulator = 0.0           # накопитель реального времени
        dt_fixed = 1 / 60.0        # фиксированный шаг логики (60 Hz)

        while self.running:
            # clock.tick(120) возвращает время с прошлого кадра в миллисекундах
            # и ограничивает FPS до 120
            duration = clock.tick(120)
            accumulator += duration / 1000.0  # переводим мс → секунды

            # 1. Обработка ввода (мышь, клавиатура, ресайз)
            self.input_handler.process_events()

            # 2. Обновление игровой логики с фиксированным шагом
            if not self.in_menu and not self.manager.game_over:
                # Если накопилось несколько шагов — выполняем все
                while accumulator >= dt_fixed:
                    accumulator -= dt_fixed
                    self.manager.update(dt_fixed)
            else:
                # В меню или game over — логику не обновляем
                accumulator = 0

            # 3. Отрисовка текущего состояния
            w, h = self.screen.get_size()
            if self.in_menu:
                self.renderer.draw_menu(
                    self.screen, self.btn_new, self.btn_cont,
                    os.path.exists("td_seed_save.json")
                )
            else:
                self.renderer.draw_game(self.screen, self.manager, self.btn_to_menu, w, h)

            # Показываем нарисованный кадр на экране
            pygame.display.flip()

        # Корректно завершаем pygame при выходе
        pygame.quit()
