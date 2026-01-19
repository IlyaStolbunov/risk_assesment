"""
Модуль загрузки конфигурации нечеткой системы из JSON
"""

import json
import numpy as np


class ConfigLoader:
    """Загрузчик конфигурации из JSON файла"""

    @staticmethod
    def load_config(filepath):
        """
        Загрузка конфигурации из JSON файла

        Возвращает словарь с конфигурацией или None в случае ошибки
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Валидация конфигурации
            if not ConfigLoader.validate_config(config):
                raise ValueError("Неверный формат конфигурационного файла")

            return config

        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            return None

    @staticmethod
    def validate_config(config):
        """Проверка корректности конфигурации"""
        required_sections = ['variables', 'rules']

        for section in required_sections:
            if section not in config:
                return False

        # Проверка переменных
        required_variables = ['vibration', 'noise', 'chemical', 'health']
        for var in required_variables:
            if var not in config['variables']:
                return False

        return True

    @staticmethod
    def get_default_config():
        """Получение конфигурации по умолчанию"""
        return {
            "variables": {
                "vibration": {
                    "range": [0, 10, 0.1],
                    "terms": {
                        "low": {"type": "trimf", "params": [0, 0, 5]},
                        "medium": {"type": "trimf", "params": [0, 5, 10]},
                        "high": {"type": "trimf", "params": [5, 10, 10]}
                    }
                },
                "noise": {
                    "range": [0, 10, 0.1],
                    "terms": {
                        "low": {"type": "trimf", "params": [0, 0, 5]},
                        "medium": {"type": "trimf", "params": [0, 5, 10]},
                        "high": {"type": "trimf", "params": [5, 10, 10]}
                    }
                },
                "chemical": {
                    "range": [0, 10, 0.1],
                    "terms": {
                        "low": {"type": "trimf", "params": [0, 0, 4]},
                        "medium": {"type": "trimf", "params": [0, 4, 8]},
                        "high": {"type": "trimf", "params": [4, 8, 10]}
                    }
                },
                "health": {
                    "range": [0, 1, 0.01],
                    "terms": {
                        "bad": {"type": "trimf", "params": [0, 0, 0.5]},
                        "average": {"type": "trimf", "params": [0, 0.5, 1]},
                        "good": {"type": "trimf", "params": [0.5, 1, 1]}
                    }
                }
            },
            "output": {
                "risk": {
                    "range": [0, 100, 1],
                    "terms": {
                        "very_low": {"type": "trimf", "params": [0, 0, 25]},
                        "low": {"type": "trimf", "params": [0, 25, 50]},
                        "medium": {"type": "trimf", "params": [25, 50, 75]},
                        "high": {"type": "trimf", "params": [50, 75, 100]},
                        "very_high": {"type": "trimf", "params": [75, 100, 100]}
                    }
                }
            },
            "rules": [
                {
                    "if": [
                        {"variable": "vibration", "term": "high", "operator": "or"},
                        {"variable": "noise", "term": "high", "operator": "or"},
                        {"variable": "chemical", "term": "high"}
                    ],
                    "then": "high"
                },
                {
                    "if": [
                        {"variable": "health", "term": "bad", "operator": "and"},
                        {"variable": "vibration", "term": "medium", "operator": "or"},
                        {"variable": "noise", "term": "medium", "operator": "or"},
                        {"variable": "chemical", "term": "medium"}
                    ],
                    "then": "very_high"
                },
                {
                    "if": [
                        {"variable": "vibration", "term": "low", "operator": "and"},
                        {"variable": "noise", "term": "low", "operator": "and"},
                        {"variable": "chemical", "term": "low", "operator": "and"},
                        {"variable": "health", "term": "good"}
                    ],
                    "then": "very_low"
                }
            ]
        }

    @staticmethod
    def save_config(config, filepath):
        """Сохранение конфигурации в JSON файл"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")
            return False