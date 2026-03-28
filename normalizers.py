"""Модуль для нормализации физических параметров в шкалу [0,1]"""

class ParameterNormalizer:
    """Нормализация физических параметров в шкалу риска (0-1)"""

    # Предельные значения для нормализации (по нормативным документам)
    # 0 - соответствует ПДК/ПДУ, 1 - критическое превышение
    LIMITS = {
        'noise': {
            'pdu': 80,  # ПДУ шума, дБА (по СанПиН)
            'critical': 110,  # Критический уровень, выше которого риск максимален
            'description': 'дБА'
        },
        'vibration': {
            'pdu': 100,  # ПДУ вибрации, дБ (по СанПиН)
            'critical': 120,  # Критический уровень
            'description': 'дБ'
        },
        'chemical': {
            'pdu': 0.3,  # ПДК марганца в сварочных аэрозолях, мг/м³
            'critical': 1.5,  # Критический уровень (5 ПДК)
            'description': 'мг/м³'
        }
    }

    @classmethod
    def normalize_noise(cls, value_db):
        """
        Нормализация уровня шума
        value_db: значение в дБА
        возвращает: значение в шкале [0,1]
        """
        limits = cls.LIMITS['noise']
        return cls._normalize(value_db, limits['pdu'], limits['critical'])

    @classmethod
    def normalize_vibration(cls, value_db):
        """
        Нормализация уровня вибрации
        value_db: значение в дБ
        возвращает: значение в шкале [0,1]
        """
        limits = cls.LIMITS['vibration']
        return cls._normalize(value_db, limits['pdu'], limits['critical'])

    @classmethod
    def normalize_chemical(cls, value_mgm3):
        """
        Нормализация концентрации химического вещества (марганец)
        value_mgm3: значение в мг/м³
        возвращает: значение в шкале [0,1]
        """
        limits = cls.LIMITS['chemical']
        return cls._normalize(value_mgm3, limits['pdu'], limits['critical'])

    @classmethod
    def _normalize(cls, value, pdu, critical):
        """
        Базовый метод нормализации с нелинейной функцией
        Используется сигмоида для более плавного перехода
        """
        if value <= pdu:
            # Значение ниже ПДУ - линейно от 0 до 0.3
            return (value / pdu) * 0.3 if pdu > 0 else 0
        elif value >= critical:
            # Выше критического - максимальный риск
            return 1.0
        else:
            # Между ПДУ и критическим - нелинейный рост
            # Используем квадратичную функцию для ускорения роста риска
            t = (value - pdu) / (critical - pdu)  # 0..1
            # Квадратичная: риск растет быстрее при приближении к критическому
            return 0.3 + (t ** 1.5) * 0.7

    @classmethod
    def denormalize_noise(cls, normalized_value):
        """Обратное преобразование для отображения"""
        limits = cls.LIMITS['noise']
        return cls._denormalize(normalized_value, limits['pdu'], limits['critical'])

    @classmethod
    def denormalize_vibration(cls, normalized_value):
        """Обратное преобразование для отображения"""
        limits = cls.LIMITS['vibration']
        return cls._denormalize(normalized_value, limits['pdu'], limits['critical'])

    @classmethod
    def denormalize_chemical(cls, normalized_value):
        """Обратное преобразование для отображения"""
        limits = cls.LIMITS['chemical']
        return cls._denormalize(normalized_value, limits['pdu'], limits['critical'])

    @classmethod
    def _denormalize(cls, normalized, pdu, critical):
        """Обратное преобразование из шкалы [0,1] в физические значения"""
        if normalized <= 0.3:
            # Линейный участок до ПДУ
            return (normalized / 0.3) * pdu if pdu > 0 else 0
        else:
            # Нелинейный участок от ПДУ до критического
            t = ((normalized - 0.3) / 0.7) ** (1 / 1.5)
            return pdu + t * (critical - pdu)

    @classmethod
    def get_parameter_info(cls, param_type):
        """Получить информацию о параметре"""
        limits = cls.LIMITS.get(param_type, {})
        return {
            'description': limits.get('description', ''),
            'pdu': limits.get('pdu', 0),
            'critical': limits.get('critical', 0)
        }