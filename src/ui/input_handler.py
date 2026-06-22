import pygame
import os
from src import config as cfg  # Изменен импорт
from src.game_manager import GameManager  # Изменен импорт

class InputHandler:
    def __init__(self, app):
        self.app = app  

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                self.app.running = False
                
            elif event.type == pygame.VIDEORESIZE:
                self.app.resize_window(event.w, event.h)
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if self.app.in_menu:
                    if event.button == 1:
                        if self.app.btn_new.collidepoint(pos):
                            if os.path.exists("td_seed_save.json"):
                                os.remove("td_seed_save.json")
                            self.app.manager = GameManager(load_save=False)
                            self.app.manager.enemies_to_spawn = 5
                            self.app.in_menu = False
                        elif self.app.btn_cont.collidepoint(pos) and os.path.exists("td_seed_save.json"):
                            self.app.manager = GameManager(load_save=True)
                            self.app.manager.enemies_to_spawn = 5
                            self.app.in_menu = False
                else:
                    if self.app.btn_to_menu.collidepoint(pos) and event.button == 1:
                        self.app.manager.save()  
                        self.app.in_menu = True
                    elif pos[1] < cfg.rows * cfg.GRID_SIZE and not self.app.manager.game_over: 
                        if event.button == 1:   
                            self.app.manager.handle_click(pos)
                        elif event.button == 3: 
                            self.app.manager.handle_right_click(pos)
                    elif self.app.manager.game_over and event.button == 1: 
                        self.app.in_menu = True
                        
            elif event.type == pygame.KEYDOWN and not self.app.in_menu and not self.app.manager.game_over:
                if event.key == pygame.K_1: self.app.manager.selected_type = "LMG"
                if event.key == pygame.K_2: self.app.manager.selected_type = "SNIPER"