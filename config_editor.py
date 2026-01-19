import json
from PyQt6.QtWidgets import *

class FunctionParamWidget(QWidget):
    """Виджет для ввода параметров функции"""

    def __init__(self, func_type="trimf", params=None):
        super().__init__()
        self.func_type = func_type
        self.params = params or self.get_default_params()
        self.setup_ui()

    def get_default_params(self):
        """Параметры по умолчанию"""
        if self.func_type == 'trimf':
            return [0, 0, 5]
        elif self.func_type == 'trapmf':
            return [0, 0, 5, 5]
        elif self.func_type == 'gaussmf':
            return [5, 1]
        elif self.func_type == 'gbellmf':
            return [1, 2, 5]
        elif self.func_type == 'sigmf':
            return [1, 5]
        return []

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Надписи для параметров
        labels = []
        if self.func_type == 'trimf':
            labels = ['a:', 'b:', 'c:']
        elif self.func_type == 'trapmf':
            labels = ['a:', 'b:', 'c:', 'd:']
        elif self.func_type == 'gaussmf':
            labels = ['центр:', 'ширина:']
        elif self.func_type == 'gbellmf':
            labels = ['a:', 'b:', 'c:']
        elif self.func_type == 'sigmf':
            labels = ['наклон:', 'центр:']

        self.spin_boxes = []
        for i, label in enumerate(labels):
            layout.addWidget(QLabel(label))

            spin_box = QDoubleSpinBox()
            spin_box.setRange(-1000, 1000)
            spin_box.setSingleStep(0.1)
            spin_box.setDecimals(2)
            spin_box.setValue(self.params[i] if i < len(self.params) else 0)

            self.spin_boxes.append(spin_box)
            layout.addWidget(spin_box)

        layout.addStretch()
        self.setLayout(layout)

    def get_params(self):
        """Получение параметров"""
        return [sb.value() for sb in self.spin_boxes]

class TermWidget(QWidget):
    """Виджет для редактирования одного терма"""

    def __init__(self, term_name="", term_config=None, on_delete=None):
        super().__init__()
        self.term_name = term_name
        self.term_config = term_config or {"type": "trimf", "params": [0, 0, 5]}
        self.on_delete = on_delete
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Заголовок
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"<b>{self.term_name}</b>"))
        header_layout.addStretch()

        # Кнопка удаления
        if self.on_delete:
            delete_btn = QPushButton("×")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda: self.on_delete(self.term_name))
            header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # Выбор типа функции
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип:"))

        self.func_combo = QComboBox()
        self.func_combo.addItems(["trimf", "trapmf", "gaussmf", "gbellmf", "sigmf"])

        # Устанавливаем текущее значение
        current_type = self.term_config.get('type', 'trimf')
        index = self.func_combo.findText(current_type)
        if index >= 0:
            self.func_combo.setCurrentIndex(index)

        type_layout.addWidget(self.func_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Параметры функции
        self.param_widget = FunctionParamWidget(
            current_type,
            self.term_config.get('params', [])
        )
        layout.addWidget(self.param_widget)

        # Обновляем параметры при изменении типа функции
        self.func_combo.currentTextChanged.connect(self.update_params_widget)

        self.setLayout(layout)

    def update_params_widget(self, func_type):
        """Обновление виджета параметров"""
        # Удаляем старый виджет
        self.layout().removeWidget(self.param_widget)
        self.param_widget.deleteLater()

        # Создаем новый
        self.param_widget = FunctionParamWidget(func_type)
        self.layout().addWidget(self.param_widget)

    def get_config(self):
        """Получение конфигурации"""
        params = self.param_widget.get_params()

        # Сортируем для треугольной и трапециевидной
        func_type = self.func_combo.currentText()
        if func_type in ['trimf', 'trapmf']:
            params = sorted(params)

        return {
            "type": func_type,
            "params": params
        }

class VariableWidget(QWidget):
    """Виджет для редактирования переменной"""

    def __init__(self, var_name="", var_config=None, on_delete=None):
        super().__init__()
        self.var_name = var_name
        self.var_config = var_config or {
            "range": [0, 10, 0.1],
            "terms": {}
        }
        self.on_delete = on_delete
        self.term_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Заголовок переменной
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"<h3>{self.var_name.upper()}</h3>"))
        header_layout.addStretch()

        # Кнопка удаления переменной
        if self.on_delete:
            delete_btn = QPushButton("Удалить переменную")
            delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
            delete_btn.clicked.connect(lambda: self.on_delete(self.var_name))
            header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # Диапазон значений
        range_group = QGroupBox("Диапазон значений")
        range_layout = QHBoxLayout()

        range_layout.addWidget(QLabel("от:"))
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(-1000, 1000)
        self.min_spin.setValue(self.var_config['range'][0])
        range_layout.addWidget(self.min_spin)

        range_layout.addWidget(QLabel("до:"))
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(-1000, 1000)
        self.max_spin.setValue(self.var_config['range'][1])
        range_layout.addWidget(self.max_spin)

        range_layout.addStretch()
        range_group.setLayout(range_layout)
        layout.addWidget(range_group)

        # Список термов
        terms_group = QGroupBox("Термы (функции принадлежности)")
        self.terms_layout = QVBoxLayout()

        # Загружаем существующие термы
        for term_name, term_config in self.var_config['terms'].items():
            self.add_term_widget(term_name, term_config)

        terms_group.setLayout(self.terms_layout)
        layout.addWidget(terms_group)

        # Кнопка добавления терма
        add_term_btn = QPushButton("+ Добавить терм")
        add_term_btn.clicked.connect(self.add_term)
        layout.addWidget(add_term_btn)

        self.setLayout(layout)

    def add_term_widget(self, term_name, term_config=None):
        """Добавление виджета терма"""
        if term_name in self.term_widgets:
            return

        term_widget = TermWidget(
            term_name,
            term_config,
            on_delete=self.remove_term_widget
        )

        self.term_widgets[term_name] = term_widget
        self.terms_layout.addWidget(term_widget)

    def remove_term_widget(self, term_name):
        """Удаление терма"""
        if term_name in self.term_widgets:
            widget = self.term_widgets.pop(term_name)
            widget.setParent(None)
            widget.deleteLater()

    def add_term(self):
        """Добавление нового терма"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Новый терм")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Введите название терма:"))

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("например: низкий, средний, высокий")
        layout.addWidget(name_edit)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            term_name = name_edit.text().strip()
            if term_name and term_name not in self.term_widgets:
                self.add_term_widget(term_name)

    def get_config(self):
        """Получение конфигурации переменной"""
        terms = {}
        for term_name, widget in self.term_widgets.items():
            terms[term_name] = widget.get_config()

        return {
            "range": [self.min_spin.value(), self.max_spin.value(), 0.1],
            "terms": terms
        }

class RuleConditionWidget(QWidget):
    """Виджет для одного условия правила"""

    def __init__(self, condition=None, available_vars=None, on_delete=None):
        super().__init__()
        self.condition = condition or {"variable": "vibration", "term": "low"}
        self.available_vars = available_vars or ["vibration", "noise", "chemical", "health"]
        self.on_delete = on_delete
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Выбор переменной
        self.var_combo = QComboBox()
        self.var_combo.addItems(self.available_vars)

        if 'variable' in self.condition:
            index = self.var_combo.findText(self.condition['variable'])
            if index >= 0:
                self.var_combo.setCurrentIndex(index)

        layout.addWidget(self.var_combo)

        # Выбор терма
        self.term_combo = QComboBox()
        self.update_terms()
        self.var_combo.currentTextChanged.connect(self.update_terms)

        if 'term' in self.condition:
            index = self.term_combo.findText(self.condition['term'])
            if index >= 0:
                self.term_combo.setCurrentIndex(index)

        layout.addWidget(self.term_combo)

        # Оператор (скрыт для первого условия)
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["И", "ИЛИ"])

        if 'operator' in self.condition:
            op_text = "И" if self.condition['operator'] == "and" else "ИЛИ"
            index = self.operator_combo.findText(op_text)
            if index >= 0:
                self.operator_combo.setCurrentIndex(index)

        layout.addWidget(self.operator_combo)

        # Кнопка удаления
        if self.on_delete:
            delete_btn = QPushButton("×")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(self.on_delete)
            layout.addWidget(delete_btn)

        layout.addStretch()
        self.setLayout(layout)

    def update_terms(self):
        """Обновление списка термов"""
        # В реальном приложении нужно получать термы из конфигурации
        # Сейчас используем стандартные
        variable = self.var_combo.currentText()

        self.term_combo.clear()
        if variable == "health":
            self.term_combo.addItems(["bad", "average", "good"])
        else:
            self.term_combo.addItems(["low", "medium", "high"])

    def get_config(self):
        """Получение конфигурации условия"""
        return {
            "variable": self.var_combo.currentText(),
            "term": self.term_combo.currentText(),
            "operator": "and" if self.operator_combo.currentText() == "И" else "or"
        }

class RuleWidget(QWidget):
    """Виджет для редактирования правила"""

    def __init__(self, rule_config=None, available_vars=None, on_delete=None):
        super().__init__()
        self.rule_config = rule_config or {
            "if": [{"variable": "vibration", "term": "high"}],
            "then": "high"
        }
        self.available_vars = available_vars or ["vibration", "noise", "chemical", "health"]
        self.on_delete = on_delete
        self.condition_widgets = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)

        # Заголовок правила
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<b>ПРАВИЛО</b>"))
        header_layout.addStretch()

        # Кнопка удаления правила
        if self.on_delete:
            delete_btn = QPushButton("Удалить правило")
            delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
            delete_btn.clicked.connect(self.on_delete)
            header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # Условия
        conditions_group = QGroupBox("Условия (ЕСЛИ)")
        self.conditions_layout = QVBoxLayout()

        # Загружаем существующие условия
        for condition in self.rule_config['if']:
            self.add_condition_widget(condition)

        conditions_group.setLayout(self.conditions_layout)
        layout.addWidget(conditions_group)

        # Кнопка добавления условия
        add_condition_btn = QPushButton("+ Добавить условие")
        add_condition_btn.clicked.connect(self.add_condition)
        layout.addWidget(add_condition_btn)

        # Вывод
        then_group = QGroupBox("Вывод (ТО)")
        then_layout = QHBoxLayout()

        then_layout.addWidget(QLabel("Риск:"))
        self.then_combo = QComboBox()
        self.then_combo.addItems(["very_low", "low", "medium", "high", "very_high"])

        if 'then' in self.rule_config:
            index = self.then_combo.findText(self.rule_config['then'])
            if index >= 0:
                self.then_combo.setCurrentIndex(index)

        then_layout.addWidget(self.then_combo)
        then_layout.addStretch()
        then_group.setLayout(then_layout)
        layout.addWidget(then_group)

        self.setLayout(layout)

    def add_condition_widget(self, condition=None):
        """Добавление виджета условия"""
        condition_widget = RuleConditionWidget(
            condition,
            self.available_vars,
            on_delete=lambda: self.remove_condition_widget(condition_widget)
        )

        self.condition_widgets.append(condition_widget)
        self.conditions_layout.addWidget(condition_widget)

    def remove_condition_widget(self, widget):
        """Удаление условия"""
        self.condition_widgets.remove(widget)
        widget.setParent(None)
        widget.deleteLater()

    def add_condition(self):
        """Добавление нового условия"""
        self.add_condition_widget()

    def get_config(self):
        """Получение конфигурации правила"""
        conditions = []
        for i, widget in enumerate(self.condition_widgets):
            condition = widget.get_config()

            # Для первого условия убираем оператор
            if i == 0 and 'operator' in condition:
                del condition['operator']

            conditions.append(condition)

        return {
            "if": conditions,
            "then": self.then_combo.currentText()
        }

class ConfigEditor(QDialog):
    """Основной диалог редактора конфигурации"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or self.get_default_config()
        self.variable_widgets = {}
        self.rule_widgets = []
        self.setup_ui()
        self.load_config()

    def get_default_config(self):
        """Конфигурация по умолчанию"""
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
                }
            ]
        }

    def setup_ui(self):
        self.setWindowTitle("Редактор конфигурации нечеткой системы")
        self.setMinimumSize(900, 700)

        # Основной layout
        main_layout = QVBoxLayout()

        # Вкладки
        self.tab_widget = QTabWidget()

        # Вкладка переменных
        vars_tab = QWidget()
        vars_layout = QVBoxLayout(vars_tab)

        # Прокручиваемая область для переменных
        vars_scroll = QScrollArea()
        vars_scroll.setWidgetResizable(True)

        self.vars_container = QWidget()
        self.vars_layout = QVBoxLayout(self.vars_container)

        vars_scroll.setWidget(self.vars_container)
        vars_layout.addWidget(vars_scroll)

        # Кнопка добавления переменной
        add_var_btn = QPushButton("+ Добавить переменную")
        add_var_btn.clicked.connect(self.add_variable)
        vars_layout.addWidget(add_var_btn)

        self.tab_widget.addTab(vars_tab, "Переменные")

        # Вкладка правил
        rules_tab = QWidget()
        rules_layout = QVBoxLayout(rules_tab)

        # Прокручиваемая область для правил
        rules_scroll = QScrollArea()
        rules_scroll.setWidgetResizable(True)

        self.rules_container = QWidget()
        self.rules_layout = QVBoxLayout(self.rules_container)

        rules_scroll.setWidget(self.rules_container)
        rules_layout.addWidget(rules_scroll)

        # Кнопка добавления правила
        add_rule_btn = QPushButton("+ Добавить правило")
        add_rule_btn.clicked.connect(self.add_rule)
        rules_layout.addWidget(add_rule_btn)

        self.tab_widget.addTab(rules_tab, "Правила")

        main_layout.addWidget(self.tab_widget)

        # Кнопки сохранения/отмены
        button_box = QHBoxLayout()

        save_btn = QPushButton("Сохранить конфигурацию")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self.accept)

        save_as_btn = QPushButton("Сохранить в файл...")
        save_as_btn.clicked.connect(self.save_to_file)

        load_btn = QPushButton("Загрузить из файла...")
        load_btn.clicked.connect(self.load_from_file)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)

        button_box.addWidget(save_btn)
        button_box.addWidget(save_as_btn)
        button_box.addWidget(load_btn)
        button_box.addStretch()
        button_box.addWidget(cancel_btn)

        main_layout.addLayout(button_box)

        self.setLayout(main_layout)

    def load_config(self):
        """Загрузка конфигурации"""
        # Загружаем переменные
        variables = self.config.get('variables', {})
        for var_name, var_config in variables.items():
            self.add_variable_widget(var_name, var_config)

        # Загружаем правила
        rules = self.config.get('rules', [])
        for rule_config in rules:
            self.add_rule_widget(rule_config)

    def add_variable_widget(self, var_name, var_config=None):
        """Добавление виджета переменной"""
        if var_name in self.variable_widgets:
            return

        widget = VariableWidget(
            var_name,
            var_config,
            on_delete=lambda name: self.remove_variable_widget(name)
        )

        self.variable_widgets[var_name] = widget
        self.vars_layout.addWidget(widget)

    def remove_variable_widget(self, var_name):
        """Удаление переменной"""
        if var_name in self.variable_widgets:
            widget = self.variable_widgets.pop(var_name)
            widget.setParent(None)
            widget.deleteLater()

    def add_variable(self):
        """Добавление новой переменной"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Новая переменная")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Введите название переменной:"))

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("например: temperature, pressure")
        layout.addWidget(name_edit)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            var_name = name_edit.text().strip().lower()
            if var_name and var_name not in self.variable_widgets:
                self.add_variable_widget(var_name)

    def add_rule_widget(self, rule_config=None):
        """Добавление виджета правила"""
        available_vars = list(self.variable_widgets.keys())

        widget = RuleWidget(
            rule_config,
            available_vars,
            on_delete=lambda: self.remove_rule_widget(widget)
        )

        self.rule_widgets.append(widget)
        self.rules_layout.addWidget(widget)

    def remove_rule_widget(self, widget):
        """Удаление правила"""
        self.rule_widgets.remove(widget)
        widget.setParent(None)
        widget.deleteLater()

    def add_rule(self):
        """Добавление нового правила"""
        self.add_rule_widget()

    def save_to_file(self):
        """Сохранение в файл"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить конфигурацию", "fuzzy_config.json",
            "JSON файлы (*.json);;Все файлы (*.*)"
        )

        if file_path:
            try:
                config = self.get_current_config()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                QMessageBox.information(self, "Успех", f"Конфигурация сохранена в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")

    def load_from_file(self):
        """Загрузка из файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить конфигурацию", "",
            "JSON файлы (*.json);;Все файлы (*.*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)

                # Очищаем текущие виджеты
                for widget in list(self.variable_widgets.values()):
                    widget.setParent(None)
                    widget.deleteLater()
                self.variable_widgets.clear()

                for widget in self.rule_widgets:
                    widget.setParent(None)
                    widget.deleteLater()
                self.rule_widgets.clear()

                # Загружаем новую конфигурацию
                self.load_config()

                QMessageBox.information(self, "Успех", "Конфигурация загружена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {str(e)}")

    def get_current_config(self):
        """Получение текущей конфигурации"""
        # Собираем переменные
        variables = {}
        for var_name, widget in self.variable_widgets.items():
            variables[var_name] = widget.get_config()

        # Собираем правила
        rules = []
        for widget in self.rule_widgets:
            rules.append(widget.get_config())

        # Возвращаем полную конфигурацию
        return {
            "variables": variables,
            "output": self.config.get('output', {
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
            }),
            "rules": rules
        }