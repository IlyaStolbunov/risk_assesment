import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Фиксированные имена переменных
INPUT_VARS = ["vibration", "noise", "chemical", "health"]
OUTPUT_VAR = "risk"


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
        self.risk_ctrl = None
        self.simulation = None

        if config:
            self.create_system_from_config(config)
        else:
            self.create_default_system()

    def create_system_from_config(self, config):
        """Создание системы из конфигурационного словаря"""
        self.config = config

        # Создание входных переменных
        for var_name in INPUT_VARS:
            if var_name in config['variables']:
                self._create_input_variable(var_name, config['variables'][var_name])

        # Создание выходной переменной
        if OUTPUT_VAR in config.get('output', {}):
            self._create_output_variable(OUTPUT_VAR, config['output'][OUTPUT_VAR])

        # Создание правил
        self._create_rules(config.get('rules', []))

        # Создание системы управления
        self._create_control_system()

    def _create_input_variable(self, name, config):
        """Создание входной переменной"""
        # Range больше не используется, всегда 0-1
        universe = np.arange(0, 1.01, 0.01)
        variable = ctrl.Antecedent(universe, name)

        # Создание термов
        for term_name, term_config in config['terms'].items():
            self._create_term(variable, term_name, term_config)

        self.input_variables[name] = variable
        return variable

    def _create_output_variable(self, name, config):
        """Создание выходной переменной"""
        universe = np.arange(0, 1.01, 0.01)
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
        elif term_type == 'zmf':
            variable[term_name] = fuzz.zmf(variable.universe, *params)
        elif term_type == 'smf':
            variable[term_name] = fuzz.smf(variable.universe, *params)
        elif term_type == 'pimf':
            variable[term_name] = fuzz.pimf(variable.universe, *params)
        else:
            raise ValueError(f"Неизвестный тип функции: {term_type}")

    def _create_rules(self, rules_config):
        """Создание правил из конфигурации"""
        self.rules = []

        if OUTPUT_VAR not in self.output_variables:
            raise ValueError("Выходная переменная 'risk' не найдена")

        output_var = self.output_variables[OUTPUT_VAR]

        for rule_config in rules_config:
            condition = None

            # Обработка условий
            for i, condition_config in enumerate(rule_config['if']):
                var_name = condition_config['variable']
                term_name = condition_config['term']

                if var_name not in self.input_variables:
                    raise ValueError(f"Неизвестная переменная: {var_name}")

                if term_name not in self.input_variables[var_name].terms:
                    raise ValueError(f"Неизвестный терм '{term_name}' для переменной '{var_name}'")

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
            if then_term not in output_var.terms:
                raise ValueError(f"Неизвестный терм '{then_term}' для выходной переменной '{OUTPUT_VAR}'")

            output = output_var[then_term]

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
        from config_editor import get_default_config
        default_config = get_default_config()
        self.create_system_from_config(default_config)

    def calculate_risk(self, vibration_val, noise_val, chemical_val, health_val):
        """
        Расчет уровня риска

        Args:
            vibration_val: значение вибрации (0-1)
            noise_val: значение шума (0-1)
            chemical_val: значение химического фактора (0-1)
            health_val: показатель здоровья (0-1)

        Returns:
            Словарь с результатами расчета
        """
        try:
            if not self.simulation:
                raise ValueError("Система не инициализирована")

            # Ограничиваем значения диапазоном 0-1
            vibration_val = max(0.0, min(1.0, vibration_val))
            noise_val = max(0.0, min(1.0, noise_val))
            chemical_val = max(0.0, min(1.0, chemical_val))
            health_val = max(0.0, min(1.0, health_val))

            # Устанавливаем входные значения
            if 'vibration' in self.input_variables:
                self.simulation.input['vibration'] = vibration_val

            if 'noise' in self.input_variables:
                self.simulation.input['noise'] = noise_val

            if 'chemical' in self.input_variables:
                self.simulation.input['chemical'] = chemical_val

            if 'health' in self.input_variables:
                self.simulation.input['health'] = health_val

            # Выполняем расчет
            self.simulation.compute()

            # Получаем значение выходной переменной
            risk_value = self.simulation.output[OUTPUT_VAR]

            risk_value = max(0.0, min(1.0, risk_value))

            # Определяем категорию риска на основе текущих термов
            category = self._categorize_risk(risk_value)

            return {
                'value': round(risk_value, 3),
                'percent': f"{risk_value*100:.1f}%",  # Конвертируем в проценты для отображения
                'category': category,
                'success': True
            }

        except Exception as e:
            print(f"Ошибка расчета риска: {e}")
            return {
                'value': 0,
                'percent': "0%",
                'category': "Ошибка расчета",
                'success': False,
                'error': str(e)
            }

    def _categorize_risk(self, risk_value):
        """
        Категоризация риска на основе текущих термов выходной переменной

        Args:
            risk_value: числовое значение риска (0-1)

        Returns:
            str: название категории
        """
        if OUTPUT_VAR not in self.output_variables:
            return "Неизвестно"

        output_var = self.output_variables[OUTPUT_VAR]

        # Находим терм с максимальной степенью принадлежности
        max_membership = 0
        best_term = None

        for term_name in output_var.terms:
            # Вычисляем степень принадлежности для данного значения
            membership = fuzz.interp_membership(
                output_var.universe,
                output_var[term_name].mf,
                risk_value
            )

            if membership > max_membership:
                max_membership = membership
                best_term = term_name

        return best_term if best_term else "Неизвестно"