import pandas as pd
import fileinput, glob, os
import re
import math
import matplotlib.pyplot as plt
import numpy as np
import pylab
from pathlib import Path

from utils import plot_result

verify_FLUENT = True
verify_QUBIQ = True
verify_gas = True

GOST = True



style_Q = '-'
style_F = '--'

line_width = 2

verify_sources = [verify_FLUENT, verify_QUBIQ]
number_of_sources = sum(verify_sources)

path_verification = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\Verification\hot_high'
dir_verification = 'run'

if verify_QUBIQ:
    # path_qubiq_particles_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\QUBIQ\LES\points_averaged_QUBIQ.csv'
    path_qubiq_particles_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\QUBIQ\LES_HOT_HIGH\points_averaged_QUBIQ.csv'
if verify_gas:
    # path_qubiq_gas_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\QUBIQ\LES\data_averaged_QUBIQ_3D.csv'
    # path_qubiq_gas_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\QUBIQ\LES\Integration_results\slice_integration\combined_results.csv'
    path_qubiq_gas_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\FLUENT\06_LES_high_regenerated\2nd_mom_time\run_QUBIQ\slices\combined_results.csv'


if verify_FLUENT:
    # path_fluent_particles_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\FLUENT\03_LES_analytic\points_averaged_FLUENT.csv'
    path_fluent_particles_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\FLUENT\06_LES_high_regenerated\2nd_mom_time\points_averaged_FLUENT.csv'


if verify_gas:
    # path_fluent_gas_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\FLUENT\02_LES\data_averaged_FLUENT_3D.csv'
    # path_fluent_gas_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\FLUENT\03_LES_analytic\run\slices\combined_results.csv'
    path_fluent_gas_01 = r'D:\YASIM\VORON\2026_12_Iskra_OPZ\FLUENT\06_LES_high_regenerated\2nd_mom_time\run_done\slices\combined_results.csv'



# y_limits = {
#     'Temperature': [2000, 2100],
#     'Pressure': [500000, 503000],
#     'Velocity': [0, 20],
#     'Y_Air': [0, 1],
#     'Y_CP': [0, 1],
#     'turbulent_kinetic_energy': [0, 0.3],
#     'specific_dissipation_rate': [0, 4000]
# }

# iskra OPZ hot low
# y_limits = {
#     'particle_diameter': [0, 5],
#     'particle_temperature': [0, 2000],
#     'particle_mass_flow_rate': [0, 1],
#     'particle_mass': [0, 1.8e-13],
#     'combustion_efficiency': [-0.25, 1.1],
#     'gas_temperature': [500, 2500],
#     'gas_pressure': [0, 1400000],
#     'gas_velocity': [0, 1000],
#     'gas_Y_air': [0, 1],
#     'gas_Y_cp': [0, 1],
#     'gas_Y_gpg': [0, 0.1],
#     'gas_mass_flow_rate': [0, 8]
# }

# iskra OPZ hot high
y_limits = {
    'particle_diameter': [0, 5],
    'particle_temperature': [0, 2000],
    'particle_mass_flow_rate': [0, 0.2],
    'particle_mass': [0, 1.8e-13],
    'combustion_efficiency': [-0.25, 1.1],
    'gas_temperature': [500, 3200],
    'gas_pressure': [0, 400000],
    'gas_velocity': [0, 2000],
    'gas_Y_air': [0, 1],
    'gas_Y_cp': [0, 1],
    'gas_Y_gpg': [0, 0.1],
    'gas_mass_flow_rate': [0, 2]
}

x_limit_low = -0.5
x_limit_high = 1.7
# x_limit = 0.4

# iskra OPZ hot low
# mfr_fuel_particles_in = 0.495
# mfr_fuel_gas_in = 0.405
# mfr_oxidizer_in = 6.58

# iskra OPZ hot high
mfr_fuel_particles_in = 0.1155
mfr_fuel_gas_in = 0.0945
mfr_oxidizer_in = 1.27



mfr_gas = mfr_oxidizer_in + mfr_fuel_gas_in
mfr_all = mfr_gas + mfr_fuel_particles_in

mass_stoichiometric_ratio = 5.37

path_verification_current_run = ''.join((path_verification, '/', dir_verification))
Path(path_verification_current_run).mkdir(parents=True, exist_ok=True)
os.chdir(path_verification_current_run)

if verify_FLUENT:
    df_fluent_particles_01 = pd.read_csv(path_fluent_particles_01, index_col='CoordinateX')

if verify_gas:
    df_fluent_gas_01 = pd.read_csv(path_fluent_gas_01, index_col='CoordinateX')

if verify_QUBIQ:
    df_qubiq_particles_01 = pd.read_csv(path_qubiq_particles_01, index_col='CoordinateX')

if verify_gas:
    df_qubiq_gas_01 = pd.read_csv(path_qubiq_gas_01, index_col='CoordinateX')


# n_particles = 2000
# ts_scale_factor = 1
#
if verify_FLUENT:
    df_fluent_particles_01['Diameter'] = df_fluent_particles_01['Diameter']*1e6
    df_fluent_particles_01['Diameter_mave'] = df_fluent_particles_01['Diameter_mave'] * 1e6
    # При условии альфа > 1:
    df_fluent_particles_01['Combustion_Efficiency'] = np.maximum(1 - (df_fluent_particles_01['Mass_Flow_Rate']/mfr_fuel_particles_in), 0)

if verify_QUBIQ:
    df_qubiq_particles_01['Diameter'] = df_qubiq_particles_01['Diameter']*1e6


def combustion_efficiency(mass_stoichiometric_ratio, mfr_fuel_in, mfr_oxidizer_in, mfr_products, mfr_oxidizer, mfr_fuel, Y_products, Y_oxidizer, Y_fuel):
    alpha = mfr_oxidizer_in / (mfr_fuel_in * mass_stoichiometric_ratio)

    mfr_oxidizer_can_react = mfr_oxidizer_in
    mfr_fuel_can_react = mfr_fuel_in
    mfr_oxidizer_left = 0
    mfr_fuel_left = 0

    if alpha >= 1:
        mfr_oxidizer_can_react = mfr_oxidizer_in / alpha
        mfr_oxidizer_left = mfr_oxidizer_in * (alpha - 1)
    else:
        mfr_fuel_can_react = mfr_fuel_in * alpha
        mfr_fuel_left = mfr_fuel_in * (1 - alpha)

    # Максимально возможное количество продуктов если всё прореагирует
    mfr_products_max = mfr_fuel_can_react + mfr_oxidizer_can_react
    etta_mfr_products = mfr_products / mfr_products_max
    # 1 - доля окислителя, которая могла прореагировать, но не прореагировала
    etta_mfr_oxidizer = 1 - (mfr_oxidizer - mfr_oxidizer_left) / mfr_oxidizer_can_react
    # 1 - доля топлива, которая могла прореагировать, но не прореагировала
    etta_mfr_fuel = 1 - (mfr_fuel - mfr_fuel_left) / mfr_fuel_can_react

    # РАСЧЕТ ПО МАССОВЫМ ДОЛЯМ
    Y_products_max = mfr_products_max / (mfr_fuel_can_react + mfr_oxidizer_can_react + mfr_fuel_left + mfr_oxidizer_left)
    etta_Y_products = Y_products / Y_products_max

    Y_oxidizer_can_react = mfr_oxidizer_can_react / (mfr_fuel_can_react + mfr_oxidizer_can_react + mfr_fuel_left + mfr_oxidizer_left)
    Y_oxidizer_left = mfr_oxidizer_left / (mfr_fuel_can_react + mfr_oxidizer_can_react + mfr_fuel_left + mfr_oxidizer_left)
    etta_Y_oxidizer = 1 - (Y_oxidizer - Y_oxidizer_left) / Y_oxidizer_can_react

    Y_fuel_can_react = mfr_fuel_can_react / (mfr_fuel_can_react + mfr_oxidizer_can_react + mfr_fuel_left + mfr_oxidizer_left)
    Y_fuel_left = mfr_fuel_left / (mfr_fuel_can_react + mfr_oxidizer_can_react + mfr_fuel_left + mfr_oxidizer_left)
    etta_Y_fuel = 1 - (Y_fuel - Y_fuel_left) / Y_fuel_can_react
    # print(f'Вычисление полноты сгорания: K0 = {mass_stoichiometric_ratio}, альфа = {alpha}, ')
    return alpha, etta_mfr_products, etta_mfr_oxidizer, etta_mfr_fuel, etta_Y_products, etta_Y_oxidizer, etta_Y_fuel



if verify_FLUENT and verify_gas:
    df_fluent_gas_01 = df_fluent_gas_01.rename(columns={
        'RhoVx': 'mfr',
        'RhoVx_gpg': 'mfr_gpg',
        'RhoVx_cp': 'mfr_cp',
        'RhoVx_air': 'mfr_air',
    })

    df_fluent_gas_01['etta_mfr_products'] = np.nan
    df_fluent_gas_01['etta_mfr_oxidizer'] = np.nan
    df_fluent_gas_01['etta_mfr_fuel'] = np.nan
    df_fluent_gas_01['etta_Y_products'] = np.nan
    df_fluent_gas_01['etta_Y_oxidizer'] = np.nan
    df_fluent_gas_01['etta_Y_fuel'] = np.nan

    mfr_fuel_in = mfr_fuel_particles_in + mfr_fuel_gas_in

    for idx, row in df_fluent_gas_01.iterrows():
        mfr_products = row['mfr_cp']
        mfr_fuel = row['mfr_gpg']
        mfr_oxidizer = row['mfr_air']
        Y_products = row['Y_cp']
        Y_oxidizer = row['Y_air']
        Y_fuel = row['Y_gpg']

        alpha, etta_mfr_products, etta_mfr_oxidizer, etta_mfr_fuel, etta_Y_products, etta_Y_oxidizer, etta_Y_fuel = combustion_efficiency(
                    mass_stoichiometric_ratio,
                    mfr_fuel_in, mfr_oxidizer_in,
                    mfr_products, mfr_oxidizer, mfr_fuel,
                    Y_products, Y_oxidizer, Y_fuel
                )

        df_fluent_gas_01.at[idx, 'alpha'] = alpha
        df_fluent_gas_01.at[idx, 'etta_mfr_products'] = etta_mfr_products
        df_fluent_gas_01.at[idx, 'etta_mfr_oxidizer'] = etta_mfr_oxidizer
        df_fluent_gas_01.at[idx, 'etta_mfr_fuel'] = etta_mfr_fuel
        df_fluent_gas_01.at[idx, 'etta_Y_products'] = etta_Y_products
        df_fluent_gas_01.at[idx, 'etta_Y_oxidizer'] = etta_Y_oxidizer
        df_fluent_gas_01.at[idx, 'etta_Y_fuel'] = etta_Y_fuel


if verify_QUBIQ and verify_gas:
    df_qubiq_gas_01 = df_qubiq_gas_01.rename(columns={
        'RhoVx': 'mfr',
        'RhoVx_GPG': 'mfr_gpg',
        'RhoVx_CP': 'mfr_cp',
        'RhoVx_Air': 'mfr_air',
        'Y_GPG': 'Y_gpg',
        'Y_CP': 'Y_cp',
        'Y_Air': 'Y_air',
    })

    df_qubiq_gas_01['etta_mfr_products'] = np.nan
    df_qubiq_gas_01['etta_mfr_oxidizer'] = np.nan
    df_qubiq_gas_01['etta_mfr_fuel'] = np.nan
    df_qubiq_gas_01['etta_Y_products'] = np.nan
    df_qubiq_gas_01['etta_Y_oxidizer'] = np.nan
    df_qubiq_gas_01['etta_Y_fuel'] = np.nan

    mfr_fuel_in = mfr_fuel_particles_in + mfr_fuel_gas_in

    for idx, row in df_qubiq_gas_01.iterrows():
        mfr_products = row['mfr_cp']
        mfr_fuel = row['mfr_gpg']
        mfr_oxidizer = row['mfr_air']
        Y_products = row['Y_cp']
        Y_oxidizer = row['Y_air']
        Y_fuel = row['Y_gpg']

        alpha, etta_mfr_products, etta_mfr_oxidizer, etta_mfr_fuel, etta_Y_products, etta_Y_oxidizer, etta_Y_fuel = combustion_efficiency(
                    mass_stoichiometric_ratio,
                    mfr_fuel_in, mfr_oxidizer_in,
                    mfr_products, mfr_oxidizer, mfr_fuel,
                    Y_products, Y_oxidizer, Y_fuel
                )

        df_qubiq_gas_01.at[idx, 'alpha'] = alpha
        df_qubiq_gas_01.at[idx, 'etta_mfr_products'] = etta_mfr_products
        df_qubiq_gas_01.at[idx, 'etta_mfr_oxidizer'] = etta_mfr_oxidizer
        df_qubiq_gas_01.at[idx, 'etta_mfr_fuel'] = etta_mfr_fuel
        df_qubiq_gas_01.at[idx, 'etta_Y_products'] = etta_Y_products
        df_qubiq_gas_01.at[idx, 'etta_Y_oxidizer'] = etta_Y_oxidizer
        df_qubiq_gas_01.at[idx, 'etta_Y_fuel'] = etta_Y_fuel




x_t_label = r'$X,\ м$'

# x_t_label = r'$\tau,\ с$'
y_Cp_label = r'$Cp\ (\frac{Дж}{кг \cdot К})$'
y_H_label = r'$H\ (\frac{Дж}{кг})$'


# plot_result(['p_density'], ['-'], [r'$плотность частицы\ \left[\frac{кг}{м^3}\right]$'], r'$\rho\ \left(\frac{кг}{м^3}\right)$', '04_p_density')



# colors = plt.cm.tab10.colors[:len(section_names)]
colors = plt.cm.tab10.colors[:10]

# plot_result('01_ptot', x_label, r'$p*,\ Па$', (data, section_names, styles, section_names_for_plot, y_limits, colors), GOST=GOST, x_limits=x_limits, swap_axes=False)

y_limits_default = None

pic_base_name = ''




# ЧАСТИЦЫ
if verify_QUBIQ and verify_FLUENT:
    plot_result(f"{pic_base_name}particle_diameter", x_t_label, r'$d,\ мкм$', (df_qubiq_particles_01, ['Diameter'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['particle_diameter'], colors),
                                                                              (df_fluent_particles_01, ['Diameter'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width)
    plot_result(f"{pic_base_name}particle_temperature", x_t_label, r'$T,\ K$', (df_qubiq_particles_01, ['Temperature'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits_default, colors),
                                                                               (df_fluent_particles_01, ['Temperature'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width)
    plot_result(f"{pic_base_name}particle_mass_flow_rate", x_t_label, r'$\dot{m},\ кг/с$', (df_fluent_particles_01, ['Mass_Flow_Rate'], [style_F], ['ПК «ANSYS Fluent»'], y_limits['particle_mass_flow_rate'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[mfr_fuel_particles_in])
    plot_result(f"{pic_base_name}particle_diameter_mave", x_t_label, r'$d,\ мкм$', (df_fluent_particles_01, ['Diameter_mave'], [style_F], ['ПК «ANSYS Fluent»'], y_limits['particle_diameter'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width)
    plot_result(f"{pic_base_name}particle_mass", x_t_label, r'$m,\ кг$', (df_fluent_particles_01, ['Mass'], [style_F], ['ПК «ANSYS Fluent»'], y_limits['particle_mass'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width)
    plot_result(f"{pic_base_name}particle_mass_mave", x_t_label, r'$m,\ кг$', (df_fluent_particles_01, ['Mass_mave'], [style_F], ['ПК «ANSYS Fluent»'], y_limits['particle_mass'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width)
    plot_result(f"{pic_base_name}particle_combustion_efficiency", x_t_label, r'$\eta$', (df_fluent_particles_01, ['Combustion_Efficiency'], [style_F], ['ПК «ANSYS Fluent»'], y_limits['combustion_efficiency'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[1])

# ГАЗ
if verify_gas:
    plot_result(f"{pic_base_name}gas_temperature", x_t_label, r'$T,\ K$', (df_qubiq_gas_01, ['Temperature'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['gas_temperature'], colors),
                                                                          (df_fluent_gas_01, ['Temperature'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width)
    plot_result(f"{pic_base_name}gas_pressure", x_t_label, r'$p,\ Па$', (df_qubiq_gas_01, ['Pressure'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['gas_pressure'], colors),
                                                                        (df_fluent_gas_01, ['Pressure'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width)
    plot_result(f"{pic_base_name}gas_velocity", x_t_label, r'$\upsilon,\ м/с$', (df_qubiq_gas_01, ['Velocity'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['gas_velocity'], colors),
                                                                                (df_fluent_gas_01, ['Velocity'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width)
    plot_result(f"{pic_base_name}gas_Y", x_t_label, r'$Y$', (df_qubiq_gas_01, ['Y_air', 'Y_cp', 'Y_gpg'], [style_Q, style_Q, style_Q], ['СПК «ГиперКуб-ГРАФ» - массовая доля воздуха', 'СПК «ГиперКуб-ГРАФ» - массовая доля ПС', 'СПК «ГиперКуб-ГРАФ» - массовая доля ГПГ'], y_limits['gas_Y_air'], colors),
                                                            (df_fluent_gas_01, ['Y_air', 'Y_cp', 'Y_gpg'], [style_F, style_F, style_F], ['ПК «ANSYS Fluent» - массовая доля воздуха', 'ПК «ANSYS Fluent» - массовая доля ПС', 'ПК «ANSYS Fluent» - массовая доля ГПГ'], y_limits_default, colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width),
    plot_result(f"{pic_base_name}gas_Y2", x_t_label, r'$Y$', (df_qubiq_gas_01, ['Y_air', 'Y_cp'], [style_Q, style_Q], ['СПК «ГиперКуб-ГРАФ» - массовая доля воздуха', 'СПК «ГиперКуб-ГРАФ» - массовая доля ПС'], y_limits['gas_Y_air'], colors),
                                                             (df_fluent_gas_01, ['Y_air', 'Y_cp'], [style_F, style_F], ['ПК «ANSYS Fluent» - массовая доля воздуха', 'ПК «ANSYS Fluent» - массовая доля ПС'], y_limits_default, colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width),
    plot_result(f"{pic_base_name}gas_Y3", x_t_label, r'$Y$', (df_qubiq_gas_01, ['Y_gpg'], [style_Q], ['СПК «ГиперКуб-ГРАФ» - массовая доля ГПГ'], y_limits['gas_Y_gpg'], colors),
                                                             (df_fluent_gas_01, ['Y_gpg'], [style_F], ['ПК «ANSYS Fluent» - массовая доля ГПГ'], y_limits_default, colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width),

    # FLUENT
    plot_result(f"{pic_base_name}gas_mfr_FLUENT", x_t_label, r'$\dot{m},\ кг/с$', (df_fluent_gas_01, ['mfr', 'mfr_gpg', 'mfr_cp', 'mfr_air'], [style_F]*4, ['ПК «ANSYS Fluent» - расход', 'ПК «ANSYS Fluent» - расход ГПГ', 'ПК «ANSYS Fluent» - расход ПС', 'ПК «ANSYS Fluent» - расход воздуха'], y_limits['gas_mass_flow_rate'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[mfr_all, mfr_gas])

    plot_result(f"{pic_base_name}gas_etta_FLUENT_01", x_t_label, r'$\eta$', (df_fluent_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer', 'etta_mfr_fuel', 'etta_Y_products', 'etta_Y_oxidizer', 'etta_Y_fuel'], [style_F]*6, ['ПК «ANSYS Fluent» - полнота по расходу продуктов', 'ПК «ANSYS Fluent» - полнота по расходу окислителя', 'ПК «ANSYS Fluent» - полнота по расходу топлива', 'ПК «ANSYS Fluent» - полнота по массовой доле продуктов', 'ПК «ANSYS Fluent» - полнота по массовой доле окислителя', 'ПК «ANSYS Fluent» - полнота по массовой доле топлива'], y_limits['combustion_efficiency'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[1])

    plot_result(f"{pic_base_name}gas_etta_FLUENT_02", x_t_label, r'$\eta$', (df_fluent_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer', 'etta_Y_products', 'etta_Y_oxidizer'], [style_F]*4, ['ПК «ANSYS Fluent» - полнота по расходу продуктов', 'ПК «ANSYS Fluent» - полнота по расходу окислителя', 'ПК «ANSYS Fluent» - полнота по массовой доле продуктов', 'ПК «ANSYS Fluent» - полнота по массовой доле окислителя'], y_limits['combustion_efficiency'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[1])

    # QUBIQ
    plot_result(f"{pic_base_name}gas_mfr_QUBIQ", x_t_label, r'$\dot{m},\ кг/с$', (df_qubiq_gas_01, ['mfr', 'mfr_gpg', 'mfr_cp', 'mfr_air'], [style_Q]*4, ['СПК «ГиперКуб-ГРАФ» - расход', 'СПК «ГиперКуб-ГРАФ» - расход ГПГ', 'СПК «ГиперКуб-ГРАФ» - расход ПС', 'СПК «ГиперКуб-ГРАФ» - расход воздуха'], y_limits['gas_mass_flow_rate'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[mfr_all, mfr_gas])

    plot_result(f"{pic_base_name}gas_etta_QUBIQ_01", x_t_label, r'$\eta$', (df_qubiq_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer', 'etta_mfr_fuel', 'etta_Y_products', 'etta_Y_oxidizer', 'etta_Y_fuel'], [style_Q]*6, ['СПК «ГиперКуб-ГРАФ» - полнота по расходу продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по расходу окислителя', 'СПК «ГиперКуб-ГРАФ» - полнота по расходу топлива', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле окислителя', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле топлива'], y_limits['combustion_efficiency'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[1])

    plot_result(f"{pic_base_name}gas_etta_QUBIQ_02", x_t_label, r'$\eta$', (df_qubiq_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer', 'etta_Y_products', 'etta_Y_oxidizer'], [style_Q]*4, ['СПК «ГиперКуб-ГРАФ» - полнота по расходу продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по расходу окислителя', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле окислителя'], y_limits['combustion_efficiency'], colors), GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[1])

    # СОВМЕСТНЫЕ
    plot_result(f"{pic_base_name}gas_mfr", x_t_label, r'$\dot{m},\ кг/с$',
                (df_qubiq_gas_01, ['mfr', 'mfr_gpg', 'mfr_cp', 'mfr_air'], [style_Q] * 4, ['СПК «ГиперКуб-ГРАФ» - расход', 'СПК «ГиперКуб-ГРАФ» - расход ГПГ', 'СПК «ГиперКуб-ГРАФ» - расход ПС', 'СПК «ГиперКуб-ГРАФ» - расход воздуха'], y_limits['gas_mass_flow_rate'], colors),
                (df_fluent_gas_01, ['mfr', 'mfr_gpg', 'mfr_cp', 'mfr_air'], [style_F]*4, ['ПК «ANSYS Fluent» - расход', 'ПК «ANSYS Fluent» - расход ГПГ', 'ПК «ANSYS Fluent» - расход ПС', 'ПК «ANSYS Fluent» - расход воздуха'], y_limits_default, colors),
                GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[mfr_all, mfr_gas])

    plot_result(f"{pic_base_name}gas_etta_01", x_t_label, r'$\eta$',
                (df_qubiq_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer', 'etta_mfr_fuel', 'etta_Y_products', 'etta_Y_oxidizer', 'etta_Y_fuel'], [style_Q]*6, ['СПК «ГиперКуб-ГРАФ» - полнота по расходу продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по расходу окислителя', 'СПК «ГиперКуб-ГРАФ» - полнота по расходу топлива', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле окислителя', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле топлива'], y_limits['combustion_efficiency'], colors),
                (df_fluent_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer', 'etta_mfr_fuel', 'etta_Y_products', 'etta_Y_oxidizer', 'etta_Y_fuel'], [style_F] * 6,
                 ['ПК «ANSYS Fluent» - полнота по расходу продуктов', 'ПК «ANSYS Fluent» - полнота по расходу окислителя', 'ПК «ANSYS Fluent» - полнота по расходу топлива', 'ПК «ANSYS Fluent» - полнота по массовой доле продуктов', 'ПК «ANSYS Fluent» - полнота по массовой доле окислителя', 'ПК «ANSYS Fluent» - полнота по массовой доле топлива'], y_limits_default, colors),
                GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[1])

    plot_result(f"{pic_base_name}gas_etta_02", x_t_label, r'$\eta$',
                (df_qubiq_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer', 'etta_Y_products', 'etta_Y_oxidizer'], [style_Q] * 4, ['СПК «ГиперКуб-ГРАФ» - полнота по расходу продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по расходу окислителя', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле окислителя'], y_limits['combustion_efficiency'], colors),
                (df_fluent_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer', 'etta_Y_products', 'etta_Y_oxidizer'], [style_F] * 4, ['ПК «ANSYS Fluent» - полнота по расходу продуктов', 'ПК «ANSYS Fluent» - полнота по расходу окислителя', 'ПК «ANSYS Fluent» - полнота по массовой доле продуктов', 'ПК «ANSYS Fluent» - полнота по массовой доле окислителя'], y_limits_default, colors),
                GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[1])

    plot_result(f"{pic_base_name}gas_etta_MFR", x_t_label, r'$\eta$',
                (df_qubiq_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer'], [style_Q] * 2, ['СПК «ГиперКуб-ГРАФ» - полнота по расходу продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по расходу окислителя'], y_limits['combustion_efficiency'], colors),
                (df_fluent_gas_01, ['etta_mfr_products', 'etta_mfr_oxidizer'], [style_F] * 2, ['ПК «ANSYS Fluent» - полнота по расходу продуктов', 'ПК «ANSYS Fluent» - полнота по расходу окислителя'], y_limits_default, colors),
                GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[1])

    plot_result(f"{pic_base_name}gas_etta_Y", x_t_label, r'$\eta$',
                (df_qubiq_gas_01, ['etta_Y_products', 'etta_Y_oxidizer'], [style_Q] * 2, ['СПК «ГиперКуб-ГРАФ» - полнота по массовой доле продуктов', 'СПК «ГиперКуб-ГРАФ» - полнота по массовой доле окислителя'], y_limits['combustion_efficiency'], colors),
                (df_fluent_gas_01, ['etta_Y_products', 'etta_Y_oxidizer'], [style_F] * 2, ['ПК «ANSYS Fluent» - полнота по массовой доле продуктов', 'ПК «ANSYS Fluent» - полнота по массовой доле окислителя'], y_limits_default, colors),
                GOST=GOST, x_limits=(x_limit_low, x_limit_high), swap_axes=False, line_width=line_width, horizontal_lines=[1])








    # plot_result(f"{pic_base_name}_turbulent_kinetic_energy", x_t_label, r'$k,\ \frac{\text{м}^2}{\text{с}^2}$', (df_qubiq_gas_01, ['turbulent_kinetic_energy'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['turbulent_kinetic_energy'], colors, [0, 80], [0.4], [0.1], [0.1]),
    #                                                                                                             (df_fluent_gas_01, ['turbulent_kinetic_energy'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors, [0, 80], [0.2], [0.1], [0.1]), GOST=GOST, x_limits=[x_limit_low, x_limit], swap_axes=False)
    # plot_result(f"{pic_base_name}_specific_dissipation_rate", x_t_label, r'$omega,\ \frac{1}{\text{с}}$', (df_qubiq_gas_01, ['specific_dissipation_rate'], [style_Q], ['СПК «ГиперКуб-ГРАФ»'], y_limits['specific_dissipation_rate'], colors, [0, 80], [0.4], [0.1], [0.1]),
    #                                                                                                       (df_fluent_gas_01, ['specific_dissipation_rate'], [style_F], ['ПК «ANSYS Fluent»'], y_limits_default, colors, [0, 80], [0.2], [0.1], [0.1]), GOST=GOST, x_limits=[x_limit_low, x_limit], swap_axes=False)









print('debug')







