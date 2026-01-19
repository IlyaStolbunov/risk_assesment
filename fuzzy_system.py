import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class FuzzyRiskSystem:
    """Гибкая система нечеткого вывода с конфигурацией из JSON"""

    def __init__(self, config=None):
        """
        Инициализация системы

        Args:
            config: Словарь с конфигурацией или None для использования по умолчанию
        """
        self.config = config
        self.input_variables = {}
        self.output_variables = {}
        self.rules = []

        if config:
            self.create_system_from_config(config)
        else:
            self.create_default_system()

    def create_system_from_config(self, config):
        """Создание системы из конфигурационного словаря"""
        self.config = config

        # Создание входных переменных
        for var_name, var_config in config['variables'].items():
            self._create_input_variable(var_name, var_config)

        # Создание выходных переменных
        for var_name, var_config in config.get('output', {}).items():
            self._create_output_variable(var_name, var_config)

        # Создание правил
        self._create_rules(config.get('rules', []))

        # Создание системы управления
        self._create_control_system()

    def _create_input_variable(self, name, config):
        """Создание входной переменной"""
        if 'range' not in config:
            raise ValueError(f"Отсутствует range для переменной {name}")

        # Создание универсума
        universe = np.arange(*config['range'])
        variable = ctrl.Antecedent(universe, name)

        # Создание термов
        for term_name, term_config in config['terms'].items():
            self._create_term(variable, term_name, term_config)

        self.input_variables[name] = variable
        return variable

    def _create_output_variable(self, name, config):
        """Создание выходной переменной"""
        if 'range' not in config:
            raise ValueError(f"Отсутствует range для переменной {name}")

        # Создание универсума
        universe = np.arange(*config['range'])
        variable = ctrl.Consequent(universe, name)

        # Создание термов
        for term_name, term_config in config['terms'].items():
            self._create_term(variable, term_name, term_config)

        self.output_variables[name] = variable
        return variable

    def _create_term(self, variable, term_name, term_config):
        """Создание терма для переменной"""
        term_type = term_config.get('type', 'trimf')
        params = term_config.get('params', [])

        if term_type == 'trimf':
            variable[term_name] = fuzz.trimf(variable.universe, params)
        elif term_type == 'trapmf':
            variable[term_name] = fuzz.trapmf(variable.universe, params)
        elif term_type == 'gaussmf':
            variable[term_name] = fuzz.gaussmf(variable.universe, *params)
        elif term_type == 'gbellmf':
            variable[term_name] = fuzz.gbellmf(variable.universe, *params)
        elif term_type == 'sigmf':
            variable[term_name] = fuzz.sigmf(variable.universe, *params)
        else:
            raise ValueError(f"Неизвестный тип функции: {term_type}")

    def _create_rules(self, rules_config):
        """Создание правил из конфигурации"""
        self.rules = []

        for rule_config in rules_config:
            condition = None

            # Обработка условий
            for i, condition_config in enumerate(rule_config['if']):
                var_name = condition_config['variable']
                term_name = condition_config['term']

                if var_name not in self.input_variables:
                    raise ValueError(f"Неизвестная переменная: {var_name}")

                term = self.input_variables[var_name][term_name]

                if i == 0:
                    condition = term
                else:
                    operator = condition_config.get('operator', 'and')
                    if operator == 'and':
                        condition = condition & term
                    elif operator == 'or':
                        condition = condition | term

            # Обработка вывода
            then_term = rule_config['then']
            if 'risk' not in self.output_variables:
                raise ValueError("Выходная переменная 'risk' не найдена")

            if then_term not in self.output_variables['risk'].terms:
                raise ValueError(f"Неизвестный терм риска: {then_term}")

            output = self.output_variables['risk'][then_term]

            # Создание правила
            rule = ctrl.Rule(condition, output)
            self.rules.append(rule)

    def _create_control_system(self):
        """Создание системы управления"""
        if not self.rules:
            raise ValueError("Нет правил для создания системы")

        self.risk_ctrl = ctrl.ControlSystem(self.rules)
        self.simulation = ctrl.ControlSystemSimulation(self.risk_ctrl)

    def create_default_system(self):
        """Создание системы по умолчанию"""
        from config_loader import ConfigLoader
        default_config = ConfigLoader.get_default_config()
        self.create_system_from_config(default_config)

    def calculate_risk(self, vibration_val, noise_val, chemical_val, health_val):
        """
        Расчет уровня риска

        Args:
            vibration_val: 0-10
            noise_val: 0-10
            chemical_val: 0-10
            health_val: 0-1

        Returns:
            Словарь с результатами расчета
        """
        try:
            # Устанавливаем входные значения
            self.simulation.input['vibration'] = max(0, min(10, vibration_val))
            self.simulation.input['noise'] = max(0, min(10, noise_val))
            self.simulation.input['chemical'] = max(0, min(10, chemical_val))
            self.simulation.input['health'] = max(0.0, min(1.0, health_val))

            # Выполняем расчет
            self.simulation.compute()
            risk_value = self.simulation.output['risk']

            # Определяем категорию риска
            category, color = self._categorize_risk(risk_value)

            return {
                'value': round(risk_value, 2),
                'percent': f"{risk_value:.1f}%",
                'category': category,
                'color': color,
                'success': True
            }

        except Exception as e:
            print(f"Ошибка расчета риска: {e}")
            return {
                'value': 0,
                'percent': "0%",
                'category': "Ошибка расчета",
                'color': "#999999",
                'success': False,
                'error': str(e)
            }

    def _categorize_risk(self, risk_value):
        """Категоризация риска"""
        if risk_value <= 25:
            return "Очень низкий", "#4CAF50"
        elif risk_value <= 50:
            return "Низкий", "#8BC34A"
        elif risk_value <= 75:
            return "Средний", "#FFC107"
        elif risk_value <= 90:
            return "Высокий", "#FF9800"
        else:
            return "Очень высокий", "#F44336"

    def get_config_info(self):
        """Получение информации о текущей конфигурации"""
        if not self.config:
            return "Используется конфигурация по умолчанию"

        info = []
        info.append("=== КОНФИГУРАЦИЯ СИСТЕМЫ ===")

        # Информация о переменных
        info.append("\nВходные переменные:")
        for var_name, var_config in self.config['variables'].items():
            info.append(f"  {var_name}:")
            for term_name, term_config in var_config['terms'].items():
                info.append(f"    - {term_name}: {term_config['type']} {term_config['params']}")

        # Информация о правилах
        info.append("\nПравила:")
        for i, rule in enumerate(self.config['rules'], 1):
            conditions = []
            for cond in rule['if']:
                operator = cond.get('operator', 'и')
                conditions.append(f"{cond['variable']} {cond['term']}")

            info.append(f"  {i}. ЕСЛИ {' '.join(conditions)} ТО риск {rule['then']}")

        return "\n".join(info)