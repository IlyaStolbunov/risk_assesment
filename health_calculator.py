# file name: health_calculator.py
class HealthCalculator:
    """Калькулятор показателя здоровья с учетом данных из БД"""

    @staticmethod
    def calculate_health_score(employee):
        """
        Рассчитывает показатель здоровья (0-1)
        """
        base_score = 1.0

        # Штрафы за диагнозы по категориям
        if hasattr(employee, 'diagnoses') and employee.diagnoses:
            penalties = {
                'Сердечно-сосудистые': 0.20,
                'Опорно-двигательный аппарат': 0.15,
                'Органы зрения': 0.12,
                'Желудочно-кишечные': 0.10,
                'ЛОР-органы': 0.08,
                'Дыхательная система': 0.07,
                'Мочевыделительная система': 0.06,
                'Эндокринные': 0.05,
                'Прочие': 0.03
            }

            for category, diagnosis_list in employee.diagnoses.items():
                if category in penalties:
                    base_penalty = penalties[category]

                    # Учитываем количество диагнозов в категории
                    num_diagnoses = len(diagnosis_list)
                    penalty = min(base_penalty * (1 + 0.2 * (num_diagnoses - 1)), base_penalty * 2)
                    base_score -= penalty

        # Штраф за инвалидность
        if hasattr(employee, 'disability_group') and employee.disability_group:
            disability_penalties = {1: 0.25, 2: 0.15, 3: 0.10}
            base_score -= disability_penalties.get(employee.disability_group, 0)

        # Штраф за профвредность
        if hasattr(employee, 'prof_harm_code') and employee.prof_harm_code:
            base_score -= 0.15

        # Штраф за возраст > 50 лет
        if hasattr(employee, 'get_age'):
            age = employee.get_age()
            if age and age > 50:
                age_penalty = min((age - 50) * 0.005, 0.10)  # 0.5% за каждый год после 50, но не более 10%
                base_score -= age_penalty

        # Штраф за стаж > 20 лет
        if hasattr(employee, 'get_experience'):
            experience = employee.get_experience()
            if experience and experience > 20:
                exp_penalty = min((experience - 20) * 0.01, 0.15)  # 1% за каждый год после 20, но не более 15%
                base_score -= exp_penalty

        # Ограничиваем от 0 до 1
        return max(0.0, min(1.0, base_score))

    @staticmethod
    def get_health_description(score):
        """Описание показателя здоровья"""
        if score >= 0.8:
            return "Отличное"
        elif score >= 0.6:
            return "Хорошее"
        elif score >= 0.4:
            return "Удовлетворительное"
        elif score >= 0.2:
            return "Плохое"
        else:
            return "Критическое"