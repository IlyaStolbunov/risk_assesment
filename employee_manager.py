class Employee:
    """Класс работника"""

    def __init__(self, employee_id, full_name, position, gender,
                 diagnoses=None, disability=False):
        self.id = employee_id
        self.full_name = full_name
        self.position = position
        self.gender = gender
        self.diagnoses = diagnoses or {
            'professional': False,  # проф. вредность
            'gastro': False,  # ЖКТ
            'vision': False,  # Зрение
            'ent': False,  # ЛОР
            'cardio': False  # ССЗ
        }
        self.disability = disability

    def to_dict(self):
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'position': self.position,
            'gender': self.gender,
            'diagnoses': self.diagnoses.copy(),
            'disability': self.disability
        }

    def __str__(self):
        return f"{self.full_name} ({self.position})"


class EmployeeManager:
    """Менеджер работников (временная замена БД)"""

    def __init__(self):
        self.employees = []
        self.next_id = 1
        self._create_test_data()

    def _create_test_data(self):
        """Создание тестовых данных"""
        test_employees = [
            Employee(self.next_id, "Иванов Иван Иванович", "Инженер", "М",
                     {'vision': True}, False),
            Employee(self.next_id + 1, "Петров Петр Петрович", "Рабочий", "М",
                     {'professional': True, 'cardio': True}, True),
            Employee(self.next_id + 2, "Сидорова Анна Сергеевна", "Химик", "Ж",
                     {'gastro': True, 'ent': True}, False),
            Employee(self.next_id + 3, "Кузнецов Алексей Викторович", "Техник", "М",
                     {}, False),
            Employee(self.next_id + 4, "Смирнова Ольга Дмитриевна", "Лаборант", "Ж",
                     {'professional': True, 'vision': True, 'cardio': True}, True),
        ]
        self.employees.extend(test_employees)
        self.next_id += len(test_employees)

    def get_all_employees(self):
        """Получить всех работников"""
        return self.employees.copy()

    def search_employees(self, query):
        """Поиск работников по ФИО или должности"""
        query = query.lower()
        return [emp for emp in self.employees
                if query in emp.full_name.lower()
                or query in emp.position.lower()]

    def get_employee_by_id(self, employee_id):
        """Получить работника по ID"""
        for emp in self.employees:
            if emp.id == employee_id:
                return emp
        return None

    def add_employee(self, full_name, position, gender, diagnoses, disability):
        """Добавить нового работника"""
        employee = Employee(self.next_id, full_name, position, gender,
                            diagnoses, disability)
        self.employees.append(employee)
        self.next_id += 1
        return employee

    def update_employee(self, employee_id, **kwargs):
        """Обновить данные работника"""
        employee = self.get_employee_by_id(employee_id)
        if not employee:
            return False

        for key, value in kwargs.items():
            if hasattr(employee, key):
                setattr(employee, key, value)
        return True

    def delete_employee(self, employee_id):
        """Удалить работника"""
        employee = self.get_employee_by_id(employee_id)
        if employee:
            self.employees.remove(employee)
            return True
        return False