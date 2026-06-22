import json
import os

class SaveManager:
    SAVE_FILE = "td_seed_save.json"

    @classmethod
    def save_game(cls, game_state_dict):
        try:
            with open(cls.SAVE_FILE, "w") as file:
                json.dump(game_state_dict, file)
        except IOError as e:
            print(f"Ошибка сохранения данных: {e}")

    @classmethod
    def load_game(cls):
        if not os.path.exists(cls.SAVE_FILE):
            return None
        try:
            with open(cls.SAVE_FILE, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            return None

    @classmethod
    def delete_save(cls):
        if os.path.exists(cls.SAVE_FILE):
            os.remove(cls.SAVE_FILE)