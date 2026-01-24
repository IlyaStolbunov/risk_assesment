from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from employee_manager import EmployeeManager
from health_calculator import HealthCalculator
from fuzzy_system import FuzzyRiskSystem


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
    """Модель таблицы для отображения работников"""

    def __init__(self, employees):
        super().__init__()
        self.employees = employees
        self.headers = ['ID', 'ФИО', 'Должность', 'Пол', 'Возраст', 'Здоровье',
                        'Диагнозы (основные)', 'Проф.вредность', 'Инвалидность']

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
            try:
                if col == 0:
                    return str(employee.id)
                elif col == 1:
                    return employee.full_name
                elif col == 2:
                    return employee.position
                elif col == 3:
                    return employee.gender
                elif col == 4:
                    age = employee.get_age()
                    return str(age) if age is not None else ""
                elif col == 5:
                    score = HealthCalculator.calculate_health_score(employee)
                    desc = HealthCalculator.get_health_description(score)
                    return f"{score:.2f} ({desc})"
                elif col == 6:
                    # Отображаем первые 2-3 диагноза
                    if hasattr(employee, 'diagnoses') and employee.diagnoses:
                        all_diagnoses = []
                        for category, diagnoses in employee.diagnoses.items():
                            if diagnoses:
                                all_diagnoses.extend(diagnoses[:1])  # По одному из каждой категории

                        if all_diagnoses:
                            if len(all_diagnoses) > 2:
                                return ", ".join(all_diagnoses[:2]) + "..."
                            return ", ".join(all_diagnoses)
                    return ""
                elif col == 7:
                    return employee.prof_harm_code if hasattr(employee,
                                                              'prof_harm_code') and employee.prof_harm_code else ""
                elif col == 8:
                    if hasattr(employee, 'disability_group') and employee.disability_group:
                        return f"Гр.{employee.disability_group}"
                    return ""
            except Exception as e:
                print(f"Error getting data for cell {index.row()}, {col}: {e}")
                return "Ошибка"

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [0, 3, 4, 5, 7, 8]:
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft

        elif role == Qt.ItemDataRole.ToolTipRole:
            if col == 6 and hasattr(employee, 'diagnoses') and employee.diagnoses:
                tooltip = "<b>Диагнозы:</b><br>"
                for category, diagnoses in employee.diagnoses.items():
                    if diagnoses:
                        tooltip += f"<b>{category}:</b><br>"
                        for diag in diagnoses:
                            tooltip += f"• {diag}<br>"
                        tooltip += "<br>"
                return tooltip

        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]
        return None


class DiagnosisInputWidget(QWidget):
    """Виджет для ввода диагнозов"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.diagnosis_widgets = []  # Список виджетов для каждого диагноза
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Заголовок
        title_label = QLabel("Диагнозы:")
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)

        # Контейнер для виджетов диагнозов
        self.diagnoses_container = QVBoxLayout()
        layout.addLayout(self.diagnoses_container)

        # Кнопка добавления нового диагноза
        add_btn = QPushButton("+ Добавить диагноз")
        add_btn.clicked.connect(self.add_diagnosis_widget)
        layout.addWidget(add_btn)

    def add_diagnosis_widget(self):
        """Добавить виджет для ввода одного диагноза"""
        diagnosis_widget = QWidget()
        diagnosis_layout = QHBoxLayout(diagnosis_widget)

        # Выбор категории
        category_combo = QComboBox()
        category_combo.addItem("Выберите категорию...", "")

        # Загружаем категории из БД
        from employee_manager import EmployeeManager
        manager = EmployeeManager()
        categories = manager.get_diagnosis_categories()

        for cat in categories:
            category_combo.addItem(cat['category'], cat['category'])

        # Поле для ввода названия диагноза
        diagnosis_edit = QLineEdit()
        diagnosis_edit.setPlaceholderText("Введите название диагноза...")

        # Кнопка удаления
        remove_btn = QPushButton("✕")
        remove_btn.setMaximumWidth(30)
        remove_btn.clicked.connect(lambda: self.remove_diagnosis_widget(diagnosis_widget))

        diagnosis_layout.addWidget(category_combo)
        diagnosis_layout.addWidget(diagnosis_edit, 1)  # Растягиваемое поле
        diagnosis_layout.addWidget(remove_btn)

        # Сохраняем ссылки на виджеты
        diagnosis_data = {
            'widget': diagnosis_widget,
            'category_combo': category_combo,
            'diagnosis_edit': diagnosis_edit
        }
        self.diagnosis_widgets.append(diagnosis_data)

        self.diagnoses_container.addWidget(diagnosis_widget)

    def remove_diagnosis_widget(self, widget):
        """Удалить виджет диагноза"""
        for i, data in enumerate(self.diagnosis_widgets):
            if data['widget'] == widget:
                widget.setParent(None)
                widget.deleteLater()
                self.diagnosis_widgets.pop(i)
                break

    def get_diagnoses(self):
        """Получить все введенные диагнозы"""
        diagnoses_by_category = {}

        for data in self.diagnosis_widgets:
            category = data['category_combo'].currentData()
            diagnosis_name = data['diagnosis_edit'].text().strip()

            if category and diagnosis_name:
                if category not in diagnoses_by_category:
                    diagnoses_by_category[category] = []

                if diagnosis_name not in diagnoses_by_category[category]:
                    diagnoses_by_category[category].append(diagnosis_name)

        return diagnoses_by_category

    def set_diagnoses(self, diagnoses_dict):
        """Установить диагнозы из существующего сотрудника"""
        # Удаляем все текущие виджеты
        for data in self.diagnosis_widgets[:]:
            self.remove_diagnosis_widget(data['widget'])

        # Добавляем виджеты для каждого диагноза
        if diagnoses_dict:
            for category, diagnosis_list in diagnoses_dict.items():
                for diagnosis_name in diagnosis_list:
                    self.add_diagnosis_widget()

                    # Устанавливаем значения в последнем добавленном виджете
                    if self.diagnosis_widgets:
                        last_data = self.diagnosis_widgets[-1]

                        # Устанавливаем категорию
                        index = last_data['category_combo'].findData(category)
                        if index >= 0:
                            last_data['category_combo'].setCurrentIndex(index)

                        # Устанавливаем название диагноза
                        last_data['diagnosis_edit'].setText(diagnosis_name)


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
        self.setMinimumWidth(600)

        # Основной layout
        main_layout = QVBoxLayout()

        # Scroll area для прокрутки
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # 1. Основная информация
        info_group = QGroupBox("Основная информация")
        info_layout = QFormLayout()

        self.name_edit = QLineEdit()
        info_layout.addRow("Фамилия:", self.name_edit)

        # Должность
        self.position_combo = QComboBox()
        from employee_manager import EmployeeManager
        manager = EmployeeManager()
        positions = manager.get_positions()
        for pos in positions:
            self.position_combo.addItem(pos['name'], pos['id'])
        info_layout.addRow("Должность:", self.position_combo)

        # Пол
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["М", "Ж"])
        info_layout.addRow("Пол:", self.gender_combo)

        # Дата рождения
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setCalendarPopup(True)
        self.birth_date_edit.setDate(QDate.currentDate().addYears(-30))
        info_layout.addRow("Дата рождения:", self.birth_date_edit)

        # Дата начала работы
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        info_layout.addRow("Дата начала работы:", self.start_date_edit)

        info_group.setLayout(info_layout)
        content_layout.addWidget(info_group)

        # 2. Диагнозы
        self.diagnosis_widget = DiagnosisInputWidget()
        content_layout.addWidget(self.diagnosis_widget)

        # 3. Профвредность
        prof_group = QGroupBox("Профессиональная вредность")
        prof_layout = QFormLayout()

        self.prof_harm_edit = QLineEdit()
        self.prof_harm_edit.setPlaceholderText("Например: Т75.2")
        prof_layout.addRow("Код профвредности:", self.prof_harm_edit)

        self.prof_harm_year_edit = QDateEdit()
        self.prof_harm_year_edit.setCalendarPopup(True)
        self.prof_harm_year_edit.setDate(QDate.currentDate())
        prof_layout.addRow("Год установления:", self.prof_harm_year_edit)

        prof_group.setLayout(prof_layout)
        content_layout.addWidget(prof_group)

        # 4. Инвалидность
        disability_group = QGroupBox("Инвалидность")
        disability_layout = QFormLayout()

        self.disability_combo = QComboBox()
        self.disability_combo.addItem("Нет", None)
        self.disability_combo.addItem("1 группа", 1)
        self.disability_combo.addItem("2 группа", 2)
        self.disability_combo.addItem("3 группа", 3)
        disability_layout.addRow("Группа инвалидности:", self.disability_combo)

        disability_group.setLayout(disability_layout)
        content_layout.addWidget(disability_group)

        # Добавляем растягивающийся спейсер
        content_layout.addStretch()

        # Устанавливаем виджет в scroll area
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # 5. Кнопки
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def load_employee_data(self):
        """Загрузка данных работника в форму"""
        if not self.employee:
            return

        self.name_edit.setText(self.employee.full_name)

        # Установка должности
        for i in range(self.position_combo.count()):
            if self.position_combo.itemText(i) == self.employee.position:
                self.position_combo.setCurrentIndex(i)
                break

        # Установка пола
        index = self.gender_combo.findText(self.employee.gender)
        if index >= 0:
            self.gender_combo.setCurrentIndex(index)

        # Даты
        if hasattr(self.employee, 'birth_date') and self.employee.birth_date:
            try:
                birth_date = QDate.fromString(str(self.employee.birth_date), 'yyyy-MM-dd')
                self.birth_date_edit.setDate(birth_date)
            except:
                pass

        if hasattr(self.employee, 'start_year') and self.employee.start_year:
            try:
                start_date = QDate.fromString(str(self.employee.start_year), 'yyyy-MM-dd')
                self.start_date_edit.setDate(start_date)
            except:
                pass

        # Диагнозы
        if hasattr(self.employee, 'diagnoses') and self.employee.diagnoses:
            self.diagnosis_widget.set_diagnoses(self.employee.diagnoses)

        # Профвредность
        if hasattr(self.employee, 'prof_harm_code') and self.employee.prof_harm_code:
            self.prof_harm_edit.setText(self.employee.prof_harm_code)

        if hasattr(self.employee, 'prof_harm_year') and self.employee.prof_harm_year:
            try:
                prof_year = QDate.fromString(str(self.employee.prof_harm_year), 'yyyy-MM-dd')
                self.prof_harm_year_edit.setDate(prof_year)
            except:
                pass

        # Инвалидность
        if hasattr(self.employee, 'disability_group') and self.employee.disability_group:
            for i in range(self.disability_combo.count()):
                if self.disability_combo.itemData(i) == self.employee.disability_group:
                    self.disability_combo.setCurrentIndex(i)
                    break

    def validate_and_accept(self):
        """Проверка данных и закрытие диалога"""
        # Проверяем обязательные поля
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите фамилию работника!")
            return

        # Получаем диагнозы
        diagnoses = self.diagnosis_widget.get_diagnoses()

        # Формируем данные
        employee_data = {
            'full_name': self.name_edit.text().strip(),
            'position_id': self.position_combo.currentData(),
            'gender': self.gender_combo.currentText(),
            'birth_date': self.birth_date_edit.date().toString('yyyy-MM-dd'),
            'start_year': self.start_date_edit.date().toString('yyyy-MM-dd'),
            'department_id': 1,  # По умолчанию
            'diagnoses': diagnoses
        }

        # Профвредность
        prof_harm_code = self.prof_harm_edit.text().strip()
        if prof_harm_code:
            employee_data['prof_harm_code'] = prof_harm_code
            employee_data['prof_harm_year'] = self.prof_harm_year_edit.date().toString('yyyy-MM-dd')

        # Инвалидность
        disability_group = self.disability_combo.currentData()
        if disability_group is not None:
            employee_data['disability_group'] = disability_group

        # Сохраняем данные
        self.employee_data = employee_data
        self.accept()

    def get_employee_data(self):
        """Получить данные из формы"""
        return getattr(self, 'employee_data', None)


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
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()

        # Инициализируем менеджер сотрудников
        self.employee_manager = EmployeeManager('database/risk_assesment.db')

        # Инициализируем систему нечеткой логики
        try:
            from fuzzy_system import FuzzyRiskSystem
            self.fuzzy_system = FuzzyRiskSystem()
        except ImportError:
            print("Warning: Fuzzy system not available")
            self.fuzzy_system = None

        self.current_config_file = None
        self.setup_ui()
        self.load_employees()

    def setup_ui(self):
        self.setWindowTitle("Система оценки рисков здоровья работников")
        self.resize(1000, 600)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной layout
        main_layout = QVBoxLayout(central_widget)

        self.create_menu_bar()

        # Панель поиска
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по фамилии или должности...")
        self.search_edit.textChanged.connect(self.search_employees)
        search_layout.addWidget(self.search_edit)
        main_layout.addLayout(search_layout)

        # Таблица работников
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_view.doubleClicked.connect(self.on_table_double_click)

        # Настройки таблицы
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setShowGrid(True)  # Показывать сетку
        self.table_view.setSortingEnabled(True)

        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

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
        self.status_bar.showMessage("Готово")

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

    def create_menu_bar(self):
        """Создание меню"""
        menubar = self.menuBar()

        # Добавляем новый пункт
        edit_config_action = QAction("Редактировать конфигурацию...", self)
        edit_config_action.triggered.connect(self.edit_configuration)
        menubar.addAction(edit_config_action)

    def on_table_double_click(self, index):
        """Обработка двойного клика по таблице"""
        self.edit_selected_employee()

    def load_employees(self, employees=None):
        """Загрузка работников в таблицу"""
        try:
            if employees is None:
                employees = self.employee_manager.get_all_employees()

            if employees:
                self.model = EmployeeTableModel(employees)
                self.table_view.setModel(self.model)

                # Настройка ширины колонок
                header = self.table_view.horizontalHeader()
                header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
                header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
                header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
                header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
                header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
                header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)

                # Фиксированные ширины
                self.table_view.setColumnWidth(0, 50)
                self.table_view.setColumnWidth(3, 50)
                self.table_view.setColumnWidth(4, 70)
                self.table_view.setColumnWidth(5, 120)
                self.table_view.setColumnWidth(7, 100)
                self.table_view.setColumnWidth(8, 80)

                self.status_bar.showMessage(f"Загружено сотрудников: {len(employees)}", 3000)
            else:
                self.status_bar.showMessage("Нет данных о сотрудниках", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить сотрудников: {str(e)}")

    def search_employees(self):
        """Поиск работников"""
        query = self.search_edit.text()
        employees = self.employee_manager.search_employees(query)
        self.load_employees(employees)

    def add_employee(self):
        """Добавление нового работника"""
        dialog = AddEditEmployeeDialog(self)
        if dialog.exec():
            data = dialog.get_employee_data()
            if data:
                try:
                    employee = self.employee_manager.add_employee(**data)
                    if employee:
                        self.load_employees()
                        self.status_bar.showMessage(f"Добавлен сотрудник: {employee.full_name}", 3000)
                    else:
                        QMessageBox.warning(self, "Ошибка", "Не удалось добавить сотрудника")
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении: {str(e)}")

    def edit_selected_employee(self):
        """Редактирование выбранного работника"""
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите работника для редактирования!")
            return

        try:
            row = selected[0].row()
            employee_id = self.model.employees[row].id
            employee = self.employee_manager.get_employee_by_id(employee_id)

            if employee:
                dialog = AddEditEmployeeDialog(self, employee)
                if dialog.exec():
                    data = dialog.get_employee_data()
                    if data:
                        success = self.employee_manager.update_employee(employee_id, **data)
                        if success:
                            self.load_employees()
                            self.status_bar.showMessage("Данные обновлены", 3000)
                        else:
                            QMessageBox.warning(self, "Ошибка", "Не удалось обновить данные")
            else:
                QMessageBox.warning(self, "Ошибка", "Сотрудник не найден")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при редактировании: {str(e)}")

    def delete_selected_employee(self):
        """Удаление выбранного работника"""
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите работника для удаления!")
            return

        try:
            row = selected[0].row()
            employee_id = self.model.employees[row].id
            employee_name = self.model.employees[row].full_name

            # Подтверждение удаления
            reply = QMessageBox.question(
                self, "Подтверждение",
                f"Удалить работника {employee_name}?\nВся связанная информация также будет удалена.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success = self.employee_manager.delete_employee(employee_id)
                if success:
                    self.load_employees()
                    self.status_bar.showMessage(f"Сотрудник {employee_name} удален", 3000)
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось удалить сотрудника")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")

    def calculate_risk_for_selected(self):
        """Расчет риска для выбранного работника"""
        selected = self.table_view.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите работника для расчета риска!")
            return

        try:
            row = selected[0].row()
            employee_id = self.model.employees[row].id
            employee = self.employee_manager.get_employee_by_id(employee_id)

            if employee and self.fuzzy_system:
                dialog = RiskCalculatorDialog(self, employee, self.fuzzy_system)
                dialog.exec()
            elif not self.fuzzy_system:
                QMessageBox.warning(self, "Ошибка", "Система нечеткой логики не доступна")
            else:
                QMessageBox.warning(self, "Ошибка", "Сотрудник не найден")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при расчете риска: {str(e)}")