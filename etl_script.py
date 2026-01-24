import pandas as pd
import re
from datetime import datetime

df = pd.read_excel('origin_data/Тестовый документ.xlsx')

positions_data = [
    {'id': 1, 'name': 'котельщик'},
    {'id': 2, 'name': 'сварщик'}
]

df_positions = pd.DataFrame(positions_data)
print(f"Таблица positions: {len(df_positions)} записей")
print(df_positions)

departments_data = [
    {'id': 1},
    {'id': 5}
]

df_departments = pd.DataFrame(departments_data)
print(f"Таблица departments: {len(df_departments)} записей")
print(df_departments)

categories_mapping = {
    'Др.Дзы': 'Прочие',
    'ОДА': 'Опорно-двигательный аппарат',
    'ССЗ': 'Сердечно-сосудистые',
    'ЖКТ': 'Желудочно-кишечные',
    'ЛОР': 'ЛОР-органы',
    'Зрение': 'Органы зрения',
    'Одых': 'Дыхательная система',
    'Почки': 'Мочевыделительная система',
    'Энд': 'Эндокринные',
}

categories_data = []
for idx, (col_name, category_name) in enumerate(categories_mapping.items(), 1):
    categories_data.append({
        'id': idx,
        'category': category_name
    })

df_categories = pd.DataFrame(categories_data)
print(f"Таблица diagnosis_categories: {len(df_categories)} записей")
print(df_categories)

def clean_string(value):
    if pd.isna(value):
        return None
    return str(value).strip()

def determine_position_id(position_text):
    if pd.isna(position_text):
        return None

    text = str(position_text).lower()
    if 'котельщик' in text:
        return 1
    elif 'свар' in text:
        return 2
    return None

# Обрабатываем каждого работника
employees_data = []

for idx, row in df.iterrows():
    if pd.isna(row['Фамилия']):
        continue

    # Фамилия
    lastname = clean_string(row['Фамилия']).capitalize()

    # Дата рождения
    birth_date = row['Дата рожд']
    if isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date.split()[0], '%Y-%m-%d')
        except:
            birth_date = None
    elif isinstance(birth_date, (datetime, pd.Timestamp)):
        pass  # уже datetime
    else:
        birth_date = None

    # Пол
    gender = clean_string(row['пол'])

    # Должность
    position_description = clean_string(row['Должность'])
    position_id = int(determine_position_id(position_description))

    # Предприятие
    department_id = None
    if pd.notna(row['предприятие']):
        dept_code = int(row['предприятие'])
        department_id = 1 if dept_code == 1 else 2 if dept_code == 5 else None

    # Стаж (год начала)
    start_year_dt = None
    if pd.notna(row['стаж с']):
        try:
            year = int(row['стаж с'])
            start_year_dt = datetime(year, 1, 1)
        except:
            start_year_dt = None

    employees_data.append({
        'id': idx + 1,
        'lastname': lastname,
        'birth_date': birth_date,
        'gender': gender,
        'position_id': position_id,
        'department_id': department_id,
        'start_year': start_year_dt
    })

df_employees = pd.DataFrame(employees_data)
df_employees.at[30, 'position_id'] = 2
print(f"Таблица employees: {len(df_employees)} записей")
print(df_employees)

employee_harm_data = []
harm_id_counter = 1

for idx, row in df.iterrows():
    if pd.isna(row['Фамилия']):
        continue

    employee_id = idx + 1

    # Проверяем, есть ли данные о профвредности
    prof_harm_code = clean_string(row['проф.вредн Дз'])
    prof_harm_year = row['проф.вредн Год']

    if prof_harm_code or pd.notna(prof_harm_year):
        # Год профвредности
        prof_harm_year_dt = None
        if pd.notna(prof_harm_year):
            try:
                year = int(prof_harm_year)
                prof_harm_year_dt = datetime(year, 1, 1)
            except:
                prof_harm_year_dt = None

        employee_harm_data.append({
            'id': harm_id_counter,
            'employee_id': employee_id,
            'prof_harm_code': prof_harm_code,
            'prof_harm_year': prof_harm_year_dt
        })
        harm_id_counter += 1

df_employee_harm = pd.DataFrame(employee_harm_data)
print(f"Таблица employee_harm: {len(df_employee_harm)} записей")
if len(df_employee_harm) > 0:
    print(df_employee_harm.head())
else:
    print("Нет данных о профвредностях")

employee_disability_data = []
disability_id_counter = 1

for idx, row in df.iterrows():
    if pd.isna(row['Фамилия']):
        continue

    employee_id = idx + 1

    # Группа инвалидности
    disability_group = None
    if pd.notna(row['Гр.ИНВ общ']):
        try:
            disability_group = int(row['Гр.ИНВ общ'])
        except:
            pass

    if disability_group is not None:
        employee_disability_data.append({
            'id': disability_id_counter,
            'employee_id': employee_id,
            'disability_group': disability_group
        })
        disability_id_counter += 1

df_employee_disability = pd.DataFrame(employee_disability_data)
print(f"Таблица employee_disability: {len(df_employee_disability)} записей")
if len(df_employee_disability) > 0:
    print(df_employee_disability.head())
else:
    print("Нет данных об инвалидности")

def extract_diagnosis_name(text):
    """Извлекаем название диагноза из текста"""
    if pd.isna(text):
        return None

    text_str = str(text).strip()

    # Если текст пустой, возвращаем None
    if not text_str:
        return None

    # Просто возвращаем текст как есть
    # Можем убрать лишние пробелы
    text_str = re.sub(r'\s+', ' ', text_str)

    return text_str

# Собираем все уникальные диагнозы из всех столбцов
all_diagnoses = {}
diagnosis_id_counter = 1

# Маппинг столбцов на категории
column_to_category = {
    'Др.Дзы': df_categories[df_categories['category'] == 'Прочие']['id'].iloc[0],
    'ОДА': df_categories[df_categories['category'] == 'Опорно-двигательный аппарат']['id'].iloc[0],
    'ССЗ': df_categories[df_categories['category'] == 'Сердечно-сосудистые']['id'].iloc[0],
    'ЖКТ': df_categories[df_categories['category'] == 'Желудочно-кишечные']['id'].iloc[0],
    'ЛОР': df_categories[df_categories['category'] == 'ЛОР-органы']['id'].iloc[0],
    'Зрение': df_categories[df_categories['category'] == 'Органы зрения']['id'].iloc[0],
    'Одых': df_categories[df_categories['category'] == 'Дыхательная система']['id'].iloc[0],
    'Почки': df_categories[df_categories['category'] == 'Мочевыделительная система']['id'].iloc[0],
    'Энд': df_categories[df_categories['category'] == 'Эндокринные']['id'].iloc[0]
}

# Проходим по всем столбцам с диагнозами
for column_name, category_id in column_to_category.items():
    if column_name in df.columns:
        for cell in df[column_name].dropna():
            if pd.notna(cell) and cell != '':
                # Разбиваем ячейку на отдельные диагнозы (если их несколько)
                if isinstance(cell, str):
                    # Разделители: точка с запятой, запятая
                    parts = re.split(r'[;,]', cell)
                    for part in parts:
                        part = part.strip()
                        if part:  # если не пустая строка
                            name = extract_diagnosis_name(part)
                            if name:  # если есть название
                                # Создаем ключ для проверки уникальности
                                key = (name, category_id)
                                if key not in all_diagnoses:
                                    all_diagnoses[key] = {
                                        'id': diagnosis_id_counter,
                                        'name': name,
                                        'category_id': category_id
                                    }
                                    diagnosis_id_counter += 1

# Создаем DataFrame диагнозов
diagnoses_list = list(all_diagnoses.values())
df_diagnoses = pd.DataFrame(diagnoses_list)

print(f"Таблица diagnoses: {len(df_diagnoses)} записей")
print(df_diagnoses)

# Создаем словарь для быстрого поиска id диагноза
diagnosis_map = {}
for _, row in df_diagnoses.iterrows():
    key = (row['name'], row['category_id'])
    diagnosis_map[key] = row['id']

# Собираем связи работник-диагноз
employee_diagnoses_data = []

for emp_idx, emp_row in df_employees.iterrows():
    emp_id = emp_row['id']
    original_row_idx = emp_row.name  # индекс в исходном DataFrame

    # Проходим по всем столбцам с диагнозами
    for column_name, category_id in column_to_category.items():
        if column_name in df.columns:
            cell = df.at[original_row_idx, column_name]
            if pd.notna(cell) and cell != '':
                # Разбиваем на отдельные диагнозы
                if isinstance(cell, str):
                    parts = re.split(r'[;,]', cell)
                    for part in parts:
                        part = part.strip()
                        if part:
                            name = extract_diagnosis_name(part)
                            if name:
                                # Ищем id диагноза
                                key = (name, category_id)
                                diagnosis_id = diagnosis_map.get(key)

                                if diagnosis_id:
                                    employee_diagnoses_data.append({
                                        'employee_id': emp_id,
                                        'diagnosis_id': diagnosis_id
                                    })

# Создаем DataFrame связей
df_employee_diagnoses = pd.DataFrame(employee_diagnoses_data)

# Убираем дубликаты (на всякий случай)
df_employee_diagnoses = df_employee_diagnoses.drop_duplicates()

print(f"Таблица employee_diagnoses: {len(df_employee_diagnoses)} записей")
print(df_employee_diagnoses.head(10))

from sqlalchemy import create_engine
engine = create_engine('sqlite:///database/risk_assesment.db')

df_employees.to_sql(name='employees', con=engine, if_exists='append', index=False)
df_employee_harm.to_sql(name='employee_harm', con=engine, if_exists='append', index=False)
df_employee_disability.to_sql(name='employee_disability', con=engine, if_exists='append', index=False)
#df_categories.to_sql(name='diagnosis_categories', con=engine, if_exists='append', index=False)
df_diagnoses.to_sql(name='diagnoses', con=engine, if_exists='append', index=False)
#df_departments.to_sql(name='departments', con=engine, if_exists='append', index=False)
#df_positions.to_sql(name='positions', con=engine, if_exists='append', index=False)
df_employee_diagnoses.to_sql(name='employee_diagnoses', con=engine, if_exists='append', index=False)