"""
Игровые сущности: враги, башни и снаряды.
Башни реализованы через наследование — базовый класс Tower
содержит общую логику, а LMGTower и SniperTower задают свои параметры.
"""

import math
from src import config as cfg


class Enemy:
    """Враг, который движется по заданному пути от точки входа к базе.
    Характеристики (HP, скорость, награда) зависят от номера волны."""

    def __init__(self, path, wave):
        # Путь приходит в координатах сетки (например, (3, 5) — 3-я колонка, 5-я строка).
        # Переводим в пиксельные координаты, указывающие на центр каждой клетки.
        # Формула: x_пикс = колонка * размер_клетки + половина_клетки
        self.path = [
            (node[0] * cfg.GRID_SIZE + cfg.GRID_SIZE // 2,
             node[1] * cfg.GRID_SIZE + cfg.GRID_SIZE // 2)
            for node in path
        ]
        self.path_index = 0  # индекс текущей точки, к которой враг движется
        self.x, self.y = self.path[0] if self.path else (0, 0)

        # HP растёт с каждой волной: базовый_хп * (1 + (волна-1) * коэффициент)
        # Например, волна 5: 90 * (1 + 4 * 0.25) = 90 * 2.0 = 180 HP
        self.max_hp = int(cfg.BASE_ENEMY_HP * (1 + (wave - 1) * cfg.ENEMY_HP_SCALE))
        self.hp = self.max_hp

        # Скорость тоже растёт, но ограничена максимумом
        self.speed = min(cfg.MAX_ENEMY_SPEED,
                         cfg.BASE_ENEMY_SPEED + (wave - 1) * cfg.ENEMY_SPEED_SCALE)

        # Награда за убийство немного растёт каждые несколько волн
        self.reward = cfg.BASE_ENEMY_REWARD + (wave // cfg.REWARD_WAVE_DIVISOR)

        # Сколько пикселей враг прошёл — используется башнями для приоритета:
        # стреляют в того, кто ушёл дальше всех (ближе к базе)
        self.distance_traveled = 0

    def is_alive(self):
        """Возвращает True, если у врага остались очки здоровья."""
        return self.hp > 0

    def move(self, dt):
        """Передвигает врага к следующей точке пути.

        Аргументы:
            dt — время кадра в секундах (например, 1/60 = 0.0167)

        Возвращает:
            True — если враг дошёл до конца пути (до базы)
            False — если враг ещё в пути
        """
        # Если мы уже на последней точке — значит дошли до базы
        if self.path_index >= len(self.path) - 1:
            return True

        # Берём координаты следующей точки пути
        target_x, target_y = self.path[self.path_index + 1]

        # Вычисляем вектор направления от текущей позиции к цели
        dx = target_x - self.x
        dy = target_y - self.y

        # Расстояние до следующей точки (теорема Пифагора)
        dist = math.hypot(dx, dy)

        # Сколько пикселей можем пройти за этот кадр
        step = self.speed * dt

        if dist <= step:
            # Достигли следующей точки — перемещаемся точно в неё
            self.x, self.y = target_x, target_y
            self.path_index += 1
        else:
            # Ещё не дошли — двигаемся в направлении цели.
            # Нормализуем вектор (делим на длину) и умножаем на шаг
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
            self.distance_traveled += step

        return False

    def tick(self, dt):
        """Обновляет состояние врага за один кадр.

        Возвращает строку-статус:
            "DEAD"     — враг убит (HP <= 0)
            "FINISHED" — враг дошёл до базы
            "RUNNING"  — враг ещё жив и в пути
        """
        if not self.is_alive():
            return "DEAD"
        if self.move(dt):
            return "FINISHED"
        return "RUNNING"


# =======================================================================
# БАШНИ — реализованы через наследование (паттерн «Шаблонный метод»).
# Базовый класс Tower содержит всю логику стрельбы и поиска цели.
# Подклассы (LMGTower, SniperTower) только задают свои числовые параметры
# через атрибуты класса — это позволяет легко добавлять новые типы башен.
# =======================================================================


class Tower:
    """Базовый класс для всех типов башен.

    Атрибуты класса (переопределяются в подклассах):
        base_damage — базовый урон за выстрел
        base_range  — базовый радиус поражения в пикселях
        max_cd      — время перезарядки между выстрелами (секунды)
        color       — цвет отображения на карте (RGB)
        cost        — стоимость постройки в золоте
        type_name   — строковое имя типа ("LMG", "SNIPER")
    """

    base_damage = 0
    base_range = 0
    max_cd = 0
    color = cfg.WHITE
    cost = 0
    type_name = ""

    def __init__(self, gx, gy, level=1):
        """Создаёт башню на клетке (gx, gy) с указанным уровнем.

        Аргументы:
            gx, gy — координаты на сетке (номер колонки, номер строки)
            level  — уровень башни (влияет на урон и дальность)
        """
        # Позиция на сетке (для логики размещения)
        self.gx = gx
        self.gy = gy

        # Позиция в пикселях (центр клетки — для расчёта расстояний)
        self.x = gx * cfg.GRID_SIZE + cfg.GRID_SIZE // 2
        self.y = gy * cfg.GRID_SIZE + cfg.GRID_SIZE // 2

        self.cooldown = 0  # таймер перезарядки (когда > 0, башня не стреляет)
        self.level = level
        self.upgrade_stats(level)

    def upgrade_stats(self, level):
        """Пересчитывает урон и дальность по формуле уровня.

        Формула: значение = база * (1 + (уровень - 1) * коэффициент)
        Пример для LMG уровня 3: урон = 20 * (1 + 2 * 0.3) = 20 * 1.6 = 32
        """
        self.damage = int(self.base_damage * (1 + (level - 1) * cfg.DAMAGE_SCALE))
        self.range = int(self.base_range * (1 + (level - 1) * cfg.RANGE_SCALE))

    def has_line_of_sight(self, target, obstacles):
        """Проверяет, есть ли прямая видимость от башни до цели.

        Использует алгоритм Брезенхэма — растеризацию отрезка на сетке.
        Проходим по всем клеткам между башней и целью; если хотя бы одна
        из них — препятствие, значит видимости нет.

        Аргументы:
            target    — объект врага с координатами (target.x, target.y)
            obstacles — множество (set) клеток-препятствий

        Возвращает:
            True  — путь свободен, башня видит цель
            False — между башней и целью есть стена
        """
        # Переводим пиксельные координаты цели обратно в координаты сетки
        target_gx = int(target.x // cfg.GRID_SIZE)
        target_gy = int(target.y // cfg.GRID_SIZE)

        # Начальная и конечная точки линии
        curr_x, curr_y = self.gx, self.gy
        end_x, end_y = target_gx, target_gy

        # Алгоритм Брезенхэма для рисования линии на сетке:
        # dx, dy — расстояния по осям
        dx = abs(end_x - curr_x)
        dy = abs(end_y - curr_y)

        # sx, sy — направление шага (+1 вправо/вниз, -1 влево/вверх)
        sx = 1 if curr_x < end_x else -1
        sy = 1 if curr_y < end_y else -1

        # err — ошибка накопления, определяет когда делать шаг по второй оси
        err = dx - dy

        # Идём по линии клетка за клеткой
        while (curr_x, curr_y) != (end_x, end_y):
            # Если текущая клетка — препятствие, видимости нет
            if (curr_x, curr_y) in obstacles:
                return False

            # Вычисляем удвоенную ошибку для выбора направления шага
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                curr_x += sx  # шаг по горизонтали
            if e2 < dx:
                err += dx
                curr_y += sy  # шаг по вертикали

        return True  # ни одного препятствия на пути

    def find_target(self, active_enemies, obstacles):
        """Выбирает лучшую цель для стрельбы.

        Приоритет: враг, который прошёл дальше всех по пути (ближе к базе)
        и находится в радиусе поражения башни с прямой видимостью.

        Возвращает объект Enemy или None, если целей нет.
        """
        best_target = None
        max_progress = -1.0  # максимальное пройденное расстояние

        for enemy in active_enemies:
            if enemy.is_alive():
                # Расстояние от башни до врага (в пикселях)
                dist = math.hypot(enemy.x - self.x, enemy.y - self.y)

                # Проверяем: в радиусе + ушёл дальше текущего лучшего + видим его
                if dist <= self.range and enemy.distance_traveled > max_progress:
                    if self.has_line_of_sight(enemy, obstacles):
                        max_progress = enemy.distance_traveled
                        best_target = enemy

        return best_target

    def update_and_shoot(self, projectiles, dt, active_enemies, obstacles):
        """Обновляет таймер перезарядки и стреляет при готовности.

        Если перезарядка прошла и есть подходящая цель — создаёт снаряд
        и добавляет его в общий список projectiles.
        """
        # Пока идёт перезарядка — уменьшаем таймер и не стреляем
        if self.cooldown > 0:
            self.cooldown -= dt
            return

        # Ищем цель и стреляем
        target = self.find_target(active_enemies, obstacles)
        if target:
            projectiles.append(Projectile(self.x, self.y, target, self.damage))
            self.cooldown = self.max_cd  # начинаем перезарядку


class LMGTower(Tower):
    """Лёгкий пулемёт (LMG).
    Быстрая стрельба (0.3 сек), малый урон (20), короткая дальность (140 пикс).
    Дешёвый (50 золота) — хорош для массовой обороны."""

    base_damage = 20
    base_range = 140
    max_cd = 0.3
    color = cfg.BLUE
    cost = 50
    type_name = "LMG"


class SniperTower(Tower):
    """Снайперская башня.
    Медленная стрельба (1.2 сек), высокий урон (70), большая дальность (240 пикс).
    Дорогая (125 золота) — эффективна против сильных врагов."""

    base_damage = 70
    base_range = 240
    max_cd = 1.2
    color = cfg.PURPLE
    cost = 125
    type_name = "SNIPER"


# Словарь типов башен: по строковому имени получаем класс.
# Используется для создания башен из сохранения и при клике игрока.
TOWER_TYPES = {
    "LMG": LMGTower,
    "SNIPER": SniperTower,
}


def create_tower(gx, gy, tower_type, level=1):
    """Фабричная функция — создаёт башню нужного типа по строковому имени.

    Аргументы:
        gx, gy     — позиция на сетке
        tower_type  — строка "LMG" или "SNIPER"
        level       — уровень башни

    Возвращает экземпляр LMGTower или SniperTower.
    """
    tower_class = TOWER_TYPES[tower_type]
    return tower_class(gx, gy, level)


class Projectile:
    """Снаряд, который летит от башни к вражеской цели.
    При достижении цели наносит урон и исчезает."""

    def __init__(self, x, y, target, damage):
        """
        Аргументы:
            x, y    — начальная позиция (координаты башни)
            target  — объект Enemy, к которому летит снаряд
            damage  — урон, который нанесётся при попадании
        """
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.active = True  # False = снаряд нужно удалить

    def update(self, dt, active_enemies):
        """Двигает снаряд к цели и проверяет попадание.

        Если цель уже мертва или удалена из списка — снаряд исчезает.
        Если снаряд долетел (расстояние <= радиус попадания) — наносит урон.
        """
        # Если цель удалена из игры или уже мертва — снаряд пропадает
        if self.target not in active_enemies or not self.target.is_alive():
            self.active = False
            return

        # Вектор от снаряда к цели
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)

        # Проверяем попадание: если расстояние меньше радиуса — наносим урон
        if dist <= cfg.PROJECTILE_HIT_RADIUS:
            self.target.hp -= self.damage
            self.active = False
            return

        # Двигаемся к цели
        step = cfg.PROJECTILE_SPEED * dt
        if dist <= step:
            # За один кадр долетаем до цели
            self.target.hp -= self.damage
            self.active = False
        else:
            # Летим в направлении цели (нормализованный вектор * скорость)
            self.x += (dx / dist) * step
            self.y += (dy / dist) * step
