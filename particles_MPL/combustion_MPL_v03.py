import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.patches import Polygon
import numpy as np
import pandas as pd
import scipy.integrate as integrate
from scipy import interpolate
import math
import ast
import json

# import class_terra_component as tc
# import class_mixture_component as dc
# import class_material as material
import os
import yaml
import re
from chempy import balance_stoichiometry
from chempy import mass_fractions
from chempy import chemistry
from pprint import pprint
from enum import Enum, auto
from pathlib import Path
from configparser import ConfigParser

from utils import material, output, terra_results, mixture_reference





path = r'D:\YASIM\VORON\2026_17_MPL\DATA'
dir_run = 'RUN'
dir_props_out = 'props_out'
dir_soulution = 'solution'

path_prop = r'D:\SCRIPTS\particles_MPL'
file_props = 'props_full_database.txt'
file_config = 'run_config.ini'
file_MPL = 'MPL_constants.txt'

# ПЕРЕХОД НА НОВЫЙ ОБЩИЙ ТЕРРА ФАЙЛ
path_data = r'D:\YASIM\!Chemical_Kinetics'
# terra_props = 'props_TERRA.txt'
# terra_props = 'terra_props_full_2013.csv'
terra_props = 'terra_props_full_old.csv'

path_run = ''.join((path, '/', dir_run))
Path(path_run).mkdir(parents=True, exist_ok=True)
os.chdir(path_run)



config = ConfigParser()
config.read(''.join((path_prop, '\\', file_config)))

show_plots = config.getboolean('boolean', 'show_plots')
small_mass_cut_off = config.getboolean('boolean', 'small_mass_cut_off')
# particle minimum diameter limit [mkm]
p_diameter_min_limit = config.getfloat('boolean', 'p_diameter_min_limit')
separate_heat_fluxes = config.getboolean('boolean', 'separate_heat_fluxes')

fuel_name = config['run']['fuel_name']

df_props = pd.read_csv(''.join((path_prop, '\\', file_props)), delimiter=' ', index_col='name')
df_props['T_range'] = df_props['T_range'].apply(lambda x: np.fromstring(x.replace('\'', '').replace('\"', '').replace('\n', ''), dtype=float, sep=','))
df_props['f_ranges'] = df_props['f_ranges'].apply(lambda x: np.array(ast.literal_eval(x.replace('\'', '').replace('\"', '').replace('\n', ''))))

MPL_constants = pd.read_csv(''.join((path_prop, '\\', file_MPL)), delimiter=' ', index_col='fuel_name')
MPL_constants['fuel_composition'] = MPL_constants['fuel_composition'].apply(lambda x: ast.literal_eval(x))
MPL_constants['products_equilibrium_composition'] = MPL_constants['products_equilibrium_composition'].apply(lambda x: ast.literal_eval(x))


# test = df_props['T_range']['B2O3(c)']

# PARTICLE MATERIAL PARAMETERS START
# !!! СЛЕДИТЬ ЗА СОСТАВОМ САМОСТОЯТЕЛЬНО !!!
# !!! КОМПОНЕНТЫ МОГУТ ПОВТОРЯТЬСЯ - ЭТО ОТСЛЕЖИВАЕТСЯ В КЛАССЕ МАТЕРИАЛА, НЕОБХОДИМО ПРИ ВЫЧИСЛЕНИИ ПРОДУКТОВ СГОРАНИЯ И СОСТАВА ГАЗОВОЙ СМЕСИ !!!
# !!! СУММЫ ДОЛЕЙ ДОЛЖНЫ БЫТЬ = 1 // В КОДЕ ЕСТЬ ПРОВЕРКИ НА СЛУЧАЙ НЕКОРРЕКТНОГО ЗАДАНИЯ ВХОДНЫХ СОСТАВОВ!!!



p_volatile = {'B2O3(c)': 1}

try:
    p_combustible = MPL_constants['fuel_composition'][fuel_name]
except ValueError:
    print('\nERROR - No fuel with name ', fuel_name, ' in MPL database\n')
    exit(1)

p_inert = {'Al2O3(c)': 1}

p_volatile_reference = mixture_reference.create_mixture_reference(p_volatile, material.Source.T)
p_combustible_reference = mixture_reference.create_mixture_reference(p_combustible, material.Source.T)
p_inert_reference = mixture_reference.create_mixture_reference(p_inert, material.Source.T)

particle_start_mass_fractions = {'volatile': config.getfloat('particle_start_mass_fractions', 'volatile'),
                                 'combustible': config.getfloat('particle_start_mass_fractions', 'combustible'),
                                 'inert': config.getfloat('particle_start_mass_fractions', 'inert')}
# MPL constants
# [s/m]
comb_k0 = MPL_constants['comb_k0'][fuel_name]
# [s/m]
comb_A = MPL_constants['comb_A'][fuel_name]
# [J/mol]
comb_Ea = MPL_constants['comb_Ea'][fuel_name]
# [Pa-s]
Rho_Dv_0 = MPL_constants['Rho_Dv_0'][fuel_name]
# [Pa-s]
Rho_Dc_0 = MPL_constants['Rho_Dc_0'][fuel_name]
# combustible component full oxidation energy fraction that particle absorbs
x_pop_ox = MPL_constants['x_pop_ox'][fuel_name]


particle_mixture_reference = {'volatile': p_volatile_reference,
                              'combustible': p_combustible_reference,
                              'inert': p_inert_reference}







# PARTICLE MATERIAL PARAMETERS END


# Universal gas constant [J/mol-K]
R0 = 8.31
# Temperature for Formatiom Enthalpy
T0 = 298.15

# Low temperature point in piecewise-linear Cp data - needed to calculate H for correctly fit Terra values
T_base = config.getfloat('solver', 'T_base')
# temperature delta to fit phase transition latent heat
dT_phase_transition = config.getfloat('solver', 'dT_phase_transition')
# first temperature value in Cp range
T_first = config.getfloat('solver', 'T_first')
# last temperature value in Cp range
T_last = config.getfloat('solver', 'T_last')
# temperature delta for Cp range
dT = config.getfloat('solver', 'dT')




# GAS MATERIAL PARAMETERS START
# gas components:
# - O2 - oxygen (oxidizer)
# - GGP - Gas Generation Products (gaseous fuel)
# - CPG - Combustion Products of Gaseous fuel: O2 + GGP reaction
# - CPCF - Combustion Products of Condensed solid gasified fuel - Final complete oxidation
# - GV - Gas form of particle Volatile component
# - N2 - nitrogen (gaseous inert)

gas_start_mass_fractions = {'oxidizer': config.getfloat('gas_start_mass_fractions', 'oxidizer'),
                            'volatile': config.getfloat('gas_start_mass_fractions', 'volatile'),
                            'nitrogen': config.getfloat('gas_start_mass_fractions', 'nitrogen'),
                            'CPCP': config.getfloat('gas_start_mass_fractions', 'CPCP'),
                            'CPCF': config.getfloat('gas_start_mass_fractions', 'CPCF')}

oxidizer = 'O2'
products_preliminary = {'B4C': {'BO', 'CO'},
                        'BN': {'BO', 'N2'},
                        'C': {'CO'},
                        'SiC': {'SiO', 'CO'},
                        'Fe3C': {'FeO', 'CO'},
                        'Al': {'AlO'},
                        'B': {'BO'}}
products_final = {'B4C': {'B2O3', 'CO2'},
                  'BN': {'B2O3', 'N2'},
                  'C': {'CO2'},
                  'SiC': {'SiO2', 'CO2'},
                  'Fe3C': {'FeO2', 'CO2'},
                  'Al': {'Al2O3'},
                  'B': {'B2O3'}}
# Not Needed now
products_final_from_middle = {'CO': 'CO2',
                              'SiO': 'SiO2',
                              'FeO': 'Fe2O3',
                              'BO2': 'B2O3'}




# Исходные данные

# volatile and combustible dissapearance fraction limit:
Y_min_p_limit_fraction = config.getfloat('solver', 'Y_min_p_limit_fraction')
# oxidizer dissapearance fraction limit
Y_min_g_limit_fraction = config.getfloat('solver', 'Y_min_g_limit_fraction')

# particle diameter
p_start_diameter = config.getfloat('run', 'p_start_diameter')
# particle temperature
p_start_temperature = config.getfloat('run', 'p_start_temperature')
# particle mass fraction


# time step [s]
dt = config.getfloat('run', 'dt')
t_end = config.getfloat('run', 't_end')

# particles in parcel
n_particles = config.getint('run', 'n_particles')

# gas temperature [K]
g_start_temperature = config.getfloat('run', 'g_start_temperature')
# gas pressure [Pa]
g_pressure = config.getfloat('run', 'g_pressure')
# gas slip velocity [m/s]
g_slip_velocity = config.getfloat('run', 'g_slip_velocity')
# gas cell length [m]
g_cell_length = config.getfloat('run', 'g_cell_length')
# gas cell volume
g_cell_volume = pow(g_cell_length, 3)

_gas_mode = config['run']['mode']


class GasMode(Enum):
    no_sources = auto()
    isobaric = auto()
    isochoric = auto()


if _gas_mode == 'no_sources':
    g_mode = GasMode.no_sources
elif _gas_mode == 'isobaric':
    g_mode = GasMode.isobaric
elif _gas_mode == 'isochoric':
    g_mode = GasMode.isochoric
else:
    print('\nERROR - Incorrect gas mode in config file specified\n')
    exit(1)




# Determine primary combustion products composition
def calculate_reactions(_fuel_mixture, _oxidizer, _products):
    mf_products = {}
    K_mass = {}
    K_mass_mixture = 0
    for key, value in _fuel_mixture.items():
        _fuel = re.sub(r'\(c\)', '', key)
        for key2, value2 in _products.items():
            if key2 == _fuel:
                reactants, products = {_fuel, _oxidizer}, value2
                reac, prod = balance_stoichiometry(reactants, products)
                r = chemistry.Reaction(*balance_stoichiometry(reac, prod)).string()
                print(r)
                mf_reac = mass_fractions(reac)
                mf_prod = mass_fractions(prod)
                K_mass[key2] = mf_reac[_oxidizer] / mf_reac[_fuel]
                print('reactants mass fractions: ', mf_reac, 'products mass fractions: ', mf_prod, 'K_mass: ', K_mass[key2])
                for p in products:
                    if p in mf_products.keys():
                        mf_products[p] += mf_prod[p] * value
                    else:
                        mf_products[p] = mf_prod[p] * value
                K_mass_mixture += K_mass[key2] * value
    return mf_products, K_mass_mixture


print('\ncalculating primary combustion reactions: ')
mf_products_preliminary, K_mass_preliminary = calculate_reactions(p_combustible, oxidizer, products_preliminary)
mf_products_preliminary_reference = mixture_reference.create_mixture_reference(mf_products_preliminary, material.Source.T)

print('\ncalculating final combustion reactions: ')
mf_products_final, K_mass_final = calculate_reactions(p_combustible, oxidizer, products_final)
mf_products_final_reference = mixture_reference.create_mixture_reference(mf_products_final, material.Source.T)

try:
    mf_products_equilibrium = MPL_constants['products_equilibrium_composition'][fuel_name]
    mf_products_equilibrium_reference = mixture_reference.create_mixture_reference(mf_products_equilibrium, material.Source.T)
except ValueError:
    print('ERROR - No fuel with name ', fuel_name, ' in MPL database')
    exit(1)

_products_mode = config['run']['products']

g_oxidizer = {'O2': 1}
g_GGP = {'some_values_0': 1}
g_CPCP = mf_products_preliminary
g_volatile = {'B2O3': 1}
g_N2 = {'N2': 1}

g_oxidizer_reference = mixture_reference.create_mixture_reference(g_oxidizer, material.Source.T)
g_GGP_reference = mixture_reference.create_mixture_reference(g_GGP, material.Source.T)
g_CPCP_reference = mixture_reference.create_mixture_reference(g_CPCP, material.Source.T)
g_volatile_reference = mixture_reference.create_mixture_reference(g_volatile, material.Source.T)
g_N2_reference = mixture_reference.create_mixture_reference(g_N2, material.Source.T)

# Setting g_CPCF
if _products_mode == 'full':
    g_CPCF = mf_products_final
    g_CPCF_reference = mf_products_final_reference
elif _products_mode == 'equilibrium':
    if mf_products_equilibrium:
        g_CPCF = mf_products_equilibrium
        g_CPCF_reference = mf_products_equilibrium_reference
    else:
        print('\nWARNING - Incorrectly specified products mode. Equilibrium data not available, using complete combustion products\n')
        g_CPCF = mf_products_final
        g_CPCF_reference = mf_products_final_reference
else:
    print('\nERROR - Incorrect products mode in config file specified. Only full / equilibrium values allowed\n')
    exit(1)


gas_mixture_reference = {'oxidizer': g_oxidizer_reference,
                         'volatile': g_volatile_reference,
                         'nitrogen': g_N2_reference,
                         'CPCP': g_CPCP_reference,
                         'CPCF': g_CPCF_reference}

# GAS MATERIAL PARAMETERS END



# CHECK INPUT MASS FRACTIONS CORRECTNESS



def check_mass_fractions(input_dict, message):
    eps_mass_fractions = 0.001
    error = abs(1 - sum(input_dict.values()))
    if error > eps_mass_fractions:
        print('Check ', message, ' input. Acceptable sum error:', eps_mass_fractions, ' current mixture input error:', error)
        exit(1)
    else:
        print(message, ' mixture input error:', error, ' // acceptable input')


check_mass_fractions(p_volatile, 'particle volatile mass fractions')
check_mass_fractions(p_combustible, 'particle combustible mass fractions')
check_mass_fractions(p_inert, 'particle inert mass fractions')
check_mass_fractions(particle_start_mass_fractions, 'particle start mass fractions')

check_mass_fractions(g_CPCP, 'gas products preliminary mass fractions')
check_mass_fractions(g_CPCF, 'gas products final mass fractions')
check_mass_fractions(gas_start_mass_fractions, 'gas start mass fractions')


print('continueing program')

print('debug')


def get_Cp(component, T):
    return component.get_Cp(T)

vector_get_Cp = np.vectorize(get_Cp, excluded=['component'])

def get_H(component, T):
    return component.get_H(T)

vector_get_H = np.vectorize(get_H, excluded=['component'])

def get_mu(component):
    return component.get_mu()

def get_rho(component):
    return component.get_rho()

def get_dH0(component):
    return component.get_dH0()





def fine_check_Cp_H(component, Tmin, Tmax, dT):
    T_grid_fine = np.arange(Tmin, Tmax+dT, dT)
    Cp_grid_fine = vector_get_Cp(component, T_grid_fine)
    H_grid_fine = vector_get_H(component, T_grid_fine)

    # Графики
    plt.figure(1)
    plt.grid(True)
    plt.plot(T_grid_fine, Cp_grid_fine)
    plt.legend((r'$Ср$'), fontsize='medium', loc='best')
    plt.title(r'$Теплоёмкость$')
    plt.xlabel(r'$Т\ (К)$')
    plt.ylabel(r'$C_p\ (\frac{Дж}{кг\cdot К})$')
    plt.xlim(0)
    plt.ylim(0)
    plt.savefig(''.join(('pic_', component.name, '_07_Cp_fine_check.jpeg')), dpi=400, bbox_inches='tight')
    plt.close()

    plt.figure(2)
    plt.grid(True)
    plt.plot(T_grid_fine, H_grid_fine)
    plt.legend((r'$H$'), fontsize='medium', loc='best')
    plt.title(r'$Энтальпия$')
    plt.xlabel(r'$Т\ (К)$')
    plt.ylabel(r'$H\ (\frac{Дж}{кг})$')
    plt.xlim(0)
    plt.ylim(0)
    plt.savefig(''.join(('pic_', component.name, '_08_H_fine_check.jpeg')), dpi=400, bbox_inches='tight')
    plt.close()
    return None

# fine_check_Cp_H(test_component5, 0, 700, 10)




print('debug')


def calc_sphere_surface(diameter):
    return math.pi*diameter*diameter


def calc_sphere_volume(diameter):
    return math.pi / 6 * diameter * diameter * diameter


def calc_sphere_diameter(volume):
    return math.pow(6 * volume / math.pi, 1/3)




df_terra = pd.read_csv(''.join((path_data, '\\', terra_props)), delimiter=' ')
df_terra['T_range'] = df_terra['T_range'].apply(lambda x: np.fromstring(x.replace('\'', '').replace('\"', '').replace('\n', ''), dtype=float, sep=','))
df_terra['f_ranges'] = df_terra['f_ranges'].apply(lambda x: np.array(ast.literal_eval(x.replace('\'', '').replace('\"', '').replace('\n', ''))))
df_terra['name_isomer'] = df_terra['name_isomer'].fillna('')
df_terra['name'] = df_terra['name_brutto'] + ' ' + df_terra['name_isomer']
df_terra['name'] = df_terra['name'].str.strip()
df_terra.set_index('name', inplace=True)


components_chemkin = []

# particle material initialization
dispersed_material = material.Material(particle_mixture_reference, 'mat_particle', df_terra, components_chemkin, show_plots, False, T0, T_base, dT_phase_transition, T_first, T_last, dT)

# gas material initialization
gas_material = material.Material(gas_mixture_reference, 'mat_gas', df_terra, components_chemkin, show_plots, True, T0, T_base, dT_phase_transition, T_first, T_last, dT)


# gas mass fractions representing pure oxidizer, volatile and N2 component
g_mass_fractions_pure_oxidizer = {'oxidizer': 1, 'volatile': 0, 'nitrogen': 0, 'CPCP':0, 'CPCF': 0}
g_mass_fractions_pure_volatile = {'oxidizer': 0, 'volatile': 1, 'nitrogen': 0, 'CPCP':0, 'CPCF': 0}
g_mass_fractions_pure_N2 = {'oxidizer': 0, 'volatile': 0, 'nitrogen': 1, 'CPCP': 0, 'CPCF': 0}
g_mass_fractions_pure_CPCP = {'oxidizer': 0, 'volatile': 0, 'nitrogen': 0, 'CPCP': 1, 'CPCF': 0}
g_mass_fractions_pure_CPCF = {'oxidizer': 0, 'volatile': 0, 'nitrogen': 0, 'CPCP': 0, 'CPCF': 1}











# USED BEFORE KINETIC THEORY PROPS WAS IMPLEMENTED
# file_props_gas = 'props_air.yaml'
# with open(''.join((path_prop, '\\', file_props_gas))) as f:
#     # read_data = yaml.load(f, Loader=yaml.FullLoader)
#     dict_props_gas = yaml.safe_load(f)


def interpolated_value(x_eval, input_dict):
    x_array = np.fromiter(input_dict.keys(), dtype=float)
    y_array = np.fromiter(input_dict.values(), dtype=float)
    return np.interp(x_eval, x_array, y_array)






# oxidizer molar mass [kg/mol]
g_oxidizer_M = gas_material.get_mu(g_mass_fractions_pure_oxidizer)/1000
# gaseous volatile component molar mass [kg/mol]
g_vol_M = gas_material.get_mu(g_mass_fractions_pure_volatile)/1000













# particle mass fractions representing pure combustible, volatile and inert component
p_mass_fractions_pure_combustible = {'volatile': 0, 'combustible': 1, 'inert': 0}
p_mass_fractions_pure_volatile = {'volatile': 1, 'combustible': 0, 'inert': 0}
p_mass_fractions_pure_inert = {'volatile': 0, 'combustible': 0, 'inert': 1}

# particle volatile component molar mass [kg/mol] (may use g_vol_M as well)
p_vol_M = dispersed_material.get_mu(p_mass_fractions_pure_volatile)/1000

# particle density for pure combustible, volatile and inert component [kg/m^3]
p_comb_density = dispersed_material.get_density(p_mass_fractions_pure_combustible)
p_vol_density = dispersed_material.get_density(p_mass_fractions_pure_volatile)
p_inert_density = dispersed_material.get_density(p_mass_fractions_pure_inert)


# particle volatile component boiling temperature [K]
p_vol_Tb = 2133
# particle pressure for defining boiling temperature [Pa]
p_vol_Pb = 100000
# stoichiometric ratio for preliminary fuel O2 oxidation
# K_mass_preliminary = 1.277
# stoichiometric ratio for secondary complete fuel O2 oxidation
# K_mass_final = 2.034


# particle components formation heat [J/kg] at 298.15 K
p_comb_H0 = dispersed_material.get_formation_heat(p_mass_fractions_pure_combustible)/dispersed_material.get_mu(p_mass_fractions_pure_combustible) * 1000
p_vol_H0 = dispersed_material.get_formation_heat(p_mass_fractions_pure_volatile)/dispersed_material.get_mu(p_mass_fractions_pure_volatile) * 1000
p_inert_H0 = dispersed_material.get_formation_heat(p_mass_fractions_pure_inert)/dispersed_material.get_mu(p_mass_fractions_pure_inert) * 1000


# gas components formation heat [J/kg] at 298.15 K
g_GV_H0 = gas_material.get_formation_heat(g_mass_fractions_pure_volatile)/gas_material.get_mu(g_mass_fractions_pure_volatile) * 1000
g_O2_H0 = gas_material.get_formation_heat(g_mass_fractions_pure_oxidizer)/gas_material.get_mu(g_mass_fractions_pure_oxidizer) * 1000
g_CPCP_H0 = gas_material.get_formation_heat(g_mass_fractions_pure_CPCP)/gas_material.get_mu(g_mass_fractions_pure_CPCP) * 1000
g_CPCF_H0 = gas_material.get_formation_heat(g_mass_fractions_pure_CPCF)/gas_material.get_mu(g_mass_fractions_pure_CPCF) * 1000



print('debug')


def make_step(_p_mass_fractions, _p_temperature, _p_diameter, _g_mass_fractions, _g_temperature):
    # particle mass fractions
    p_mass_fractions = _p_mass_fractions
    # particle temperature
    p_temperature = _p_temperature
    # particle enthalpy
    p_enthalpy = dispersed_material.get_enthalpy(p_mass_fractions, p_temperature)
    # particle diameter
    p_diameter = _p_diameter
    # gas mass fractions
    g_mass_fractions = _g_mass_fractions
    # gas temperature
    g_temperature = _g_temperature

    # AIR PARAMETERS - USED BEFORE KINETIC THEORY CALCULATIONS WERE IMPLEMENTED
    # gas heat conductivity [W/m-K]
    # g_heat_conductivity = interpolated_value(g_temperature, dict_props_gas['heat_conductivity'])
    # gas heat capacity [J/kg-K]
    # g_heat_capacity = interpolated_value(g_temperature, dict_props_gas['heat_capacity'])
    # gas viscosity [Pa-s]
    # g_viscosity = interpolated_value(g_temperature, dict_props_gas['viscosity'])

    # CURRENT GAS MIXTURE PARAMETERS
    # gas heat conductivity [W/m-K]
    g_heat_conductivity = gas_material.get_heat_conductivity(g_mass_fractions, g_temperature)
    # gas heat capacity [J/kg-K]
    g_heat_capacity = gas_material.get_heat_capacity(g_mass_fractions, g_temperature)
    # gas viscosity [Pa-s]
    g_viscosity = gas_material.get_viscosity(g_mass_fractions, g_temperature)

    # gas mass fraction of O2 oxidizer
    g_Y_O2 = g_mass_fractions['oxidizer']
    # gas mass fraction of GV volatile
    g_Y_GV = g_mass_fractions['volatile']
    # gas mixture molar mass [kg/mol]
    g_M = gas_material.get_mu(g_mass_fractions) / 1000

    # particle mass fraction of combustible component
    p_Y_comb = p_mass_fractions['combustible']
    # particle mass fraction of volatile component
    p_Y_vol = p_mass_fractions['volatile']
    # particle mass fraction of inert component
    p_Y_inert = p_mass_fractions['inert']

    # particle surface area
    p_surface_area = calc_sphere_surface(p_diameter)
    # particle density
    p_density = dispersed_material.get_density(p_mass_fractions)
    print('p_density is: ', p_density, p_vol_density, p_comb_density, p_inert_density, p_mass_fractions)
    # particle volume
    p_volume = calc_sphere_volume(p_diameter)
    # particle mass
    p_mass = p_density * p_volume
    # particle mass of combustible, volatile and inert components
    p_mass_comb = p_mass * p_Y_comb
    p_mass_vol = p_mass * p_Y_vol
    p_mass_inert = min(abs(p_mass * (1 - p_Y_comb - p_Y_vol)), p_Y_inert)

    # particle heat capacity
    p_heat_capacity = dispersed_material.get_heat_capacity(p_mass_fractions, p_temperature)

    # particle enthalpy [J/kg] for pure combustible, volatile and inert component
    p_comb_H = dispersed_material.get_enthalpy(p_mass_fractions_pure_combustible, p_temperature)
    p_vol_H = dispersed_material.get_enthalpy(p_mass_fractions_pure_volatile, p_temperature)
    p_inert_H = dispersed_material.get_enthalpy(p_mass_fractions_pure_inert, p_temperature)

    # gas components enthalpy at particle temperature [J/kg]
    g_GV_H = gas_material.get_enthalpy(g_mass_fractions_pure_volatile, p_temperature)
    g_O2_H = gas_material.get_enthalpy(g_mass_fractions_pure_oxidizer, p_temperature)
    g_CPCP_H = gas_material.get_enthalpy(g_mass_fractions_pure_CPCP, p_temperature)
    g_CPCF_H = gas_material.get_enthalpy(g_mass_fractions_pure_CPCF, p_temperature)

    # gas components enthalpy at gas temperature [J/kg]
    g_O2_H_f = gas_material.get_enthalpy(g_mass_fractions_pure_oxidizer, g_temperature)

    # particle full enthalpy [J/kg] for pure combustible, volatile and inert component
    p_comb_H_full = p_comb_H0 + p_comb_H - dispersed_material.get_enthalpy(p_mass_fractions_pure_combustible, T0)
    p_vol_H_full = p_vol_H0 + p_vol_H - dispersed_material.get_enthalpy(p_mass_fractions_pure_volatile, T0)
    p_inert_H_full = p_inert_H0 + p_inert_H - dispersed_material.get_enthalpy(p_mass_fractions_pure_inert, T0)

    # gas components full enthalpy at particle temperature [J/kg]
    g_GV_H_full = g_GV_H0 + g_GV_H - gas_material.get_enthalpy(g_mass_fractions_pure_volatile, T0)
    g_O2_H_full = g_O2_H0 + g_O2_H - gas_material.get_enthalpy(g_mass_fractions_pure_oxidizer, T0)
    g_CPCP_H_full = g_CPCP_H0 + g_CPCP_H - gas_material.get_enthalpy(g_mass_fractions_pure_CPCP, T0)
    g_CPCF_H_full = g_CPCF_H0 + g_CPCF_H - gas_material.get_enthalpy(g_mass_fractions_pure_CPCF, T0)

    print('g_CPCP_H_full g_CPCP_H0 g_CPCP_H: ', g_CPCP_H_full, g_CPCP_H0, g_CPCP_H)
    print('g_CPCF_H_full g_CPCF_H0 g_CPCF_H: ', g_CPCF_H_full, g_CPCF_H0, g_CPCF_H)



    # thermal effect of volatile components evaporation [J/kg] NEGATIVE VALUE
    dH_vol_evap = min((p_vol_H_full - g_GV_H_full), 0.0)
    # thermal effect of combusting component preliminary combustion [J/kg]
    dH_comb_preliminary = p_comb_H_full + K_mass_preliminary*g_O2_H_full - (1 + K_mass_preliminary)*g_CPCP_H_full
    # thermal effect of combusting component final combustion !!! PRELIMINARY PRODUCTS AFTERBURNING !!! [J/kg]
    dH_comb_final = g_CPCP_H_full + (K_mass_final - K_mass_preliminary)/(1+K_mass_preliminary)*g_O2_H_full - (1 + K_mass_final)/(1+K_mass_preliminary)*g_CPCF_H_full


    print('dH_vol_evap dH_comb_preliminary dH_comb_final: ', dH_vol_evap, dH_comb_preliminary, dH_comb_final)


    # combustible component surface oxidation rate [s/m]
    k_comb = comb_k0 + comb_A * math.exp(-comb_Ea / p_temperature / R0)

    # volatile component saturation vapor pressure [Pa]
    p_vol_saturation_pressure = p_vol_Pb * math.exp(-dH_vol_evap / R0 * g_vol_M * (1 / p_vol_Tb - 1 / p_temperature))

    # gas volatile component partial pressure [Pa]
    g_vol_partial_pressure = g_pressure * g_Y_GV * g_vol_M / g_M

    # MPL constant
    rho_D_vol = Rho_Dv_0 * math.sqrt(p_temperature/T0)
    # MPL constant
    rho_D_comb = Rho_Dc_0 * math.sqrt(p_temperature/T0)

    # MPL constant
    # rho_D_vol = 1.409E-4 * math.sqrt(p_temperature/3000) / 11
    # MPL constant
    # rho_D_comb = 1.409E-4 * math.sqrt(p_temperature/3000) / 5

    # Shmidt number for combustible component
    p_comb_Sc = g_viscosity / rho_D_comb
    # Shmidt number for volatile component
    p_vol_Sc = g_viscosity / rho_D_vol

    # gas density [kg/m^3]
    g_density = (g_pressure * g_M) / (g_temperature * R0)
    # gas Prandtl number
    g_Pr = g_heat_capacity * g_viscosity / g_heat_conductivity
    # particle Reynolds number
    p_Re = g_density * g_slip_velocity * p_diameter / g_viscosity
    # particle Nu number
    p_Nu = 2 + 0.6*pow(p_Re, 1/2)*pow(g_Pr, 1/3)
    # alpha inert heating or cooling
    alpha = p_Nu * g_heat_conductivity / p_diameter

    # combustible component Nu number
    p_comb_Nu = 2.0 + 0.6*pow(p_Re, 1/2)*pow(g_Pr, 1/3)
    # volatile component Nu number
    p_vol_Nu = 2.0 + 0.6*pow(p_Re, 1/2)*pow(g_Pr, 1/3)
    # inert component Nu number
    p_inert_Nu = 2.0 + 0.6*pow(p_Re, 1/2)*pow(g_Pr, 1/3)


    # function to find particle surface volatile component concentration and evaporation rate
    def evaporation_volatile():
        if p_Y_vol == 0:
            return 0, 0, 0
        else:
            call_counter = 0
            # volatile component surface evaporation rate [kg/m^2/s] (initial value)
            rate_evaporation_vol = 0
            # "blowing" coefficient (initial value)
            theta_vol = 1.0
            # relative molar concentration of volatile component on particle surface (initial value)
            X_surf_vol = min(p_vol_saturation_pressure / g_pressure, 0.999)
            # variable that holds previous iteration value of X_surf_vol
            X_surf_vol_ = 0.9*X_surf_vol
            # damping coefficient aka under-relaxation factor
            zz = 0.5
            # zz multiplication coefficient
            x_zz = 1.01
            # relative mass conctntration of volatile component on particle surface (initial value)
            Y_surf_vol = 0

            # Evaporation possibility check
            print('check evaporation possibility p_vol_saturation_pressure, g_pressure * g_Y_GV * g_vol_M / g_M ', p_vol_saturation_pressure, g_pressure * g_Y_GV * g_vol_M / g_M)

            if p_vol_saturation_pressure > g_pressure * g_Y_GV * g_vol_M / g_M and p_vol_saturation_pressure > 1E-10:
                while abs(X_surf_vol - X_surf_vol_) > 0.001 * X_surf_vol:
                    call_counter += 1
                    Y_surf_vol = X_surf_vol * p_vol_M / (X_surf_vol * p_vol_M + (1 - X_surf_vol) * g_M)
                    # print('iterating evaporation: Y_surf_vol, X_surf_vol, X_surf_vol_: ', Y_surf_vol, X_surf_vol, X_surf_vol_)
                    if Y_surf_vol > 0.001 and g_Y_GV > 0.001:
                        # "blowing" coefficient
                        theta_vol = math.log((1 - g_Y_GV) / (1 - Y_surf_vol)) / ((1 - g_Y_GV) / (1 - Y_surf_vol) - 1)
                    # Sherwood number
                    # Sh_vol = 2 + 0.376 * pow(p_Re, 1/2) * pow(p_vol_Sc, 1/3) * (1 + 3.2 * (1 - theta_vol))
                    Sh_vol = 2 + 0.6 * pow(p_Re, 1 / 2) * pow(p_vol_Sc, 1 / 3)

                    # volatile component surface evaporation rate[kg/m^2/s]
                    rate_evaporation_vol = Sh_vol * rho_D_vol / p_diameter * math.log((1 - g_Y_GV) / (1 - Y_surf_vol))
                    X_surf_vol_ = X_surf_vol
                    if zz < 1 / x_zz:
                        zz = zz * x_zz
                    else:
                        zz = 1
                    X_surf_vol = min(zz * X_surf_vol + (1 - zz) * max(p_vol_saturation_pressure - rate_evaporation_vol * math.sqrt(2 * math.pi * R0 * p_temperature / p_vol_M), 0.0) / g_pressure, 0.999)
                    print('EV call_counter Y_surf_vol X_surf_vol X_surf_vol_ g_Y_GV theta_vol Sh_vol p_Re p_vol_Sc rate_evaporation_vol rho_D_vol p_diameter zz:', call_counter, Y_surf_vol, X_surf_vol, X_surf_vol_, g_Y_GV, theta_vol, Sh_vol, p_Re, p_vol_Sc, rate_evaporation_vol, rho_D_vol, p_diameter, zz)

            else:
                theta_vol = 1
                Y_surf_vol = g_Y_GV
            return rate_evaporation_vol, Y_surf_vol, theta_vol


    # volatile component surface evaporation rate [kg/m^2/s]
    # relative mass concentration of volatile component on particle surface
    # "blowing" coefficient
    G_vol, Y_surf_vol, theta_vol = evaporation_volatile()

    print('evaporation volatile: G_vol Y_surf_vol theta_vol: ', G_vol, Y_surf_vol, theta_vol)

    # alpha volatile component
    alpha_vol = p_vol_Nu * g_heat_conductivity / p_diameter
    # volatile component convective heat flux [W/m^2]
    q_conv_vol = theta_vol * alpha_vol * (g_temperature - p_temperature)


    # function to find particle surface combustible component combustion rate
    def combustion_combustible():
        eps_Y_surf = 0.001
        call_counter = 0
        # combustible component surface combustion rate [kg/m^2/s] (initial value)
        rate_combustion_comb = 0
        # "blowing" coefficient (initial value)
        theta_comb = 1.0
        # relative mass concentration of oxidizer on particle surface (initial value)
        Y_surf_ox = g_Y_O2 / (1 + k_comb * g_pressure * p_diameter * K_mass_final * g_oxidizer_M / g_M / rho_D_comb / 2)
        if p_Y_comb == 0:
            return 0, Y_surf_ox, 0
        else:
            # variable that holds previous iteration value of Y_surf_ox
            Y_surf_ox_ = 0.9*Y_surf_ox
            # damping coefficient aka under-relaxation factor
            zz = 0.5
            # zz multiplication coefficient
            x_zz = 1.05
            # Oxidation possibility check
            if g_Y_O2 > 1e-04 and k_comb > 1E-6:
                while abs(Y_surf_ox - Y_surf_ox_) > eps_Y_surf * Y_surf_ox:
                    call_counter += 1
                    # print('iterating combustion Y_surf_ox, Y_surf_ox_: ', Y_surf_ox, Y_surf_ox_)
                    if Y_surf_ox < g_Y_O2:
                        # "blowing" coefficient
                        theta_comb = math.log((K_mass_final + g_Y_O2) / (K_mass_final + Y_surf_ox)) / ((K_mass_final + g_Y_O2) / (K_mass_final + Y_surf_ox) - 1)
                    # Sherwood number
                    # Sh_comb = 2 + 0.376 * pow(p_Re, 1/2) * pow(p_comb_Sc, 1/3) * (1 + 3.2 * (1 - theta_comb))
                    Sh_comb = 2 + 0.6 * pow(p_Re, 1 / 2) * pow(p_comb_Sc, 1 / 3)
                    # combustible component surface oxidation rate [kg/m^2/s]
                    rate_combustion_comb = Sh_comb * rho_D_comb / p_diameter * math.log((K_mass_final + g_Y_O2) / (K_mass_final + Y_surf_ox))
                    Y_surf_ox_ = Y_surf_ox
                    if zz < 1 / x_zz:
                        zz = zz * x_zz
                    else:
                        zz = 1
                    Y_surf_ox = min(max(zz * Y_surf_ox + (1.0 - zz) * rate_combustion_comb * g_M / g_oxidizer_M / k_comb / g_pressure, 0.0), g_Y_O2)
                    print('CC call_counter Y_surf_ox Y_surf_ox_ g_Y_O2 theta_comb Sh_comb p_Re p_comb_Sc rate_combustion_comb rho_D_comb p_diameter zz:', call_counter, Y_surf_ox, Y_surf_ox_, g_Y_O2, theta_comb, Sh_comb, p_Re, p_comb_Sc, rate_combustion_comb, rho_D_comb, p_diameter, zz)
                X_surf_ox = Y_surf_ox * g_oxidizer_M / g_M
                G_kinetic = k_comb * g_pressure * X_surf_ox
                if (Y_surf_ox - g_Y_O2) < eps_Y_surf and G_kinetic > rate_combustion_comb:
                    rate_combustion_comb = G_kinetic
            else:
                theta_comb = 1
                Y_surf_ox = g_Y_O2
            return rate_combustion_comb, Y_surf_ox, theta_comb


    # combustible component surface oxidation rate [kg/m^2/s]
    # relative mass concentration of combustible component on particle surface
    # "blowing" coefficient
    G_comb, Y_surf_comb, theta_comb = combustion_combustible()

    print('combustion combustible: G_comb Y_surf_comb theta_comb: ', G_comb, Y_surf_comb, theta_comb)


    # combine evaporation and combustion functions output for convenient postprocessing:
    vol_and_comb_functions_output = {'G_vol': G_vol,
                                     'Y_surf_vol': Y_surf_vol,
                                     'theta_vol': theta_vol,
                                     'G_comb': G_comb,
                                     'Y_surf_comb': Y_surf_comb,
                                     'theta_comb': theta_comb}



    # alpha combustible component
    alpha_comb = p_comb_Nu * g_heat_conductivity / p_diameter

    # combustible component convective heat flux [W/m^2]
    q_conv_comb = theta_comb * alpha_comb * (g_temperature - p_temperature)


    # combustible component reaction heat flux [W/m^2]
    q_react_comb_preliminary = dH_comb_preliminary * G_comb
    q_react_comb_final = x_pop_ox * dH_comb_final * G_comb

    # alpha inert component
    alpha_inert = p_inert_Nu * g_heat_conductivity / p_diameter
    # inert component convective heat flux [W/m^2]
    q_conv_inert = alpha_inert * (g_temperature - p_temperature)

    # PARTICLE MASS CHANGE CALCULATION
    # particle surface area fraction, covered by volatile component
    p_surface_area_vol_fraction = p_Y_vol / p_vol_density / (p_Y_vol / p_vol_density + p_Y_comb / p_comb_density + (1 - p_Y_vol - p_Y_comb) / p_inert_density)
    # particle surface area fraction, covered by combustible component
    p_surface_area_comb_fraction = p_Y_comb / p_comb_density / (p_Y_vol / p_vol_density + p_Y_comb / p_comb_density + (1 - p_Y_vol - p_Y_comb) / p_inert_density)
    # combustible component mass change rate [kg/s]
    p_dmdt_comb = p_surface_area * p_surface_area_comb_fraction * G_comb
    # volatile component mass change rate [kg/s]
    p_dmdt_vol = p_surface_area * p_surface_area_vol_fraction * G_vol

    # ADDED CHECKS FOR TIME STEP WHEN ALL COMBUSTIBLE OR VOLATILE FRACTIONS DISAPPEARS
    # particle combustible component mass change [kg]
    p_dm_comb = min(p_dmdt_comb * dt, p_mass_comb)
    # particle volatile component mass change [kg]
    p_dm_vol = min(p_dmdt_vol * dt, p_mass_vol)

    # particle new mass of combustible/volatile/inert component [kg]
    p_mass_comb_new = p_mass_comb - p_dm_comb
    p_mass_vol_new = p_mass_vol - p_dm_vol
    p_mass_inert_new = p_mass_inert

    if p_Y_vol < Y_min_p_limit_fraction:
        p_mass_vol_new = 0
        p_dm_vol = p_mass_vol
        p_dmdt_vol = p_dm_vol / dt
    if p_Y_comb < Y_min_p_limit_fraction:
        p_mass_comb_new = 0
        p_dm_comb = p_mass_comb
        p_dmdt_comb = p_dm_comb / dt

    # print('particle volatile calculation:', p_dmdt_vol * dt, p_mass_vol, p_dm_vol, p_mass_vol_new)

    # particle mass new
    p_mass_new = p_mass_comb_new + p_mass_vol_new + p_mass_inert_new

    # particle combustion and evaporation rate [m/s]
    # without limiters:
    u_vol = G_vol / p_vol_density
    u_comb = G_comb / p_comb_density
    u_vol_and_comb = u_vol + u_comb

    g_dQ_from_particle_limits = 0

    if p_mass_new != 0:
        # particle mass fractions new
        p_Y_comb_new = p_mass_comb_new / p_mass_new
        p_Y_vol_new = p_mass_vol_new / p_mass_new
        print('p mass fractions: ', p_Y_vol_new, p_Y_comb_new, p_Y_inert)
        # p_Y_inert_new = 1 - p_Y_comb_new - p_Y_vol_new
        if p_Y_inert == 0:
            p_Y_inert_new = 0
        else:
            p_Y_inert_new = 1 - p_Y_comb_new - p_Y_vol_new

        # mass fractions after evaporation and combustion
        p_mass_fractions_new = {}
        p_mass_fractions_new['combustible'] = p_Y_comb_new
        p_mass_fractions_new['volatile'] = p_Y_vol_new
        p_mass_fractions_new['inert'] = p_Y_inert_new

        # particle density new
        p_density_new = dispersed_material.get_density(p_mass_fractions_new)
        # particle volume new
        p_volume_new = p_mass_new / p_density_new
        # particle diameter
        p_diameter_new = calc_sphere_diameter(p_volume_new)
        # particle surface area new
        p_surface_area_new = calc_sphere_surface(p_diameter_new)

        if small_mass_cut_off:
            if p_diameter_new < p_diameter_min_limit*0.000001:
                # CALCULATE GAS SOURCE FROM FULL COMBUSTION AND EVAPORATION:
                # neglect inert component energy - small diameters likely to occur in calculations for combustible-volatile mixtures without inert components
                p_dm_comb = p_mass_comb
                # part of final combustion energy, that goes to particle - now all goes to gas
                g_dQ_from_particle_limits += x_pop_ox * dH_comb_final * p_dm_comb
                p_dm_vol = p_mass_vol
                p_diameter_new = 0
                p_mass_new = 0


    if p_mass_new != 0:
        # FOR LIMITED combustion and evaporation rate calculations:
        # particle mass after evaporation only
        p_mass_after_evaporation = p_mass_comb + p_mass_vol_new + p_mass_inert_new
        # particle mass fractions after evaporation only
        p_Y_comb_after_evaporation = p_mass_comb / p_mass_after_evaporation
        p_Y_vol_after_evaporation = p_mass_vol_new / p_mass_after_evaporation
        # p_Y_inert_new = 1 - p_Y_comb_new - p_Y_vol_new
        if p_Y_inert == 0:
            p_Y_inert_after_evaporation = 0
        else:
            p_Y_inert_after_evaporation = 1 - p_Y_comb_after_evaporation - p_Y_vol_after_evaporation
        # mass fractions after evaporation
        p_mass_fractions_after_evaporation = {'combustible': p_Y_comb_after_evaporation,
                                              'volatile': p_Y_vol_after_evaporation,
                                              'inert': p_Y_inert_after_evaporation}
        # particle density after evaportaion
        p_density_after_evaporation = dispersed_material.get_density(p_mass_fractions_after_evaporation)
        # particle volume after evaporation
        p_volume_after_evaporation = p_mass_after_evaporation / p_density_after_evaporation
        # particle diameter after evaporation
        p_diameter_after_evaporatoin = calc_sphere_diameter(p_volume_after_evaporation)
        # particle surface area after evaporation
        p_surface_area_after_evaporatoin = calc_sphere_surface(p_diameter_after_evaporatoin)
        # particle combustion and evaporation rate [m/s]
        u_vol_limiters = (p_diameter - p_diameter_after_evaporatoin) / 2 / dt
        u_comb_limiters = (p_diameter_after_evaporatoin - p_diameter_new) / 2 / dt
        u_vol_and_comb_limiters = u_vol_limiters + u_comb_limiters
        # combine all linear evaporation and combustion rate [m/s] in one vector for convenient output
        u_linear_rate = {'volatile': u_vol,
                         'combustible': u_comb,
                         'volatile_and_combustible': u_vol_and_comb,
                         'volatile_limiters': u_vol_limiters,
                         'combustible_limiters': u_comb_limiters,
                         'volatile_and_combustible_limiters': u_vol_and_comb_limiters}

    if p_mass_new == 0:
        print('particle mass zero')
        p_enthalpy = dispersed_material.get_enthalpy(p_mass_fractions, p_temperature)
        u_linear_rate = {'volatile': u_vol,
                         'combustible': u_comb,
                         'volatile_and_combustible': u_vol_and_comb,
                         'volatile_limiters': 0,
                         'combustible_limiters': 0,
                         'volatile_and_combustible_limiters': 0}
        q_averaged = {'evaporation': 0,
                      'convection': 0,
                      'combustion': 0,
                      'comb_preliminary': 0,
                      'comb_final': 0,
                      'comb_mass': 0,
                      'comb_preliminary_and_final': 0,
                      'total': 0,
                      'comb_preliminary_unlimited': 0,
                      'comb_final_unlimited': 0,
                      'comb_preliminary_and_final_unlimited': 0,
                      'total_unlimited_without_comb_mass': 0,
                      }

        out_dH = {'dH_vol_evap': 0,
                  'dH_comb_preliminary': dH_comb_preliminary,
                  'dH_comb_final': dH_comb_final,
                  'k_comb': k_comb}

        out_p_Q = {'p_Q': 0,
                   'p_enthalpy': p_enthalpy,
                   'p_temperature': p_temperature,
                   'p_dQ_vol_evap': 0,
                   'p_Q_after_evaporation': 0,
                   'p_enthalpy_after_evaporation': 0,
                   'p_temperature_after_evaporation': 0,
                   'p_dQ_comb_mass': 0,
                   'p_dQ_comb_prelim': 0,
                   'p_dQ_comb_final': 0,
                   'p_Q_after_combustion': 0,
                   'p_enthalpy_after_combustion': 0,
                   'p_temperature_after_combustion': 0,
                   'p_dQ_convection': 0,
                   'p_Q_new': 0,
                   'p_enthalpy_new': 0,
                   'p_temperature_new': 0}

        out_g_Q = {'g_Q': 0,
                   'g_enthalpy': 0,
                   'g_temperature': g_temperature,
                   'g_dQ': 0,
                   'g_dQ_GV_mass': 0,
                   'g_dQ_CPCF_mass': 0,
                   'g_dQ_oxidizer_mass': 0,
                   'g_dQ_convection': 0,
                   'g_dQ_final_combustion': 0,
                   'g_dQ_from_particle_limits': g_dQ_from_particle_limits,
                   'g_Q_new': 0,
                   'g_enthalpy_new': 0,
                   'g_temperature_new': 0}

        out_misc = {'p_vol_saturation_pressure': p_vol_saturation_pressure,
                    'g_vol_partial_pressure': g_vol_partial_pressure,
                    'p_density': p_density,
                    'p_mass': p_mass,
                    'p_mass_fractions': p_mass_fractions,
                    'g_mass_fractions': g_mass_fractions}

        return (p_mass_fractions, p_temperature, 0, g_mass_fractions, g_temperature, u_linear_rate, q_averaged, vol_and_comb_functions_output, out_dH, out_p_Q, out_g_Q, out_misc)

    # gas mass [kg]
    g_mass = g_density * g_cell_volume
    # gas mass source [kg/s]
    # g_dmdt = p_dmdt_comb + p_dmdt_vol






    # CALCULATING NEW PARTICLE TEMPERATURE
    # volatile component evaporation energy source is always negative,
    # all convective energy sources are positive in case of gas heating particle (Tg > Tp) and negative in case of gas cooling particle (Tg < Tp)
    # all chemical reactions energy sources for primary oxidation and complete combustion are always positive
    # chemical reactions energy source from mass deletion is always negative
    # !!! ATTENTION !!! we should consider all possible thermal conditions for all possible combustible/volatile/inert mixture compositions
    # to avoid unphysical results especially on last time steps, big time steps and small particle diameters
    # 1) evaporation
    # 2) convection
    # 3) chemical heating
    # that separation allows for particle cooling below gas temperature in case of strong evaporation, particle heating over gas temperature in case of strong reactions
    # keeps exactly Tp = Tg in case of dominating convection


    # 1-ST - ONLY EVAPORATIVE COOLING
    # particle energy source from volatile component evaporation [J]- NEGATIVE value
    p_dQ_vol_evap = dH_vol_evap * p_dm_vol
    print('p_dQ_vol_evap dH_vol_evap p_dm_vol p_dmdt_vol dt', p_dQ_vol_evap, dH_vol_evap, p_dm_vol, p_dmdt_vol, dt)
    # particle energy before evaporation
    # BECOUSE late we use function based on enthalpy value, without H0, we determine here somewhat unphysical value - with left part under temperature range based on constant interpolation
    p_Q = dispersed_material.get_enthalpy(p_mass_fractions, p_temperature) * p_mass
    # IN CASE we want to use full enthalpy physical values - use next formula, but we need accordingly function dispersed_material.temperature_from_full_enthalpy and H0 defined correctly for all components
    # p_Q = p_comb_H_full*p_mass_comb + p_vol_H_full*p_mass_vol + p_inert_H_full*p_mass_inert
    q_evap_averaged = p_dQ_vol_evap / (p_surface_area * dt)

    # regardless of separate_heat_fluxes we need low limiter for particle temperature after evaporation
    # TODO if not separate_heat_fluxes - try to evaluate based on Q after all processes

    # particle mass after evaporation
    p_mass_after_evaporation = p_mass - p_dm_vol
    # calculate low limit temperature [K] after evaporation based on saturation pressure limit [Pa] for evaporation possibility:
    p_vol_saturation_pressure_limit = 1e-10
    T_evap_low_limit = 1 / (math.log(p_vol_saturation_pressure_limit / p_vol_Pb) * R0 / g_vol_M / dH_vol_evap + 1 / p_vol_Tb)
    # particle energy limit after evaporation:
    p_Q_after_evaporation_limit = p_mass_after_evaporation * dispersed_material.get_enthalpy(p_mass_fractions_after_evaporation, T_evap_low_limit)
    print('evaporation low temperature limit: T_evap_low_limit, p_Q_after_evaporation_limit', T_evap_low_limit, p_Q_after_evaporation_limit)
    # checking for possible cooling below low temperature limit
    if (p_Q + p_dQ_vol_evap <= p_Q_after_evaporation_limit):
        print('WARNING - volatile component evaporative cooling reaches low temperature limit')
        p_dQ_vol_evap = p_Q_after_evaporation_limit - p_Q
        # MASS recalculation and redefinition
        p_dm_vol = p_dQ_vol_evap / dH_vol_evap
        p_mass_vol_new = p_mass_vol - p_dm_vol
        p_mass_new = p_mass_comb_new + p_mass_vol_new + p_mass_inert_new
        p_Y_vol_new = p_mass_vol_new / p_mass_new
        p_Y_comb_new = p_mass_comb_new / p_mass_new
        if p_Y_inert == 0:
            p_Y_inert_new = 0
        else:
            p_Y_inert_new = 1 - p_Y_comb_new - p_Y_vol_new
        print('p mass fractions after evaporation low T limiting: ', p_Y_comb_new, p_Y_vol_new, p_Y_inert_new)
        p_mass_fractions_new['combustible'] = p_Y_comb_new
        p_mass_fractions_new['volatile'] = p_Y_vol_new
        p_mass_fractions_new['inert'] = p_Y_inert_new
        p_density_new = dispersed_material.get_density(p_mass_fractions_new)
        p_volume_new = p_mass_new / p_density_new
        p_diameter_new = calc_sphere_diameter(p_volume_new)
        p_surface_area_new = calc_sphere_surface(p_diameter_new)
        p_mass_after_evaporation = p_mass - p_dm_vol


    # particle energy after evaporation [J] - output only
    p_Q_after_evaporation = p_Q + p_dQ_vol_evap







    # averaged evaporative heat flux [W/m^2]
    q_evap_averaged = p_dQ_vol_evap / ((p_surface_area + p_surface_area_after_evaporatoin) / 2 * dt)


    # particle energy after evaporation
    p_Q_after_evaporation = p_Q + p_dQ_vol_evap
    # particle enthalpy after evaporation
    p_enthalpy_after_evaporation = p_Q_after_evaporation / p_mass_after_evaporation
    # particle temperature after evaporation
    p_temperature_after_evaporation = dispersed_material.get_temperature_from_enthalpy(p_mass_fractions_after_evaporation, p_enthalpy_after_evaporation)


    print("\n p_temperature p_temperature_after_evaporation p_enthalpy p_enthalpy_after_evaporation p_Q p_Q_after_evaporation : ", p_temperature, p_temperature_after_evaporation, p_enthalpy, p_enthalpy_after_evaporation, p_Q, p_Q_after_evaporation)




    # 2-ND - ONLY CHEMICAL REACTIVE HEATING FROM PRIMARY OXIDATION AND FINAL COMBUSTION
    # so far old thermal state used in alpha, Re, Nu calculations - should be not much difference and no conservation laws violation
    # also old thermal state surface area used
    # WE SHOULD CALCULATE MASS CHANGE HERE IF USING STATE AFTER EVAPORATION AND INERT HEATING!!!
    # particle energy source from preliminary oxidation
    p_dQ_comb_prelim = p_surface_area_comb_fraction * q_react_comb_preliminary * p_surface_area * dt
    # particle energy source from final combustion
    p_dQ_comb_final = p_surface_area_comb_fraction * q_react_comb_final * p_surface_area * dt
    # particle energy source(sink) from combustion mass deletion:
    p_dQ_comb_mass = -dispersed_material.get_enthalpy(p_mass_fractions_pure_combustible, p_temperature) * p_dm_comb
    # particle energy after combustion
    p_Q_after_combustion = p_Q + p_dQ_vol_evap + p_dQ_comb_mass + p_dQ_comb_prelim + p_dQ_comb_final
    print('after combustion: p_Q, p_dQ_vol_evap, p_dQ_comb_mass, p_dQ_comb_prelim p_dQ_comb_final: ', p_Q, p_dQ_vol_evap, p_dQ_comb_mass, p_dQ_comb_prelim, p_dQ_comb_final)
    # CHECK - maximum possible combustion temperature
    # for case when small mass particle remains and strong combustion heat release should not exceed physical limits
    # max possible gas source - if all combustion energy goes to gas:
    g_dQ_comb_max = p_dm_comb*(dH_comb_preliminary + dH_comb_final)
    print('g_dQ_comb_max p_dm_comb dH_comb_preliminary dH_comb_final: ', g_dQ_comb_max, p_dm_comb, dH_comb_preliminary, dH_comb_final)


    # CALCULATE GAS SOURCES
    # calculate limits for particle combustion based on isobaric relations
    # gas initial mass oxidizer [kg]
    g_m_oxidizer = g_mass_fractions['oxidizer'] * g_mass
    # gas initial mass nitrogen [kg]
    g_m_nitrogen = g_mass_fractions['nitrogen'] * g_mass
    # gas initial mass volatile component [kg]
    g_m_vilatile = g_mass_fractions['volatile'] * g_mass
    # gas initial mass preliminary combustion products (NO NEED FOR NOW) [kg]
    g_m_CPCP = g_mass_fractions['CPCP'] * g_mass
    # gas initial mass final combustion products [kg]
    g_m_CPCF = g_mass_fractions['CPCF'] * g_mass
    # gas mass sources !!! NEEDED ONLY FOR FLUENT AND QUBIQ AND NOT USED IN THAT SCRIPT !!!
    # mass source of volatile gas component [kg/s]
    g_dY_GV_dt = p_dmdt_vol * n_particles
    # mass source of oxidizer gas component (NO CHECK FOR FULL CONSUMPTION HERE) [kg/s]
    g_dY_G_oxidizer_dt = -K_mass_final * p_dmdt_comb * n_particles
    # mass source of CPCF gas component [kg/s]
    g_dY_G_CPCF_dt = (1 + K_mass_final) * p_dmdt_comb * n_particles
    # gas new mass of oxidizer [kg]
    g_m_oxidizer_new = max(g_m_oxidizer - p_dm_comb * n_particles * K_mass_final, 0)
    if g_m_oxidizer_new == 0:
        print('full oxidizer consumption')
    # gas new mass of nitrogen [kg]
    g_m_nitrogen_new = g_m_nitrogen
    # gas new mass of volatile component [kg]
    g_m_volatile_new = g_m_vilatile + p_dm_vol * n_particles
    # gas new mass of preliminary combustion products (NO NEED FOR NOW) [kg]
    g_m_CPCP_new = g_m_CPCP
    # gas new mass of final combustion products [kg]
    g_m_CPCF_new = g_m_CPCF + (1 + K_mass_final) * p_dm_comb * n_particles
    # gas mass new [kg]
    g_mass_new = g_m_oxidizer_new + g_m_nitrogen_new + g_m_volatile_new + g_m_CPCP_new + g_m_CPCF_new
    # new gas mass fractions
    g_mass_fractions_new = {'oxidizer': g_m_oxidizer_new / g_mass_new,
                            'volatile': g_m_volatile_new / g_mass_new,
                            'nitrogen': g_m_nitrogen_new / g_mass_new,
                            'CPCP': g_m_CPCP_new / g_mass_new,
                            'CPCF': g_m_CPCF_new / g_mass_new}
    if g_mass_fractions_new['oxidizer'] < Y_min_g_limit_fraction:
        g_mass_fractions_new['oxidizer'] = 0
    # gas new molar mass [kg/mol]
    g_M = gas_material.get_mu(g_mass_fractions_new) / 1000
    if not separate_heat_fluxes:
        p_temperature_after_evaporation = p_temperature

    # gas enthalpy [J/kg] for pure volatile component at temperature after evaporation
    g_GV_H_after_evaporation = gas_material.get_enthalpy(g_mass_fractions_pure_volatile, p_temperature_after_evaporation)
    # gas full energy source for volatile component mass addition [J]
    g_dQ_GV_mass = p_dm_vol * (g_GV_H + g_GV_H_after_evaporation)/2
    # gas full energy source for final combustion products mass addition [J]
    g_dQ_CPCF_mass = (1 + K_mass_final) * p_dm_comb * g_CPCF_H
    # gas full energy source (sink) for oxidizer consumption [J]- NEGATIVE value
    g_dQ_oxidizer_mass = - K_mass_final * p_dm_comb * g_O2_H_f
    # Full energy source for final combustion:
    g_dQ_final_combustion = p_dQ_comb_final / x_pop_ox * (1 - x_pop_ox)
    # initial gas enthalpy [J/kg]
    g_enthalpy = gas_material.get_enthalpy(g_mass_fractions, g_temperature)
    # initial gas full energy [J]:
    g_Q = g_enthalpy * g_mass
    if p_dm_comb > 0:
        # gas pure CPCF cloud maximum possible energy [J] per one particle if all combustion energy goes to gas:
        # g_CPCF_cloud_Q_max = (g_dQ_CPCF_mass + g_dQ_comb_max)
        g_CPCF_cloud_Q_max = g_dQ_comb_max
        print('g_dQ_CPCF_mass g_dQ_comb_max', g_dQ_CPCF_mass, g_dQ_comb_max)
        # gas pure CPCF cloud maximum possible enthalpy [J] per one particle if all combustion energy goes to gas:
        g_CPCF_cloud_enthalpy_max = g_CPCF_cloud_Q_max / p_dm_comb / (1+K_mass_final)
        print('g_CPCF_cloud_enthalpy_max', g_CPCF_cloud_enthalpy_max)
        # gas pure CPCF cloud maximum temperature [K] if all combustion energy goes to gas:
        g_CPCF_cloud_temperature_max = gas_material.get_temperature_from_enthalpy(g_mass_fractions_pure_CPCF, g_CPCF_cloud_enthalpy_max)
        # LIMIT particle temperature after combustion:
        p_temperature_after_combustion_max = g_CPCF_cloud_temperature_max
        p_Q_after_combustion_max = dispersed_material.get_enthalpy(p_mass_fractions_new, p_temperature_after_combustion_max) * p_mass_new
        print('p_temperature_after_combustion_max g_CPCF_cloud_enthalpy_max p_Q_after_combustion_max: ', p_temperature_after_combustion_max, g_CPCF_cloud_enthalpy_max, p_Q_after_combustion_max)
        # gas energy source from extra particle energy that does not fit into particle because of maximum temperature limits:
        if p_Q_after_combustion > p_Q_after_combustion_max:
            print('reaching max particle temperature in chemical reaction heating, p_Q_after_combustion, p_Q_after_combustion_max', p_Q_after_combustion, p_Q_after_combustion_max)
            p_Q_after_combustion = p_Q_after_combustion_max
            g_dQ_from_particle_limits += (p_Q_after_combustion - p_Q_after_combustion_max)
        # particle enthalpy after combustion [J/kg]
        p_enthalpy_after_combustion = p_Q_after_combustion / p_mass_new
        # particle temperature after combuston [K]
        p_temperature_after_combustion = dispersed_material.get_temperature_from_enthalpy(p_mass_fractions_new, p_enthalpy_after_combustion)
    else:
        p_enthalpy_after_combustion = p_enthalpy_after_evaporation
        p_temperature_after_combustion = p_temperature_after_evaporation


    if not separate_heat_fluxes:
        q_comb_averaged_preliminary = p_dQ_comb_prelim / (p_surface_area * dt)
        q_comb_averaged_final = p_dQ_comb_final / (p_surface_area * dt)
        q_comb_averaged_mass = p_dQ_comb_mass / (p_surface_area * dt)
        q_comb_averaged = (p_dQ_comb_prelim + p_dQ_comb_final + p_dQ_comb_mass) / (p_surface_area * dt)
    else:
        # heat flux components from combustion (for output only)
        q_comb_averaged_preliminary = p_dQ_comb_prelim / ((p_surface_area_after_evaporatoin + p_surface_area_new) / 2 * dt)
        q_comb_averaged_final = p_dQ_comb_final / ((p_surface_area_after_evaporatoin + p_surface_area_new) / 2 * dt)
        q_comb_averaged_mass = p_dQ_comb_mass / ((p_surface_area_after_evaporatoin + p_surface_area_new) / 2 * dt)
        # averaged combustion heat flux [W/m^2]
        q_comb_averaged = (p_Q_after_combustion - p_Q_after_evaporation) / ((p_surface_area_after_evaporatoin + p_surface_area_new) / 2 * dt)
        # total heat flux to particle [W/m^2]







    # 3-RD - ONLY CONVECTIVE HEATING OR COOLING
    # define gas total energy limits - to limit particle convective heating temperature
    def calculate_mid_temperature_universal():
        eps_Q = 0.0001
        if not separate_heat_fluxes:
            # NOT USED NOW - NO ANY LIMITATION!!!
            T1 = p_temperature
        else:
            T1 = p_temperature_after_combustion
        T2 = g_temperature
        p_dQ = eps_Q
        g_dQ = eps_Q
        def _p_dQ(T):
            if not separate_heat_fluxes:
                # NOT USED NOW - NO ANY LIMITATION!!!
                return (dispersed_material.get_enthalpy(p_mass_fractions, T) - p_enthalpy) * p_mass * n_particles
            else:
                return (dispersed_material.get_enthalpy(p_mass_fractions_new, T) - p_enthalpy_after_combustion)*p_mass_new * n_particles
        def _g_dQ(T):
            return (gas_material.get_enthalpy(g_mass_fractions, T) - g_enthalpy)*g_mass
        while abs(p_dQ + g_dQ) > eps_Q:
            T_cur = (T1 + T2) / 2
            p_dQ = _p_dQ(T_cur)
            g_dQ = _g_dQ(T_cur)
            if not separate_heat_fluxes:
                print('p_temperature T1 T_cur T2 g_temperature p_dQ g_dQ: ', p_temperature, T1, T_cur, T2, g_temperature, p_dQ, g_dQ)
            else:
                print('p_temperature_after_combustion T1 T_cur T2 g_temperature p_dQ g_dQ: ', p_temperature_after_combustion, T1, T_cur, T2, g_temperature, p_dQ, g_dQ)
            if p_dQ > 0 > g_dQ:
                if p_dQ + g_dQ > 0:
                    T2 = T_cur
                else:
                    T1 = T_cur
            else:
                if p_dQ + g_dQ > 0:
                    T1 = T_cur
                else:
                    T2 = T_cur
        return T_cur, g_dQ
    temperature_energy_balance, gas_source_limit = calculate_mid_temperature_universal()
    # combustible / volatile / inert component convective heat flux [W/m^2]
    # so far old thermal state used in alpha, Re, Nu calculations - should be not much difference and no conservation laws violation
    # also old thermal state surface area used
    if not separate_heat_fluxes:
        q_conv_comb = theta_comb * alpha_comb * (g_temperature - p_temperature)
        q_conv_vol = theta_vol * alpha_vol * (g_temperature - p_temperature)
        q_conv_inert = alpha_inert * (g_temperature - p_temperature)
        p_dQ_convection = (q_conv_comb * p_surface_area_comb_fraction + q_conv_vol * p_surface_area_vol_fraction + q_conv_inert * (1 - p_surface_area_comb_fraction - p_surface_area_vol_fraction)) * p_surface_area * dt
        gas_energy_source = - p_dQ_convection
        q_conv_averaged = p_dQ_convection / (p_surface_area * dt)
        p_Q_new = p_Q + p_dQ_vol_evap + p_dQ_comb_mass + p_dQ_comb_prelim + p_dQ_comb_final + p_dQ_convection
        if p_Q_new < 0:
            p_Q_new = 1
    else:
        q_conv_comb = theta_comb * alpha_comb * (g_temperature - p_temperature_after_combustion)
        q_conv_vol = theta_vol * alpha_vol * (g_temperature - p_temperature_after_combustion)
        print('q_conv_vol theta_vol alpha_vol g_temperature p_temperature_after_combustion', q_conv_vol, theta_vol, alpha_vol, g_temperature, p_temperature_after_combustion)
        q_conv_inert = alpha_inert * (g_temperature - p_temperature_after_combustion)
        # particle energy source from convective heating
        p_dQ_convection = (q_conv_comb * p_surface_area_comb_fraction + q_conv_vol * p_surface_area_vol_fraction + q_conv_inert * (1 - p_surface_area_comb_fraction - p_surface_area_vol_fraction)) * p_surface_area_new * dt
        print('p_dQ_convection q_conv_comb p_surface_area_comb_fraction q_conv_vol p_surface_area_vol_fraction q_conv_inert p_surface_area_new', p_dQ_convection, q_conv_comb, p_surface_area_comb_fraction, q_conv_vol, p_surface_area_vol_fraction, q_conv_inert, p_surface_area_new)
        # particle limit possible energy with diameter after evaporation, at the gas temperature
        p_Q_convection_limit = dispersed_material.get_enthalpy(p_mass_fractions_new, temperature_energy_balance) * p_mass_new
        # particle energy after convection
        p_Q_new = p_Q_after_combustion + p_dQ_convection
        gas_energy_source = - p_dQ_convection
        # checking for particle reaching convective limits
        print('after convection before limiting: p_dQ_convection p_Q_new p_Q_convection_limit', p_dQ_convection, p_Q_new, p_Q_convection_limit)
        if p_dQ_convection > 0 and p_Q_new >= p_Q_convection_limit:
            print('reaching max convective heating: p_Q_new  p_Q_convection_limit', p_Q_new, p_Q_convection_limit)
            p_Q_new = p_Q_convection_limit
            gas_energy_source = gas_source_limit / n_particles
        if p_dQ_convection < 0 and p_Q_new <= p_Q_convection_limit:
            print('reaching max convective cooling: p_Q_new  p_Q_convection_limit', p_Q_new, p_Q_convection_limit)
            p_Q_new = p_Q_convection_limit
            gas_energy_source = gas_source_limit / n_particles
        print('after convection after limiting: p_dQ_convection p_Q_new p_Q_convection_limit q_conv_vol p_surface_area_vol_fraction', p_dQ_convection, p_Q_new, p_Q_convection_limit, q_conv_vol, p_surface_area_vol_fraction)
        # averaged convective heat flux [W/m^2]
        q_conv_averaged = (p_Q_new - p_Q_after_combustion) / (p_surface_area_new * dt)

    # gas full energy source (sink) for inert heating or cooling - including volatile/combustible/inert particle components:
    g_dQ_convection = gas_energy_source
    # particle enthalpy new [J/kg]
    p_enthalpy_new = p_Q_new / p_mass_new
    # particle temperature new [K]
    p_temperature_new = dispersed_material.get_temperature_from_enthalpy(p_mass_fractions_new, p_enthalpy_new)
    # print('temperatures after convection: p_temperature_after_evaporation temperature_energy_balance g_temperature p_temperature_after_convection_and_evaporation:', p_temperature_after_evaporation, temperature_energy_balance, g_temperature, p_temperature_after_convection_and_evaporation)

    q_total_averaged = q_evap_averaged + q_conv_averaged + q_comb_averaged

    # combine all heat flux to particle [W/m^2] in one vector for convenient output
    q_averaged = {'evaporation': q_evap_averaged,
                  'convection': q_conv_averaged,
                  'combustion': q_comb_averaged,
                  'comb_preliminary': q_comb_averaged_preliminary,
                  'comb_final': q_comb_averaged_final,
                  'comb_mass': q_comb_averaged_mass,
                  'comb_preliminary_and_final': q_comb_averaged_preliminary + q_comb_averaged_final,
                  'total': q_total_averaged,
                  'comb_preliminary_unlimited': q_react_comb_preliminary,
                  'comb_final_unlimited': q_react_comb_final,
                  'comb_preliminary_and_final_unlimited': q_react_comb_preliminary + q_react_comb_final,
                  'total_unlimited_without_comb_mass': q_evap_averaged + q_conv_averaged + q_react_comb_preliminary + q_react_comb_final}
    # gas full energy source [J]:
    g_dQ = (g_dQ_GV_mass + g_dQ_CPCF_mass + g_dQ_oxidizer_mass + g_dQ_convection + g_dQ_final_combustion + g_dQ_from_particle_limits) * n_particles
    # gas full energy new [J]:
    g_Q_new = g_Q + g_dQ
    # gas enthalpy new [J/kg]:
    g_enthalpy_new = g_Q_new / g_mass_new
    # gas temperature new [K]:
    g_temperature_new = gas_material.get_temperature_from_enthalpy(g_mass_fractions_new, g_enthalpy_new)


    print('\ngas total energy components: g_Q_new g_Q g_dQ g_dQ_GV_mass g_dQ_CPCF_mass g_dQ_oxidizer_mass g_dQ_convection g_dQ_final_combustion g_dQ_comb_max g_dQ_from_particle_limits g_temperature_new:')
    print(g_Q_new, g_Q, g_dQ, g_dQ_GV_mass, g_dQ_CPCF_mass, g_dQ_oxidizer_mass, g_dQ_convection, g_dQ_final_combustion, g_dQ_comb_max, g_dQ_from_particle_limits, g_temperature_new)


    if p_dm_comb > 0:
        print('p_temperature_new p_temperature_after_combustion_max', p_temperature_new, p_temperature_after_combustion_max)


    # output dictionaties:

    out_dH = {'dH_vol_evap': dH_vol_evap,
              'dH_comb_preliminary': dH_comb_preliminary,
              'dH_comb_final': dH_comb_final,
              'k_comb': k_comb}

    out_p_Q = {'p_Q': p_Q,
               'p_enthalpy': p_enthalpy,
               'p_temperature': p_temperature,
               'p_dQ_vol_evap': p_dQ_vol_evap,
               'p_Q_after_evaporation': p_Q_after_evaporation,
               'p_enthalpy_after_evaporation': p_enthalpy_after_evaporation,
               'p_temperature_after_evaporation': p_temperature_after_evaporation,
               'p_dQ_comb_mass': p_dQ_comb_mass,
               'p_dQ_comb_prelim': p_dQ_comb_prelim,
               'p_dQ_comb_final': p_dQ_comb_final,
               'p_Q_after_combustion': p_Q_after_combustion,
               'p_enthalpy_after_combustion': p_enthalpy_after_combustion,
               'p_temperature_after_combustion': p_temperature_after_combustion,
               'p_dQ_convection': p_dQ_convection,
               'p_Q_new': p_Q_new,
               'p_enthalpy_new': p_enthalpy_new,
               'p_temperature_new': p_temperature_new}

    out_g_Q = {'g_Q': g_Q,
               'g_enthalpy': g_enthalpy,
               'g_temperature': g_temperature,
               'g_dQ': g_dQ,
               'g_dQ_GV_mass': g_dQ_GV_mass,
               'g_dQ_CPCF_mass': g_dQ_CPCF_mass,
               'g_dQ_oxidizer_mass': g_dQ_oxidizer_mass,
               'g_dQ_convection': g_dQ_convection,
               'g_dQ_final_combustion': g_dQ_final_combustion,
               'g_dQ_from_particle_limits': g_dQ_from_particle_limits,
               'g_Q_new': g_Q_new,
               'g_enthalpy_new': g_enthalpy_new,
               'g_temperature_new': g_temperature_new}



    out_misc = {'p_vol_saturation_pressure': p_vol_saturation_pressure,
                'g_vol_partial_pressure': g_vol_partial_pressure,
                'p_density': p_density,
                'p_mass': p_mass,
                'p_mass_fractions': p_mass_fractions,
                'g_mass_fractions': g_mass_fractions}



    # GAS SOURCES:

    if g_mode == GasMode.no_sources:
        # new gas temperature
        g_temperature_new = g_temperature
        # new gas mass fractions
        g_mass_fractions_new = g_mass_fractions

    else:
        if g_mode == GasMode.isobaric:
            # all gas sources already defined
            pass

        if g_mode == GasMode.isochoric:
            pass

    return (p_mass_fractions_new, p_temperature_new, p_diameter_new, g_mass_fractions_new, g_temperature_new, u_linear_rate, q_averaged, vol_and_comb_functions_output, out_dH, out_p_Q, out_g_Q, out_misc)



# Start parameters
p_mass_fractions = particle_start_mass_fractions
p_temperature = p_start_temperature
p_diameter = p_start_diameter
g_mass_fractions = gas_start_mass_fractions
g_temperature = g_start_temperature

p_enthalpy = dispersed_material.get_enthalpy(particle_start_mass_fractions, p_start_temperature)
g_enthalpy = gas_material.get_enthalpy(gas_start_mass_fractions, g_start_temperature)
p_density = dispersed_material.get_density(p_mass_fractions)
p_volume = calc_sphere_volume(p_diameter)
p_mass = p_density * p_volume

array_size = math.ceil(t_end/dt)+1

ar_time = np.zeros(array_size)
ar_p_Y_combustible = np.zeros(array_size)
ar_p_Y_volatile = np.zeros(array_size)
ar_p_Y_inert = np.zeros(array_size)
ar_g_Y_oxidizer = np.zeros(array_size)
ar_g_Y_volatile = np.zeros(array_size)
ar_g_Y_nitrogen = np.zeros(array_size)
ar_g_Y_CPCP = np.zeros(array_size)
ar_g_Y_CPCF = np.zeros(array_size)
ar_p_diameter = np.zeros(array_size)
ar_p_mass = np.zeros(array_size)
ar_p_mass_combustible = np.zeros(array_size)
ar_p_mass_volatile = np.zeros(array_size)
ar_p_mass_inert = np.zeros(array_size)
ar_p_density = np.zeros(array_size)

ar_u_vol = np.zeros(array_size)
ar_u_comb = np.zeros(array_size)
ar_u_vol_and_comb = np.zeros(array_size)
ar_u_vol_limiters = np.zeros(array_size)
ar_u_comb_limiters = np.zeros(array_size)
ar_u_vol_and_comb_limiters = np.zeros(array_size)

ar_q_evap = np.zeros(array_size)
ar_q_conv = np.zeros(array_size)
ar_q_comb = np.zeros(array_size)
ar_q_total = np.zeros(array_size)

ar_q_comb_prelim = np.zeros(array_size)
ar_q_comb_final = np.zeros(array_size)
ar_q_comb_mass = np.zeros(array_size)
ar_q_comb_prelim_and_final = np.zeros(array_size)

ar_q_nonlim_comb_prelim = np.zeros(array_size)
ar_q_nonlim_comb_final = np.zeros(array_size)
ar_q_nonlim_comb_prelim_and_final = np.zeros(array_size)
ar_q_nonlim_total_without_comb_mass = np.zeros(array_size)

ar_vcf_G_vol = np.zeros(array_size)
ar_vcf_Y_surf_vol = np.zeros(array_size)
ar_vcf_theta_vol = np.zeros(array_size)
ar_vcf_G_comb = np.zeros(array_size)
ar_vcf_Y_surf_comb = np.zeros(array_size)
ar_vcf_theta_comb = np.zeros(array_size)

ar_p_vol_saturation_pressure = np.zeros(array_size)
ar_g_vol_partial_pressure = np.zeros(array_size)

ar_dH_vol_evap = np.zeros(array_size)
ar_dH_comb_preliminary = np.zeros(array_size)
ar_dH_comb_final = np.zeros(array_size)
ar_k_comb = np.zeros(array_size)



ar_p_Q = np.zeros(array_size)
ar_p_enthalpy = np.zeros(array_size)
ar_p_temperature = np.zeros(array_size)
ar_p_dQ_vol_evap = np.zeros(array_size)
ar_p_Q_after_evaporation = np.zeros(array_size)
ar_p_enthalpy_after_evaporation = np.zeros(array_size)
ar_p_temperature_after_evaporation = np.zeros(array_size)
ar_p_dQ_comb_mass = np.zeros(array_size)
ar_p_dQ_comb_prelim = np.zeros(array_size)
ar_p_dQ_comb_final = np.zeros(array_size)
ar_p_Q_after_combustion = np.zeros(array_size)
ar_p_enthalpy_after_combustion = np.zeros(array_size)
ar_p_temperature_after_combustion = np.zeros(array_size)
ar_p_dQ_convection = np.zeros(array_size)
ar_p_Q_new = np.zeros(array_size)
ar_p_enthalpy_new = np.zeros(array_size)
ar_p_temperature_new = np.zeros(array_size)

ar_g_Q = np.zeros(array_size)
ar_g_enthalpy = np.zeros(array_size)
ar_g_temperature = np.zeros(array_size)
ar_g_dQ = np.zeros(array_size)
ar_g_dQ_GV_mass = np.zeros(array_size)
ar_g_dQ_CPCF_mass = np.zeros(array_size)
ar_g_dQ_oxidizer_mass = np.zeros(array_size)
ar_g_dQ_convection = np.zeros(array_size)
ar_g_dQ_final_combustion = np.zeros(array_size)
ar_g_dQ_from_particle_limits = np.zeros(array_size)
ar_g_Q_new = np.zeros(array_size)
ar_g_enthalpy_new = np.zeros(array_size)
ar_g_temperature_new = np.zeros(array_size)




t = 0
i = 0

ar_time[0] = t
ar_p_diameter[0] = p_diameter * 1000000
ar_p_mass[0] = p_mass
ar_p_temperature[0] = p_temperature
ar_p_mass_combustible[0] = p_mass * p_mass_fractions['combustible']
ar_p_mass_volatile[0] = p_mass * p_mass_fractions['volatile']
ar_p_mass_inert[0] = p_mass * p_mass_fractions['inert']
ar_p_enthalpy[0] = p_enthalpy
ar_p_density[0] = p_density
ar_p_Y_combustible[0] = p_mass_fractions['combustible']
ar_p_Y_volatile[0] = p_mass_fractions['volatile']
ar_p_Y_inert[0] = p_mass_fractions['inert']
ar_g_temperature[0] = g_temperature
ar_g_enthalpy[0] = g_enthalpy
ar_g_Y_oxidizer[0] = g_mass_fractions['oxidizer']
ar_g_Y_volatile[0] = g_mass_fractions['volatile']
ar_g_Y_nitrogen[0] = g_mass_fractions['nitrogen']
ar_g_Y_CPCP[0] = g_mass_fractions['CPCP']
ar_g_Y_CPCF[0] = g_mass_fractions['CPCF']


# p_diameter_new, p_mass_new, p_temperature_new, p_enthalpy_new, p_density_new, p_mass_fractions_new, g_temperature_new, g_mass_fractions_new = make_step(p_mass_fractions, p_temperature, p_diameter, g_mass_fractions, g_temperature)
#
# p_diameter, p_mass, p_temperature, p_enthalpy, p_density, p_mass_fractions, g_temperature, g_mass_fractions = p_diameter_new, p_mass_new, p_temperature_new, p_enthalpy_new, p_density_new, p_mass_fractions_new, g_temperature_new, g_mass_fractions_new

t_complete_volatile_evaporation = None
t_complete_combustible_combustion = None
t_complete_oxidizer_consumption = None
eps = dt * 0.001
eps_T = 0.001
once_more = iter([True, False])
is_more = True

print('\nMAIN LOOP')
while t < t_end and is_more:
    p_mass_fractions_new, p_temperature_new, p_diameter_new, g_mass_fractions_new, g_temperature_new, u_linear_rate, q_averaged, vol_and_comb_functions_output, out_dH, out_p_Q, out_g_Q, out_misc = make_step(p_mass_fractions, p_temperature, p_diameter, g_mass_fractions, g_temperature)

    i += 1
    t += dt
    print('current iteration, time, p_diameter, p_temperature: ', i, t, p_diameter_new * 1000000, p_temperature_new, '\n')
    ar_time[i] = t
    ar_p_diameter[i] = p_diameter * 1000000
    ar_p_mass[i] = out_misc['p_mass']
    ar_p_density[i] = out_misc['p_density']
    ar_p_vol_saturation_pressure[i] = out_misc['p_vol_saturation_pressure']
    ar_g_vol_partial_pressure[i] = out_misc['g_vol_partial_pressure']

    ar_p_mass_volatile[i] = ar_p_mass[i] * out_misc['p_mass_fractions']['volatile']
    ar_p_mass_combustible[i] = ar_p_mass[i] * out_misc['p_mass_fractions']['combustible']
    ar_p_mass_inert[i] = ar_p_mass[i] * out_misc['p_mass_fractions']['inert']
    ar_p_Y_volatile[i] = out_misc['p_mass_fractions']['volatile']
    ar_p_Y_combustible[i] = out_misc['p_mass_fractions']['combustible']
    ar_p_Y_inert[i] = out_misc['p_mass_fractions']['inert']
    ar_g_Y_oxidizer[i] = out_misc['g_mass_fractions']['oxidizer']
    ar_g_Y_volatile[i] = out_misc['g_mass_fractions']['volatile']
    ar_g_Y_nitrogen[i] = out_misc['g_mass_fractions']['nitrogen']
    ar_g_Y_CPCP[i] = out_misc['g_mass_fractions']['CPCP']
    ar_g_Y_CPCF[i] = out_misc['g_mass_fractions']['CPCF']
    # LATER if needed - output new mass fractions
    # ar_p_Y_combustible[i] = p_mass_fractions_new['combustible']
    # ar_p_Y_volatile[i] = p_mass_fractions_new['volatile']
    # ar_p_Y_inert[i] = p_mass_fractions_new['inert']
    # ar_g_Y_oxidizer[i] = g_mass_fractions_new['oxidizer']
    # ar_g_Y_volatile[i] = g_mass_fractions_new['volatile']
    # ar_g_Y_nitrogen[i] = g_mass_fractions_new['nitrogen']
    # ar_g_Y_CPCP[i] = g_mass_fractions_new['CPCP']
    # ar_g_Y_CPCF[i] = g_mass_fractions_new['CPCF']

    ar_u_vol[i] = u_linear_rate['volatile']
    ar_u_comb[i] = u_linear_rate['combustible']
    ar_u_vol_and_comb[i] = u_linear_rate['volatile_and_combustible']
    ar_u_vol_limiters[i] = u_linear_rate['volatile_limiters']
    ar_u_comb_limiters[i] = u_linear_rate['combustible_limiters']
    ar_u_vol_and_comb_limiters[i] = u_linear_rate['volatile_and_combustible_limiters']

    ar_q_evap[i] = q_averaged['evaporation']
    ar_q_conv[i] = q_averaged['convection']
    ar_q_comb[i] = q_averaged['combustion']
    ar_q_total[i] = q_averaged['total']
    ar_q_comb_prelim[i] = q_averaged['comb_preliminary']
    ar_q_comb_final[i] = q_averaged['comb_final']
    ar_q_comb_mass[i] = q_averaged['comb_mass']
    ar_q_comb_prelim_and_final[i] = q_averaged['comb_preliminary_and_final']

    ar_q_nonlim_comb_prelim[i] = q_averaged['comb_preliminary_unlimited']
    ar_q_nonlim_comb_final[i] = q_averaged['comb_final_unlimited']
    ar_q_nonlim_comb_prelim_and_final[i] = q_averaged['comb_preliminary_and_final_unlimited']
    ar_q_nonlim_total_without_comb_mass[i] = q_averaged['total_unlimited_without_comb_mass']

    ar_vcf_G_vol[i] = vol_and_comb_functions_output['G_vol']
    ar_vcf_Y_surf_vol[i] = vol_and_comb_functions_output['Y_surf_vol']
    ar_vcf_theta_vol[i] = vol_and_comb_functions_output['theta_vol']
    ar_vcf_G_comb[i] = vol_and_comb_functions_output['G_comb']
    ar_vcf_Y_surf_comb[i] = vol_and_comb_functions_output['Y_surf_comb']
    ar_vcf_theta_comb[i] = vol_and_comb_functions_output['theta_comb']

    ar_dH_vol_evap[i] = out_dH['dH_vol_evap']
    ar_dH_comb_preliminary[i] = out_dH['dH_comb_preliminary']
    ar_dH_comb_final[i] = out_dH['dH_comb_final']
    ar_k_comb[i] = out_dH['k_comb']

    ar_p_Q[i] = out_p_Q['p_Q']
    ar_p_enthalpy[i] = out_p_Q['p_enthalpy']
    ar_p_temperature[i] = out_p_Q['p_temperature']
    ar_p_dQ_vol_evap[i] = out_p_Q['p_dQ_vol_evap']
    ar_p_Q_after_evaporation[i] = out_p_Q['p_Q_after_evaporation']
    ar_p_enthalpy_after_evaporation[i] = out_p_Q['p_enthalpy_after_evaporation']
    ar_p_temperature_after_evaporation[i] = out_p_Q['p_temperature_after_evaporation']
    ar_p_dQ_comb_mass[i] = out_p_Q['p_dQ_comb_mass']
    ar_p_dQ_comb_prelim[i] = out_p_Q['p_dQ_comb_prelim']
    ar_p_dQ_comb_final[i] = out_p_Q['p_dQ_comb_final']
    ar_p_Q_after_combustion[i] = out_p_Q['p_Q_after_combustion']
    ar_p_enthalpy_after_combustion[i] = out_p_Q['p_enthalpy_after_combustion']
    ar_p_temperature_after_combustion[i] = out_p_Q['p_temperature_after_combustion']
    ar_p_dQ_convection[i] = out_p_Q['p_dQ_convection']
    ar_p_Q_new[i] = out_p_Q['p_Q_new']
    ar_p_enthalpy_new[i] = out_p_Q['p_enthalpy_new']
    ar_p_temperature_new[i] = out_p_Q['p_temperature_new']

    ar_g_Q[i] = out_g_Q['g_Q']
    ar_g_enthalpy[i] = out_g_Q['g_enthalpy']
    ar_g_temperature[i] = out_g_Q['g_temperature']
    ar_g_dQ[i] = out_g_Q['g_dQ']
    ar_g_dQ_GV_mass[i] = out_g_Q['g_dQ_GV_mass']
    ar_g_dQ_CPCF_mass[i] = out_g_Q['g_dQ_CPCF_mass']
    ar_g_dQ_oxidizer_mass[i] = out_g_Q['g_dQ_oxidizer_mass']
    ar_g_dQ_convection[i] = out_g_Q['g_dQ_convection']
    ar_g_dQ_final_combustion[i] = out_g_Q['g_dQ_final_combustion']
    ar_g_dQ_from_particle_limits[i] = out_g_Q['g_dQ_from_particle_limits']
    ar_g_Q_new[i] = out_g_Q['g_Q_new']
    ar_g_enthalpy_new[i] = out_g_Q['g_enthalpy_new']
    ar_g_temperature_new[i] = out_g_Q['g_temperature_new']



    # NEW PARTICLE STATE
    p_mass_fractions, p_temperature, p_diameter, g_mass_fractions, g_temperature = p_mass_fractions_new, p_temperature_new, p_diameter_new, g_mass_fractions_new, g_temperature_new


    if t_complete_volatile_evaporation is None and p_mass_fractions_new['volatile'] == 0 or (p_diameter_new == 0 and t_complete_combustible_combustion is not None):
        t_complete_volatile_evaporation = t
    if t_complete_combustible_combustion is None and p_mass_fractions_new['combustible'] == 0 or (p_diameter_new == 0 and t_complete_volatile_evaporation is not None):
        t_complete_combustible_combustion = t
    if t_complete_oxidizer_consumption is None and g_mass_fractions_new['oxidizer'] == 0:
        t_complete_oxidizer_consumption = t
    # cases of full solve:
    # 1) for fuel without inert component - all vilatile and combustible gone
    # 2) for fuel with inert component - all vilatile and combustible gone and particle temperature equals gas temperature
    # 3)


    if t_complete_volatile_evaporation is not None and t_complete_combustible_combustion is not None and (p_mass_fractions_new['inert'] == 0 or abs(p_temperature_new - g_temperature_new) < eps_T):
        is_more = next(once_more)
    if t_complete_volatile_evaporation is not None and t_complete_oxidizer_consumption is not None and (p_mass_fractions_new['inert'] == 0 or abs(p_temperature_new - g_temperature_new) < eps_T):
        is_more = next(once_more)

    print('particle and gas temperature: ', p_temperature_new, g_temperature_new, (p_temperature_new == g_temperature_new))

    if abs(t_end - t) < eps:
        print('\ncompleting calculation based on limited max time, t = ', t)
        # in case of t < t_end by small < eps value because of numerical operations with floating point precision we need break here
        break
    if p_diameter_new == 0:
        print('\ncompleting calculation based on full solve conditions, t = ', t)
        break


if not is_more:
    print('\ncompleting calculation based on full solve conditions, t = ', t)


ar_u_vol[0] = ar_u_vol[1]
ar_u_comb[0] = ar_u_comb[1]
ar_u_vol_and_comb[0] = ar_u_vol_and_comb[1]
ar_u_vol_limiters[0] = ar_u_vol_limiters[1]
ar_u_comb_limiters[0] = ar_u_comb_limiters[1]
ar_u_vol_and_comb_limiters[0] = ar_u_vol_and_comb_limiters[1]

ar_q_evap[0] = ar_q_evap[1]
ar_q_conv[0] = ar_q_conv[1]
ar_q_comb[0] = ar_q_comb[1]
ar_q_total[0] = ar_q_total[1]
ar_q_nonlim_comb_prelim[0] = ar_q_nonlim_comb_prelim[1]
ar_q_nonlim_comb_final[0] = ar_q_nonlim_comb_final[1]
ar_q_nonlim_comb_prelim_and_final[0] = ar_q_nonlim_comb_prelim_and_final[1]
ar_q_nonlim_total_without_comb_mass[0] = ar_q_nonlim_total_without_comb_mass[1]

ar_vcf_G_vol[0] = ar_vcf_G_vol[1]
ar_vcf_Y_surf_vol[0] = ar_vcf_Y_surf_vol[1]
ar_vcf_theta_vol[0] = ar_vcf_theta_vol[1]
ar_vcf_G_comb[0] = ar_vcf_G_comb[1]
ar_vcf_Y_surf_comb[0] = ar_vcf_Y_surf_comb[1]
ar_vcf_theta_comb[0] = ar_vcf_theta_comb[1]

ar_p_vol_saturation_pressure[0] = ar_p_vol_saturation_pressure[1]
ar_g_vol_partial_pressure[0] = ar_g_vol_partial_pressure[1]

ar_dH_vol_evap[0] = ar_dH_vol_evap[1]
ar_dH_comb_preliminary[0] = ar_dH_comb_preliminary[1]
ar_dH_comb_final[0] = ar_dH_comb_final[1]
ar_k_comb[0] = ar_k_comb[1]

ar_p_Q[0] = ar_p_Q[1]
# ar_p_enthalpy[0] = ar_p_enthalpy[1]
# ar_p_temperature[0] = ar_p_temperature[1]
ar_p_dQ_vol_evap[0] = ar_p_dQ_vol_evap[1]
ar_p_Q_after_evaporation[0] = ar_p_Q_after_evaporation[1]
ar_p_enthalpy_after_evaporation[0] = ar_p_enthalpy_after_evaporation[1]
ar_p_temperature_after_evaporation[0] = ar_p_temperature_after_evaporation[1]
ar_p_dQ_comb_mass[0] = ar_p_dQ_comb_mass[1]
ar_p_dQ_comb_prelim[0] = ar_p_dQ_comb_prelim[1]
ar_p_dQ_comb_final[0] = ar_p_dQ_comb_final[1]
ar_p_Q_after_combustion[0] = ar_p_Q_after_combustion[1]
ar_p_enthalpy_after_combustion[0] = ar_p_enthalpy_after_combustion[1]
ar_p_temperature_after_combustion[0] = ar_p_temperature_after_combustion[1]
ar_p_dQ_convection[0] = ar_p_dQ_convection[1]
ar_p_Q_new[0] = ar_p_Q_new[1]
ar_p_enthalpy_new[0] = ar_p_enthalpy_new[1]
ar_p_temperature_new[0] = ar_p_temperature_new[1]

ar_g_Q[0] = ar_g_Q[1]
ar_g_dQ[0] = ar_g_dQ[1]
# ar_g_enthalpy[0] = ar_g_enthalpy[1]
# ar_g_temperature[0] = ar_g_temperature[1]
ar_g_dQ_GV_mass[0] = ar_g_dQ_GV_mass[1]
ar_g_dQ_CPCF_mass[0] = ar_g_dQ_CPCF_mass[1]
ar_g_dQ_oxidizer_mass[0] = ar_g_dQ_oxidizer_mass[1]
ar_g_dQ_convection[0] = ar_g_dQ_convection[1]
ar_g_dQ_final_combustion[0] = ar_g_dQ_final_combustion[1]
ar_g_dQ_from_particle_limits[0] = ar_g_dQ_from_particle_limits[1]
ar_g_Q_new[0] = ar_g_Q_new[1]
ar_g_enthalpy_new[0] = ar_g_enthalpy_new[1]
ar_g_temperature_new[0] = ar_g_temperature_new[1]




columns = {'time[s]': ar_time[0:i+1],
           'p_diameter[mkm]': ar_p_diameter[0:i+1],
           'p_mass[kg]': ar_p_mass[0:i+1],
           'p_mass_combustible[kg]': ar_p_mass_combustible[0:i+1],
           'p_mass_volatile[kg]': ar_p_mass_volatile[0:i+1],
           'p_mass_inert[kg]': ar_p_mass_inert[0:i+1],
           'p_temperature[K]': ar_p_temperature[0:i+1],
           'p_density[kg/m^3]': ar_p_density[0:i+1],
           'p_Y_combustible': ar_p_Y_combustible[0:i+1],
           'p_Y_volatile': ar_p_Y_volatile[0:i+1],
           'p_Y_inert': ar_p_Y_inert[0:i+1],
           'g_temperature[K]': ar_g_temperature[0:i+1],
           'g_enthalpy[J/kg]': ar_g_enthalpy[0:i+1],
           'g_Y_oxidizer': ar_g_Y_oxidizer[0:i+1],
           'g_Y_volatile': ar_g_Y_volatile[0:i+1],
           'g_Y_nitrogen': ar_g_Y_nitrogen[0:i+1],
           'g_Y_CPCP': ar_g_Y_CPCP[0:i+1],
           'g_Y_CPCF': ar_g_Y_CPCF[0:i+1],
           'p_enthalpy[J/kg]': ar_p_enthalpy[0:i+1],
           'u_vol[m/s]': ar_u_vol[0:i+1],
           'u_comb[m/s]': ar_u_comb[0:i+1],
           'u_vol_and_comb[m/s]': ar_u_vol_and_comb[0:i+1],
           'u_vol_limiters[m/s]': ar_u_vol_limiters[0:i+1],
           'u_comb_limiters[m/s]': ar_u_comb_limiters[0:i+1],
           'u_vol_and_comb_limiters[m/s]': ar_u_vol_and_comb_limiters[0:i+1],
           'q_evap[W/m^2]': ar_q_evap[0:i+1],
           'q_conv[W/m^2]': ar_q_conv[0:i+1],
           'q_comb[W/m^2]': ar_q_comb[0:i+1],
           'q_comb_prelim[W/m^2]': ar_q_comb_prelim[0:i+1],
           'q_comb_final[W/m^2]': ar_q_comb_final[0:i+1],
           'q_comb_prelim_and_final[W/m^2]': ar_q_comb_prelim_and_final[0:i+1],
           'q_comb_mass[W/m^2]': ar_q_comb_mass[0:i+1],
           'q_total[W/m^2]': ar_q_total[0:i+1],
           'q_unlim_comb_prelim[W/m^2]': ar_q_nonlim_comb_prelim[0:i+1],
           'q_unlim_comb_final[W/m^2]': ar_q_nonlim_comb_final[0:i+1],
           'q_unlim_comb_prelim_and_final[W/m^2]': ar_q_nonlim_comb_prelim_and_final[0:i+1],
           'q_unlim_total_without_comb_mass[W/m^2]': ar_q_nonlim_total_without_comb_mass[0:i+1],
           'G_vol[kg/m^2/s]': ar_vcf_G_vol[0:i+1],
           'Y_surf_vol': ar_vcf_Y_surf_vol[0:i+1],
           'theta_vol': ar_vcf_theta_vol[0:i+1],
           'G_comb[kg/m^2/s]': ar_vcf_G_comb[0:i+1],
           'Y_surf_comb': ar_vcf_Y_surf_comb[0:i+1],
           'theta_comb': ar_vcf_theta_comb[0:i+1],
           'p_vol_saturation_pressure[Pa]': ar_p_vol_saturation_pressure[0:i+1],
           'g_vol_partial_pressure[Pa]': ar_g_vol_partial_pressure[0:i+1],
           'dH_vol_evap[J/kg]': ar_dH_vol_evap[0:i+1],
           'dH_comb_preliminary[J/kg]': ar_dH_comb_preliminary[0:i+1],
           'dH_comb_final[J/kg]': ar_dH_comb_final[0:i+1],
           'k_comb[s/m]': ar_k_comb[0:i+1],
           'p_Q[J]': ar_p_Q[0:i+1],
           'p_dQ_vol_evap[J]': ar_p_dQ_vol_evap[0:i+1],
           'p_Q_after_evaporation[J]': ar_p_Q_after_evaporation[0:i+1],
           'p_enthalpy_after_evaporation[J/kg]': ar_p_enthalpy_after_evaporation[0:i+1],
           'p_temperature_after_evaporation[K]': ar_p_temperature_after_evaporation[0:i+1],
           'p_dQ_comb_mass[J]': ar_p_dQ_comb_mass[0:i+1],
           'p_dQ_comb_prelim[J]': ar_p_dQ_comb_prelim[0:i+1],
           'p_dQ_comb_final[J]': ar_p_dQ_comb_final[0:i+1],
           'p_Q_after_combustion[J]': ar_p_Q_after_combustion[0:i+1],
           'p_enthalpy_after_combustion[J/kg]': ar_p_enthalpy_after_combustion[0:i+1],
           'p_temperature_after_combustion[K]': ar_p_temperature_after_combustion[0:i+1],
           'p_dQ_convection[J]': ar_p_dQ_convection[0:i+1],
           'p_Q_new[J]': ar_p_Q_new[0:i+1],
           'p_enthalpy_new[J/kg]': ar_p_enthalpy_new[0:i+1],
           'p_temperature_new[K]': ar_p_temperature_new[0:i+1],
           'g_Q[J]': ar_g_Q[0:i+1],
           'g_dQ[J]': ar_g_dQ[0:i+1],
           'g_dQ_GV_mass[J]': ar_g_dQ_GV_mass[0:i+1],
           'g_dQ_CPCF_mass[J]': ar_g_dQ_CPCF_mass[0:i+1],
           'g_dQ_oxidizer_mass[J]': ar_g_dQ_oxidizer_mass[0:i+1],
           'g_dQ_convection[J]': ar_g_dQ_convection[0:i+1],
           'g_dQ_final_combustion[J]': ar_g_dQ_final_combustion[0:i+1],
           'g_dQ_from_particle_limits[J]': ar_g_dQ_from_particle_limits[0:i+1],
           'g_Q_new[J]': ar_g_Q_new[0:i+1],
           'g_temperature_new[K]': ar_g_temperature_new[0:i + 1],
           'g_enthalpy_new[J/kg]': ar_g_enthalpy_new[0:i + 1]}



result = pd.DataFrame(columns, index=ar_time[0:i+1])


path_solution = ''.join((path_run, '\\', dir_soulution))
os.makedirs(path_solution, exist_ok=True)

os.chdir(path_solution)


x_t_label = r'$время\ (с)$'
y_Cp_label = r'$Cp\ (\frac{Дж}{кг \cdot К})$'
y_H_label = r'$H\ (\frac{Дж}{кг})$'


def plot_result(y, style, label, ylabel, pic_name):
    result.plot(y=y, use_index=True, style=style, grid=True, label=label, xlabel=x_t_label, ylabel=ylabel, xlim=0)
    if t_complete_volatile_evaporation is not None:
        plt.axvline(t_complete_volatile_evaporation, color='black', linestyle='--', label=''.join(('полное испарение летучего,\nt = ', '{0:.{1}}'.format(t_complete_volatile_evaporation, 6), ' с')))
    if t_complete_combustible_combustion is not None:
        plt.axvline(t_complete_combustible_combustion, color='black', linestyle='--', label=''.join(('полное сгорание горючего,\nt = ', '{0:.{1}}'.format(t_complete_combustible_combustion, 6), ' с')))
    if t_complete_oxidizer_consumption is not None:
        plt.axvline(t_complete_oxidizer_consumption, color='black', linestyle='--', label=''.join(('полное выгорание окислителя,\nt = ', '{0:.{1}}'.format(t_complete_oxidizer_consumption, 6), ' с')))
    plt.legend(loc='best', fontsize='small')
    plt.savefig(''.join(('pic_', pic_name, '.jpeg')), dpi=400, bbox_inches='tight')
    plt.close()


plot_result(['p_diameter[mkm]'], ['o-'], [r'$диаметр\ частицы\ [мкм]$'], r'$d\ (мкм)$', '01_p_diameter')
plot_result(['p_mass[kg]'], ['o-'], [r'$масса\ частицы\ [кг]$'], r'$m\ (кг)$', '02_p_mass')
plot_result(['p_mass[kg]', 'p_mass_combustible[kg]', 'p_mass_volatile[kg]', 'p_mass_inert[kg]'], ['o-', '-', '-', '-'], [r'$масса\ частицы\ [кг]$', r'$масса\ горючего\ компонента\ частицы\ [кг]$', r'$масса\ летучего\ компонента\ частицы\ [кг]$', r'$масса\ инертного\ компонента\ частицы\ [кг]$'], r'$m\ (кг)$', '03_p_mass_all')
plot_result(['p_temperature[K]'], ['o-'], [r'$температура\ частицы\ [К]$'], r'$T\ (K)$', '04_p_temperature')
plot_result(['p_density[kg/m^3]'], ['o-'], [r'$плотность частицы\ \left[\frac{кг}{м^3}\right]$'], r'$\rho\ \left(\frac{кг}{м^3}\right)$', '05_p_density')
plot_result(['p_Y_combustible', 'p_Y_volatile', 'p_Y_inert'], ['-', '-', '-'], ['массовая доля горючих', 'массовая доля летучих', 'массовая доля инертных'], r'$Y$', '06_p_mass_fractions')
plot_result(['g_temperature[K]'], ['o-'], [r'$температура\ газа\ [К]$'], r'$T\ (K)$', '07_g_temperature')
plot_result(['g_Y_oxidizer', 'g_Y_volatile', 'g_Y_nitrogen', 'g_Y_CPCP', 'g_Y_CPCF'], ['-', '-', '-', '-', '-'], ['массовая доля окислителя', 'массовая доля летучего', 'массовая доля азота', 'массовая доля первичных продуктов окисления', 'массовая доля конечных продуктов окисления'], r'$Y$', '08_g_mass_fractions')
plot_result(['p_temperature[K]', 'g_temperature[K]'], ['-', '-'], [r'$температура\ частицы\ [К]$', r'$температура\ газа\ [К]$'], r'$T\ (K)$', '09_gp_temperature')
plot_result(['p_enthalpy[J/kg]'], ['-'], [r'$энтальпия\ частицы\ \left[\frac{Дж}{кг}\right]$'], r'$H\ \left(\frac{Дж}{кг}\right)$', '10_p_enthalpy')

plot_result(['p_vol_saturation_pressure[Pa]', 'g_vol_partial_pressure[Pa]'], ['-', '-'], [r'$давление насыщенных паров летучего компонента [Па]$', r'$парциальное давление летучего компонента газа [Па]$'], r'$p\ (Па)$', '21_p_saturation_pressure')


plot_result(['u_vol[m/s]', 'u_comb[m/s]', 'u_vol_and_comb[m/s]'], ['-', '-', '-'], ['линейная скорость испарения', 'линейная скорость горения', 'линейная скорость испарения и горения'], r'$u\ \left(\frac{м}{с}\right)$', '11_u_rate')
plot_result(['u_vol_limiters[m/s]', 'u_comb_limiters[m/s]', 'u_vol_and_comb_limiters[m/s]'], ['-', '-', '-'], ['линейная скорость испарения с огр.', 'линейная скорость горения с огр.', 'линейная скорость испарения и горения с огр.'], r'$u\ \left(\frac{м}{с}\right)$', '12_u_rate_limiters')
plot_result(['u_vol[m/s]', 'u_vol_limiters[m/s]'], ['-', '-'], ['линейная скорость испарения', 'линейная скорость испарения с огр.'], r'$u\ \left(\frac{м}{с}\right)$', '12_u_rate_evap')
plot_result(['u_comb[m/s]', 'u_comb_limiters[m/s]'], ['-', '-'], ['линейная скорость горения', 'линейная скорость горения с огр.'], r'$u\ \left(\frac{м}{с}\right)$', '12_u_rate_comb')
plot_result(['u_vol_and_comb[m/s]', 'u_vol_and_comb_limiters[m/s]'], ['-', '-'], ['линейная скорость испарения и горения', 'линейная скорость испарения и горения с огр.'], r'$u\ \left(\frac{м}{с}\right)$', '13_u_rate_comb')



plot_result(['q_evap[W/m^2]', 'q_conv[W/m^2]', 'q_comb[W/m^2]', 'q_total[W/m^2]'], ['-', '-', '-', '-'], ['тепловой поток от испарения', 'тепловой поток от конвекции', 'тепловой поток от горения', 'тепловой поток суммарный'], r'$q\ \left(\frac{Вт}{м^2}\right)$', '14_q_heat_flux')
plot_result(['q_conv[W/m^2]', 'q_comb[W/m^2]'], ['-', '-'], ['тепловой поток от конвекции', 'тепловой поток от горения'], r'$q\ \left(\frac{Вт}{м^2}\right)$', '15_q_conv_comb')
plot_result(['q_unlim_comb_prelim[W/m^2]', 'q_unlim_comb_final[W/m^2]', 'q_unlim_comb_prelim_and_final[W/m^2]'], ['-', '-', '-'], ['тепловой поток от горения первичных без огр.', 'тепловой поток от горения конечных без огр.', 'тепловой поток от горения суммарный без огр.'], r'$q\ \left(\frac{Вт}{м^2}\right)$', '16_q_comb_unlim')
plot_result(['q_unlim_total_without_comb_mass[W/m^2]'], ['-'], ['тепловой поток суммарный без огр. без компонента уноса массы горючего'], r'$q\ \left(\frac{Вт}{м^2}\right)$', '17_q_total_unlim')
plot_result(['q_comb_prelim[W/m^2]', 'q_comb_final[W/m^2]', 'q_comb_prelim_and_final[W/m^2]'], ['-', '-', '-'], ['тепловой поток от горения первичных', 'тепловой поток от горения конечных', 'тепловой поток от горения суммарный'], r'$q\ \left(\frac{Вт}{м^2}\right)$', '18_q_comb_without_mass')
plot_result(['q_comb_prelim[W/m^2]', 'q_comb_final[W/m^2]', 'q_comb_mass[W/m^2]', 'q_comb[W/m^2]'], ['-', '-', '-', '-'], ['тепловой поток от горения первичных', 'тепловой поток от горения конечных', 'тепловой поток от горения унос массы', 'тепловой поток от горения'], r'$q\ \left(\frac{Вт}{м^2}\right)$', '19_q_comb_with_mass')
plot_result(['q_comb_prelim[W/m^2]', 'q_unlim_comb_prelim[W/m^2]', 'q_comb_final[W/m^2]', 'q_unlim_comb_final[W/m^2]', 'q_comb_prelim_and_final[W/m^2]', 'q_unlim_comb_prelim_and_final[W/m^2]'], ['-', '-', '-', '-', '-', '-'], ['тепловой поток от горения первичных', 'тепловой поток от горения первичных без огр.', 'тепловой поток от горения конечных', 'тепловой поток от горения конечных без огр.', 'тепловой поток от горения суммарный', 'тепловой поток от горения суммарный без огр.'], r'$q\ \left(\frac{Вт}{м^2}\right)$', '20_q_comb_lim_unlim')

plot_result(['p_temperature[K]', 'p_temperature_after_evaporation[K]', 'p_temperature_after_combustion[K]', 'p_temperature_new[K]', 'g_temperature[K]', 'g_temperature_new[K]'], ['-', '-', '-', '-', '-', '-'], ['температура частицы', 'температура частицы после испарения', 'температура частицы после горения', 'температура частицы новая', 'температура газа', 'температура газа новая'], r'$T\ (K)$', '21_pg_T')


columns_initial_conditions = {'dt[s]': dt,
                              't_end[s]': t_end,
                              'p_d[mkm]': p_start_diameter*1000000,
                              'p_T[K]': p_start_temperature,
                              'p_Y_volatile': particle_start_mass_fractions['volatile'],
                              'p_Y_combustible': particle_start_mass_fractions['combustible'],
                              'p_Y_inert': particle_start_mass_fractions['inert'],
                              'g_T[K]': g_start_temperature,
                              'g_P[Pa]': g_pressure,
                              'g_v[m/s]': g_slip_velocity,
                              'g_Y_oxidizer': gas_start_mass_fractions['oxidizer'],
                              'g_Y_volatile': gas_start_mass_fractions['volatile'],
                              'g_Y_nitrogen': gas_start_mass_fractions['nitrogen'],
                              'g_Y_CPCP': gas_start_mass_fractions['CPCP'],
                              'g_Y_CPCF': gas_start_mass_fractions['CPCF'],
                              'p_enthalpy[K]': p_enthalpy,
                              'K_mass_preliminary': K_mass_preliminary,
                              'K_mass_final': K_mass_final,
                              'p_comb_H0': p_comb_H0,
                              'p_vol_H0': p_vol_H0,
                              'p_inert_H0': p_inert_H0,
                              'g_GV_H0': g_GV_H0,
                              'g_O2_H0': g_O2_H0,
                              'g_CPCP_H0': g_CPCP_H0,
                              'g_CPCF_H0': g_CPCF_H0
                              }
data_initial_conditions = pd.DataFrame.from_dict(columns_initial_conditions, orient='index', columns=['variable'])

columns_results = {}
if t_complete_volatile_evaporation is not None:
    columns_results['t_complete_volatile_evaporation'] = t_complete_volatile_evaporation
if t_complete_combustible_combustion is not None:
    columns_results['t_complete_combustible_combustion'] = t_complete_combustible_combustion
if t_complete_oxidizer_consumption is not None:
    columns_results['t_complete_oxidizer_consumption'] = t_complete_oxidizer_consumption

writer = pd.ExcelWriter(''.join(('result', '.xlsx')), engine="xlsxwriter")
result.to_excel(writer, index=False, sheet_name='result')
data_initial_conditions.to_excel(writer, index=True, sheet_name='initial')

pd.DataFrame.from_dict(mf_products_preliminary, orient='index', columns=['variable']).to_excel(writer, index=True, sheet_name='mf_products_preliminary')
pd.DataFrame.from_dict(mf_products_final, orient='index', columns=['variable']).to_excel(writer, index=True, sheet_name='mf_products_final_full')
pd.DataFrame.from_dict(g_CPCF, orient='index', columns=['variable']).to_excel(writer, index=True, sheet_name='mf_products_final')
pd.DataFrame.from_dict(columns_results, orient='index', columns=['variable']).to_excel(writer, index=True, sheet_name='output_averaged')

# mf_products_preliminary.to_excel(writer, index=True, sheet_name='mf_products_preliminary')
# mf_products_final.to_excel(writer, index=True, sheet_name='mf_products_final_full')
# g_CPCF.to_excel(writer, index=True, sheet_name='mf_products_final')
writer.close()



print('OOP debug')

