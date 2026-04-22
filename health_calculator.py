class HealthCalculator:
    """Калькулятор показателя дефицита здоровья (0 - отлично, 1 - максимальный дефицит)"""

    CATEGORY_WEIGHTS = {
        'Сердечно-сосудистые': 0.131,
        'Опорно-двигательный аппарат': 0.230,
        'Органы зрения': 0.184,
        'Желудочно-кишечные': 0.141,
        'ЛОР-органы': 0.065,
        'Дыхательная система': 0.194,
        'Мочевыделительная система': 0.088,
        'Эндокринные': 0.086,
        'Прочие': 0.025
    }

    # Базовый вклад первого диагноза в категории (от 0 до 1)
    BASE_DIAGNOSIS_CONTRIBUTION = 0.5  # Первый диагноз дает 50% от максимального вклада категории

    @staticmethod
    def _calculate_category_contribution(weight, num_diagnoses):
        """
        Рассчитывает вклад категории диагнозов в общий дефицит здоровья
        Возвращает значение от 0 до weight (максимальный вклад категории)

        Используется нелинейная функция с насыщением:
        - 1 диагноз: weight * 0.5
        - 2 диагноза: weight * 0.75
        - 3 диагноза: weight * 0.875
        - и т.д.
        """
        if num_diagnoses == 0:
            return 0.0

        # Нелинейное увеличение вклада: каждый доп. диагноз дает все меньший прирост
        contribution_factor = 1 - (1 - HealthCalculator.BASE_DIAGNOSIS_CONTRIBUTION) ** num_diagnoses
        return weight * contribution_factor

    @staticmethod
    def _calculate_disability_contribution(disability_group):
        """Расчет вклада инвалидности в дефицит здоровья"""
        if not disability_group:
            return 0.0

        disability_contributions = {
            1: 0.35,  # 1 группа - максимальный вклад
            2: 0.25,
            3: 0.15
        }
        return disability_contributions.get(disability_group, 0)
    '''
    @staticmethod
        def _calculate_age_contribution(age):
            """Расчет возрастного вклада в дефицит здоровья"""
            if not age or age <= 40:
                return 0.0
    
            if age >= 70:
                return 0.25  # максимальный вклад от возраста 25%
    
            # Плавное увеличение вклада с 40 до 70 лет
            return min((age - 40) * 0.00833, 0.25)  # 0.00833 = 0.25/30
    
        @staticmethod
        def _calculate_experience_contribution(experience):
            """Расчет вклада стажа в дефицит здоровья"""
            if not experience or experience <= 10:
                return 0.0
    
            if experience >= 40:
                return 0.20  # максимальный вклад от стажа 20%
    
            # Плавное увеличение вклада с 10 до 40 лет
            return min((experience - 10) * 0.00667, 0.20)  # 0.00667 = 0.2/30
    '''


    @staticmethod
    def _calculate_prof_harm_contribution(prof_harm_code):
        """Расчет вклада профвредности в дефицит здоровья"""
        if not prof_harm_code:
            return 0.0

        # Профвредность увеличивает дефицит здоровья в зависимости от класса
        harm_contributions = {
            'Т75.2': 0.15,
        }
        return harm_contributions.get(str(prof_harm_code), 0.15)

    @staticmethod
    def calculate_health_score(employee):
        """
        Рассчитывает показатель дефицита здоровья (0-1)
        0 - отличное здоровье (дефицит минимален)
        1 - критическое здоровье (дефицит максимален)

        Используется мультипликативно-аддитивная модель:
        HealthScore = 1 - (1 - D_diseases) * (1 - D_disability) * (1 - D_age) * (1 - D_exp) * (1 - D_prof)

        Где D_* - это вклады различных факторов в дефицит здоровья (0-1)
        """

        # 1. Вклад заболеваний (агрегируем по категориям)
        diseases_contribution = 0.0
        if hasattr(employee, 'diagnoses') and employee.diagnoses:
            total_weight = 0.0
            weighted_contribution = 0.0

            for category, diagnosis_list in employee.diagnoses.items():
                if category in HealthCalculator.CATEGORY_WEIGHTS:
                    weight = HealthCalculator.CATEGORY_WEIGHTS[category]
                    num_diagnoses = len(diagnosis_list)

                    category_contribution = HealthCalculator._calculate_category_contribution(weight, num_diagnoses)
                    weighted_contribution += category_contribution
                    total_weight += weight

            # Нормализуем вклад, чтобы он не превышал 1
            if total_weight > 0:
                diseases_contribution = min(weighted_contribution / total_weight, 1.0)

        # 2. Вклад инвалидности
        disability_contribution = HealthCalculator._calculate_disability_contribution(
            getattr(employee, 'disability_group', None)
        )

        # 3. Возрастной вклад
        #age = getattr(employee, 'get_age', lambda: None)()
        #age_contribution = HealthCalculator._calculate_age_contribution(age)

        # 4. Вклад стажа
        #experience = getattr(employee, 'get_experience', lambda: None)()
        #exp_contribution = HealthCalculator._calculate_experience_contribution(experience)

        # 5. Вклад профвредности
        prof_contribution = HealthCalculator._calculate_prof_harm_contribution(
            getattr(employee, 'prof_harm_code', None)
        )

        # Композиция вкладов (мультипликативная, как в нечеткой логике)
        # Формула: общий дефицит = 1 - произведение (1 - вклад_i)
        # Это гарантирует, что результат всегда в [0, 1]
        health_score = 1 - (
                (1 - diseases_contribution) *
                (1 - disability_contribution) *
                #(1 - age_contribution) *
                #(1 - exp_contribution) *
                (1 - prof_contribution)
        )

        # Ограничиваем от 0 до 1
        return max(0.0, min(1.0, health_score))