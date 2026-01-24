import sqlite3
from typing import List, Dict, Optional

class DatabaseManager:
    """Менеджер базы данных"""

    def __init__(self, db_path: str = 'database/risk_assesment.db'):
        self.db_path = db_path

    def get_connection(self):
        """Получить соединение с БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_employees_with_details(self) -> List[Dict]:
        """Получить всех сотрудников с деталями"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Основная информация о сотрудниках
            query = """
            SELECT 
                e.id,
                e.lastname as full_name,
                p.name as position,
                e.gender,
                e.birth_date,
                e.start_year,
                d.id as department_id,
                eh.prof_harm_code,
                eh.prof_harm_year,
                ed.disability_group
            FROM employees e
            LEFT JOIN positions p ON e.position_id = p.id
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN employee_harm eh ON e.id = eh.employee_id
            LEFT JOIN employee_disability ed ON e.id = ed.employee_id
            ORDER BY e.lastname
            """

            cursor.execute(query)
            employees = []

            for row in cursor.fetchall():
                emp_dict = dict(row)
                emp_id = emp_dict['id']

                # Получаем диагнозы для сотрудника
                diag_query = """
                SELECT 
                    d.name as diagnosis_name,
                    dc.category as category
                FROM employee_diagnoses ediag
                JOIN diagnoses d ON ediag.diagnosis_id = d.id
                JOIN diagnosis_categories dc ON d.category_id = dc.id
                WHERE ediag.employee_id = ?
                """

                cursor.execute(diag_query, (emp_id,))
                diagnoses = cursor.fetchall()

                # Группируем диагнозы по категориям
                diagnoses_by_category = {}
                for diag in diagnoses:
                    category = diag['category']
                    diagnosis_name = diag['diagnosis_name']

                    if category not in diagnoses_by_category:
                        diagnoses_by_category[category] = []

                    if diagnosis_name not in diagnoses_by_category[category]:
                        diagnoses_by_category[category].append(diagnosis_name)

                emp_dict['diagnoses'] = diagnoses_by_category
                employees.append(emp_dict)

            return employees

        except Exception as e:
            print(f"Error getting employees: {e}")
            return []
        finally:
            conn.close()

    def get_employee_by_id(self, employee_id: int) -> Optional[Dict]:
        """Получить сотрудника по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            query = """
            SELECT 
                e.id,
                e.lastname as full_name,
                p.name as position,
                e.gender,
                e.birth_date,
                e.start_year,
                d.id as department_id,
                eh.prof_harm_code,
                eh.prof_harm_year,
                ed.disability_group
            FROM employees e
            LEFT JOIN positions p ON e.position_id = p.id
            LEFT JOIN departments d ON e.department_id = d.id
            LEFT JOIN employee_harm eh ON e.id = eh.employee_id
            LEFT JOIN employee_disability ed ON e.id = ed.employee_id
            WHERE e.id = ?
            """

            cursor.execute(query, (employee_id,))
            row = cursor.fetchone()

            if not row:
                return None

            emp_dict = dict(row)

            # Получаем диагнозы
            diag_query = """
            SELECT 
                d.id as diagnosis_id,
                d.name as diagnosis_name,
                dc.category as category
            FROM employee_diagnoses ediag
            JOIN diagnoses d ON ediag.diagnosis_id = d.id
            JOIN diagnosis_categories dc ON d.category_id = dc.id
            WHERE ediag.employee_id = ?
            """

            cursor.execute(diag_query, (employee_id,))
            diagnoses = cursor.fetchall()

            # Группируем диагнозы по категориям
            diagnoses_by_category = {}
            for diag in diagnoses:
                category = diag['category']
                diagnosis_name = diag['diagnosis_name']

                if category not in diagnoses_by_category:
                    diagnoses_by_category[category] = []

                if diagnosis_name not in diagnoses_by_category[category]:
                    diagnoses_by_category[category].append(diagnosis_name)

            emp_dict['diagnoses'] = diagnoses_by_category

            return emp_dict

        except Exception as e:
            print(f"Error getting employee: {e}")
            return None
        finally:
            conn.close()

    def add_employee(self, employee_data: Dict) -> int:
        """Добавить нового сотрудника"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Добавляем основную информацию
            cursor.execute("""
            INSERT INTO employees (lastname, birth_date, gender, position_id, department_id, start_year)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                employee_data['full_name'],
                employee_data['birth_date'],
                employee_data['gender'],
                employee_data['position_id'],
                employee_data.get('department_id', 1),
                employee_data.get('start_year')
            ))

            employee_id = cursor.lastrowid

            # Добавляем диагнозы (как новые записи в таблицу диагнозов)
            if 'diagnoses' in employee_data:
                for category_name, diagnosis_names in employee_data['diagnoses'].items():
                    for diagnosis_name in diagnosis_names:
                        if diagnosis_name.strip():  # Проверяем, что диагноз не пустой
                            # Находим ID категории
                            cursor.execute("SELECT id FROM diagnosis_categories WHERE category = ?", (category_name,))
                            category_row = cursor.fetchone()

                            if category_row:
                                category_id = category_row['id']

                                # Проверяем, существует ли уже такой диагноз
                                cursor.execute("SELECT id FROM diagnoses WHERE name = ? AND category_id = ?",
                                               (diagnosis_name, category_id))
                                existing_diag = cursor.fetchone()

                                if existing_diag:
                                    diagnosis_id = existing_diag['id']
                                else:
                                    # Добавляем новый диагноз
                                    cursor.execute("INSERT INTO diagnoses (name, category_id) VALUES (?, ?)",
                                                   (diagnosis_name, category_id))
                                    diagnosis_id = cursor.lastrowid

                                # Связываем диагноз с сотрудником
                                cursor.execute("""
                                INSERT OR IGNORE INTO employee_diagnoses (employee_id, diagnosis_id)
                                VALUES (?, ?)
                                """, (employee_id, diagnosis_id))

            # Добавляем профвредность, если есть
            if employee_data.get('prof_harm_code'):
                cursor.execute("""
                INSERT INTO employee_harm (employee_id, prof_harm_code, prof_harm_year)
                VALUES (?, ?, ?)
                """, (employee_id, employee_data['prof_harm_code'], employee_data.get('prof_harm_year')))

            # Добавляем инвалидность, если есть
            if employee_data.get('disability_group'):
                cursor.execute("""
                INSERT INTO employee_disability (employee_id, disability_group)
                VALUES (?, ?)
                """, (employee_id, employee_data['disability_group']))

            conn.commit()
            return employee_id

        except Exception as e:
            conn.rollback()
            print(f"Error adding employee: {e}")
            raise
        finally:
            conn.close()

    def update_employee(self, employee_id: int, employee_data: Dict) -> bool:
        """Обновить информацию о сотруднике"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Обновляем основную информацию
            cursor.execute("""
            UPDATE employees 
            SET lastname = ?, birth_date = ?, gender = ?, 
                position_id = ?, department_id = ?, start_year = ?
            WHERE id = ?
            """, (
                employee_data['full_name'],
                employee_data['birth_date'],
                employee_data['gender'],
                employee_data['position_id'],
                employee_data.get('department_id', 1),
                employee_data.get('start_year'),
                employee_id
            ))

            # Удаляем старые диагнозы сотрудника
            cursor.execute("DELETE FROM employee_diagnoses WHERE employee_id = ?", (employee_id,))

            # Добавляем новые диагнозы
            if 'diagnoses' in employee_data:
                for category_name, diagnosis_names in employee_data['diagnoses'].items():
                    for diagnosis_name in diagnosis_names:
                        if diagnosis_name.strip():
                            # Находим ID категории
                            cursor.execute("SELECT id FROM diagnosis_categories WHERE category = ?", (category_name,))
                            category_row = cursor.fetchone()

                            if category_row:
                                category_id = category_row['id']

                                # Проверяем, существует ли уже такой диагноз
                                cursor.execute("SELECT id FROM diagnoses WHERE name = ? AND category_id = ?",
                                               (diagnosis_name, category_id))
                                existing_diag = cursor.fetchone()

                                if existing_diag:
                                    diagnosis_id = existing_diag['id']
                                else:
                                    # Добавляем новый диагноз
                                    cursor.execute("INSERT INTO diagnoses (name, category_id) VALUES (?, ?)",
                                                   (diagnosis_name, category_id))
                                    diagnosis_id = cursor.lastrowid

                                # Связываем диагноз с сотрудником
                                cursor.execute("""
                                INSERT INTO employee_diagnoses (employee_id, diagnosis_id)
                                VALUES (?, ?)
                                """, (employee_id, diagnosis_id))

            # Обновляем профвредность
            cursor.execute("DELETE FROM employee_harm WHERE employee_id = ?", (employee_id,))
            if employee_data.get('prof_harm_code'):
                cursor.execute("""
                INSERT INTO employee_harm (employee_id, prof_harm_code, prof_harm_year)
                VALUES (?, ?, ?)
                """, (employee_id, employee_data['prof_harm_code'], employee_data.get('prof_harm_year')))

            # Обновляем инвалидность
            cursor.execute("DELETE FROM employee_disability WHERE employee_id = ?", (employee_id,))
            if employee_data.get('disability_group'):
                cursor.execute("""
                INSERT INTO employee_disability (employee_id, disability_group)
                VALUES (?, ?)
                """, (employee_id, employee_data['disability_group']))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            print(f"Error updating employee: {e}")
            return False
        finally:
            conn.close()

    def delete_employee(self, employee_id: int) -> bool:
        """Удалить сотрудника"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Удаляем связанные записи
            cursor.execute("DELETE FROM employee_diagnoses WHERE employee_id = ?", (employee_id,))
            cursor.execute("DELETE FROM employee_harm WHERE employee_id = ?", (employee_id,))
            cursor.execute("DELETE FROM employee_disability WHERE employee_id = ?", (employee_id,))

            # Удаляем сотрудника
            cursor.execute("DELETE FROM employees WHERE id = ?", (employee_id,))

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            print(f"Error deleting employee: {e}")
            return False
        finally:
            conn.close()

    def search_employees(self, query: str) -> List[Dict]:
        """Поиск сотрудников"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            search_term = f"%{query}%"

            cursor.execute("""
            SELECT DISTINCT e.id
            FROM employees e
            LEFT JOIN positions p ON e.position_id = p.id
            WHERE e.lastname LIKE ? OR p.name LIKE ?
            """, (search_term, search_term))

            employee_ids = [row['id'] for row in cursor.fetchall()]
            employees = []

            for emp_id in employee_ids:
                emp_data = self.get_employee_by_id(emp_id)
                if emp_data:
                    employees.append(emp_data)

            return employees

        except Exception as e:
            print(f"Error searching employees: {e}")
            return []
        finally:
            conn.close()

    def get_diagnosis_categories(self) -> List[Dict]:
        """Получить все категории диагнозов"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT id, category FROM diagnosis_categories ORDER BY category")
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting categories: {e}")
            return []
        finally:
            conn.close()

    def get_positions(self) -> List[Dict]:
        """Получить все должности"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT id, name FROM positions ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []
        finally:
            conn.close()