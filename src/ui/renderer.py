"""
Модуль отрисовки — рисует все визуальные элементы игры.
Не содержит логики — только визуализация состояния из GameManager.
Разделён на приватные методы по зонам: сетка, путь, враги, HUD и т.д.
"""

import pygame
from .. import config as cfg


class GameRenderer:
    """Отвечает за отрисовку всех элементов: карта, враги, башни, интерфейс."""

    def __init__(self):
        # Три шрифта для разных элементов интерфейса
        self.font = pygame.font.SysFont('Arial', 20)            # обычный текст
        self.font_bold = pygame.font.SysFont('Arial', 22, bold=True)  # значения (жирный)
        self.big_font = pygame.font.SysFont('Arial', 48, bold=True)   # заголовок GAME OVER

    # ============================
    # Меню
    # ============================

    def draw_menu(self, screen, btn_new, btn_cont, save_exists):
        """Рисует главное меню с двумя кнопками."""
        screen.fill((20, 20, 20))  # тёмный фон

        # Кнопка «Новая игра» — всегда синяя
        pygame.draw.rect(screen, cfg.BLUE, btn_new, border_radius=4)

        # Кнопка «Продолжить» — зелёная если есть сохранение, серая если нет
        cont_color = cfg.GREEN if save_exists else (70, 70, 70)
        pygame.draw.rect(screen, cont_color, btn_cont, border_radius=4)

        # Текст на кнопках
        screen.blit(self.font.render("Новая игра", True, cfg.WHITE),
                     (btn_new.x + 85, btn_new.y + 12))
        screen.blit(self.font.render("Продолжить", True, cfg.WHITE),
                     (btn_cont.x + 85, btn_cont.y + 12))

    # ============================
    # Игровой экран
    # ============================

    def draw_game(self, screen, manager, btn_to_menu, width, height):
        """Рисует все элементы игрового экрана в правильном порядке.
        Порядок важен: то, что рисуется позже, перекрывает предыдущее."""
        screen.fill(cfg.SAND)                              # 1. Песочный фон
        self._draw_grid(screen, manager)                   # 2. Сетка + стены
        self._draw_path(screen, manager)                   # 3. Путь врагов
        self._draw_base_hp(screen, manager)                # 4. HP-бар базы
        self._draw_towers(screen, manager)                 # 5. Башни
        self._draw_enemies(screen, manager)                # 6. Враги
        self._draw_projectiles(screen, manager)            # 7. Снаряды
        self._draw_hud(screen, manager, btn_to_menu, width, height)  # 8. Панель
        self._draw_upgrade_text(screen, manager, width)    # 9. Уведомление
        if manager.game_over:
            self._draw_game_over(screen, width, height)    # 10. Экран поражения

    def _draw_grid(self, screen, manager):
        """Рисует сетку клеток. Препятствия (стены каньона) — коричневые."""
        for cx in range(cfg.cols):
            for cy in range(cfg.rows):
                rect = (cx * cfg.GRID_SIZE, cy * cfg.GRID_SIZE,
                        cfg.GRID_SIZE, cfg.GRID_SIZE)
                # Тонкая граница клетки
                pygame.draw.rect(screen, (225, 215, 160), rect, 1)
                # Если клетка — препятствие, закрашиваем коричневым
                if (cx, cy) in manager.obstacles:
                    pygame.draw.rect(screen, cfg.BROWN, rect)

    def _draw_path(self, screen, manager):
        """Рисует путь врагов светло-зелёным, точку входа и базу."""
        # Путь — светло-зелёные клетки
        for node in manager.path:
            rect = (node[0] * cfg.GRID_SIZE, node[1] * cfg.GRID_SIZE,
                    cfg.GRID_SIZE, cfg.GRID_SIZE)
            pygame.draw.rect(screen, (215, 240, 215), rect)

        # Точка входа врагов — ярко-зелёная
        start = (manager.start_node[0] * cfg.GRID_SIZE,
                 manager.start_node[1] * cfg.GRID_SIZE,
                 cfg.GRID_SIZE, cfg.GRID_SIZE)
        # База (цель врагов) — синяя
        end = (manager.end_node[0] * cfg.GRID_SIZE,
               manager.end_node[1] * cfg.GRID_SIZE,
               cfg.GRID_SIZE, cfg.GRID_SIZE)
        pygame.draw.rect(screen, cfg.GREEN, start)
        pygame.draw.rect(screen, cfg.BLUE, end)

    def _draw_base_hp(self, screen, manager):
        """Рисует полоску здоровья базы над клеткой базы.
        Красная полоса = максимум, зелёная часть = текущее HP."""
        if manager.game_over:
            return
        bx = manager.end_node[0] * cfg.GRID_SIZE
        by = manager.end_node[1] * cfg.GRID_SIZE
        hp_ratio = manager.base_hp / manager.max_base_hp
        # Фон полоски (красный = потерянное HP)
        pygame.draw.rect(screen, cfg.RED, (bx, by - 12, cfg.GRID_SIZE, 5))
        # Текущее HP (зелёная часть, ширина пропорциональна HP)
        pygame.draw.rect(screen, cfg.GREEN, (bx, by - 12, cfg.GRID_SIZE * hp_ratio, 5))

    def _draw_towers(self, screen, manager):
        """Рисует каждую башню цветным квадратом (цвет зависит от типа).
        Квадрат чуть меньше клетки (отступ 4px) для визуального разделения."""
        for tower in manager.towers:
            rect = (tower.gx * cfg.GRID_SIZE + 4, tower.gy * cfg.GRID_SIZE + 4,
                    cfg.GRID_SIZE - 8, cfg.GRID_SIZE - 8)
            pygame.draw.rect(screen, tower.color, rect)

    def _draw_enemies(self, screen, manager):
        """Рисует врагов красными кругами с полоской здоровья сверху."""
        for enemy in manager.enemies:
            # Тело врага — красный круг
            pygame.draw.circle(screen, cfg.RED, (int(enemy.x), int(enemy.y)), 12)
            # Полоска HP: красный фон + зелёная часть
            hp_ratio = enemy.hp / enemy.max_hp
            pygame.draw.rect(screen, cfg.RED, (enemy.x - 15, enemy.y - 20, 30, 4))
            pygame.draw.rect(screen, cfg.GREEN, (enemy.x - 15, enemy.y - 20, 30 * hp_ratio, 4))

    def _draw_projectiles(self, screen, manager):
        """Рисует снаряды маленькими жёлтыми кругами."""
        for proj in manager.projectiles:
            pygame.draw.circle(screen, cfg.YELLOW, (int(proj.x), int(proj.y)), 4)

    # ============================
    # Нижняя панель (HUD)
    # ============================

    def _draw_hud(self, screen, manager, btn_to_menu, width, height):
        """Рисует нижнюю информационную панель.

        Верхняя строка: золото, волна, HP базы
        Нижняя строка: уровень башен, текущее оружие, подсказки клавиш
        """
        # Тёмный фон панели
        pygame.draw.rect(screen, cfg.DARK_GREY,
                         (0, height - cfg.HUD_HEIGHT, width, cfg.HUD_HEIGHT))

        y_top = height - 90  # координата верхней строки
        x = 20               # начальный отступ слева

        # --- Золото (жёлтым цветом) ---
        gold_label = self.font.render("Gold: ", True, (180, 180, 180))
        gold_val = self.font_bold.render(str(manager.money), True, cfg.YELLOW)
        screen.blit(gold_label, (x, y_top))
        screen.blit(gold_val, (x + gold_label.get_width(), y_top))

        # --- Волна (белым цветом) ---
        x2 = x + gold_label.get_width() + gold_val.get_width() + 30
        wave_label = self.font.render("Wave: ", True, (180, 180, 180))
        wave_val = self.font_bold.render(str(manager.wave), True, cfg.WHITE)
        screen.blit(wave_label, (x2, y_top))
        screen.blit(wave_val, (x2 + wave_label.get_width(), y_top))

        # --- HP базы (зелёным, а если мало — красным) ---
        x3 = x2 + wave_label.get_width() + wave_val.get_width() + 30
        hp_label = self.font.render("HP: ", True, (180, 180, 180))
        # Порог: если HP меньше трети — красный цвет
        hp_color = cfg.GREEN if manager.base_hp > manager.max_base_hp // 3 else cfg.RED
        hp_val = self.font_bold.render(
            f"{manager.base_hp}/{manager.max_base_hp}", True, hp_color
        )
        screen.blit(hp_label, (x3, y_top))
        screen.blit(hp_val, (x3 + hp_label.get_width(), y_top))

        # --- Нижняя строка ---
        y_bot = height - 55

        # Уровень башен и подсказка продажи (серым)
        lvl_text = self.font.render(
            f"Уровень Т-{manager.tower_level}  |  ПКМ — продать", True, (150, 150, 150)
        )
        screen.blit(lvl_text, (x, y_bot))

        # Текущее оружие — подсвечено цветом типа башни
        weapon_label = self.font.render("Оружие: ", True, (180, 180, 180))
        weapon_color = cfg.BLUE if manager.selected_type == "LMG" else cfg.PURPLE
        weapon_val = self.font_bold.render(manager.selected_type, True, weapon_color)
        keys_text = self.font.render("  [1] LMG  [2] SNIPER", True, (140, 140, 140))
        wx = width // 2
        screen.blit(weapon_label, (wx, y_bot))
        screen.blit(weapon_val, (wx + weapon_label.get_width(), y_bot))
        screen.blit(keys_text, (wx + weapon_label.get_width() + weapon_val.get_width(), y_bot))

        # --- Кнопка «В меню» ---
        pygame.draw.rect(screen, cfg.RED, btn_to_menu, border_radius=4)
        menu_text = self.font_bold.render("В меню", True, cfg.WHITE)
        # Центрируем текст внутри кнопки
        screen.blit(menu_text, (btn_to_menu.x + btn_to_menu.width // 2 - menu_text.get_width() // 2,
                                btn_to_menu.y + btn_to_menu.height // 2 - menu_text.get_height() // 2))

    # ============================
    # Всплывающие элементы
    # ============================

    def _draw_upgrade_text(self, screen, manager, width):
        """Рисует уведомление об улучшении по центру верхней части экрана.
        Текст с жёлтой рамкой на тёмном фоне, исчезает через несколько секунд."""
        if manager.upgrade_text_timer <= 0:
            return
        text_surface = self.font.render(manager.upgrade_text, True, cfg.YELLOW)
        text_rect = text_surface.get_rect(center=(width // 2, 40))
        # Фон под текстом (чуть больше текста)
        bg_rect = pygame.Rect(text_rect.x - 15, text_rect.y - 8,
                               text_rect.width + 30, text_rect.height + 16)
        pygame.draw.rect(screen, (15, 15, 15), bg_rect, border_radius=6)
        pygame.draw.rect(screen, cfg.YELLOW, bg_rect, width=2, border_radius=6)
        screen.blit(text_surface, text_rect)

    def _draw_game_over(self, screen, width, height):
        """Рисует экран поражения: полупрозрачное затемнение + текст.
        Затемнение создаётся через Surface с альфа-каналом (180 из 255)."""
        # Создаём полупрозрачную чёрную поверхность
        overlay = pygame.Surface((width, height - cfg.HUD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # 180 = ~70% непрозрачности
        screen.blit(overlay, (0, 0))
        # Надписи по центру
        text_go = self.big_font.render("GAME OVER", True, cfg.RED)
        text_sub = self.font.render("Дом разрушен! Кликните для меню.", True, cfg.WHITE)
        screen.blit(text_go, (width // 2 - text_go.get_width() // 2, height // 2 - 60))
        screen.blit(text_sub, (width // 2 - text_sub.get_width() // 2, height // 2 + 10))
