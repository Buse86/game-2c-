"""
Обработчик ввода — реагирует на события мыши и клавиатуры.
Распределяет события между меню и игровым процессом.
Не содержит игровой логики — только передаёт действия в GameManager.
"""

import pygame
import os
from src import config as cfg
from src.game_manager import GameManager


class InputHandler:
    """Принимает события pygame и вызывает соответствующие действия."""

    def __init__(self, app):
        """
        Аргументы:
            app — ссылка на главный объект GameApp
                  (нужна для доступа к состоянию приложения и менеджеру)
        """
        self.app = app

    def process_events(self):
        """Обрабатывает все события pygame, накопившиеся за текущий кадр.
        pygame.event.get() возвращает список всех событий с прошлого вызова."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Крестик окна — выходим из приложения
                self.app.running = False

            elif event.type == pygame.VIDEORESIZE:
                # Пользователь изменил размер окна
                self.app.resize_window(event.w, event.h)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Нажатие кнопки мыши
                self._handle_mouse(event)

            elif event.type == pygame.KEYDOWN:
                # Нажатие клавиши на клавиатуре
                self._handle_key(event)

    def _handle_mouse(self, event):
        """Распределяет клики мыши: меню или игровое поле.

        event.button:
            1 = ЛКМ (левая кнопка мыши)
            3 = ПКМ (правая кнопка мыши)
        """
        pos = pygame.mouse.get_pos()  # текущая позиция курсора

        if self.app.in_menu:
            # В меню обрабатываем только ЛКМ
            if event.button == 1:
                self._handle_menu_click(pos)
        else:
            # В игре — и ЛКМ, и ПКМ
            self._handle_game_click(event, pos)

    def _handle_menu_click(self, pos):
        """Обрабатывает клик в главном меню."""

        if self.app.btn_new.collidepoint(pos):
            # Нажали «Новая игра»
            # Удаляем старое сохранение, если есть
            if os.path.exists("td_seed_save.json"):
                os.remove("td_seed_save.json")
            # Создаём новый GameManager без загрузки
            self.app.manager = GameManager(load_save=False)
            self.app.manager.enemies_to_spawn = cfg.BASE_ENEMIES_PER_WAVE
            self.app.in_menu = False  # переходим в игру

        elif self.app.btn_cont.collidepoint(pos) and os.path.exists("td_seed_save.json"):
            # Нажали «Продолжить» (только если файл сохранения существует)
            self.app.manager = GameManager(load_save=True)
            self.app.manager.enemies_to_spawn = cfg.BASE_ENEMIES_PER_WAVE
            self.app.in_menu = False

    def _handle_game_click(self, event, pos):
        """Обрабатывает клики во время активной игры."""

        if self.app.btn_to_menu.collidepoint(pos) and event.button == 1:
            # Кнопка «В меню» — сохраняем прогресс и возвращаемся
            self.app.manager.save()
            self.app.in_menu = True

        elif pos[1] < cfg.rows * cfg.GRID_SIZE and not self.app.manager.game_over:
            # Клик по игровому полю (выше HUD-панели)
            if event.button == 1:
                # ЛКМ — поставить башню
                self.app.manager.handle_click(pos)
            elif event.button == 3:
                # ПКМ — продать башню
                self.app.manager.handle_right_click(pos)

        elif self.app.manager.game_over and event.button == 1:
            # После проигрыша любой клик возвращает в меню
            self.app.in_menu = True

    def _handle_key(self, event):
        """Обрабатывает нажатия клавиш.
        Клавиши 1 и 2 — переключение типа башни для постройки."""
        # В меню и при game over клавиатура не работает
        if self.app.in_menu or self.app.manager.game_over:
            return

        if event.key == pygame.K_1:
            self.app.manager.selected_type = "LMG"      # клавиша 1 = пулемёт
        elif event.key == pygame.K_2:
            self.app.manager.selected_type = "SNIPER"    # клавиша 2 = снайпер
