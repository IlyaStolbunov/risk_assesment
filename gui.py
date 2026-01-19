import os
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from employee_manager import EmployeeManager
from health_calculator import HealthCalculator
from fuzzy_system import FuzzyRiskSystem
from config_loader import ConfigLoader


class ConfigInfoDialog(QDialog):
    """Диалог отображения информации о конфигурации"""

    def __init__(self, parent=None, config_info=""):
        super().__init__(parent)
        self.setup_ui(config_info)

    def setup_ui(self, config_info):
        self.setWindowTitle("Информация о конфигурации")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout()

        # Текстовое поле с информацией
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setFont(QFont("Courier New", 10))
        self.info_text.setText(config_info)

        layout.addWidget(self.info_text)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

class EmployeeTableModel(QAbstractTableModel):
    """Модель таблицы для отображения работников с диагнозами"""

    def __init__(self, employees):
        super().__init__()
        self.employees = employees
        self.headers = ['ID', 'ФИО', 'Должность', 'Пол', 'Здоровье',
                       'Проф.вредность', 'ЖКТ', 'Зрение', 'ЛОР', 'ССЗ', 'Инвалидность']

    def rowCount(self, parent=None):
        return len(self.employees)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        employee = self.employees[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return str(employee.id)
            elif col == 1:
                return employee.full_name
            elif col == 2:
                return employee.position
            elif col == 3:
                return employee.gender
            elif col == 4:
                score = HealthCalculator.calculate_health_score(employee)
                desc = HealthCalculator.get_health_description(score)
                return f"{score:.2f} ({desc})"
            elif col == 5:
                return "✓" if employee.diagnoses.get('professional', False) else ""
            elif col == 6:
                return "✓" if employee.diagnoses.get('gastro', False) else ""
            elif col == 7:
                return "✓" if employee.diagnoses.get('vision', False) else ""
            elif col == 8:
                return "✓" if employee.diagnoses.get('ent', False) else ""
            elif col == 9:
                return "✓" if employee.diagnoses.get('cardio', False) else ""
            elif col == 10:
                return "✓" if employee.disability else ""

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignCenter

        elif role == Qt.ItemDataRole.FontRole:
            # Жирный шрифт для диагнозов
            if 5 <= col <= 10:
                font = QFont()
                font.setBold(True)
                return font

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None


class AddEditEmployeeDialog(QDialog):
    """Диалог добавления/редактирования работника"""

    def __init__(self, parent=None, employee=None):
        super().__init__(parent)
        self.employee = employee
        self.setup_ui()

        if employee:
            self.load_employee_data()

    def setup_ui(self):
        self.setWindowTitle("Добавить работника" if not self.employee else "Редактировать работника")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Поля ввода
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        form_layout.addRow("ФИО:", self.name_edit)

        self.position_edit = QLineEdit()
        form_layout.addRow("Должность:", self.position_edit)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["М", "Ж"])
        form_layout.addRow("Пол:", self.gender_combo)

        layout.addLayout(form_layout)

        # Диагнозы
        layout.addWidget(QLabel("Диагнозы:"))

        self.diagnoses_group = QGroupBox()
        diagnoses_layout = QVBoxLayout()

        self.prof_check = QCheckBox("Профессиональная вредность")
        self.gastro_check = QCheckBox("Заболевания ЖКТ")
        self.vision_check = QCheckBox("Проблемы со зрением")
        self.ent_check = QCheckBox("ЛОР заболевания")
        self.cardio_check = QCheckBox("Сердечно-сосудистые заболевания")

        diagnoses_layout.addWidget(self.prof_check)
        diagnoses_layout.addWidget(self.gastro_check)
        diagnoses_layout.addWidget(self.vision_check)
        diagnoses_layout.addWidget(self.ent_check)
        diagnoses_layout.addWidget(self.cardio_check)

        self.diagnoses_group.setLayout(diagnoses_layout)
        layout.addWidget(self.diagnoses_group)

        # Инвалидность
        self.disability_check = QCheckBox("Инвалидность")
        layout.addWidget(self.disability_check)

        # Кнопки
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_employee_data(self):
        """Загрузка данных работника в форму"""
        if not self.employee:
            return

        self.name_edit.setText(self.employee.full_name)
        self.position_edit.setText(self.employee.position)

        index = self.gender_combo.findText(self.employee.gender)
        if index >= 0:
            self.gender_combo.setCurrentIndex(index)

        self.prof_check.setChecked(self.employee.diagnoses.get('professional', False))
        self.gastro_check.setChecked(self.employee.diagnoses.get('gastro', False))
        self.vision_check.setChecked(self.employee.diagnoses.get('vision', False))
        self.ent_check.setChecked(self.employee.diagnoses.get('ent', False))
        self.cardio_check.setChecked(self.employee.diagnoses.get('cardio', False))
        self.disability_check.setChecked(self.employee.disability)

    def get_employee_data(self):
        """Получение данных из формы"""
        diagnoses = {
            'professional': self.prof_check.isChecked(),
            'gastro': self.gastro_check.isChecked(),
            'vision': self.vision_check.isChecked(),
            'ent': self.ent_check.isChecked(),
            'cardio': self.cardio_check.isChecked()
        }

        return {
            'full_name': self.name_edit.text().strip(),
            'position': self.position_edit.text().strip(),
            'gender': self.gender_combo.currentText(),
            'diagnoses': diagnoses,
            'disability': self.disability_check.isChecked()
        }


class RiskCalculatorDialog(QDialog):
    """Диалог расчета риска (обновлен для работы с конфигурируемой системой)"""

    def __init__(self, parent=None, employee=None, fuzzy_system=None):
        super().__init__(parent)
        self.employee = employee

        # Используем переданную систему или создаем новую
        if fuzzy_system:
            self.fuzzy_system = fuzzy_system
        else:
            self.fuzzy_system = FuzzyRiskSystem()

        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"Расчет риска для {self.employee.full_name}")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Информация о работнике
        info_group = QGroupBox("Информация о работнике")
        info_layout = QFormLayout()

        health_score = HealthCalculator.calculate_health_score(self.employee)
        health_desc = HealthCalculator.get_health_description(health_score)

        info_layout.addRow("ФИО:", QLabel(self.employee.full_name))
        info_layout.addRow("Должность:", QLabel(self.employee.position))
        info_layout.addRow("Показатель здоровья:",
                           QLabel(f"{health_score:.2f} ({health_desc})"))

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Параметры риска
        params_group = QGroupBox("Параметры рабочей среды")
        params_layout = QFormLayout()

        # Вибрация
        self.vibration_slider = QSlider(Qt.Orientation.Horizontal)
        self.vibration_slider.setRange(0, 100)
        self.vibration_slider.setValue(50)
        self.vibration_label = QLabel("5.0")
        self.vibration_value_edit = QLineEdit("5.0")
        self.vibration_value_edit.setMaximumWidth(60)
        self.vibration_value_edit.textChanged.connect(
            lambda: self.update_slider_from_edit(self.vibration_slider,
                                                 self.vibration_value_edit, 0, 10))

        vibration_layout = QHBoxLayout()
        vibration_layout.addWidget(self.vibration_slider)
        vibration_layout.addWidget(self.vibration_value_edit)
        params_layout.addRow("Вибрация (0-10):", vibration_layout)

        # Шум
        self.noise_slider = QSlider(Qt.Orientation.Horizontal)
        self.noise_slider.setRange(0, 100)
        self.noise_slider.setValue(30)
        self.noise_value_edit = QLineEdit("3.0")
        self.noise_value_edit.setMaximumWidth(60)
        self.noise_value_edit.textChanged.connect(
            lambda: self.update_slider_from_edit(self.noise_slider,
                                                 self.noise_value_edit, 0, 10))

        noise_layout = QHBoxLayout()
        noise_layout.addWidget(self.noise_slider)
        noise_layout.addWidget(self.noise_value_edit)
        params_layout.addRow("Шум (0-10):", noise_layout)

        # Химический фактор
        self.chemical_slider = QSlider(Qt.Orientation.Horizontal)
        self.chemical_slider.setRange(0, 100)
        self.chemical_slider.setValue(20)
        self.chemical_value_edit = QLineEdit("2.0")
        self.chemical_value_edit.setMaximumWidth(60)
        self.chemical_value_edit.textChanged.connect(
            lambda: self.update_slider_from_edit(self.chemical_slider,
                                                 self.chemical_value_edit, 0, 10))

        chemical_layout = QHBoxLayout()
        chemical_layout.addWidget(self.chemical_slider)
        chemical_layout.addWidget(self.chemical_value_edit)
        params_layout.addRow("Химический фактор (0-10):", chemical_layout)

        # Подключение слайдеров
        self.vibration_slider.valueChanged.connect(
            lambda v: self.vibration_value_edit.setText(f"{v / 10:.1f}"))
        self.noise_slider.valueChanged.connect(
            lambda v: self.noise_value_edit.setText(f"{v / 10:.1f}"))
        self.chemical_slider.valueChanged.connect(
            lambda v: self.chemical_value_edit.setText(f"{v / 10:.1f}"))

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Кнопка расчета
        btn_layout = QHBoxLayout()
        self.calculate_btn = QPushButton("Рассчитать риск")
        self.calculate_btn.clicked.connect(self.calculate_risk)

        btn_layout.addWidget(self.calculate_btn)
        layout.addLayout(btn_layout)

        # Результат
        self.result_group = QGroupBox("Результат расчета")
        self.result_layout = QVBoxLayout()
        self.result_label = QLabel("Нажмите 'Рассчитать риск'")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_layout.addWidget(self.result_label)
        self.result_group.setLayout(self.result_layout)
        layout.addWidget(self.result_group)

        # Кнопки
        button_layout = QHBoxLayout()
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def update_slider_from_edit(self, slider, edit, min_val, max_val):
        """Обновление слайдера из текстового поля"""
        try:
            value = float(edit.text())
            value = max(min_val, min(max_val, value))
            slider_value = int((value - min_val) / (max_val - min_val) * 100)
            slider.setValue(slider_value)
        except ValueError:
            pass

    def calculate_risk(self):
        """Выполнить расчет риска"""
        try:
            # Получаем значения
            vibration_val = float(self.vibration_value_edit.text())
            noise_val = float(self.noise_value_edit.text())
            chemical_val = float(self.chemical_value_edit.text())
            health_val = HealthCalculator.calculate_health_score(self.employee)

            # Валидация
            vibration_val = max(0, min(10, vibration_val))
            noise_val = max(0, min(10, noise_val))
            chemical_val = max(0, min(10, chemical_val))

            # Рассчитываем риск
            result = self.fuzzy_system.calculate_risk(
                vibration_val, noise_val, chemical_val, health_val
            )

            if result['success']:
                # Отображаем результат
                result_text = f"""
                <div style='text-align: center;'>
                    <h2>Уровень риска: {result['percent']}</h2>
                    <h3 style='color: {result['color']};'>{result['category']}</h3>
                </div>
                """

                self.result_label.setText(result_text)

            else:
                QMessageBox.warning(self, "Ошибка расчета",
                                    f"Не удалось рассчитать риск: {result.get('error', 'Неизвестная ошибка')}")

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода",
                                "Пожалуйста, введите корректные числовые значения")



class MainWindow(QMainWindow):
    """Главное окно приложения с меню загрузки конфигурации"""

    def __init__(self):
        super().__init__()
        self.employee_manager = EmployeeManager()
        self.fuzzy_system = FuzzyRiskSystem()  # Система по умолчанию
        self.current_config_file = None
        self.setup_ui()
        self.load_employees()

    def setup_ui(self):
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.resize(800, 600)  # Большой размер при запуске
        # Основной layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Создание меню
        self.create_menu_bar()

        # Панель поиска
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по ФИО или должности...")
        self.search_edit.textChanged.connect(self.search_employees)

        #search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(self.search_edit)
        main_layout.addLayout(search_layout)

        # Таблица работников
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.doubleClicked.connect(self.edit_employee)

        main_layout.addWidget(self.table_view)

        # Панель кнопок
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("Добавить работника")
        self.add_btn.clicked.connect(self.add_employee)

        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.clicked.connect(self.edit_selected_employee)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_selected_employee)

        self.calculate_btn = QPushButton("Рассчитать риск")
        self.calculate_btn.clicked.connect(self.calculate_risk_for_selected)
        self.calculate_btn.setStyleSheet("background-color: #4CAF50; color: white;")

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.calculate_btn)

        main_layout.addLayout(button_layout)

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def create_menu_bar(self):
        """Создание меню"""
        menubar = self.menuBar()

        # Добавляем новый пункт
        edit_config_action = QAction("Редактировать конфигурацию...", self)
        edit_config_action.triggered.connect(self.edit_configuration)
        menubar.addAction(edit_config_action)

    def load_configuration(self):
        """Загрузка конфигурации из файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл конфигурации",
            "",
            "JSON файлы (*.json);;Все файлы (*.*)"
        )

        if file_path:
            config = ConfigLoader.load_config(file_path)
            if config:
                try:
                    # Создаем новую систему с загруженной конфигурацией
                    self.fuzzy_system = FuzzyRiskSystem(config)
                    self.current_config_file = file_path

                    # Обновляем статус
                    filename = os.path.basename(file_path)
                    self.config_label.setText(f"Конфигурация: {filename}")
                    self.config_label.setStyleSheet("background-color: #c8e6c9; padding: 5px;")

                    self.status_bar.showMessage(f"Конфигурация загружена: {filename}", 3000)

                except Exception as e:
                    QMessageBox.critical(self, "Ошибка",
                                         f"Не удалось загрузить конфигурацию: {str(e)}")
            else:
                QMessageBox.warning(self, "Ошибка",
                                    "Неверный формат конфигурационного файла")

    def save_configuration(self):
        """Сохранение текущей конфигурации в файл"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить конфигурацию",
            "fuzzy_config.json",
            "JSON файлы (*.json);;Все файлы (*.*)"
        )

        if file_path:
            if self.fuzzy_system.config:
                success = ConfigLoader.save_config(self.fuzzy_system.config, file_path)
                if success:
                    self.status_bar.showMessage(f"Конфигурация сохранена: {os.path.basename(file_path)}", 3000)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось сохранить конфигурацию")
            else:
                QMessageBox.information(self, "Информация",
                                        "Текущая конфигурация является конфигурацией по умолчанию")

    def load_employees(self, employees=None):
        """Загрузка работников в таблицу"""
        if employees is None:
            employees = self.employee_manager.get_all_employees()

        self.model = EmployeeTableModel(employees)
        self.table_view.setModel(self.model)

        # Настраиваем ширину колонок (автоматическая настройка)
        header = self.table_view.horizontalHeader()

        # Устанавливаем режимы растягивания для разных колонок
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # ID - фиксированная
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # ФИО - растягиваемая
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Должность - по содержимому
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Пол - фиксированная
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Здоровье - по содержимому

        # Диагнозы - фиксированная ширина
        for i in range(5, 10):  # Колонки с диагнозами
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

        header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)  # Инвалидность - по содержимому

        # Устанавливаем фиксированные ширины
        self.table_view.setColumnWidth(0, 60)  # ID
        self.table_view.setColumnWidth(3, 80)  # Пол
        self.table_view.setColumnWidth(5, 120)  # Проф.вредность
        self.table_view.setColumnWidth(6, 80)  # ЖКТ
        self.table_view.setColumnWidth(7, 100)  # Зрение
        self.table_view.setColumnWidth(8, 80)  # ЛОР
        self.table_view.setColumnWidth(9, 80)  # ССЗ

    def search_employees(self):
        """Поиск работников"""
        query = self.search_edit.text()
        if query:
            employees = self.employee_manager.search_employees(query)
        else:
            employees = self.employee_manager.get_all_employees()

        self.load_employees(employees)

    def add_employee(self):
        """Добавление нового работника"""
        dialog = AddEditEmployeeDialog(self)
        if dialog.exec():
            data = dialog.get_employee_data()

            # Проверка обязательных полей
            if not data['full_name'] or not data['position']:
                QMessageBox.warning(self, "Ошибка",
                                    "Заполните все обязательные поля!")
                return

            # Добавляем работника
            self.employee_manager.add_employee(**data)
            self.load_employees()
            self.status_bar.showMessage("Работник добавлен", 3000)

    def edit_selected_employee(self):
        """Редактирование выбранного работника"""
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите работника для редактирования!")
            return

        employee_id = int(self.model.employees[selected[0].row()].id)
        self.edit_employee_by_id(employee_id)

    def edit_employee(self, index):
        """Редактирование по двойному клику"""
        employee_id = int(self.model.employees[index.row()].id)
        self.edit_employee_by_id(employee_id)

    def edit_employee_by_id(self, employee_id):
        """Редактирование работника по ID"""
        employee = self.employee_manager.get_employee_by_id(employee_id)
        if not employee:
            return

        dialog = AddEditEmployeeDialog(self, employee)
        if dialog.exec():
            data = dialog.get_employee_data()

            # Обновляем работника
            self.employee_manager.update_employee(employee_id, **data)
            self.load_employees()
            self.status_bar.showMessage("Данные обновлены", 3000)

    def delete_selected_employee(self):
        """Удаление выбранного работника"""
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите работника для удаления!")
            return

        employee_id = int(self.model.employees[selected[0].row()].id)
        employee = self.employee_manager.get_employee_by_id(employee_id)

        # Подтверждение удаления
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить работника {employee.full_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.employee_manager.delete_employee(employee_id)
            self.load_employees()
            self.status_bar.showMessage("Работник удален", 3000)

    def calculate_risk_for_selected(self):
        """Расчет риска для выбранного работника с текущей конфигурацией"""
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка",
                                "Выберите работника для расчета риска!")
            return

        employee_id = int(self.model.employees[selected[0].row()].id)
        employee = self.employee_manager.get_employee_by_id(employee_id)

        # Открываем диалог расчета риска с текущей системой
        dialog = RiskCalculatorDialog(self, employee, self.fuzzy_system)
        dialog.exec()

    def edit_configuration(self):
        """Открытие интерактивного редактора конфигурации"""
        try:
            from config_editor import ConfigEditor

            # Получаем текущую конфигурацию
            current_config = None
            if hasattr(self.fuzzy_system, 'config'):
                current_config = self.fuzzy_system.config
            else:
                # Если нет конфигурации, используем пустую
                from config_loader import ConfigLoader
                current_config = ConfigLoader.get_default_config()

            # Создаем редактор
            editor = ConfigEditor(self, current_config)
            editor.setModal(True)

            # Показываем диалог
            if editor.exec() == QDialog.DialogCode.Accepted:
                # Получаем новую конфигурацию
                new_config = editor.get_current_config()

                try:
                    # Создаем новую систему
                    from fuzzy_system import FuzzyRiskSystem
                    self.fuzzy_system = FuzzyRiskSystem(new_config)

                    self.status_bar.showMessage("Конфигурация обновлена", 3000)

                except Exception as e:
                    error_msg = f"Не удалось применить конфигурацию:\n{str(e)[:200]}"
                    QMessageBox.critical(self, "Ошибка", error_msg)

        except Exception as e:
            error_msg = f"Ошибка при открытии редактора:\n{str(e)}"
            print(f"DEBUG ERROR: {error_msg}")
            QMessageBox.critical(self, "Ошибка", error_msg)