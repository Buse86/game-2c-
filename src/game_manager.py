"""
Менеджер игры — управляет всем игровым состоянием:
спавн врагов, обновление башен и снарядов, проверка волн,
сохранение/загрузка, обработка кликов игрока.
"""

import json
import os
import random
from src import config as cfg
from src.navigation import NavigationEngine
from src.map_generator import MapGenerator
from src.entities import create_tower, Enemy, TOWER_TYPES


class GameManager:
    """Центральный класс, хранящий и обновляющий состояние игры."""

    def __init__(self, load_save):
        """Инициализирует игру — новую или из сохранения.

        Аргументы:
            load_save — True = загрузить сохранение, False = новая игра
        """
        # --- Состояние игрока ---
        self.money = cfg.START_MONEY          # текущее золото
        self.wave = 1                          # номер текущей волны
        self.base_hp = cfg.START_HP            # текущее здоровье базы
        self.max_base_hp = cfg.START_HP        # максимальное здоровье базы
        self.tower_level = 1                   # глобальный уровень башен
        self.game_over = False                 # флаг окончания игры
        self.world_seed = 0                    # сид карты (для воспроизводимости)

        # --- Текст уведомления об улучшении ---
        self.upgrade_text = ""                 # текст, показываемый при апгрейде
        self.upgrade_text_timer = 0.0          # таймер показа (секунды)

        # --- Навигация ---
        # Точка входа врагов — левый край, середина по высоте
        self.start_node = (0, cfg.rows // 2)
        # База — правый край, середина по высоте
        self.end_node = (cfg.cols - 1, cfg.rows // 2)
        self.nav = NavigationEngine()          # движок поиска пути

        # --- Игровые объекты ---
        self.enemies = []                      # список активных врагов
        self.towers = []                       # список построенных башен
        self.projectiles = []                  # список летящих снарядов
        self.selected_type = "LMG"             # текущий тип башни для постройки
        self.spawn_timer = 0                   # таймер между спавнами врагов
        self.enemies_to_spawn = 0              # сколько врагов осталось создать

        # --- Загрузка или создание карты ---
        if load_save and os.path.exists("td_seed_save.json"):
            self._load_game()
        else:
            self._new_game()

        # Строим путь для врагов от входа до базы
        self.path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)

    # ============================
    # Создание и загрузка игры
    # ============================

    def _new_game(self):
        """Генерирует новую карту, подбирая сид с проходимым каньоном."""
        self.obstacles = set()
        # Генерируем карты, пока не получим проходимую
        while len(self.obstacles) == 0:
            random.seed(None)  # сбрасываем генератор для случайного сида
            self.world_seed = random.randint(1, 9999999)
            self.obstacles = MapGenerator.generate_canyon(
                self.start_node, self.end_node, self.world_seed
            )
        # blocked_cells = препятствия + клетки с башнями
        self.blocked_cells = self.obstacles.copy()

    def _load_game(self):
        """Загружает состояние игры из JSON-файла сохранения."""
        with open("td_seed_save.json", "r") as f:
            data = json.load(f)

        # Восстанавливаем параметры игрока
        self.money = data["money"]
        self.wave = data["wave"]
        self.base_hp = data.get("base_hp", cfg.START_HP)
        self.max_base_hp = data.get("max_base_hp", cfg.START_HP)
        self.tower_level = data.get("tower_level", 1)
        self.world_seed = data["world_seed"]

        # Восстанавливаем карту по сохранённому сиду
        # (один сид = одна и та же карта)
        self.obstacles = MapGenerator.generate_canyon(
            self.start_node, self.end_node, self.world_seed
        )
        while len(self.obstacles) == 0:
            self.world_seed = random.randint(1, 9999999)
            self.obstacles = MapGenerator.generate_canyon(
                self.start_node, self.end_node, self.world_seed
            )
        self.blocked_cells = self.obstacles.copy()

        # Восстанавливаем башни из сохранения
        for tower_data in data.get("towers", []):
            gx, gy, tower_type = tower_data[0], tower_data[1], tower_data[2]
            tower = create_tower(gx, gy, tower_type, self.tower_level)
            self.towers.append(tower)
            self.blocked_cells.add((gx, gy))  # башня тоже блокирует клетку

    def save(self):
        """Сохраняет текущее состояние игры в JSON-файл.
        Карта не сохраняется — только сид, по которому она восстанавливается."""
        if self.game_over:
            return  # проигранную игру не сохраняем

        # Список башен: [x, y, тип] для каждой
        towers_list = [[t.gx, t.gy, t.type_name] for t in self.towers]
        with open("td_seed_save.json", "w") as f:
            json.dump({
                "money": self.money,
                "wave": self.wave,
                "base_hp": self.base_hp,
                "max_base_hp": self.max_base_hp,
                "tower_level": self.tower_level,
                "world_seed": self.world_seed,
                "towers": towers_list,
            }, f)

    # ============================
    # Игровой цикл (вызывается каждый кадр)
    # ============================

    def update(self, dt):
        """Главный метод обновления игровой логики.

        Аргументы:
            dt — фиксированный шаг времени (1/60 секунды)
        """
        # Уменьшаем таймер уведомления об улучшении
        if self.upgrade_text_timer > 0:
            self.upgrade_text_timer -= dt

        # Обновляем все подсистемы по порядку
        self._spawn_enemies(dt)
        self._update_enemies(dt)
        self._update_towers(dt)
        self._update_projectiles(dt)
        self._check_wave_end()

    def _spawn_enemies(self, dt):
        """Создаёт новых врагов с заданным интервалом.
        Враги появляются по одному, пока не исчерпается очередь."""
        if self.enemies_to_spawn <= 0:
            return

        self.spawn_timer += dt
        if self.spawn_timer >= cfg.SPAWN_INTERVAL:
            if self.path:  # проверяем, что путь существует
                self.enemies.append(Enemy(self.path, self.wave))
            self.enemies_to_spawn -= 1
            self.spawn_timer = 0

    def _update_enemies(self, dt):
        """Обновляет всех врагов: движение, гибель, достижение базы.

        Используем копию списка (self.enemies[:]), чтобы безопасно
        удалять элементы во время итерации.
        """
        for enemy in self.enemies[:]:
            status = enemy.tick(dt)

            if status == "FINISHED":
                # Враг прошёл весь путь и дошёл до базы
                self.base_hp -= 1
                self.enemies.remove(enemy)
                # Если база уничтожена — конец игры
                if self.base_hp <= 0:
                    self.game_over = True
                    # Удаляем сохранение проигранной игры
                    if os.path.exists("td_seed_save.json"):
                        os.remove("td_seed_save.json")

            elif status == "DEAD":
                # Враг убит башнями — получаем награду
                self.money += enemy.reward
                self.enemies.remove(enemy)

    def _update_towers(self, dt):
        """Обновляет все башни — перезарядка и стрельба по врагам."""
        for tower in self.towers:
            tower.update_and_shoot(self.projectiles, dt, self.enemies, self.obstacles)

    def _update_projectiles(self, dt):
        """Двигает все снаряды к целям и удаляет попавшие/неактивные."""
        for proj in self.projectiles[:]:
            proj.update(dt, self.enemies)
            if not proj.active:
                self.projectiles.remove(proj)

    def _check_wave_end(self):
        """Проверяет, закончилась ли текущая волна.
        Если все враги убиты/прошли — запускает следующую."""
        # Волна не закончена, если есть живые враги или ещё не все заспавнились
        if self.enemies or self.enemies_to_spawn > 0:
            return

        # Каждые N волн — глобальное улучшение
        if self.wave % cfg.UPGRADE_EVERY_N_WAVES == 0:
            self.tower_level += 1                    # уровень башен растёт
            self.max_base_hp += cfg.UPGRADE_HP_BONUS  # максимум HP базы растёт
            self.base_hp = self.max_base_hp           # полное восстановление HP
            # Пересчитываем характеристики всех существующих башен
            for tower in self.towers:
                tower.upgrade_stats(self.tower_level)
            # Показываем уведомление
            self.upgrade_text = (
                f"10 ВОЛН ПРОЙДЕНО! Орудия Т-{self.tower_level}! База укреплена!"
            )
            self.upgrade_text_timer = cfg.UPGRADE_TEXT_DURATION

        # Запускаем следующую волну
        self.wave += 1
        self.save()
        # Количество врагов: база + волна * масштаб
        self.enemies_to_spawn = cfg.BASE_ENEMIES_PER_WAVE + self.wave * cfg.ENEMIES_PER_WAVE_SCALE

    # ============================
    # Обработка действий игрока
    # ============================

    def handle_click(self, pos):
        """Обрабатывает клик ЛКМ — попытка поставить башню.

        Логика:
        1. Определяем клетку по координатам клика
        2. Проверяем: клетка свободна? хватает денег?
        3. Временно блокируем клетку и проверяем, не заблокировали ли путь
        4. Если путь есть — ставим башню, иначе отменяем
        """
        if self.game_over:
            return

        # Переводим пиксельные координаты клика в координаты сетки
        gx = pos[0] // cfg.GRID_SIZE
        gy = pos[1] // cfg.GRID_SIZE
        cell = (gx, gy)

        # Проверяем, что клетка внутри поля
        if not (0 <= gx < cfg.cols and 0 <= gy < cfg.rows):
            return
        # Нельзя ставить на занятые клетки или на путь врагов
        if cell in self.blocked_cells or cell in self.path:
            return

        # Получаем класс башни и проверяем, хватает ли денег
        tower_class = TOWER_TYPES.get(self.selected_type)
        if not tower_class or self.money < tower_class.cost:
            return

        # Пробуем разместить: добавляем клетку в заблокированные
        self.blocked_cells.add(cell)
        # Проверяем, проходим ли путь с новой башней
        new_path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)

        if new_path:
            # Путь есть — подтверждаем размещение
            self.path = new_path
            self.towers.append(create_tower(gx, gy, self.selected_type, self.tower_level))
            self.money -= tower_class.cost
            self.save()
        else:
            # Башня заблокировала бы единственный путь — отменяем
            self.blocked_cells.remove(cell)

    def handle_right_click(self, pos):
        """Обрабатывает клик ПКМ — продажа башни.
        Возвращает часть стоимости и освобождает клетку."""
        if self.game_over:
            return

        # Определяем клетку
        gx = pos[0] // cfg.GRID_SIZE
        gy = pos[1] // cfg.GRID_SIZE

        # Ищем башню на этой клетке
        for tower in self.towers[:]:
            if tower.gx == gx and tower.gy == gy:
                # Возвращаем часть стоимости (80%)
                self.money += int(tower.cost * cfg.SELL_REFUND)
                self.towers.remove(tower)
                self.blocked_cells.remove((gx, gy))
                # Перестраиваем путь без этой башни
                self.path = self.nav.find_path(
                    self.start_node, self.end_node, self.blocked_cells
                )
                self.save()
                break  # на одной клетке только одна башня

    def handle_resize(self):
        """Перестраивает карту при изменении размера окна.
        Пересоздаёт каньон и убирает башни за пределами новой сетки."""
        # Обновляем позиции входа и базы под новый размер
        self.start_node = (0, cfg.rows // 2)
        self.end_node = (cfg.cols - 1, cfg.rows // 2)

        # Пытаемся сгенерировать карту с тем же сидом для нового размера
        temp_seed = self.world_seed
        new_obs = set()
        attempts = 0
        while len(new_obs) == 0 and attempts < 5:
            new_obs = MapGenerator.generate_canyon(
                self.start_node, self.end_node, temp_seed
            )
            temp_seed += 1
            attempts += 1

        if new_obs:
            self.obstacles = new_obs
            self.blocked_cells = self.obstacles.copy()

        # Убираем башни, которые вышли за пределы новой сетки
        valid_towers = []
        for tower in self.towers:
            if 0 <= tower.gx < cfg.cols and 0 <= tower.gy < cfg.rows:
                valid_towers.append(tower)
                self.blocked_cells.add((tower.gx, tower.gy))
        self.towers = valid_towers

        # Перестраиваем путь
        self.path = self.nav.find_path(self.start_node, self.end_node, self.blocked_cells)
