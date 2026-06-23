import pygame
import os
from src import config as cfg
from src.ui.renderer import GameRenderer
from src.ui.input_handler import InputHandler


class GameApp:

    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        cfg.cols = cfg.WIDTH // cfg.GRID_SIZE
        cfg.rows = (cfg.HEIGHT - cfg.HUD_HEIGHT) // cfg.GRID_SIZE

        self.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Tower Defense by Dembitsky")

        self.renderer = GameRenderer()
        self.input_handler = InputHandler(self)

        self.manager = None
        self.in_menu = True
        self.running = True

        self._init_music()
        self._update_buttons()

    def _init_music(self):
        music_path = os.path.join(os.path.dirname(__file__), "..", "assets", "859078__josefpres__piano-loops-210-efect-4-octave-long-loop-120-bpm.wav")
        if os.path.exists(music_path):
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(cfg.MUSIC_VOLUME)
            pygame.mixer.music.play(-1)

    def _update_buttons(self):
        w, h = self.screen.get_size()
        self.btn_new = pygame.Rect(w // 2 - 150, 260, 300, 50)
        self.btn_cont = pygame.Rect(w // 2 - 150, 340, 300, 50)
        self.btn_to_menu = pygame.Rect(w - 180, h - 65, 150, 40)

    def resize_window(self, w, h):
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        cfg.cols = max(5, w // cfg.GRID_SIZE)
        cfg.rows = max(5, (h - cfg.HUD_HEIGHT) // cfg.GRID_SIZE)
        self._update_buttons()
        if self.manager:
            self.manager.handle_resize()

    def run(self):
        """Игровой цикл с паттерном Fixed Timestep.

        Проблема: если обновлять логику один раз за кадр,
        на быстром ПК (200 FPS) игра ускорится, на слабом — замедлится.

        Решение — разделить рендер и логику:
        - Рендер работает с переменным FPS (до 120)
        - Логика обновляется строго 60 раз/сек (dt_fixed = 1/60)

        accumulator копит реальное время между кадрами.
        Когда накоплено >= dt_fixed — делаем один шаг логики
        и вычитаем dt_fixed. Если кадр был долгим (лаг) —
        цикл while сделает несколько шагов, «догоняя» реальное время.
        """
        clock = pygame.time.Clock()
        accumulator = 0.0
        dt_fixed = 1 / 60.0

        while self.running:
            duration = clock.tick(120)
            accumulator += duration / 1000.0

            self.input_handler.process_events()

            if not self.in_menu and not self.manager.game_over:
                while accumulator >= dt_fixed:
                    accumulator -= dt_fixed
                    self.manager.update(dt_fixed)
            else:
                accumulator = 0

            w, h = self.screen.get_size()
            if self.in_menu:
                self.renderer.draw_menu(
                    self.screen, self.btn_new, self.btn_cont,
                    os.path.exists("td_seed_save.json")
                )
            else:
                self.renderer.draw_game(self.screen, self.manager, self.btn_to_menu, w, h)

            pygame.display.flip()

        pygame.quit()
