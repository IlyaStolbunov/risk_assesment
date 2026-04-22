"""Модуль для нормализации физических параметров в шкалу [0,1] по специальным формулам"""

import math
import numpy as np
from scipy.integrate import quad


class ParameterNormalizer:
    """Нормализация физических параметров в шкалу риска (0-1) по формулам"""

    # Константы для расчетов
    CHEMICAL_PDC = 0.2  # Среднесуточная ПДК для марганца, мг/м³
    T0 = 1.0  # Базовый период для расчета шума, год

    @classmethod
    def normalize_vibration(cls, vibration_db, experience_years):
        """
        Нормализация уровня вибрации по формуле:
        Lv - дано в дБ
        T - стаж в годах
        Lt = 10 * lg(T)
        Lc = 1.54 * (0.25 * Lv + Lt - 38)
        Lc = 10 * lg(C / C0), C0 = 0.01 = 1%
        C = C0 * 10^(Lc/10)

        vibration_db: уровень вибрации в дБ
        experience_years: стаж работы в годах
        возвращает: нормализованное значение в шкале [0,1]
        """
        if experience_years is None or experience_years <= 0:
            experience_years = 1.0  # Минимальный стаж для расчета

        # Расчет Lt = 10 * lg(T)
        Lt = 10 * math.log10(experience_years)

        # Расчет Lc
        Lc = 1.54 * (0.25 * vibration_db + Lt - 38)

        # Расчет C
        C0 = 0.01  # 1%
        C = C0 * (10 ** (Lc / 10))

        # Ограничиваем от 0 до 1
        return max(0.0, min(1.0, C))

    @classmethod
    def normalize_noise(cls, noise_db, experience_years):
        """
        Нормализация уровня шума по формуле:
        Lдш = Lэкв + 10 * lg(T / T0)
        P = -8.25 + 0.07 * Lдш
        Noise = (1 / sqrt(2*pi)) * S, где S = ∫(-∞, P) e^(x/2) dx

        noise_db: уровень шума в дБА
        experience_years: стаж работы в годах
        возвращает: нормализованное значение в шкале [0,1]
        """
        if experience_years is None or experience_years <= 0:
            experience_years = 1.0

        # Расчет Lдш
        Ldsh = noise_db + 10 * math.log10(experience_years / cls.T0)

        # Расчет P
        P = -8.25 + 0.07 * Ldsh

        # Расчет интеграла S = ∫(-∞, P) e^(x/2) dx
        # Используем scipy.integrate.quad с нижним пределом -np.inf
        def integrand(x):
            return np.exp(x / 2)

        S, _ = quad(integrand, -np.inf, P)

        # Расчет Noise
        noise_val = (1.0 / math.sqrt(2 * math.pi)) * S

        # Ограничиваем от 0 до 1
        return max(0.0, min(1.0, noise_val))

    @classmethod
    def normalize_chemical(cls, chemical_mgm3):
        """
        Нормализация концентрации химического вещества (марганец)
        Если C / ПДК > 1, то значение = 1
        Если C / ПДК ≤ 1, то значение = C / ПДК

        chemical_mgm3: концентрация марганца в мг/м³
        возвращает: нормализованное значение в шкале [0,1]
        """
        if chemical_mgm3 is None or chemical_mgm3 <= 0:
            return 0.0

        ratio = chemical_mgm3 / cls.CHEMICAL_PDC

        # Если превышает ПДК, риск максимален
        if ratio > 1.0:
            return 1.0
        else:
            # Пропорционально ПДК
            return ratio