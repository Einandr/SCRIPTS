from scipy import optimize
import math
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

from class_component import Component, piecewise_value

properties_file = r'C:\Users\YA\Desktop\YASIM\VORON\!Skripts_Common\n-heptane\props_addref2.yaml'

path = r'C:\Users\YA\Desktop\YASIM\VORON\!Skripts_Common\withprop_v6'
os.chdir(path)

sp = Component(properties_file)

# разница скоростей газа и капли [м/с]
dv = 100

# молярная масса среды, в которую диффундирует испаренное топливо: (воздух?)
M_gas = 29

# молекулярный диффузионный объем среды, в которую диффундирует испаренное топливо (воздух?):
dzeta_gas = 20.1

# концентрация пара на поверхности капли
Y_surf = 0.8

# концентрация компонента пара в газе
Y_gas = 0.75

# Давление газа
P = 100000

# минимальный диаметр частиц мкм:
d_min = 0.000001

# динамическая вязкость [Па*с]
def etta(T_gas):
    return sp.etta(T_gas)


# плотность [кг/м.куб.]
def ro(T_particle):
    return sp.ro(T_particle)


# теплопроводность газа [Вт/м*К]
def Lambda_gas(T_gas):
    return sp.Lambda_gas(T_gas)


# теплоёмкость жидкости [Дж/кг*К]
def Cp_liquid(T_particle):
    return sp.Cp_liquid(T_particle)

# энтальпия жидкости (Дж/кг]
def H_liquid(T_particle):
    return sp.H_liquid(T_particle)

def T_liquid(H_liquid):
    return sp.T_liquid(H_liquid)

# коэффициент Диффузии [м.кв./с] ДАВЛЕНИЕ ЕЩЕ В БАРАХ!!!
def D(P, T_gas):
    return pow(T_gas, 1.75)*pow(10, -7)/P * pow(1/sp.mu + 1/M_gas, 0.5) / (pow(sp.dzeta, 1/3) + pow(dzeta_gas, 1/3))

# test = D(1000, 1)

def T_boil(P):
    dict_tboil_from_psat = {y: x for x, y in sp.saturation_vapor_pressure.items()}
    return piecewise_value(P, dict_tboil_from_psat)

test = T_boil(P)

# теплота парообразования - при температуре кипения [Дж/кг]
def L_lh(T_particle):
    return sp.L_lh_Clap_Claus(T_particle)

def T_particle_from_Cp_divide_by_L_lh(Cp_divide_by_L_lh):
    return piecewise_value(Cp_divide_by_L_lh, dict_Cp_divide_by_L_lh)

def find_min_Cp_div_by_L():
    def func(T):
        return sp.Cp_divide_by_L_lh2(T)
    answer = optimize.fmin(func, 300)
    print('minimum Cp_div_by_L is', answer)
    return answer[0]

def find_max_Right_Cp_div_by_L():
    def func(T):
        return -sp.Cp_divide_by_L_lh2(T)
    answer = optimize.fminbound(func, x1=find_min_Cp_div_by_L(), x2=1000)
    print('fmax_right answer is', answer)
    return answer

# Функция немонотонна и имеет 1 или 2 решения. Выдает почему-то только 1 всегда
def calculate2(value, estimate):
    def func(T):
        return sp.Cp_divide_by_L_lh2(T) - value
    answer = optimize.fsolve(func, [100])
    print('function return:', answer)
    return answer[0]

# def calculate(value):
#     # ВЫНЕСТИ правый лимит в автоматическое его определение
#     def func(T):
#         return sp.Cp_divide_by_L_lh2(T) - value
#     try:
#         answer_left = optimize.root_scalar(func, bracket=[1, find_min_Cp_div_by_L()], method='bisect')
#         return_left = answer_left.root
#     except:
#         return_left = 0
#     try:
#         answer_right = optimize.root_scalar(func, bracket=[find_min_Cp_div_by_L(), 1000], method='bisect')
#         return_right = answer_right.root
#     except:
#         return_right = 0
#     print('value, function return:', value, return_left, return_right)
#     return return_left, return_right

# test44 = calculate(0.01)
# print('test  is ', test44)
# test66 = find_max_Right_Cp_div_by_L()
# test55 = 0

# число Прандля газа
def Pr(T_particle, T_gas):
    return Cp_liquid(T_particle)*etta(T_gas)/Lambda_gas(T_gas)

# число Шмидта
def Sc(P, T_particle, T_gas):
    return etta(T_gas)/ro(T_particle)/D(P, T_gas)

# Массовое число Сполдинга
Bm = (Y_surf-Y_gas)/(1-Y_surf)

# Тепловое число Сполдинга (Предположение Льюис = 1)
Bt = Bm


# площадь поверхности капли
def A_particle(d_particle):
    return math.pi*pow(d_particle, 2)


def Re(d_particle, T_particle, T_gas):
    return ro(T_particle)*d_particle*dv/etta(T_gas)


def m_particle(d_particle, T_particle):
    return ro(T_particle)*math.pi*pow(d_particle, 3)/6


def d_particle_from_m(m_particle, T_particle):
    return pow(6*m_particle/math.pi/ro(T_particle), 1/3)


# коэффициент теплоотдачи [Вт/м2*K]
def alpha_inert(d_particle, T_particle, T_gas):
    return (2 + 0.6 * pow(Re(d_particle, T_particle, T_gas), (1/2)) * pow(Pr(T_particle, T_gas), (1/3)))*Lambda_gas(T_gas)/d_particle


def alpha_vapor(d_particle, T_particle, T_gas):
    return alpha_inert(d_particle, T_particle, T_gas)*math.log(1+Bt)/Bt



# коэффициент массообмена [м/с]
def Kc(d_particle, P, T_particle, T_gas):
    return (2 + 0.6 * pow(Re(d_particle, T_particle, T_gas), (1/2)) * pow(Sc(P, T_particle, T_gas), (1/3)))*D(P, T_gas)/d_particle



print('test')

def dT_particle_inert(dt, d_particle, T_particle, T_gas):
    dT = alpha_inert(d_particle, T_particle, T_gas)*A_particle(d_particle)*(T_gas-T_particle)/m_particle(d_particle, T_particle)/Cp_liquid(T_particle)*dt
    delta_Tp_Tg = T_gas-T_particle
    if abs(dT) >= abs(delta_Tp_Tg):
        check_full_heating = True
    else:
        check_full_heating = False
    if check_full_heating:
        return delta_Tp_Tg
    else:
        return dT


def dm_particle(dt, d_particle, P, T_particle, T_gas):
    full_evaporation = False
    overheated = False
    dm = Kc(d_particle, P, T_particle, T_gas)*A_particle(d_particle)*ro(T_particle)*math.log(1+Bm)*dt
    m_prev = m_particle(d_particle, T_particle)
    delta_Tp_T_boil = T_boil(P) - T_particle

    if delta_Tp_T_boil < 0:
        print('!WARNING! ...overheated particle detected...', T_boil(P), delta_Tp_T_boil, T_particle)
        # Еще надо добавить вычисление источника энергии для газовой фазы:

        # Доля мгновенно испаренной массы из закона сохранения энтальпии:
        # ПРОВЕРИТЬ КАКОЙ берется L_lh - подозреваю что тут надо брать интеграль от T_particle до T_boil а не значение от T_particle
        part_instant_evaporated = -(1 - H_liquid(T_particle) / H_liquid(T_boil(P))) / (
                    L_lh(T_particle) / H_liquid(T_boil(P)) + 1)
        print('evaporation part from overheated conditions calculation:', part_instant_evaporated)
        overheated = True
        # Проверка полного испарения при наличии перегретых частиц:
        if part_instant_evaporated > 1:
            print('...full instant evaporation for overheated particle...')
            full_evaporation = True
        else:
            dm = m_particle(d_particle, T_particle)*part_instant_evaporated


    # Проверка полного испарения в нормальном неперегретом режиме - актуально на последних шагах
    if dm >= m_prev:
        print('...full evaporation from normal conditions...')
        full_evaporation = True

    if full_evaporation:
        return m_prev, full_evaporation, overheated
    else:
        return dm, full_evaporation, overheated


def dT_dm_particle_vapor(dt, d_particle, P, T_particle, T_gas):
    # Считаем, что при переходе с старого шага но новый сначала происходит испарение при старой массе и температуре.
    # Затем при новой массе вычисляется изменение температуры - так будет выполняться закон сохранения.
    # Конвективную часть вычисляем при старой массе - на законы сохранения не влияет, можно принять как при старой так и при новой.
    # Отдельно вычисляется проверка изменения температуры от конвекции,
    # Затем проводится проверка изменения от испарения - с учетом возможного повышения или понижения от конвекции.
    # Это разрешает нагреть конвективно еще больше если одновременно идет охлаждение испарением
    # Наоборот проверки и разрешения нет, но мне так и не удалось получить режи в котором бы температура на последнем шаге зашкаливала выше температуры газа
    # Думаю если постараться такой режим найти все-таки можно, поэтому считаю проверку надо оставить.
    # Благодаря последовательности проверок ушел заброс на предпоследнем шаге
    m_prev = m_particle(d_particle, T_particle)
    dm = dm_particle(dt, d_particle, P, T_particle, T_gas)
    # Если частица полностью испарилась на шаге - как в результате перегретого состояния так и в результате нормального испарения
    if dm[1]:
        return 0, 0, 0, dm[0], dm[1], dm[2]
    # Если частица перегрета - происходит снижение температуры до температуры кипения и испарение массы согласно энергетическому балансу.
    # На этом шаге дополнительно конвективный нагрев и испарение при температуре кипения не рассчитываются.
    # !!!НО ВНИМАНИЕ было бы неплохо выполнить проверку на долю испаренной массы, и если она достаточно мала - дополнительно считать испарение и нагрев.
    # Может быть актуально если частица пришла перегретой не с инжектора, а по ходу решения попала в зону с меньшим давлением.
    if dm[2]:
        return T_boil(P) - T_particle, 0, 0, dm[0], dm[1], dm[2]
    else:
        m_new = m_prev - dm[0]
        d_particle_new = d_particle_from_m(m_new, T_particle)
        # значение обнуляется на каждом новом шаге - поэтому капля из кипения может перейти обратно в испарение с охлаждением.
        boiling = False
        max_convective_heating = False
        # Если температура газа ниже температуры частицы - сначала конвективно охлаждаем, потом испаряем.
        # Проводим проверку на максимальное конвективное охлаждение, на суммарное охлаждение меньше 0
        # Допускается охлаждение ниже температуры газа за счет испарительного слагаемого,
        # при этом конвективное слагаемое не может быть больше разницы энтальпии при температуре частицы и газа
        if T_gas < T_particle:
            # Сначала конвективно охлаждаем
            dH_convection = alpha_vapor(d_particle, T_particle, T_gas) * A_particle(d_particle) * (T_gas - T_particle) * dt / m_particle(d_particle_new, T_particle)

            # Проверка на максимальное конвективное охлаждение
            if H_liquid(T_particle) + dH_convection <= H_liquid(T_gas):
                print('reaching max convective cooling')
                dH_convection = H_liquid(T_gas) - H_liquid(T_particle)

            T_particle_after_convection = T_liquid(H_liquid(T_particle) + dH_convection)
            # Теперь испаряем при новой температуре, НО ВНИМАНИЕ - для сохранения массы при зависимости плотности от температуры вычисляем массу как функцию от старой температуры:

            T_after_evaporation_from_Cp_L = sp.T_from_from_average_L_appriximately(m_new, dm[0], T_particle)
            print('initial temperature, temperature after evaporation and boiling temperature:', T_particle, T_after_evaporation_from_Cp_L, T_boil(P))
            dH_evaporation = H_liquid(T_after_evaporation_from_Cp_L) - H_liquid(T_particle)
            print(dH_evaporation)

            # dH_evaporation = - dm[0] * L_lh(T_particle_after_convection) / m_particle(d_particle_new, T_particle)
            # Делаем проверку на охлаждение меньше 0 Кельвинов
            if (dH_convection + dH_evaporation) < -H_liquid(T_particle):
                print('convective and evaporative cooling below zero - limiting')
                dT = -T_particle
            else:
                dT = T_particle - T_liquid(H_liquid(T_particle) + dH_convection + dH_evaporation)
        # return dT, dH_convection, dH_evaporation, dm[0], dm[1], dm[2]

        # Если температура газа больше температуры частицы - сначала испаряем, потом конвективно нагреваем.
        # Делаем проверку на максимальный конвективный нагрев. Делаем проверку на достижение температуры кипения.
        # Делаем проверку на достижения охлаждения до 0 Кельвинов.
        # При этом при достижении температуры кипения либо 0 Кельвинов учитывается возможный конвективный нагрев.
        if T_gas >= T_particle:

            T_after_evaporation_from_Cp_L = sp.T_from_from_average_L_appriximately(m_new, dm[0], T_particle)
            print('initial temperature, temperature after evaporation and boiling temperature:', T_particle, T_after_evaporation_from_Cp_L, T_boil(P))
            dH_evaporation = H_liquid(T_after_evaporation_from_Cp_L) - H_liquid(T_particle)
            print('dH_evaporation:', dH_evaporation)


            # dH_evaporation = - dm[0] * L_lh(T_particle) / m_particle(d_particle_new, T_particle)
            # Делаем первую проверку на достижения охлаждения до 0 Кельвинов.
            if dH_evaporation < -H_liquid(T_particle):
                print('max evaporative cooling not accounting for convective heating')
                print('!WARNING! likely incorrect L_lh input - check that near zero values supplied for frozen and zero values supplied for supercritical states')
                T_particle_after_evaporation = 0
            else:
                T_particle_after_evaporation = T_liquid(H_liquid(T_particle) + dH_evaporation)
            # Теперь нагерваем конвективно НО ВНИМАНИЕ как бы от пониженной температуры.
            # Это важно вблизи температуры кипения, потому что у нас так получится достаточно большое конвективное слагаемое и мы будем выходить на температуру кипения каждый раз.
            d_particle_after_evaporation = d_particle_from_m(m_new, T_particle_after_evaporation)
            dH_convection = alpha_vapor(d_particle_after_evaporation, T_particle_after_evaporation, T_gas) * A_particle(d_particle_after_evaporation) * (T_gas - T_particle_after_evaporation) * dt / m_particle(d_particle_after_evaporation, T_particle_after_evaporation)




            # Проверка на достижение за счет конвективнго нагрева температуры газа:
            if T_gas <= T_boil(P):
                if T_liquid(H_liquid(T_particle_after_evaporation) + dH_convection) > T_gas:
                    max_convective_heating = True
                    print('max convective heating reached')
                    dT = T_gas - T_particle
                    dH_convection = H_liquid(T_gas) - H_liquid(T_particle_after_evaporation)
                # Делаем вторую проверку на достижения охлаждения до 0 Кельвинов.
                if dH_evaporation + dH_convection < -H_liquid(T_particle):
                    print('max evaporative cooling even with simultaneous convective heating')
                    print('!WARNING! likely incorrect L_lh input - check that near zero values supplied for frozen and zero values supplied for supercritical states')
                    dT = - T_particle
                else:
                    if not max_convective_heating:
                        print('normal convective heating not reaching gas temperature nor boiling point')
                        dT = T_liquid(H_liquid(T_particle_after_evaporation) + dH_convection) - T_particle

            # Проверка на достижение за счет конвективно нагрева температуры кипения:
            if T_gas >= T_boil(P):
                if T_liquid(H_liquid(T_particle_after_evaporation) + dH_convection) > T_boil(P):
                    boiling = True
                    dT = T_boil(P) - T_particle
                    dH_convection = H_liquid(T_boil(P)) - H_liquid(T_particle_after_evaporation)
                    print('boiling point reached', T_boil(P), dT, T_particle-dT, dH_evaporation, dH_convection)
                # Делаем вторую проверку на достижения охлаждения до 0 Кельвинов.
                if dH_evaporation + dH_convection < -H_liquid(T_particle):
                    print('max evaporative cooling even with simultaneous convective heating')
                    print('!WARNING! likely incorrect L_lh input - check that near zero values supplied for frozen and zero values supplied for supercritical states')
                    dT = - T_particle
                else:
                    if not boiling:
                        dT = T_liquid(H_liquid(T_particle_after_evaporation) + dH_convection) - T_particle
                        print('normal heating', T_boil(P), dT, T_particle-dT, dH_evaporation, dH_convection)


            return dT, dH_convection, dH_evaporation, dm[0], dm[1], dm[2]



def calculate_inert(d_particle, T_particle, T_gas, dt, time_end):
    headers = ['t', 'T', 'dT', 'd', 'Re', 'alpha']
    time = 0
    T_now = T_particle
    T_prev = T_particle
    list_of_rows = []
    while time <= time_end:
        dT = dT_particle(dt, d_particle, T_prev, T_gas)
        solution = [time, T_now, dT, d_particle, Re(d_particle, T_particle, T_gas), alpha_inert(d_particle, T_particle, T_gas)]
        list_of_rows.append(solution)
        # вот тут менял местами две следующие строчки - результаты в папке с запаздыванием
        T_now += dT
        T_prev = T_now
        time += dt
    data = pd.DataFrame(list_of_rows, columns=headers)
    name = ''.join(('solution', ' d_', str(d_particle), ' Tp_', str(T_particle), ' Tg_', str(T_gas), ' dt_', str(dt)))
    data.to_excel(''.join((name, '.xlsx')))
    data.plot(x='t', y='T', style='o-', grid=True)
    plt.savefig(''.join((name, '.jpeg')), dpi=400, bbox_inches='tight')
    return data


def calculate_vapor(d_particle, T_particle, T_gas, dt, time_end):
    headers = ['t', 'T', 'dT', 'dH_conv', 'dH_evap', 'd', 'm', 'dm', 'Re', 'alpha', 'Bm', 'Sc']
    time = 0
    T_prev = T_particle
    T_now = T_particle
    d_prev = d_particle
    d_now = d_particle
    m_now = m_particle(d_particle, T_particle)
    list_of_rows = []
    while time <= time_end:
        # Чтобы избежать повторных вызовов функции dm, так как она все равно нужна внутри dT, добавил выводы внутрь dT изменил название на dT_dm
        # dm = dm_particle(dt, d_prev, P, T_prev, T_gas)[0]
        dT_dm = dT_dm_particle_vapor(dt, d_prev, P, T_prev, T_gas)
        # print(dT_dm)
        dT = [dT_dm[0], dT_dm[1], dT_dm[2]]
        dm = [dT_dm[3], dT_dm[4], dT_dm[5]]
        solution = [time, T_now, dT[0], dT[1], dT[2], d_now, m_particle(d_now, T_now), dm[0], Re(d_prev, T_prev, T_gas), alpha_vapor(d_prev, T_prev, T_gas), Bm, Sc(P, T_prev, T_gas)]
        list_of_rows.append(solution)
        # print(dm)
        print(time, m_now, T_now, dT_dm, L_lh(T_now))
        if dm[1]:
            print('full evaporation')
            break
        else:
            T_now += dT[0]
            m_now -= dm[0]
            d_now = d_particle_from_m(m_now, T_now)
            T_prev = T_now
            d_prev = d_now
            time += dt

    data = pd.DataFrame(list_of_rows, columns=headers)
    name = ''.join(('solution', ' d_', str(d_particle), ' Tp_', str(T_particle), ' Tg_', str(T_gas), ' dt_', str(dt)))
    data.to_excel(''.join((name, '.xlsx')))
    data.plot(x='t', y='T', style='o-', grid=True)
    plt.savefig(''.join((name, ' temperature.jpeg')), dpi=400, bbox_inches='tight')
    data.plot(x='t', y='d', style='o-', grid=True)
    plt.savefig(''.join((name, ' diameter.jpeg')), dpi=400, bbox_inches='tight')
    data.plot(x='t', y='m', style='o-', grid=True)
    plt.savefig(''.join((name, ' mass.jpeg')), dpi=400, bbox_inches='tight')
    return data



# Диаметр, начальная температура капли, температура газа, шаг по времени, конечное время
TR = calculate_vapor(0.02, 500, 300, 0.1, 100)

print('debug')
