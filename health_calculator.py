class HealthCalculator:
    """Калькулятор показателя здоровья"""

    @staticmethod
    def calculate_health_score(employee):
        """
        Рассчитывает показатель здоровья (0-1)

        Формула:
        1.0 - (штрафы за диагнозы и инвалидность)
        """
        base_score = 1.0

        # Штрафы за диагнозы
        penalties = {
            'professional': 0.20,  # проф. вредность -20%
            'cardio': 0.15,  # ССЗ -15%
            'vision': 0.10,  # проблемы со зрением -10%
            'gastro': 0.08,  # ЖКТ -8%
            'ent': 0.05  # ЛОР -5%
        }

        # Применяем штрафы
        for diagnosis, penalty in penalties.items():
            if employee.diagnoses.get(diagnosis, False):
                base_score -= penalty

        # Дополнительный штраф за инвалидность
        if employee.disability:
            base_score -= 0.10

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