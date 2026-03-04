from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtCore import pyqtSignal

from employee_manager import EmployeeManager

class DepartmentDialog(QDialog):
    """Диалог добавления/редактирования предприятия"""

    def __init__(self, parent=None, department=None):
        super().__init__(parent)
        self.department = department
        self.employee_manager = EmployeeManager()
        self.setup_ui()

        if department:
            self.load_department_data()

    def setup_ui(self):
        self.setWindowTitle("Добавить предприятие" if not self.department else "Редактировать предприятие")
        self.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Форма
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите название предприятия...")
        form_layout.addRow("Название:", self.name_edit)

        layout.addLayout(form_layout)

        # Кнопки
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.validate_and_accept)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_department_data(self):
        """Загрузка данных предприятия в форму"""
        if self.department:
            self.name_edit.setText(self.department.get('name', ''))

    def validate_and_accept(self):
        """Проверка данных и закрытие диалога"""
        name = self.name_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название предприятия!")
            return

        try:
            if self.department:
                # Редактирование
                self.employee_manager.update_department(self.department['id'], name)
            else:
                # Добавление
                self.employee_manager.add_department(name)

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить предприятие: {str(e)}")

    def get_department_data(self):
        """Получить данные из формы"""
        return {
            'name': self.name_edit.text().strip()
        }


class DepartmentsWindow(QMainWindow):
    """Окно управления предприятиями"""

    departments_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.employee_manager = EmployeeManager()
        self.main_window = parent
        self.setup_ui()
        self.load_departments()
        self.departments_changed.connect(self.main_window.load_employees)

    def setup_ui(self):
        self.setWindowTitle("Управление предприятиями")
        self.resize(600, 400)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Таблица предприятий
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(2)
        self.table_widget.setHorizontalHeaderLabels(["ID", "Название"])

        # Настройка таблицы
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table_widget.setAlternatingRowColors(True)

        layout.addWidget(self.table_widget)

        # Панель кнопок
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.add_department)

        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.clicked.connect(self.edit_department)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.clicked.connect(self.delete_department)
        self.delete_btn.setStyleSheet("background-color: #f44336; color: white;")

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.close)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

    def load_departments(self):
        """Загрузка предприятий в таблицу"""
        try:
            departments = self.employee_manager.get_departments()

            self.table_widget.setRowCount(len(departments))

            for row, dept in enumerate(departments):
                # ID
                id_item = QTableWidgetItem(str(dept['id']))
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table_widget.setItem(row, 0, id_item)

                # Название
                name_item = QTableWidgetItem(dept['name'])
                self.table_widget.setItem(row, 1, name_item)

            self.status_bar.showMessage(f"Загружено предприятий: {len(departments)}", 3000)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить предприятия: {str(e)}")

    def get_selected_department(self):
        """Получить выбранное предприятие"""
        selected_rows = self.table_widget.selectionModel().selectedRows()

        if not selected_rows:
            return None

        row = selected_rows[0].row()

        return {
            'id': int(self.table_widget.item(row, 0).text()),
            'name': self.table_widget.item(row, 1).text()
        }

    def add_department(self):
        """Добавить новое предприятие"""
        dialog = DepartmentDialog(self)

        if dialog.exec():
            self.load_departments()
            self.departments_changed.emit()
            self.status_bar.showMessage("Предприятие добавлено", 3000)

    def edit_department(self):
        """Редактировать выбранное предприятие"""
        department = self.get_selected_department()

        if not department:
            QMessageBox.warning(self, "Ошибка", "Выберите предприятие для редактирования!")
            return

        dialog = DepartmentDialog(self, department)

        if dialog.exec():
            self.load_departments()
            self.departments_changed.emit()
            self.status_bar.showMessage("Предприятие обновлено", 3000)

    def delete_department(self):
        """Удалить выбранное предприятие"""
        department = self.get_selected_department()

        if not department:
            QMessageBox.warning(self, "Ошибка", "Выберите предприятие для удаления!")
            return

        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Удалить предприятие '{department['name']}'?\n\n"
            f"ВНИМАНИЕ: Все сотрудники этого предприятия также будут удалены!\n"
            f"Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.employee_manager.delete_department(department['id'])
                self.load_departments()
                self.departments_changed.emit()
                self.status_bar.showMessage(f"Предприятие '{department['name']}' удалено", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить предприятие: {str(e)}")