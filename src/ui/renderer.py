import pygame
from .. import config as cfg  # Изменен импорт

class GameRenderer:
    def __init__(self):
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 48, bold=True)

    def draw_menu(self, screen, btn_new, btn_cont, save_exists):
        screen.fill((20, 20, 20))
        pygame.draw.rect(screen, cfg.BLUE, btn_new, border_radius=4)
        cc = cfg.GREEN if save_exists else (70, 70, 70)
        pygame.draw.rect(screen, cc, btn_cont, border_radius=4)
        screen.blit(self.font.render("Новая игра", True, cfg.WHITE), (btn_new.x + 85, btn_new.y + 12))
        screen.blit(self.font.render("Продолжить", True, cfg.WHITE), (btn_cont.x + 85, btn_cont.y + 12))

    def draw_game(self, screen, manager, btn_to_menu, current_width, current_height):
        screen.fill(cfg.SAND)
        for cx in range(cfg.cols):
            for cy in range(cfg.rows):
                pygame.draw.rect(screen, (225, 215, 160), (cx*cfg.GRID_SIZE, cy*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE), 1)
                if (cx, cy) in manager.obstacles:
                    pygame.draw.rect(screen, cfg.BROWN, (cx*cfg.GRID_SIZE, cy*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE))
        
        for n in manager.path:
            pygame.draw.rect(screen, (215, 240, 215), (n[0]*cfg.GRID_SIZE, n[1]*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE))
        
        pygame.draw.rect(screen, cfg.GREEN, (manager.start_node[0]*cfg.GRID_SIZE, manager.start_node[1]*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE))
        pygame.draw.rect(screen, cfg.BLUE, (manager.end_node[0]*cfg.GRID_SIZE, manager.end_node[1]*cfg.GRID_SIZE, cfg.GRID_SIZE, cfg.GRID_SIZE))
        
        if not manager.game_over:
            bx, by = manager.end_node[0] * cfg.GRID_SIZE, manager.end_node[1] * cfg.GRID_SIZE
            pygame.draw.rect(screen, cfg.RED, (bx, by - 12, cfg.GRID_SIZE, 5))
            pygame.draw.rect(screen, cfg.GREEN, (bx, by - 12, cfg.GRID_SIZE * (manager.base_hp / manager.max_base_hp), 5))

        for t in manager.towers: 
            pygame.draw.rect(screen, t.color, (t.gx*cfg.GRID_SIZE+4, t.gy*cfg.GRID_SIZE+4, cfg.GRID_SIZE-8, cfg.GRID_SIZE-8))
        
        for e in manager.enemies: 
            pygame.draw.circle(screen, cfg.RED, (int(e.x), int(e.y)), 12)
            pygame.draw.rect(screen, cfg.RED, (e.x - 15, e.y - 20, 30, 4))
            pygame.draw.rect(screen, cfg.GREEN, (e.x - 15, e.y - 20, 30 * (e.hp / e.max_hp), 4))
            
        for p in manager.projectiles: 
            pygame.draw.circle(screen, cfg.YELLOW, (int(p.x), int(p.y)), 4)

        pygame.draw.rect(screen, cfg.DARK_GREY, (0, current_height-100, current_width, 100))
        screen.blit(self.font.render(f"Gold: {manager.money}  Wave: {manager.wave}  Base HP: {manager.base_hp}/{manager.max_base_hp}", True, cfg.WHITE), (30, current_height-75))
        screen.blit(self.font.render(f"Weapon Lvl: T-{manager.tower_level} (ПКМ на турель — удалить)", True, (200, 200, 200)), (30, current_height-40))
        screen.blit(self.font.render(f"Weapon: {manager.selected_type} (1: LMG, 2: SNIPER)", True, cfg.WHITE), (current_width//2 - 100, current_height-60))

        pygame.draw.rect(screen, cfg.RED, btn_to_menu, border_radius=4)
        screen.blit(self.font.render("В меню", True, cfg.WHITE), (btn_to_menu.x + 42, btn_to_menu.y + 7))

        if manager.upgrade_text_timer > 0:
            t_surf = self.font.render(manager.upgrade_text, True, cfg.YELLOW)
            t_rect = t_surf.get_rect(center=(current_width // 2, 40))
            b_rect = pygame.Rect(t_rect.x - 15, t_rect.y - 8, t_rect.width + 30, t_rect.height + 16)
            pygame.draw.rect(screen, (15, 15, 15), b_rect, border_radius=6)
            pygame.draw.rect(screen, cfg.YELLOW, b_rect, width=2, border_radius=6)
            screen.blit(t_surf, t_rect)

        if manager.game_over:
            s = pygame.Surface((current_width, current_height-100), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180)) 
            screen.blit(s, (0, 0))
            text_go = self.big_font.render("GAME OVER", True, cfg.RED)
            text_sub = self.font.render("Главный дом разрушен! Кликните для меню.", True, cfg.WHITE)
            screen.blit(text_go, (current_width//2 - text_go.get_width()//2, current_height//2 - 60))
            screen.blit(text_sub, (current_width//2 - text_sub.get_width()//2, current_height//2 + 10))