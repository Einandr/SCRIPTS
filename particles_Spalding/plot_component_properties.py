import re
from mendeleev import element
import yaml
import os
import numpy as np
import scipy.integrate as integrate
import matplotlib.pyplot as plt
from scipy import optimize

from component_Spalding import Component, piecewise_value

# Константы:
R0 = 8.31
dzeta_C = 16.5
dzeta_H = 1.98

name = 'kerosene'
formula = 'c9.74h20.06'

dir_yaml_gas = r'D:\YASIM\VORON\2026_15_Spalding_Combustion\materials\gas'
name_yaml_gas = 'KEROSENE_Dagaut'
dir_yaml_liquid = r'D:\YASIM\VORON\2026_15_Spalding_Combustion\materials\dispersed_liquid'
name_yaml_liquid = 'kerosene_T1'

work_path = r'D:\YASIM\VORON\2026_15_Spalding_Combustion'
dir_output = 'run'

path_output = os.path.join(work_path, dir_output)
os.makedirs(path_output, exist_ok=True)


path_yaml_gas = os.path.join(dir_yaml_gas, f"{name_yaml_gas}.yaml")
path_yaml_liquid = os.path.join(dir_yaml_liquid, f"{name_yaml_liquid}.yaml")

os.chdir(path_output)

component = Component(path_yaml_gas, path_yaml_liquid, name, formula)

temperature_boiling = 450
gas_full_enthalpy = component.get_gas_full_enthalpy(temperature_boiling)
liquid_full_enthalpy = component.get_liquid_full_enthalpy(temperature_boiling)
latent_heat_at_boiling_point = gas_full_enthalpy - liquid_full_enthalpy
print(f'gas full enthalpy = {gas_full_enthalpy}, liquid full enthalpy = {liquid_full_enthalpy}, boiling point = {temperature_boiling}, latent heat at boiling point = {latent_heat_at_boiling_point}')



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

