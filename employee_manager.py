from database import DatabaseManager
from datetime import datetime


class Employee:
    """Класс работника с данными из БД"""

    def __init__(self, employee_dict: dict):
        self.id = employee_dict['id']
        self.full_name = employee_dict['full_name']
        self.position = employee_dict['position']
        self.gender = employee_dict['gender']
        self.birth_date = employee_dict.get('birth_date')
        self.start_year = employee_dict.get('start_year')
        self.department_id = employee_dict.get('department_id', 1)

        # Диагнозы
        self.diagnoses = employee_dict.get('diagnoses', {})

        # Профвредность
        self.prof_harm_code = employee_dict.get('prof_harm_code')
        self.prof_harm_year = employee_dict.get('prof_harm_year')

        # Инвалидность
        self.disability_group = employee_dict.get('disability_group')

    def get_age(self):
        """Рассчитать возраст"""
        if not self.birth_date:
            print("Нет возраста")
            return None

        try:
            formats = [
                '%Y-%m-%d',
                '%d.%m.%Y',
                '%d/%m/%Y',
                '%Y/%m/%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f'
            ]
            for fmt in formats:
                try:
                    birth_date = datetime.strptime(str(self.birth_date), fmt)
                except:
                    continue
            today = datetime.now()
            age = today.year - birth_date.year

            # Проверяем, был ли уже день рождения в этом году
            if (today.month, today.day) < (birth_date.month, birth_date.day):
                age -= 1

            return age
        except:
            return None

    def get_experience(self):
        """Получить стаж работы"""
        if not self.start_year:
            return None

        try:
            start_date = datetime.strptime(str(self.start_year), '%Y-%m-%d')
            today = datetime.now()
            experience = today.year - start_date.year

            if (today.month, today.day) < (start_date.month, start_date.day):
                experience -= 1

            return experience
        except:
            return None


class EmployeeManager:
    """Менеджер работников (работает с БД)"""

    def __init__(self, db_path: str = 'database/risk_assesment.db'):
        self.db = DatabaseManager(db_path)

    def get_all_employees(self) -> list:
        """Получить всех работников"""
        employees_data = self.db.get_all_employees_with_details()
        return [Employee(emp_data) for emp_data in employees_data]

    def get_employee_by_id(self, employee_id: int) -> Employee:
        """Получить работника по ID"""
        emp_data = self.db.get_employee_by_id(employee_id)
        if emp_data:
            return Employee(emp_data)
        return None

    def search_employees(self, query: str) -> list:
        """Поиск работников по ФИО или должности"""
        if not query or not query.strip():
            return self.get_all_employees()

        employees_data = self.db.search_employees(query.strip())
        return [Employee(emp_data) for emp_data in employees_data]

    def add_employee(self, **kwargs) -> Employee:
        """Добавить нового работника"""
        employee_id = self.db.add_employee(kwargs)
        return self.get_employee_by_id(employee_id) if employee_id else None

    def update_employee(self, employee_id: int, **kwargs) -> bool:
        """Обновить данные работника"""
        return self.db.update_employee(employee_id, kwargs)

    def delete_employee(self, employee_id: int) -> bool:
        """Удалить работника"""
        return self.db.delete_employee(employee_id)

    def get_positions(self) -> list:
        """Получить список должностей"""
        return self.db.get_positions()

    def get_diagnosis_categories(self) -> list:
        """Получить категории диагнозов"""
        return self.db.get_diagnosis_categories()