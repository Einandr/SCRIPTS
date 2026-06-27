import re
from mendeleev import element
import yaml
import os
import numpy as np
import scipy.integrate as integrate
import matplotlib.pyplot as plt
from scipy import optimize


# Константы:
R0 = 8.31
dzeta_C = 16.5
dzeta_H = 1.98


def piecewise_value(x, mydict):
    x_values = np.array(list(mydict.keys()))
    y_values = np.array(list(mydict.values()))
    return np.interp(x, x_values, y_values)


def integrate_value(x, mydict):
    # IN FUTURE - use other integration function for piecewise data
    # x_values = np.array(list(mydict.keys()))
    # y_values = np.array(list(mydict.values()))
    I = integrate.quad(piecewise_value, 0, x, args=mydict)
    # print('inside integration ', x, I)
    return I[0]


def find_root(func, value, *args):
    # def inner_func(T):
    #     return sp.Cp_divide_by_L_lh2(T) - value
    # answer = optimize.fsolve((func(*args) - value), [estimate])
    try:
        answer = optimize.root_scalar((func(*args) - value), bracket=[0, 500], method='bisect')
        print('function return:', answer)
        answer_return = answer.root
    except:
        print('not found root of function')
        answer_return = 0
    return answer_return


class Component:
    def __init__(self, file):
        with open(file) as f:
            data = yaml.safe_load(f)
        print(data)
        self.name = data['name']
        self.formula = data['formula']
        self.boiling_pressure = data['boiling_pressure']
        self.boiling_latent_heat = data['boiling_latent_heat']
        self.boiling_latent_heat = re.split(r'\s', self.boiling_latent_heat)
        self.boiling_latent_heat = [float(x) for x in self.boiling_latent_heat if x]
        self.temperature_fusion = data['temperature_fusion']
        self.temperature_critical = data['temperature_critical']
        self.density = data['density']
        self.density_sat_vapor = data['density_sat_vapor']
        self.heat_capacity_gas = data['heat_capacity_gas']
        self.heat_capacity_liquid = data['heat_capacity_liquid']
        self.heat_conductivity_gas = data['heat_conductivity_gas']
        self.latent_heat = data['latent_heat']
        self.saturation_vapor_pressure = data['saturation_vapor_pressure']
        self.surface_tension = data['surface_tension']
        self.viscosity = data['viscosity']
        self.sp_list = (re.sub(r'(\d+[.,]?)', r'\1 ', self.formula))     # выделяем границу молей предыдущего компонента и имени следующего
        self.sp_list = (re.sub(r'([a-zA-Z]+)', r'\1 ', self.sp_list))         # выделяем границу компонента и его количества молей
        self.sp_list = re.split(r'\s', self.sp_list)                    # разбиваем строку по пробелам
        self.sp_list = [x for x in self.sp_list if x]
        self.sp_components = [x for ind, x in enumerate(self.sp_list) if ((ind % 2) != 1)]
        self.sp_moles = [x for ind, x in enumerate(self.sp_list) if ((ind % 2) != 0)]

        # Calculate molar mass
        self.mu = 0
        for ind, x in enumerate(self.sp_components):
            self.el = element(x)
            self.moles = float(self.sp_moles[ind])
            self.mu += self.el.atomic_weight * self.moles

        # Calculate diffusive volume
        self.dzeta = 0
        for ind, x in enumerate(self.sp_components):
            self.el = element(x)
            self.moles = float(self.sp_moles[ind])
            if x == 'C':
                self.dzeta += dzeta_C * self.moles
            if x =='H':
                self.dzeta += dzeta_H * self.moles
        print('atomic diffusive volume: ', self.dzeta)

        # Calculate gas enthalpy
        print('\nCalculating gas enthalpy for species', self.formula, '...')
        self.__x_values = list(self.heat_capacity_gas.keys())
        self.__y_values = []
        for item in self.__x_values:
            self.__y_values.append(integrate_value(item, self.heat_capacity_gas))
        self.enthalpy_gas = dict(zip(self.__x_values, self.__y_values))


        # Calculate integral of gas enthalpy
        print('\nCalculating integral of gas enthalpy for species', self.formula, '...')
        self.__x_values = list(self.enthalpy_gas.keys())
        self.__y_values = []
        for item in self.__x_values:
            self.__y_values.append(integrate_value(item, self.enthalpy_gas))
        self.integral_of_enthalpy_gas = dict(zip(self.__x_values, self.__y_values))


        # Calculate liquid enthalpy
        print('\nCalculating liquid enthalpy for species', self.formula, '...')
        self.__x_values = list(self.heat_capacity_liquid.keys())
        self.__y_values = []
        for item in self.__x_values:
            self.__y_values.append(integrate_value(item, self.heat_capacity_liquid))
        self.enthalpy_liquid = dict(zip(self.__x_values, self.__y_values))
        print(self.enthalpy_liquid)

        # Calculate L_Lh from Clausius-Clapeyron equation
        print('\nCalculating L_lh form Clausius-Clapeyron equation', self.formula, '...')
        self.__T_from_density_sat_vapor = list(self.density_sat_vapor.keys())
        self.__T_min_from_density_sat_vapor = min(self.__T_from_density_sat_vapor)
        self.__T_from_psat = []
        for item in np.array(list(self.saturation_vapor_pressure.keys())):
            if item < self.__T_min_from_density_sat_vapor:
                self.__T_from_psat.append(item)
        self.__T_min_from_psat = min(self.__T_from_psat)
        self.__T_from_density = []
        for item in np.array(list(self.density.keys())):
            if item < self.__T_min_from_psat:
                self.__T_from_density.append(item)
        print('added temperatures:', self.__T_from_density, self.__T_from_psat, self.__T_from_density_sat_vapor)
        self.__T = self.__T_from_density + self.__T_from_psat + self.__T_from_density_sat_vapor
        if self.temperature_fusion < min(self.__T):
            self.__T.insert(0, self.temperature_fusion)
            print('inserted fusion temperature')
        elif self.temperature_fusion == min(self.__T):
            print('fusion temperature equals minimum of liquid data temperature. No extra insertion')
        else:
            print('!WARNING! likely incorrect input, fusion temperature above minimum denstiy data temperature')
        if self.temperature_critical > max(self.__T):
            self.__T.append(self.temperature_critical)
            print('appended critical temperature')
        elif self.temperature_critical == max(self.__T):
            print('critical temperature equals maximum of saturation vapor density data temperature. No extra addition')
        else:
            print('!WARNING! likely incorrect input, critical temperature below maximum saturation vapor density data temperature')
        print('added temperatures:', self.__T)
        # ВАЖНЫ ТОЛЬКО ДАННЫЕ ДЛЯ ДАВЛЕНИЯ НАСЫЩЕННЫХ ПАРОВ - ИНАЧЕ НУЛЕВЫЕ ГРАДИЕНТЫ И БЕСКОНЕЧНОСТИ НА КРАЯХ
        self.__T = list(self.saturation_vapor_pressure.keys())
        self.__sat_vap_pres = list(self.saturation_vapor_pressure.values())
        self.__ro_luqid = []
        self.__ro_sat_vap = []
        self.__Cp_liquid = []
        for item in self.__T:
            self.__ro_luqid.append(piecewise_value(item, self.density))
            self.__ro_sat_vap.append(piecewise_value(item, self.density_sat_vapor))
            self.__Cp_liquid.append(piecewise_value(item, self.heat_capacity_liquid))
        self.__dp_dt = np.gradient(self.__sat_vap_pres, self.__T)
        print(self.__T)
        print(self.__sat_vap_pres)
        print(self.__dp_dt)
        # formula: L = T * dp/dT *(1/ro_sat_vap - 1/ro_liq)
        self.__L_Clap_Claus = np.array(self.__T) * self.__dp_dt * (1/np.array(self.__ro_sat_vap) - 1/np.array(self.__ro_luqid))
        print('L form Clausius-Clapeyron is:')
        self.latent_heat_from_Clausius_Clapeyron = dict(zip(self.__T, self.__L_Clap_Claus))
        print(self.latent_heat_from_Clausius_Clapeyron)
        self.__Cp_divide_by_L = np.array(self.__Cp_liquid)/np.array(self.__L_Clap_Claus)
        print('Cp_divide_by_L is:')
        self.heat_capacity_liquid_divide_by_latent_heat = dict(zip(self.__T, self.__Cp_divide_by_L))
        print(self.heat_capacity_liquid_divide_by_latent_heat)



        # Calculate integral of Latent heat:
        print('\nCalculating integral of Latent heat', self.formula, '...')
        self.__x_values = list(self.latent_heat_from_Clausius_Clapeyron.keys())
        self.__y_values = []
        for item in self.__x_values:
            self.__y_values.append(integrate_value(item, self.latent_heat_from_Clausius_Clapeyron))
        self.integral_of_latent_heat = dict(zip(self.__x_values, self.__y_values))




        # Calculate Cp/L_lh integral
        print('\nCalculating Cp/L_lh integral', self.formula, '...')
        self.__Integral_Cp_divide_by_L = []
        self.__min_T_for_integral = min(self.__T)
        self.__base_integral = integrate_value(self.__min_T_for_integral, self.heat_capacity_liquid_divide_by_latent_heat)
        for item in self.__T:
            self.__Integral_Cp_divide_by_L.append(integrate_value(item, self.heat_capacity_liquid_divide_by_latent_heat) - self.__base_integral)
        self.integral_heat_capacity_liquid_divide_by_latent_heat = dict(zip(self.__T, self.__Integral_Cp_divide_by_L))
        print('integral Cp/L is:')
        print(self.integral_heat_capacity_liquid_divide_by_latent_heat)










    def ro(self, T):
        return piecewise_value(T, self.density)

    def ro_sat_vapor(self, T):
        return piecewise_value(T, self.density_sat_vapor)

    def Cp_gas(self, T):
        return piecewise_value(T, self.heat_capacity_gas)

    def Cp_liquid(self, T):
        return piecewise_value(T, self.heat_capacity_liquid)

    def H_gas(self, T):
        return piecewise_value(T, self.enthalpy_gas)

    def Integral_H_gas(self, T):
        return piecewise_value(T, self.integral_of_enthalpy_gas)

    def H_liquid(self, T):
        return piecewise_value(T, self.enthalpy_liquid)

    def T_liquid(self, H):
        y_values = np.array(list(self.enthalpy_liquid.keys()))
        x_values = np.array(list(self.enthalpy_liquid.values()))
        return np.interp(H, x_values, y_values)

    def Lambda_gas(self, T):
        return piecewise_value(T, self.heat_conductivity_gas)

    def P_sat(self, T):
        return piecewise_value(T, self.saturation_vapor_pressure)

    def sigma(self, T):
        return piecewise_value(T, self.surface_tension)

    def etta(self, T):
        return piecewise_value(T, self.viscosity)

    def L_lh_table(self, T):
        return piecewise_value(T, self.latent_heat)

    def L_lh_from_Cp(self, T):
        T_bp = self.boiling_latent_heat[0]
        L_lh_bp = self.boiling_latent_heat[1]
        delta_Cp_gas = self.H_gas(T) - self.H_gas(T_bp)
        delta_Cp_liquid = self.H_liquid(T_bp) - self.H_liquid(T)
        print(delta_Cp_gas)
        print(delta_Cp_liquid)
        print(T_bp)
        print(L_lh_bp)
        return delta_Cp_liquid + self.boiling_latent_heat[1] + delta_Cp_gas

    def L_lh_from_delta_Cp(self, T):
        return (self.Cp_gas(T) - self.Cp_liquid(T))*T

    def L_lh_Clap_Claus(self, T):
        return piecewise_value(T, self.latent_heat_from_Clausius_Clapeyron)

    def Integral_L_lh(self, T):
        return piecewise_value(T, self.integral_of_latent_heat)

    def Cp_div_by_L(self, T):
        return piecewise_value(T, self.heat_capacity_liquid_divide_by_latent_heat)

    # под интегралом обе функции (неправильно)
    def Integral_Cp_div_by_L(self, T):
        return piecewise_value(T, self.integral_heat_capacity_liquid_divide_by_latent_heat)


    #НЕПРАВИЛЬНО
    def T_from_Integral_Cp_div_by_L(self, value):
        def inner_func(T):
            return self.Integral_Cp_div_by_L(T)-value
        try:
            answer = optimize.root_scalar(inner_func, bracket=[0, 500], method='bisect')
            print('function return:', answer)
            answer_return = answer.root
        except:
            print('not found root of function')
            answer_return = 0
        return answer_return

    # НЕПРАВИЛЬНО
    def function_m_int_L_minus_int_H(self, m, dm, T):
        return dm * self.Integral_L_lh(T) - m * self.Integral_H_gas(T)

    # НЕПРАВИЛЬНО
    def T_from_function_with_double_integrals(self,m, dm, T0):
        def inner_func(T):
            return self.function_m_int_L_minus_int_H(m, dm, T) - self.function_m_int_L_minus_int_H(m, dm, T0)
        try:
            answer = optimize.root_scalar(inner_func, bracket=[0, 530], method='bisect')
            print('function return:', answer)
            answer_return = answer.root
        except:
            print('not found root of function')
            answer_return = 0
        return answer_return


    def T_from_from_average_L_appriximately(self,m, dm, T0):
        def inner_func(T):
            return dm*(self.L_lh_Clap_Claus(T) + self.L_lh_Clap_Claus(T0))/2 - m*(self.H_gas(T0)-self.H_gas(T))
        try:
            answer = optimize.root_scalar(inner_func, bracket=[1, 530], method='bisect')
            print('function return:', answer)
            answer_return = answer.root
        except:
            print('not found root of function')
            answer_return = 0
        return answer_return


# def find_root(func, value, *args):
#     # def inner_func(T):
#     #     return sp.Cp_divide_by_L_lh2(T) - value
#     # answer = optimize.fsolve((func(*args) - value), [estimate])
#     try:
#         answer = optimize.root_scalar((func(*args) - value), bracket=[0, 500], method='bisect')
#         print('function return:', answer)
#         answer_return = answer.root
#     except:
#         print('not found root of function')
#         answer_return = 0
#     return answer_return



path = r'D:\YASIM\!VORON\!Skripts_Common\n-heptane'
testfile = 'props_addref2.yaml'
os.chdir(path)

component = Component(testfile)

test0 = component.H_liquid(500)
test = component.T_liquid(test0)

test1 = component.Integral_Cp_div_by_L(300)

t1 = 450
t2 = 340

int_1 = component.Integral_Cp_div_by_L(t1)
int_2 = component.Integral_Cp_div_by_L(t2)

tback_1 = component.T_from_Integral_Cp_div_by_L(int_1)
tback_2 = component.T_from_Integral_Cp_div_by_L(int_2)


# t = np.linspace(0, 1000, 1001)
t = np.linspace(150, 600, 451)
L_fromCp = component.L_lh_from_Cp(t)
L_from_deltaCp = component.L_lh_from_delta_Cp(t)
L_from_Clap_Claus = component.L_lh_Clap_Claus(t)
L_from_table = component.L_lh_table(t)

func_psat = component.P_sat(t)

func_L_Cp = component.Cp_div_by_L(t)
func_int_L_Cp = component.Integral_Cp_div_by_L(t)

func_int_L = component.function_m_int_L_minus_int_H(0.0001, 0.000001, t)

print('here', func_int_L_Cp)


plt.plot(t, L_from_table, '-', label='table')
plt.plot(t, L_fromCp, '-', label='fromCp')
plt.plot(t, L_from_Clap_Claus, '-', label='Clap-Claus')
plt.plot(t, L_from_deltaCp, '-', label='from_deltaCp')
plt.grid()
plt.legend()
plt.savefig('fig_LLL.jpeg', dpi=400, bbox_inches='tight')
plt.close()

plt.plot(t, func_L_Cp, '-', label='table')
plt.savefig('fig_L_div_by_Cp.jpeg', dpi=400, bbox_inches='tight')
plt.close()

plt.plot(t, func_int_L_Cp, '-', label='table')
plt.savefig('fig_int_L_div_by_Cp.jpeg', dpi=400, bbox_inches='tight')
plt.close()

plt.plot(t, func_psat, '-', label='table')
plt.savefig('fig_psat.jpeg', dpi=400, bbox_inches='tight')
plt.close()

print(component.name)
print(component.formula)
print(component.mu)
print(component.density)

