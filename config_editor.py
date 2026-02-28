import json

import numpy as np
import matplotlib

import skfuzzy as fuzz

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal, Qt

# Фиксированные имена переменных
INPUT_VARS = ["vibration", "noise", "chemical", "health"]
OUTPUT_VAR = "risk"

import os

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "configs/default_config.json")


class MplCanvas(FigureCanvas):
    """Виджет для отображения графиков matplotlib"""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)


class FunctionParamWidget(QWidget):
    """Виджет для ввода параметров функции"""

    def __init__(self, func_type="trimf", params=None):
        super().__init__()
        self.func_type = func_type
        self.params = params or self.get_default_params()
        self.setup_ui()

    def get_default_params(self):
        if self.func_type == 'trimf':
            return [0, 0, 0.5]
        elif self.func_type == 'trapmf':
            return [0, 0, 0.5, 0.5]
        elif self.func_type == 'gaussmf':
            return [0.5, 0.1]
        elif self.func_type == 'gbellmf':
            return [1, 2, 0.5]
        elif self.func_type == 'sigmf':
            return [10, 0.5]
        elif self.func_type == 'zmf':
            return [0.2, 0.8]
        elif self.func_type == 'smf':
            return [0.2, 0.8]
        elif self.func_type == 'pimf':
            return [0.2, 0.4, 0.6, 0.8]
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
        elif self.func_type == 'zmf':
            labels = ['a:', 'b:']
        elif self.func_type == 'smf':
            labels = ['a:', 'b:']
        elif self.func_type == 'pimf':
            labels = ['a:', 'b:', 'c:', 'd:']

        self.spin_boxes = []
        for i, label in enumerate(labels):
            layout.addWidget(QLabel(label))

            spin_box = QDoubleSpinBox()
            spin_box.setRange(0.001, 1.0)
            spin_box.setSingleStep(0.05)
            spin_box.setDecimals(3)
            spin_box.setValue(self.params[i] if i < len(self.params) else 0.5)
            spin_box.valueChanged.connect(lambda: self.term_changed.emit() if hasattr(self, 'term_changed') else None)

            self.spin_boxes.append(spin_box)
            layout.addWidget(spin_box)

        layout.addStretch()
        self.setLayout(layout)

    def get_params(self):
        """Получение параметров"""
        return [sb.value() for sb in self.spin_boxes]


class ClickableLabel(QLabel):
    """Кликабельный label для переименования терма"""
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)


class TermWidget(QWidget):
    """Виджет для редактирования одного терма"""

    term_changed = pyqtSignal()
    term_renamed = pyqtSignal(str, str)  # старое имя, новое имя

    def __init__(self, term_name="", term_config=None, on_delete=None):
        super().__init__()
        self.term_name = term_name
        self.term_config = term_config or {"type": "trimf", "params": [0, 0, 0.5]}
        self.on_delete = on_delete
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        # Заголовок с кликабельным label
        header_layout = QHBoxLayout()

        # Используем кликабельный label для названия терма
        self.name_label = ClickableLabel(f"<b>{self.term_name}</b>")
        self.name_label.setToolTip("Дважды кликните чтобы переименовать")
        self.name_label.doubleClicked.connect(self.rename_term)
        header_layout.addWidget(self.name_label)

        header_layout.addStretch()

        # Кнопка удаления
        if self.on_delete:
            delete_btn = QPushButton("×")
            delete_btn.setMaximumWidth(30)
            delete_btn.setToolTip("Удалить терм")
            delete_btn.clicked.connect(lambda: self.on_delete(self.term_name))
            header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        # Выбор типа функции
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Тип:"))

        self.func_combo = QComboBox()
        self.func_combo.addItems(["trimf", "trapmf", "gaussmf", "gbellmf", "sigmf", "zmf", "smf", "pimf"])

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
        # Добавляем сигнал для отслеживания изменений параметров
        self.param_widget.term_changed = self.term_changed
        layout.addWidget(self.param_widget)

        # Обновляем параметры при изменении типа функции
        self.func_combo.currentTextChanged.connect(self.update_params_widget)
        self.func_combo.currentTextChanged.connect(lambda: self.term_changed.emit())

        self.setLayout(layout)

    def rename_term(self):
        """Переименование терма"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Переименование терма")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Введите новое название терма:"))

        name_edit = QLineEdit()
        name_edit.setText(self.term_name)
        name_edit.selectAll()
        layout.addWidget(name_edit)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_name = name_edit.text().strip()
            if new_name and new_name != self.term_name:
                old_name = self.term_name
                self.term_name = new_name
                self.name_label.setText(f"<b>{new_name}</b>")
                self.term_renamed.emit(old_name, new_name)

    def update_params_widget(self, func_type):
        """Обновление виджета параметров"""
        # Удаляем старый виджет
        self.layout().removeWidget(self.param_widget)
        self.param_widget.deleteLater()

        # Создаем новый
        self.param_widget = FunctionParamWidget(func_type)
        self.param_widget.term_changed = self.term_changed
        self.layout().addWidget(self.param_widget)

        self.term_changed.emit()

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


class VariableEditPanel(QWidget):
    """Панель редактирования входной переменной с комбобоксом выбора"""

    variable_changed = pyqtSignal(str)  # имя переменной
    terms_changed = pyqtSignal(str)  # имя переменной

    def __init__(self, variable_widgets):
        super().__init__()
        self.variable_widgets = variable_widgets
        self.current_var = "vibration"
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Выбор переменной
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Переменная:"))

        self.var_combo = QComboBox()
        var_display_names = {
            "vibration": "Вибрация",
            "noise": "Шум",
            "chemical": "Химический фактор",
            "health": "Здоровье"
        }

        for var in INPUT_VARS:
            self.var_combo.addItem(var_display_names.get(var, var), var)

        self.var_combo.currentIndexChanged.connect(self.on_variable_changed)
        selector_layout.addWidget(self.var_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)

        # Область прокрутки для виджета переменной
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Контейнер для виджета переменной
        self.variable_container = QWidget()
        self.container_layout = QVBoxLayout(self.variable_container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area.setWidget(self.variable_container)
        layout.addWidget(self.scroll_area)

        self.setLayout(layout)

        # Показываем первую переменную
        self.show_variable("vibration")

    def on_variable_changed(self):
        """Обработка смены переменной в комбобоксе"""
        var_name = self.var_combo.currentData()
        self.show_variable(var_name)
        self.variable_changed.emit(var_name)

    def show_variable(self, var_name):
        """Отображение виджета выбранной переменной"""
        # Очищаем контейнер
        for i in reversed(range(self.container_layout.count())):
            widget = self.container_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Добавляем виджет выбранной переменной
        if var_name in self.variable_widgets:
            widget = self.variable_widgets[var_name]
            self.container_layout.addWidget(widget)
            self.current_var = var_name

    def update_current_variable(self):
        """Обновление отображения текущей переменной"""
        self.show_variable(self.current_var)

    def get_current_var_name(self):
        """Получение имени текущей переменной"""
        return self.current_var


class VariableWidget(QWidget):
    """Виджет для редактирования одной переменной"""

    terms_changed = pyqtSignal(str)  # имя переменной

    def __init__(self, var_name="", var_config=None):
        super().__init__()
        self.var_name = var_name
        # Игнорируем range в конфиге, используем фиксированный
        self.var_config = var_config or {
            "terms": {}
        }
        self.term_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Список термов
        terms_group = QGroupBox("Термы")
        self.terms_layout = QVBoxLayout()
        self.terms_layout.setContentsMargins(10, 10, 10, 10)
        self.terms_layout.setSpacing(5)

        # Загружаем существующие термы
        for term_name, term_config in self.var_config.get('terms', {}).items():
            self.add_term_widget(term_name, term_config)

        # Добавляем stretch чтобы элементы не растягивались
        self.terms_layout.addStretch()

        terms_group.setLayout(self.terms_layout)
        layout.addWidget(terms_group)

        # Кнопка добавления терма
        add_term_btn = QPushButton("+ Добавить терм")
        add_term_btn.setToolTip("Добавить новый терм")
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

        term_widget.term_changed.connect(lambda: self.terms_changed.emit(self.var_name))
        term_widget.term_renamed.connect(lambda old_name, new_name: self.rename_term(old_name, new_name))

        self.term_widgets[term_name] = term_widget

        # Вставляем перед stretch
        self.terms_layout.insertWidget(self.terms_layout.count() - 1, term_widget)
        self.terms_changed.emit(self.var_name)

    def remove_term_widget(self, term_name):
        """Удаление терма"""
        if term_name in self.term_widgets:
            widget = self.term_widgets.pop(term_name)
            widget.setParent(None)
            widget.deleteLater()
            self.terms_changed.emit(self.var_name)

    def rename_term(self, old_name, new_name):
        """Переименование терма"""
        if old_name in self.term_widgets:
            # Обновляем словарь
            self.term_widgets[new_name] = self.term_widgets.pop(old_name)
            self.terms_changed.emit(self.var_name)

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
        """Получение конфигурации переменной (без range)"""
        terms = {}
        for term_name, widget in self.term_widgets.items():
            terms[term_name] = widget.get_config()

        return {
            "terms": terms
        }

    def get_term_names(self):
        """Получение списка имен термов"""
        return list(self.term_widgets.keys())

    def get_range(self):
        """Получение диапазона переменной"""
        return [0, 1, 0.01]

    def get_term_configs(self):
        """Получение конфигураций всех термов"""
        return {name: widget.get_config() for name, widget in self.term_widgets.items()}


class RuleConditionWidget(QWidget):
    """Виджет для одного условия правила"""

    def __init__(self, condition=None, variable_terms=None, on_delete=None):
        super().__init__()
        self.condition = condition or {"variable": "vibration", "term": "low"}
        self.variable_terms = variable_terms or {}
        self.on_delete = on_delete
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Выбор переменной (фиксированный список)
        self.var_combo = QComboBox()

        # Русские названия для отображения
        var_display_names = {
            "vibration": "Вибрация",
            "noise": "Шум",
            "chemical": "Хим. фактор",
            "health": "Здоровье"
        }

        for var in INPUT_VARS:
            self.var_combo.addItem(var_display_names.get(var, var), var)

        if 'variable' in self.condition:
            index = self.var_combo.findData(self.condition['variable'])
            if index >= 0:
                self.var_combo.setCurrentIndex(index)

        layout.addWidget(self.var_combo)

        # Выбор терма
        self.term_combo = QComboBox()
        self.update_terms()
        self.var_combo.currentIndexChanged.connect(self.update_terms)

        if 'term' in self.condition:
            index = self.term_combo.findText(self.condition['term'])
            if index >= 0:
                self.term_combo.setCurrentIndex(index)

        layout.addWidget(self.term_combo)

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
        """Обновление списка термов на основе выбранной переменной"""
        variable = self.var_combo.currentData()
        self.term_combo.clear()

        if variable in self.variable_terms:
            self.term_combo.addItems(self.variable_terms[variable])

    def update_terms_from_config(self, variable_terms):
        """Обновление списка термов из конфигурации"""
        self.variable_terms = variable_terms
        self.update_terms()

    def get_config(self):
        """Получение конфигурации условия"""
        return {
            "variable": self.var_combo.currentData(),
            "term": self.term_combo.currentText(),
            "operator": "and" if self.operator_combo.currentText() == "И" else "or"
        }


class RuleWidget(QWidget):
    """Виджет для редактирования правила"""

    def __init__(self, rule_config=None, variable_terms=None, on_delete=None):
        super().__init__()
        self.rule_config = rule_config or {
            "if": [{"variable": "vibration", "term": "high"}],
            "then": "high"
        }
        self.variable_terms = variable_terms or {}
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

        # Добавляем термы выходной переменной, если они есть
        if OUTPUT_VAR in self.variable_terms:
            self.then_combo.addItems(self.variable_terms[OUTPUT_VAR])

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
            self.variable_terms,
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

    def update_terms(self, variable_terms):
        """Обновление списков термов во всех условиях"""
        self.variable_terms = variable_terms

        # Обновляем условия
        for widget in self.condition_widgets:
            widget.update_terms_from_config(variable_terms)

        # Обновляем вывод
        self.then_combo.clear()
        if OUTPUT_VAR in variable_terms:
            self.then_combo.addItems(variable_terms[OUTPUT_VAR])
            # Пытаемся восстановить выбранное значение
            current_then = self.rule_config.get('then', '')
            if current_then in variable_terms[OUTPUT_VAR]:
                self.then_combo.setCurrentText(current_then)

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


class OutputVariableWidget(QWidget):
    """Виджет для редактирования выходной переменной"""

    terms_changed = pyqtSignal()

    def __init__(self, var_name=OUTPUT_VAR, var_config=None):
        super().__init__()
        self.var_name = var_name
        self.var_config = var_config or {
            "terms": {
                "very_low": {"type": "trimf", "params": [0, 0, 0.25]},
                "low": {"type": "trimf", "params": [0, 0.25, 0.5]},
                "medium": {"type": "trimf", "params": [0.25, 0.5, 0.75]},
                "high": {"type": "trimf", "params": [0.5, 0.75, 1]},
                "very_high": {"type": "trimf", "params": [0.75, 1, 1]}
            }
        }
        self.term_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        # Основной layout без прокрутки - он будет внутри scroll_area
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Список термов
        terms_group = QGroupBox("Термы")
        self.terms_layout = QVBoxLayout()
        self.terms_layout.setContentsMargins(10, 10, 10, 10)
        self.terms_layout.setSpacing(5)

        # Загружаем существующие термы
        for term_name, term_config in self.var_config['terms'].items():
            self.add_term_widget(term_name, term_config)

        # Добавляем stretch чтобы элементы не растягивались
        self.terms_layout.addStretch()

        terms_group.setLayout(self.terms_layout)
        main_layout.addWidget(terms_group)

        # Кнопка добавления терма
        add_term_btn = QPushButton("+ Добавить терм")
        add_term_btn.setToolTip("Добавить новый терм")
        add_term_btn.clicked.connect(self.add_term)
        main_layout.addWidget(add_term_btn)

        self.setLayout(main_layout)

    def add_term_widget(self, term_name, term_config=None):
        """Добавление виджета терма"""
        if term_name in self.term_widgets:
            return

        term_widget = TermWidget(
            term_name,
            term_config,
            on_delete=self.remove_term_widget
        )

        term_widget.term_changed.connect(lambda: self.terms_changed.emit())
        term_widget.term_renamed.connect(lambda old_name, new_name: self.rename_term(old_name, new_name))

        self.term_widgets[term_name] = term_widget

        # Вставляем перед stretch
        self.terms_layout.insertWidget(self.terms_layout.count() - 1, term_widget)
        self.terms_changed.emit()

    def remove_term_widget(self, term_name):
        """Удаление терма"""
        if term_name in self.term_widgets:
            widget = self.term_widgets.pop(term_name)
            widget.setParent(None)
            widget.deleteLater()
            self.terms_changed.emit()

    def rename_term(self, old_name, new_name):
        """Переименование терма"""
        if old_name in self.term_widgets:
            # Обновляем словарь
            self.term_widgets[new_name] = self.term_widgets.pop(old_name)
            self.terms_changed.emit()

    def add_term(self):
        """Добавление нового терма"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Новый терм")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Введите название терма:"))

        name_edit = QLineEdit()
        name_edit.setPlaceholderText("например: очень_низкий, низкий, средний")
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
        """Получение конфигурации выходной переменной"""
        terms = {}
        for term_name, widget in self.term_widgets.items():
            terms[term_name] = widget.get_config()

        return {
            "terms": terms
        }

    def get_term_names(self):
        """Получение списка имен термов"""
        return list(self.term_widgets.keys())

    def get_range(self):
        """Получение диапазона переменной"""
        return [0, 1, 0.01]

    def get_term_configs(self):
        """Получение конфигураций всех термов"""
        return {name: widget.get_config() for name, widget in self.term_widgets.items()}


class OutputVariableScrollPanel(QWidget):
    """Панель с прокруткой для выходной переменной"""

    def __init__(self, output_widget):
        super().__init__()
        self.output_widget = output_widget
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Область прокрутки
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Контейнер для виджета выходной переменной
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.addWidget(self.output_widget)

        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)

        self.setLayout(layout)


class MembershipFunctionVisualizer(QWidget):
    """Виджет для визуализации функций принадлежности"""

    def __init__(self):
        super().__init__()
        self.current_var_name = None
        self.current_var_type = "input"  # "input" или "output"
        self.var_range = [0, 1, 0.01]
        self.terms = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # График
        self.canvas = MplCanvas(self, width=6, height=4, dpi=100)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

        # Изначально пустой график
        self.clear_display()

    def update_display(self, var_name, var_type, var_range, terms):
        """Обновление отображения графика"""
        self.current_var_name = var_name
        self.current_var_type = var_type
        self.var_range = var_range
        self.terms = terms

        # Очищаем график
        self.canvas.axes.clear()

        if not terms:
            self.canvas.axes.text(0.5, 0.5, "Нет термов для отображения",
                                  horizontalalignment='center',
                                  verticalalignment='center',
                                  transform=self.canvas.axes.transAxes,
                                  fontsize=12)
            self.canvas.axes.set_xlabel("Значение")
            self.canvas.axes.set_ylabel("Степень принадлежности")
            self.canvas.axes.set_xlim(0, 1)
            self.canvas.axes.set_ylim(0, 1.05)
            self.canvas.draw()
            return

        # Создаем универсум (0-1 с шагом 0.01)
        universe = np.arange(0, 1.01, 0.01)

        # Определяем цвета для разных термов
        colors = plt.cm.tab10(np.linspace(0, 1, len(terms)))

        lines_count = 0
        # Отображаем каждый терм
        for i, (term_name, term_config) in enumerate(terms.items()):
            term_type = term_config.get('type', 'trimf')
            params = term_config.get('params', [])

            # Проверяем, что параметры корректны
            if not params:
                continue

                # Вычисляем значения функции принадлежности
            try:
                if term_type == 'trimf':
                    mf_values = fuzz.trimf(universe, params)
                elif term_type == 'trapmf':
                    mf_values = fuzz.trapmf(universe, params)
                elif term_type == 'gaussmf':
                    mf_values = fuzz.gaussmf(universe, *params)
                elif term_type == 'gbellmf':
                    mf_values = fuzz.gbellmf(universe, *params)
                elif term_type == 'sigmf':
                    mf_values = fuzz.sigmf(universe, *params)
                elif term_type == 'zmf':
                    mf_values = fuzz.zmf(universe, *params)
                elif term_type == 'smf':
                    mf_values = fuzz.smf(universe, *params)
                elif term_type == 'pimf':
                    mf_values = fuzz.pimf(universe, *params)
                else:
                    continue

                # Рисуем график
                self.canvas.axes.plot(universe, mf_values,
                                      color=colors[i % len(colors)],
                                      linewidth=2,
                                      label=term_name)
                lines_count += 1
            except Exception as e:
                print(f"Ошибка при отображении терма {term_name}: {e}")
                continue

        # Настройка графика
        var_display_names = {
            "vibration": "Вибрация",
            "noise": "Шум",
            "chemical": "Химический фактор",
            "health": "Здоровье",
            "risk": "Риск"
        }

        display_name = var_display_names.get(var_name, var_name)
        self.canvas.axes.set_title(f"{display_name}", fontsize=12)
        self.canvas.axes.set_xlabel("Значение", fontsize=10)
        self.canvas.axes.set_ylabel("Степень принадлежности", fontsize=10)
        self.canvas.axes.set_xlim(0, 1)
        self.canvas.axes.set_ylim(0, 1.05)
        self.canvas.axes.grid(True, alpha=0.3, linestyle='--')

        # Добавляем легенду только если есть линии
        if lines_count > 0:
            self.canvas.axes.legend(loc='best', fontsize=9)

        self.canvas.draw()

    def clear_display(self):
        """Очистка графика"""
        self.canvas.axes.clear()
        self.canvas.axes.text(0.5, 0.5, "Выберите переменную для просмотра",
                              horizontalalignment='center',
                              verticalalignment='center',
                              transform=self.canvas.axes.transAxes,
                              fontsize=12)
        self.canvas.axes.set_xlabel("Значение", fontsize=10)
        self.canvas.axes.set_ylabel("Степень принадлежности", fontsize=10)
        self.canvas.axes.set_xlim(0, 1)
        self.canvas.axes.set_ylim(0, 1.05)
        self.canvas.draw()


def get_default_config():
    """Получение конфигурации по умолчанию из внешнего JSON-файла"""
    try:
        with open(DEFAULT_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Если файл не найден, создаем его с конфигурацией по умолчанию
        default_config = {
            "variables": {
                "vibration": {
                    "terms": {
                        "low": {"type": "trimf", "params": [0, 0, 0.5]},
                        "medium": {"type": "trimf", "params": [0, 0.5, 1]},
                        "high": {"type": "trimf", "params": [0.5, 1, 1]}
                    }
                },
                "noise": {
                    "terms": {
                        "low": {"type": "trimf", "params": [0, 0, 0.5]},
                        "medium": {"type": "trimf", "params": [0, 0.5, 1]},
                        "high": {"type": "trimf", "params": [0.5, 1, 1]}
                    }
                },
                "chemical": {
                    "terms": {
                        "low": {"type": "trimf", "params": [0, 0, 0.4]},
                        "medium": {"type": "trimf", "params": [0, 0.4, 0.8]},
                        "high": {"type": "trimf", "params": [0.4, 0.8, 1]}
                    }
                },
                "health": {
                    "terms": {
                        "bad": {"type": "trimf", "params": [0, 0, 0.5]},
                        "average": {"type": "trimf", "params": [0, 0.5, 1]},
                        "good": {"type": "trimf", "params": [0.5, 1, 1]}
                    }
                }
            },
            "output": {
                "risk": {
                    "terms": {
                        "very_low": {"type": "trimf", "params": [0, 0, 0.25]},
                        "low": {"type": "trimf", "params": [0, 0.25, 0.5]},
                        "medium": {"type": "trimf", "params": [0.25, 0.5, 0.75]},
                        "high": {"type": "trimf", "params": [0.5, 0.75, 1]},
                        "very_high": {"type": "trimf", "params": [0.75, 1, 1]}
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

        # Сохраняем конфигурацию в файл
        try:
            print("Saving json...")
            os.makedirs(os.path.dirname(DEFAULT_CONFIG_PATH), exist_ok=True)
            with open(DEFAULT_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Не удалось создать файл конфигурации по умолчанию: {e}")

        return default_config
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации по умолчанию: {e}")
        # Возвращаем минимальную конфигурацию в случае ошибки
        return {
            "variables": {var: {"terms": {}} for var in INPUT_VARS},
            "output": {OUTPUT_VAR: {"terms": {}}},
            "rules": []
        }


class ConfigEditor(QDialog):
    """Основной диалог редактора конфигурации"""

    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or get_default_config()
        self.variable_widgets = {}
        self.output_widget = None
        self.rule_widgets = []
        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        self.setWindowTitle("Редактор конфигурации нечеткой системы")
        self.setMinimumSize(1200, 800)

        # Основной layout
        main_layout = QVBoxLayout()

        # Вкладки
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Вкладка входных переменных
        vars_tab = QWidget()
        vars_layout = QHBoxLayout(vars_tab)
        vars_layout.setContentsMargins(5, 5, 5, 5)
        vars_layout.setSpacing(10)

        # Левая часть - панель редактирования с комбобоксом
        self.vars_edit_panel = QWidget()
        self.vars_edit_panel.setMinimumWidth(400)
        self.vars_edit_layout = QVBoxLayout(self.vars_edit_panel)
        self.vars_edit_layout.setContentsMargins(0, 0, 0, 0)

        # Правая часть - визуализация
        self.vars_viz_panel = QWidget()
        self.vars_viz_layout = QVBoxLayout(self.vars_viz_panel)
        self.vars_viz_layout.setContentsMargins(0, 0, 0, 0)

        # Создаем визуализатор для входных переменных
        self.input_visualizer = MembershipFunctionVisualizer()
        self.vars_viz_layout.addWidget(self.input_visualizer)

        # Добавляем панели на вкладку
        vars_layout.addWidget(self.vars_edit_panel)
        vars_layout.addWidget(self.vars_viz_panel, 1)

        self.tab_widget.addTab(vars_tab, "Входные переменные")

        # Вкладка выходной переменной
        output_tab = QWidget()
        output_layout = QHBoxLayout(output_tab)
        output_layout.setContentsMargins(5, 5, 5, 5)
        output_layout.setSpacing(10)

        # Левая часть - панель редактирования выходной переменной
        self.output_edit_panel = QWidget()
        self.output_edit_panel.setMinimumWidth(400)
        self.output_edit_layout = QVBoxLayout(self.output_edit_panel)
        self.output_edit_layout.setContentsMargins(0, 0, 0, 0)

        # Правая часть - визуализация
        self.output_viz_panel = QWidget()
        self.output_viz_layout = QVBoxLayout(self.output_viz_panel)
        self.output_viz_layout.setContentsMargins(0, 0, 0, 0)

        # Создаем визуализатор для выходной переменной
        self.output_visualizer = MembershipFunctionVisualizer()
        self.output_viz_layout.addWidget(self.output_visualizer)

        # Добавляем панели на вкладку
        output_layout.addWidget(self.output_edit_panel)
        output_layout.addWidget(self.output_viz_panel, 1)

        self.tab_widget.addTab(output_tab, "Выходная переменная")

        # Вкладка правил
        rules_tab = QWidget()
        rules_layout = QVBoxLayout(rules_tab)
        rules_layout.setContentsMargins(5, 5, 5, 5)

        # Прокручиваемая область для правил
        rules_scroll = QScrollArea()
        rules_scroll.setWidgetResizable(True)
        rules_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.rules_container = QWidget()
        self.rules_layout = QVBoxLayout(self.rules_container)
        self.rules_layout.setContentsMargins(0, 0, 0, 0)

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
        button_box.setContentsMargins(5, 5, 5, 5)

        save_btn = QPushButton("Сохранить")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        save_btn.clicked.connect(self.accept)

        save_as_btn = QPushButton("Сохранить как...")
        save_as_btn.clicked.connect(self.save_to_file)

        load_btn = QPushButton("Загрузить...")
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
        # Создаем виджеты входных переменных
        variables = self.config.get('variables', {})
        for var_name in INPUT_VARS:
            var_config = variables.get(var_name, {"terms": {}})
            self.add_variable_widget(var_name, var_config)

        # Создаем панель редактирования входных переменных с комбобоксом
        self.vars_edit_panel_widget = VariableEditPanel(self.variable_widgets)
        self.vars_edit_panel_widget.variable_changed.connect(self.on_input_variable_changed)
        self.vars_edit_layout.addWidget(self.vars_edit_panel_widget)

        # Загружаем выходную переменную
        output_config = self.config.get('output', {})
        output_var_config = output_config.get(OUTPUT_VAR, {"terms": {}})
        self.add_output_widget(OUTPUT_VAR, output_var_config)

        # Добавляем виджет выходной переменной в панель редактирования с прокруткой
        if self.output_widget:
            self.output_scroll_panel = OutputVariableScrollPanel(self.output_widget)
            self.output_edit_layout.addWidget(self.output_scroll_panel)

        # Загружаем правила
        rules = self.config.get('rules', [])
        for rule_config in rules:
            self.add_rule_widget(rule_config)

        # Обновляем визуализацию для первой входной переменной
        self.update_input_visualization("vibration")
        # Обновляем визуализацию для выходной переменной
        self.update_output_visualization()

    def add_variable_widget(self, var_name, var_config=None):
        """Добавление виджета входной переменной"""
        if var_name in self.variable_widgets:
            return

        widget = VariableWidget(var_name, var_config)
        widget.terms_changed.connect(self.update_rules_terms)
        widget.terms_changed.connect(lambda name: self.on_input_variable_changed(name))

        self.variable_widgets[var_name] = widget

    def add_output_widget(self, var_name, var_config=None):
        """Добавление виджета выходной переменной"""
        self.output_widget = OutputVariableWidget(var_name, var_config)
        self.output_widget.terms_changed.connect(self.update_rules_terms)
        self.output_widget.terms_changed.connect(self.update_output_visualization)

    def on_input_variable_changed(self, var_name):
        """Обработка изменения входной переменной"""
        self.update_input_visualization(var_name)
        self.update_rules_terms()

    def update_input_visualization(self, var_name):
        """Обновление визуализации для входной переменной"""
        if var_name in self.variable_widgets:
            widget = self.variable_widgets[var_name]
            var_range = widget.get_range()
            terms = widget.get_term_configs()
            self.input_visualizer.update_display(var_name, "input", var_range, terms)

    def update_output_visualization(self):
        """Обновление визуализации для выходной переменной"""
        if self.output_widget:
            var_range = self.output_widget.get_range()
            terms = self.output_widget.get_term_configs()
            self.output_visualizer.update_display(OUTPUT_VAR, "output", var_range, terms)

    def on_tab_changed(self, index):
        """Обработка смены вкладки"""
        if index == 0:
            if hasattr(self, 'vars_edit_panel_widget'):
                current_var = self.vars_edit_panel_widget.get_current_var_name()
                self.update_input_visualization(current_var)
        elif index == 1:
            self.update_output_visualization()

    def update_rules_terms(self):
        """Обновление списков термов во всех правилах"""
        variable_terms = {}

        for var_name, widget in self.variable_widgets.items():
            variable_terms[var_name] = widget.get_term_names()

        if self.output_widget:
            variable_terms[OUTPUT_VAR] = self.output_widget.get_term_names()

        for rule_widget in self.rule_widgets:
            rule_widget.update_terms(variable_terms)

    def add_rule_widget(self, rule_config=None):
        """Добавление виджета правила"""
        variable_terms = {}
        for var_name, widget in self.variable_widgets.items():
            variable_terms[var_name] = widget.get_term_names()

        if self.output_widget:
            variable_terms[OUTPUT_VAR] = self.output_widget.get_term_names()

        widget = RuleWidget(
            rule_config,
            variable_terms,
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

                if self.output_widget:
                    self.output_widget.setParent(None)
                    self.output_widget.deleteLater()
                    self.output_widget = None

                for widget in self.rule_widgets:
                    widget.setParent(None)
                    widget.deleteLater()
                self.rule_widgets.clear()

                # Очищаем панели редактирования
                if hasattr(self, 'vars_edit_layout'):
                    for i in reversed(range(self.vars_edit_layout.count())):
                        widget = self.vars_edit_layout.itemAt(i).widget()
                        if widget:
                            widget.setParent(None)

                if hasattr(self, 'output_edit_layout'):
                    for i in reversed(range(self.output_edit_layout.count())):
                        widget = self.output_edit_layout.itemAt(i).widget()
                        if widget:
                            widget.setParent(None)

                # Загружаем новую конфигурацию
                self.load_config()

                QMessageBox.information(self, "Успех", "Конфигурация загружена")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {str(e)}")

    def get_current_config(self):
        """Получение текущей конфигурации"""
        variables = {}
        for var_name, widget in self.variable_widgets.items():
            variables[var_name] = widget.get_config()

        output = {}
        if self.output_widget:
            output[OUTPUT_VAR] = self.output_widget.get_config()

        rules = []
        for widget in self.rule_widgets:
            rules.append(widget.get_config())

        return {
            "variables": variables,
            "output": output,
            "rules": rules
        }