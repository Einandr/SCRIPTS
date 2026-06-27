import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import RegularGridInterpolator
from scipy.interpolate import interp1d


plots = False
# plots = True


# Нормативный вес снегового покрова по районам (кПа)
snow_regions = {
    "I": 0.5,    # кПа
    "II": 1.0,   # кПа
    "III": 1.5,  # кПа
    "IV": 2.0,   # кПа
    "V": 2.5,    # кПа
    "VI": 3.0,   # кПа
    "VII": 3.5,  # кПа
    "VIII": 4.0  # кПа
}


# Коэффициенты μ для односкатных/двускатных покрытий
def get_mu_single_pitch(alpha_deg: float) -> float:
    """Возвращает коэффициент μ для односкатных/двускатных покрытий."""
    if alpha_deg <= 30:
        return 1.0
    elif alpha_deg >= 60:
        return 0.0
    else:
        return 1.0 - (alpha_deg - 30) / 30  # Линейная интерполяция


# Коэффициент сноса снега ce
def get_ce(k: float, lc: float) -> float:
    """Возвращает коэффициент ce для пологих покрытий."""
    return max(0.5, (1.2 - 0.4 * k**0.5) * (0.8 + 0.002 * lc))


# Термический коэффициент ct
def get_ct(is_insulated: bool, alpha_deg: float) -> float:
    """Возвращает термический коэффициент ct."""
    if not is_insulated and alpha_deg > 3:
        return 0.8
    return 1.0


# Расчёт снеговой нагрузки
def calculate_snow_load(
    region: str,
    alpha_deg: float,
    is_insulated: bool = True,
    k: float = 1.0,
    lc: float = 0.0
) -> float:
    """
    Рассчитывает снеговую нагрузку S0 по СП 20.13330.2016.

    :param region: Снеговой район (I-VIII)
    :param alpha_deg: Уклон покрытия, градусы
    :param is_insulated: Утеплено ли покрытие
    :param k: Коэффициент типа местности
    :param lc: Характерный размер покрытия, м
    :return: Снеговая нагрузка S0, кПа
    """
    Sg = snow_regions[region]
    mu = get_mu_single_pitch(alpha_deg)
    ce = get_ce(k, lc)
    ct = get_ct(is_insulated, alpha_deg)
    return ce * ct * mu * Sg





# ВЕТЕР

# Нормативное ветровое давление по районам (кПа)
wind_regions = {
    "Ia": 0.17,
    "I": 0.23,
    "II": 0.30,
    "III": 0.38,
    "IV": 0.48,
    "V": 0.60,
    "VI": 0.73,
    "VII": 0.85
}

# Параметры для расчёта k(ze) и ζ(ze) на высотах 5 и 10 м
terrain_params = {
    "A": {"alpha": 0.15, "k5": 0.75, "k10": 1.00, "zeta5": 0.85, "zeta10": 0.76},
    "B": {"alpha": 0.20, "k5": 0.50, "k10": 0.65, "zeta5": 1.22, "zeta10": 1.06},
    "C": {"alpha": 0.25, "k5": 0.40, "k10": 0.40, "zeta5": 1.78, "zeta10": 1.78}
}

# Предельный Безразмерный период Tg_lim (п. 11.1.10 таблица 11.5)
Tg_lim = {
    0.15: 0.0077,
    0.22: 0.014,
    0.3: 0.023
}

# Число Струхаля St
St = {
    "round": 0.2,  # для круглых сечений
    "sharp": 0.11  # для сечений с острыми кромками
}


# Расчёт k(ze) (п. 11.1.6 формула 11.4)
def calculate_k(ze: float, terrain_type: str) -> float:
    """
    Рассчитывает коэффициент k(ze) по СП 20.13330.2016.

    :param ze: Эквивалентная высота, м
    :param terrain_type: Тип местности (A, B, C)
    :return: Коэффициент k(ze)
    """
    params = terrain_params[terrain_type]
    alpha = params["alpha"]
    k5 = params["k5"]
    k10 = params["k10"]

    # print(f"Коэффициент в формуле для давления ветра alpha - {alpha}")
    # print(f"Коэффициент в формуле для давления ветра k10 - {k10}")
    if ze <= 5:
        return k5
    elif 5 < ze < 10:
        return k5 + (k10 - k5) * (ze - 5) / (10 - 5)
    return k10 * (ze / 10) ** (2 * alpha)





def calculate_average_k_analytical(z_start: float, z_end: float, terrain_type: str) -> float:
    """
    Рассчитывает среднее значение k(ze) на интервале [z_start, z_end] аналитически.

    :param z_start: Начальная высота, м
    :param z_end: Конечная высота, м
    :param terrain_type: Тип местности (A, B, C)
    :return: Среднее значение k(ze) на интервале
    """
    params = terrain_params[terrain_type]
    alpha = params["alpha"]
    k5 = params["k5"]
    k10 = params["k10"]

    # Проверка на корректность интервала
    if z_start >= z_end:
        raise ValueError("Начальная высота должна быть меньше конечной.")

    if z_end <= 5:
        return k5

    z_start_integral = 10
    if z_start >= 10:
        z_start_integral = z_start

    if z_end > 10:
        u_start = z_start_integral / 10
        u_end = z_end / 10
        integral_formula = k10 * 10 * ((u_end ** (2 * alpha + 1)) / (2 * alpha + 1) - (u_start ** (2 * alpha + 1)) / (2 * alpha + 1))
        print(f'integral_formula = {integral_formula}')

    if z_start >= 10:
        return integral_formula / (z_end - z_start)

    integral_constant_and_linear = 0
    if z_start < 5:
        integral_constant_and_linear += (5-z_start) * k5
        print(f'integral_constant = {integral_constant_and_linear}')
    z_start_linear = 5
    z_end_linear = 10
    if 5 <= z_start < 10:
        z_start_linear = z_start
    if z_end <= 10:
        z_end_linear = z_end
    integral_constant_and_linear += k5 * (z_end_linear-z_start_linear) + (k10 - k5) / (10 - 5) * (z_end_linear*z_end_linear/2 - 5*z_end_linear - z_start_linear*z_start_linear + 5*z_start_linear)
    print(f'integral_constant_and_linear = {integral_constant_and_linear}')
    if z_end <= 10:
        return integral_constant_and_linear / (z_end - z_start)
    else:
        return (integral_constant_and_linear + integral_formula) / (z_end - z_start)



# Пример использования
z_start = 0
z_end = 70
terrain_type = "A"

average_k = calculate_average_k_analytical(z_start, z_end, terrain_type)
print(f"Среднее значение k(ze) на интервале [{z_start}, {z_end}] м: {average_k:.4f}")

print('debug')







def calculate_reynolds_number(ze: float, w0: float, terrain_type: str, d: float, gamma_f: float = 1.4) -> float:
    """
    Рассчитывает число Рейнольдса Re по формуле (В.1) СП 20.13330.2016.

    :param ze: Высота, м
    :param w0: Нормативное ветровое давление, кПа
    :param terrain_type: Тип местности (A, B, C)
    :param d: Характерный размер сооружения, м
    :param gamma_f: Коэффициент надёжности по нагрузке (по умолчанию 1.4)
    :return: Число Рейнольдса Re
    """
    k_ze = calculate_k(ze, terrain_type)
    print(f'Re calculation d = {d} wo = {w0} k_ze = {k_ze} gamma_f = {gamma_f}')
    return 0.88 * d * math.sqrt(w0 * 1000 * k_ze * gamma_f) * 1e5














# Расчёт ζ(ze) (п. 11.1.8 формула 11.6)
def calculate_zeta(ze: float, terrain_type: str) -> float:
    """
    Рассчитывает коэффициент пульсаций ζ(ze) по СП 20.13330.2016.

    :param ze: Эквивалентная высота, м
    :param terrain_type: Тип местности (A, B, C)
    :return: Коэффициент ζ(ze)
    """
    params = terrain_params[terrain_type]
    alpha = params["alpha"]
    zeta5 = params["zeta5"]
    zeta10 = params["zeta10"]
    # print(f"Коэффициент в формуле для пульсации давления ветра alpha - {alpha}")
    print(f"Коэффициент в формуле для пульсации давления ветра zeta5 - {zeta5}")
    print(f"Коэффициент в формуле для пульсации давления ветра zeta10 - {zeta10}")

    if ze <= 5:
        return zeta5
    elif 5 < ze < 10:
        return zeta5 + (zeta10 - zeta5) * (ze - 5) / (10 - 5)
    else:
        return zeta10 * (ze / 10) ** (-alpha)


# Коэффициент динамичности ξ
def calculate_xi(epsilon_1: float, delta: float) -> float:
    """
    Рассчитывает коэффициент динамичности ξ по аппроксимации.

    :param epsilon_1: Параметр ε1
    :param delta: Логарифмический декремент колебаний (0.15 или 0.3)
    :return: Коэффициент динамичности ξ
    """
    if delta == 0.15:
        if epsilon_1 <= 0.1:
            return 1 + 20 * epsilon_1
        else:
            return 3
    elif delta == 0.3:
        if epsilon_1 <= 0.2:
            return 1 + 10 * epsilon_1
        else:
            return 3
    else:
        raise ValueError("Некорректное значение логарифмического декремента колебаний")


# Безразмерный период Tg1
def calculate_epsilon_1(w0: float, k_ze: float, gamma_f: float, f1: float) -> float:
    """
    Рассчитывает параметр ε1.

    :param w0: Нормативное ветровое давление, кПа
    :param k_ze: Коэффициент k(ze)
    :param gamma_f: Коэффициент надёжности по нагрузке
    :param f1: Первая собственная частота, Гц
    :return: Параметр ε1
    """



    return (w0 * k_ze * gamma_f) ** 0.5 / (940 * f1)


# Предельное значение частоты собственных колебаний f_lim, Гц (п. 11.1.10 формула 11.9 а)
def calculate_f_lim(delta: float, w0: float, k_ze: float, gamma_f: float) -> float:
    """
    Рассчитывает предельное значение частоты собственных колебаний f_lim.

    :param delta: Логарифмический декремент колебаний (0.15, 0.22, 0.3)
    :param w0: Нормативное ветровое давление, кПа
    :param k_ze: Коэффициент k(ze)
    :param gamma_f: Коэффициент надёжности по нагрузке
    :return: Предельное значение частоты f_lim, Гц
    """
    Tg = Tg_lim[delta]
    return (w0 * 1000 * k_ze * gamma_f) ** 0.5 / (940 * Tg)


# Таблица 11.6 в виде двумерного массива numpy
v_table = np.array([
    [0.95, 0.89, 0.85, 0.80, 0.72, 0.63, 0.53],  # chi = 5
    [0.92, 0.87, 0.84, 0.78, 0.72, 0.63, 0.53],  # chi = 10
    [0.88, 0.84, 0.81, 0.76, 0.70, 0.61, 0.52],  # chi = 20
    [0.83, 0.80, 0.77, 0.73, 0.67, 0.59, 0.50],  # chi = 40
    [0.76, 0.73, 0.71, 0.68, 0.63, 0.56, 0.47],  # chi = 80
    [0.67, 0.65, 0.64, 0.61, 0.57, 0.51, 0.44],  # chi = 160
    [0.56, 0.54, 0.53, 0.51, 0.48, 0.44, 0.38]   # chi = 350
])

# Значения ρ и χ
rho_values = np.array([0.1, 5, 10, 20, 40, 80, 160])
chi_values = np.array([5, 10, 20, 40, 80, 160, 350])


# Коэффициент пространственной корреляции пульсаций давления nu (таблица 11.6)
def get_correlation_coefficient(rho: float, chi: float) -> float:
    """
    Возвращает коэффициент пространственной корреляции пульсаций давления nu с интерполяцией по ρ и χ.

    :param rho: Параметр ρ, м
    :param chi: Параметр χ, м
    :return: Коэффициент nu
    """
    # Создаём интерполятор
    interp_func = RegularGridInterpolator(
        (chi_values, rho_values),
        v_table,
        method='linear',
        bounds_error=False,  # Разрешаем экстраполяцию
        fill_value=None     # Значение по умолчанию при экстраполяции
    )
    # Интерполяция
    return float(interp_func((chi, rho)))


# Аэродинамические коэффициенты для стен прямоугольных зданий (В.1.2)
def get_wall_aerodynamic_coefficient(side: str) -> float:
    """
    Возвращает аэродинамический коэффициент для стен.

    :param side: Сторона здания (windward, leeward, lateral_A, lateral_B, lateral_C)
    :return: Коэффициент ce
    """
    if side == "windward":
        return 0.8
    elif side == "leeward":
        return -0.5
    elif side == "lateral_A":
        return -1
    elif side == "lateral_B":
        return -0.8
    elif side == "lateral_C":
        return -0.5
    else:
        raise ValueError("Некорректная сторона здания")


# Расчёт средней составляющей ветровой нагрузки
def calculate_wind_load_mean(
    wind_region: str,
    ze: float,
    terrain_type: str,
    c: float
) -> float:
    """
    Рассчитывает среднюю составляющую ветровой нагрузки wm по СП 20.13330.2016.

    :param region: Ветровой район (Ia, I, II, III, IV, V, VI, VII)
    :param ze: Эквивалентная высота, м
    :param terrain_type: Тип местности (A, B, C)
    :param c: Аэродинамический коэффициент
    :return: Средняя ветровая нагрузка wm, кПа
    """
    w0 = wind_regions[wind_region]
    k = calculate_k(ze, terrain_type)
    wm = w0 * k * c
    # print(f"Для ветрового региона {wind_region} нормативное значение ветрового давления - {w0} кПа")
    # print(f"Тип местности - {terrain_type}")
    # print(f"Расчётная эквивалентная высота ze - {ze}")
    # print(f"Коэффициент, учитывающий изменение ветрового давления для высоты k(ze) - {k}")
    # print(f"Аэродинамический коэффициент с - {c}")
    # print(f"Нормативное значение средней составляющей основной ветровой нагрузки wm - {wm} кПа")
    return wm


# Расчёт пульсационной составляющей ветровой нагрузки
def calculate_wind_load_pulsation(
    wm: float,
    ze: float,
    terrain_type: str,
    nu: float
) -> float:
    """
    Рассчитывает пульсационную составляющую ветровой нагрузки wp по СП 20.13330.2016.

    :param wm: Средняя составляющая ветровой нагрузки, кПа
    :param ze: Эквивалентная высота, м
    :param terrain_type: Тип местности (A, B, C)
    :param nu: Коэффициент пространственной корреляции
    :return: wg: Пульсационная ветровая нагрузка wp, кПа
    """
    zeta = calculate_zeta(ze, terrain_type)
    wg = wm * zeta * nu

    print(f"Коэффициент пульсации давления ветра zeta - {zeta}")
    print(f"Коэффициент пространственной корреляции пульсаций давления ветра v - {nu}")
    print(f"Нормативное значение пульсационной составляющей основной вет нагрузки wp - {wg} кПа")
    return wg


# Критическая скорость ветра V_cr_i
def calculate_V_cr_i(f_i: float, d: float, St: float, k_v: float = 1.0) -> float:
    """
    Рассчитывает критическую скорость ветра V_cr,i по формуле (11.11).

    :param f_i: Собственная частота колебаний по i-й изгибной собственной форме, Гц
    :param d: Поперечный размер сооружения, м
    :param St: Число Струхаля
    :param k_v: Коэффициент, учитывающий эффект захвата частоты (0.9–1.1)
    :return: Критическая скорость ветра V_cr,i, м/с
    """
    return k_v * f_i * d / St


# Максимальная скорость ветра на высоте V_max
def calculate_V_max(ze: float, w0: float, terrain_type: str) -> float:
    """
    Рассчитывает максимальную скорость ветра V_max по формуле (11.13).

    :param ze: Эквивалентная высота, м
    :param w0: Нормативное ветровое давление, кПа
    :param terrain_type: Тип местности (A, B, C)
    :return: Максимальная скорость ветра V_max, м/с
    """
    k_ze = calculate_k(ze, terrain_type)
    return 1.5 * math.sqrt(w0 * k_ze * 1000)


def check_resonance_condition(V_cr_i: float, V_max: float) -> bool:
    """
    Проверяет условие резонансного вихревого возбуждения (11.12).

    :param V_cr_i: Критическая скорость ветра, м/с
    :param V_max: Максимальная скорость ветра на высоте, м/с
    :return: True, если резонансное возбуждение возможно
    """
    return V_cr_i <= V_max


# Аэродинамический коэффициент поперечной силы при резонансном вихревом возбуждении (п. В.2.2)
def get_cy_cr(V_cr_i: float, V_max: float, section_shape: str, b_over_d: float = 1.0) -> float:
    """
    Возвращает коэффициент поперечной силы cy,cr с учётом формы сечения.

    :param V_cr_i: Критическая скорость ветра, м/с
    :param V_max: Максимальная скорость ветра, м/с
    :param section_shape: Форма сечения ("round", "rectangular")
    :param b_over_d: Отношение размеров b/d (для прямоугольных сечений)
    :return: Коэффициент cy,cr
    """
    ratio = V_cr_i / V_max
    print(f"Отношение критической скорости к максимальной V_cr_i / V_max = {ratio}")

    if section_shape == "round":
        print("Для кругого сечения Cy = 0.3")
        return 0.3
    elif section_shape == "rectangular":
        if b_over_d > 0.5:
            if ratio < 0.8:
                print(f"Отношение b/d = {b_over_d} > 0.5 для прямоугольных сечений, при V_cr_i / V_max < 0.8 Cy = 1.1")
                return 1.1
            else:
                print(f"Отношение b/d = {b_over_d} > 0.5 для прямоугольных сечений, при V_cr_i / V_max < 0.8 Cy = 0.6")
                return 0.6
        else:
            print(f"Отношение b/d = {b_over_d} < 0.5 для прямоугольных сечений - расчет на резонансное вихревое возбуждение можно не проводить")
            return 0
    else:
        raise ValueError("Некорректная форма сечения. Используйте 'round' или 'rectangular'")


# Интенсивность воздействия F(z), действующего при резонансном вихревом возбуждении по i-й собственной форме в направлении, перпендикулярном средней скорости ветра (п. В.2.1 формула В.8)
def calculate_F_i(z: float, V_cr_i: float, cy_cr: float, d: float, delta_s: float, phi_i: float = 1.0) -> float:
    """
    Рассчитывает интенсивность воздействия F_i(z) по формуле (В.8).

    :param z: Координата вдоль оси сооружения, м
    :param V_cr_i: Критическая скорость ветра, м/с
    :param cy_cr: Аэродинамический коэффициент поперечной силы
    :param d: Поперечный размер сооружения, м
    :param delta_s: Логарифмический декремент конструкционного демпфирования
    :param phi_i: i-я форма собственных колебаний (по умолчанию 1.0)
    :return: Интенсивность воздействия F_i(z), Н/м
    """
    return 0.61 * math.pi * (V_cr_i ** 2) * cy_cr * phi_i * d / delta_s


# При расчете сооружения на резонансное вихревое возбуждение наряду с воздействием (В.2.1) необходимо учитывать также действие ветровой нагрузки, параллельной средней скорости ветра. Средняя w_m,cr и пульсационная w_g,cr составляющие этого воздействия (п. В.2.3 формула В.10)
def calculate_w_cr(V_cr: float, V_max: float, w_m: float, w_g: float) -> tuple[float, float]:
    """
    Рассчитывает w_m,cr и w_g,cr по формулам (В.2.3).
    """
    ratio = (V_cr / V_max) ** 2
    w_m_cr = ratio * w_m
    w_g_cr = ratio * w_g
    return w_m_cr, w_g_cr



# Контрольные точки с графика относительного удлинения (рисунок В.23)
lambda_e_control = np.array([1, 10, 100, 200])
k_lambda_data = {
    0.1: np.array([0.99, 0.99, 0.995, 1]),
    0.5: np.array([0.88, 0.91, 0.98, 1]),
    0.9: np.array([0.82, 0.87, 0.97, 1]),
    0.95: np.array([0.73, 0.8, 0.96, 1]),
    1.0: np.array([0.60, 0.7, 0.95, 1])
}


def calculate_k_lambda(lambda_e: float, phi: float) -> float:
    """
    Рассчитывает коэффициент k_λ с использованием логарифмической интерполяции.

    :param lambda_e: Относительное удлинение λ_e
    :param phi: Коэффициент заполнения φ
    :return: Коэффициент k_λ
    """
    # Выбираем ближайшее значение φ из доступных
    available_phis = [0.1, 0.5, 0.9, 0.95, 1.0]
    closest_phi = min(available_phis, key=lambda x: abs(x - phi))

    # Логарифмическая интерполяция
    log_lambda_e = np.log10(lambda_e_control)
    log_k_lambda = np.log10(k_lambda_data[closest_phi])

    # Интерполяция в логарифмическом масштабе
    interp_func = interp1d(log_lambda_e, log_k_lambda, kind='linear', fill_value='extrapolate')
    log_k_lambda_interp = interp_func(np.log10(lambda_e))

    # Возвращаем результат в нормальном масштабе
    return 10 ** log_k_lambda_interp













# ИСХОДНЫЕ ДАННЫЕ СНЕГ

# Снеговой район
snow_region = "II"



# ИСХОДНЫЕ ДАННЫЕ ВЕТЕР

# Ветровой регион
wind_region = "II"

# Тип местности
# А — открытые побережья морей, озер и водохранилищ, сельские местности, в том числе с постройками высотой менее 10 м, пустыни, степи, лесостепи, тундра
# В — городские территории, лесные массивы и другие местности, равномерно покрытые препятствиями высотой более 10 м
# С — городские районы с плотной застройкой зданиями высотой более 25 м
terrain_type = "A"

# Значение суммарного логарифмического декремента колебаний delta следует принимать (п.11.1.10 таблица 11.5):
# а) для железобетонных и каменных сооружений, а также для зданий со стальным каркасом при наличии ограждающих конструкций delta = 0.3
# б) для стальных сооружений, футерованных дымовых труб, аппаратов колонного типа, в том числе на железобетонных постаментах delta = 0.15
# в) для стекла, а также смешанных сооружений, имеющих одновременно стальные и железобетонные несущие конструкции delta = 0.22
delta = 0.15

# Высота сооружения
H = 70

# Эквивалентная высота, м - согласно 11.1.5
ze = H

# Логарифмический декремент конструкционного демпфирования принимаемый равным (п. В.2.1):
# а) для металлических сооружений delta_s = 0.05
# б) для железобетонных сооружений delta_s = 0.1
delta_s = 0.05

# Коэффициент надежности по нагрузке при расчёте на резонансное вихревое возбуждение (п. 11)
gamma_f_essy_resonance = 1

# Коэффициент надежности по нагрузке при расчёте на основную и пиковую ветровую нагрузку (п. 11)
gamma_f_wind = 1.4

section_type = "round"  # Тип сечения (round или sharp)

# Поперечный размер сооружения, м
D = 4.2
# Длина трубы
L = 56

# Первая собственная частота, Гц
f1 = 1.37


# РАСЧЕТ СНЕГ
alpha_deg = 20  # уклон 20 градусов
is_insulated = True
k = 1.0  # тип местности A
lc = 50  # характерный размер, м

snow_load = calculate_snow_load(snow_region, alpha_deg, is_insulated, k, lc)
print(f"Снеговая нагрузка S0: {snow_load:.3f} кПа")



# РАСЧЕТ ВЕТЕР
print('\nВЕТЕР')

# СРЕДНЯЯ СОСТАВЛЯЮЩАЯ ОСНОВНОЙ ВЕТРОВОЙ НАГРУЗКИ
# Нормативное значение ветрового давления, кПа (п. 11.1.4, таблица 11.1)
w0 = wind_regions[wind_region]
print(f"Для ветрового региона {wind_region} нормативное значение ветрового давления - {w0} кПа")
params = terrain_params[terrain_type]
alpha = params["alpha"]
k5 = params["k5"]
k10 = params["k10"]
print(f"Коэффициенты в формуле для давления ветра: alpha = {alpha}, k5 = {k5}, k10 = {k10}")
# Коэффициент k(ze), учитывающий изменение ветрового давления для высоты ze (п. 11.1.6 формула 11.4)
k = calculate_k(ze, terrain_type)
print(f"Коэффициент, учитывающий изменение ветрового давления для высоты k = {k} при высоте ze = {ze}")

# ПРОВЕРКА НА РЕЗОНАНСНОЕ ВИХРЕВОЕ ВОЗБУЖДЕНИЕ
# Относительное удлинение
lambda_e = 2*L/D
print(f"Относительное удлинение lambda_e = {lambda_e}, при длине L = {L} и диаметре D = {D}")
# Предельное значение частоты собственных колебаний f_lim, Гц (п. 11.1.10 формула 11.9 а)
f_lim = calculate_f_lim(delta, w0, k, gamma_f_essy_resonance)
print(f"Предельное значение частоты собственных колебаний f_lim = {f_lim:.3f} Гц при логарифмическом декременте колебаний delta = {delta} и коэффициенте надежности по нагрузке {gamma_f_essy_resonance}")
# Число Струхаля
St_value = St[section_type]
# Критическая скорость ветра (п. 11.3.2 формула 11.11)
V_cr_i = calculate_V_cr_i(f1, D, St_value, 0.9)
print(f"Критическая скорость ветра V_cr,i = {V_cr_i:.2f} м/с при частоте {f1}, диаметре {D} и числе Струхаля {St_value}")
# Эквивалентная высота для проверки на резонансное вихревое возбуждение
ze_eddy_resonance = 0.8*H
# Коэффициент k(ze) для проверки на резонансное вихревое возбуждение
k_eddy_resonance = calculate_k(ze_eddy_resonance, terrain_type)
# Максимальная скорость ветра на уровне ze (п. 11.2.2 формула 11.13)
V_max = calculate_V_max(w0, k_eddy_resonance, terrain_type)
print(f"Максимальная скорость ветра V_max = {V_max:.2f} м/с при высоте {ze_eddy_resonance} и коэффициенте k = {k_eddy_resonance}")
# Проверка условия резонансного возбуждения (п. 11.3.3 формула 11.12)
resonance_possible = check_resonance_condition(V_cr_i, V_max)
print(f"Резонансное вихревое возбуждение возможно: {resonance_possible}")
# Аэродинамический коэффициент поперечной силы при резонансном вихревом возбуждении (п. В.2.2)
cy_cr = get_cy_cr(V_cr_i, V_max, "round")
print(f"Аэродинамический коэффициент поперечной силы при резонансном вихревом возбуждении Сy,cr = {cy_cr:.2f}")
# Интенсивность воздействия
F_i = calculate_F_i(ze, V_cr_i, cy_cr, D, delta_s)
print(f"Интенсивность воздействия F_i(z): {F_i:.2f} Н/м при логарифмическом декременте колебаний для металлических сооружений delta_s = {delta_s}")
# Число Рейнольдса
Re = calculate_reynolds_number(ze, w0, terrain_type, D, gamma_f_wind)
print(f"Число Рейнольдса {Re}")
# Относительное удлинение k_lambda (п. В.1.15 рисунок В.23)
k_lambda = calculate_k_lambda(lambda_e, 1)
print(f"Относительное удлинение k_lambda = {k_lambda}")
# Аэродинамический коэффициент для цилиндрической трубы - УТОЧНЯТЬ по графику В.17
ce = 0.64  # труба
# ce = get_wall_aerodynamic_coefficient("windward")  # наветренная стена







# Нормативное значение средней составляющей основной ветровой нагрузки, кПа (п.11.1.3)
wm = calculate_wind_load_mean(wind_region, ze, terrain_type, ce)
print(f"Средняя ветровая нагрузка wm: {wm:.3f} кПа на высоте {ze} при аэродинамическом коэффициенте {ce}")

print('STOP')

# Размер ρ, м (п. 11.1.11 таблица 11.7) (равен диаметру трубы или ширине наветренной стороны)
rho = 4.1
# Размер χ, м (п. 11.1.11 таблица 11.7) (равен длине трубы или высоте участка наветренной стороны)
chi = 60

# Коэффициент пространственной корреляции пульсаций давления ветра (п. 11.1.11 таблица 11.6)
nu = get_correlation_coefficient(rho, chi)

# nu = 0.8




# Расчёт пульсационной составляющей
wg = calculate_wind_load_pulsation(wm, ze, terrain_type, nu)
print(f"Пульсационная ветровая нагрузка wp: {wg:.3f} кПа")

# Полная ветровая нагрузка
w = wm + wg



# Ветровая нагрузка, параллельная скорости ветра при резонансном вихревом возбуждении (п. В.2.3)
wm_cr, wg_cr = calculate_w_cr(V_cr_i, V_max, wm, wg)
print(f"Средняя составляющая w_m,cr: {wm_cr:.4f} кПа")
print(f"Пульсационная составляющая w_g,cr: {wg_cr:.4f} кПа")










# ГРАФИКИ
if plots:
    # Диапазон значений ze
    ze_range = np.linspace(0, 300, 1000)

    # Создаём графики
    plt.figure(figsize=(14, 12))

    # График для k(ze)
    plt.subplot(3, 2, 1)
    for terrain_type in ["A", "B", "C"]:
        k_values = [calculate_k(ze, terrain_type) for ze in ze_range]
        plt.plot(ze_range, k_values, label=f"Тип местности {terrain_type}")
    plt.title(r'Коэффициент k($z_{e}$)')
    plt.xlabel(r'$z_{e}$, м')
    plt.ylabel(r'k($z_{e}$)')
    plt.ylim(bottom=0)
    plt.xlim(left=0, right=300)
    plt.grid(True)
    plt.legend()

    # График для ζ(ze)
    plt.subplot(3, 2, 2)
    for terrain_type in ["A", "B", "C"]:
        zeta_values = [calculate_zeta(ze, terrain_type) for ze in ze_range]
        plt.plot(ze_range, zeta_values, label=f"Тип местности {terrain_type}")
    plt.title(r'Коэффициент пульсаций ζ($z_{e}$)')
    plt.xlabel(r'$z_{e}$, м')
    plt.ylabel('ζ')
    plt.ylim(bottom=0)
    plt.xlim(left=0, right=300)
    plt.grid(True)
    plt.legend()

    # График для максимальной скорости ветра V_max(ze)
    plt.subplot(3, 2, 3)
    for terrain_type in ["A", "B", "C"]:
        V_max_values = [calculate_V_max(ze, w0, terrain_type) for ze in ze_range]
        plt.plot(ze_range, V_max_values, label=f"Тип местности {terrain_type}")
    # r'$omega,\ \frac{1}{\text{с}}$'  r'$\\upsilon,\ м/с$'
    plt.title(r'Максимальная скорость ветра $\upsilon_{\max}(z_{e})$')
    plt.xlabel(r'$z_{e}$, м')
    plt.ylabel(r'$\upsilon_{\max}$, м/с')
    plt.xlim(left=0, right=300)
    plt.ylim(bottom=0)
    plt.grid(True)
    plt.legend()

    # График для пульсационной составляющей ветровой нагрузки w_g(ze)
    plt.subplot(3, 2, 4)
    for terrain_type in ["A", "B", "C"]:
        w_g_values = [calculate_wind_load_pulsation(ze, w0, terrain_type, nu) for ze in ze_range]
        plt.plot(ze_range, w_g_values, label=f"Тип местности {terrain_type}")
    plt.title(r'Пульсационная составляющая ветровой нагрузки $w_g (z_{e})$')
    plt.xlabel(r'$z_{e}$, м')
    plt.ylabel(r'$w_g$, кПа')
    plt.xlim(left=0, right=300)
    plt.ylim(bottom=0)
    plt.grid(True)
    plt.legend()

    plt.subplot(3, 2, 5)
    for terrain_type in ["A", "B", "C"]:
        Re_values = [calculate_reynolds_number(ze, w0, terrain_type, D, gamma_f_wind) for ze in ze_range]
        plt.plot(ze_range, Re_values, label=f"Тип местности {terrain_type}")
    plt.title(r'Число Рейнольдса $Re$')
    plt.xlabel(r'$z_{e}$, м')
    plt.ylabel(r'$Re$')
    plt.xlim(left=0, right=300)
    plt.ylim(bottom=0)
    plt.grid(True)
    plt.legend()

    plt.subplot(3, 2, 6)
    lambda_e_plot = np.logspace(0, 2.3, 100)  # Логарифмическая шкала от 1 до 200
    for phi in [0.1, 0.5, 0.9, 0.95, 1.0]:
        lambda_e_plot = np.logspace(0, 2.3, 100)  # Логарифмическая шкала от 1 до 200
        k_lambda_values = [calculate_k_lambda(lambda_e, phi) for lambda_e in lambda_e_plot]
        plt.plot(lambda_e_plot, k_lambda_values, label=f"φ = {phi}")
    plt.xscale('log')
    custom_ticks = [1, 2, 3, 4, 5, 6, 7, 8, 10, 20, 30, 40, 60, 100, 200]
    plt.xticks(custom_ticks, [str(tick) for tick in custom_ticks])
    plt.title(r'Относительное удлинение $k_{\lambda}$')
    plt.xlabel(r'${\lambda}_{e}$, м')
    plt.ylabel(r'$k_{\lambda}$')
    plt.xlim(left=1, right=200)
    plt.ylim(bottom=0.6, top=1)
    # plt.grid(True)
    plt.grid(True, which="both", ls="-")
    plt.legend()








    # Показываем графики
    plt.tight_layout()
    plt.show()




print(f"Полная ветровая нагрузка w: {w:.3f} кПа")




