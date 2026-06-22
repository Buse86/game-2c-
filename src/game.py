import pygame
import os
from src import config as cfg
from src.entities import EnemyAI, Enemy  # Изменен импорт
from src.ui.renderer import GameRenderer  # Изменен импорт (теперь из папки ui)
from src.ui.input_handler import InputHandler  # Изменен импорт (теперь из папки ui)

class GameApp:
    def __init__(self):
        pygame.init()
        
        cfg.cols = cfg.WIDTH // cfg.GRID_SIZE
        cfg.rows = (cfg.HEIGHT - 100) // cfg.GRID_SIZE
        
        self.screen = pygame.display.set_mode((cfg.WIDTH, cfg.HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("SOLID Dynamic Tower Defense")
        
        self.renderer = GameRenderer()
        self.input_handler = InputHandler(self)
        
        self.manager = None
        self.in_menu = True
        self.running = True
        
        w, h = self.screen.get_size()
        self.btn_new = pygame.Rect(w//2 - 150, 260, 300, 50)
        self.btn_cont = pygame.Rect(w//2 - 150, 340, 300, 50)
        self.btn_to_menu = pygame.Rect(w - 180, h - 65, 150, 40)

    def resize_window(self, w, h):
        self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
        cfg.cols = max(5, w // cfg.GRID_SIZE)
        cfg.rows = max(5, (h - 100) // cfg.GRID_SIZE)
        
        self.btn_new.x, self.btn_new.y = w//2 - 150, 260
        self.btn_cont.x, self.btn_cont.y = w//2 - 150, 340
        self.btn_to_menu.x, self.btn_to_menu.y = w - 180, h - 65
        
        if self.manager:
            self.manager.handle_resize()

    def update_game_logic(self, dt):
        if self.manager.upgrade_text_timer > 0:
            self.manager.upgrade_text_timer -= dt

        if self.manager.enemies_to_spawn > 0:
            self.manager.spawn_timer += dt
            if self.manager.spawn_timer >= 0.7:
                if self.manager.path: 
                    self.manager.enemies.append(Enemy(self.manager.path, self.manager.wave))
                self.manager.enemies_to_spawn -= 1
                self.manager.spawn_timer = 0

        for e in self.manager.enemies[:]:
            ai_status = EnemyAI.tick(e, dt)
            if ai_status == "FINISHED": 
                self.manager.base_hp -= 1
                self.manager.enemies.remove(e)
                if self.manager.base_hp <= 0:
                    self.manager.game_over = True
                    if os.path.exists("td_seed_save.json"):
                        os.remove("td_seed_save.json") 
            elif ai_status == "DEAD":
                self.manager.money += e.reward
                self.manager.enemies.remove(e)

        for t in self.manager.towers: 
            t.update_and_shoot(self.manager.projectiles, dt, self.manager.enemies, self.manager.obstacles)
            
        for p in self.manager.projectiles[:]:
            p.update(dt, self.manager.enemies)
            if not p.active: self.manager.projectiles.remove(p)

        # Проверка окончания волны
        if not self.manager.enemies and self.manager.enemies_to_spawn == 0:
            if self.manager.wave % 10 == 0:
                self.manager.tower_level += 1
                self.manager.max_base_hp += 5
                self.manager.base_hp = self.manager.max_base_hp 
                for t in self.manager.towers:
                    t.upgrade_stats(self.manager.tower_level)
                self.manager.upgrade_text = f"10 ВОЛН ПРОЙДЕНО! Орудия Т-{self.manager.tower_level}! База укреплена!"
                self.manager.upgrade_text_timer = 4.0 
                
            self.manager.wave += 1
            self.manager.save()
            self.manager.enemies_to_spawn = 5 + self.manager.wave * 2
                    

    def run(self):
        clock = pygame.time.Clock()
        accumulator = 0.0
        dt_fixed = 1 / 60.0 

        while self.running:
            duration = clock.tick(120) 
            accumulator += duration / 1000.0
            
            self.input_handler.process_events()

            if not self.in_menu:
                if not self.manager.game_over:
                    while accumulator >= dt_fixed:
                        accumulator -= dt_fixed
                        self.update_game_logic(dt_fixed)
                else:
                    accumulator = 0 

            w, h = self.screen.get_size()
            if self.in_menu:
                self.renderer.draw_menu(self.screen, self.btn_new, self.btn_cont, os.path.exists("td_seed_save.json"))
            else:
                self.renderer.draw_game(self.screen, self.manager, self.btn_to_menu, w, h)

            pygame.display.flip()
            
        pygame.quit()