import yaml
import os
import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from pathlib import Path
from decimal import Decimal, InvalidOperation


path_in = r'D:\YASIM\VORON\!Materials'
file_props_excel = 'керосин_Т1.xlsx'
out_FLUENT = True
out_QUBIQ = False
name = 'kerosene-liquid'
liquid = True
calculate_diffusion = True

file_out_QUBIQ = 'props.yaml'
file_out_FLUENT = 'props.jou'

dir_out = 'RUN'
path_out = ''.join((path_in, '/', dir_out))
Path(path_out).mkdir(parents=True, exist_ok=True)
os.chdir(path_out)

T_header = 'T [K]'

# н-Гептан
# g_M_vapor = 100.203                 # молярная масса пара [кг/моль]
# g_M = 28.288239                     # молярная масса газа (воздух) [кг/моль]
# g_etta_vapor = 147.18               # молекулярный диффузионный объем пара [см^3/моль]
# g_etta = 20.1                       # молекулярный диффузионный объем газа (воздух) [см^3/моль]

# керосин Т-1
g_M_vapor = 136.6102                # молярная масса пара [кг/моль]
g_M = 28.288239                     # молярная масса газа (воздух) [кг/моль]
g_etta_vapor = 192.22               # молекулярный диффузионный объем пара [см^3/моль]
g_etta = 20.1                       # молекулярный диффузионный объем газа (воздух) [см^3/моль]

g_p_reference = 500000              # референсное давление [Па]




def diffusion_coefficient(temperature, pressure, vapor_molar_mass, gas_molar_mass, vapor_etta, gas_etta):
    """
    Рассчитывает коэффициент диффузии в [м^2/с]
    Args:
        temperature: температура газа в референсной точке [К].
        pressure: давление газа [Па]
        vapor_molar_mass: молярная масса пара [кг/моль] или [г/моль]
        gas_molar_mass: молярная масса газа (воздух) [кг/моль] или [г/моль]
        vapor_etta: молекулярный диффузионный объем пара [см^3/моль]
        gas_etta: молекулярный диффузионный объем газа (воздух) [см^3/моль]
    """
    return 0.01 * pow(temperature, 1.75) / pressure * pow((vapor_molar_mass + gas_molar_mass) / (vapor_molar_mass * gas_molar_mass), 1 / 2) / pow((pow(vapor_etta, 1 / 3) + pow(gas_etta, 1 / 3)), 2)



T_start = 200
T_end = 3000
T_delta = 200

props_headers = {
    'Cp_liq': 'Cp [Дж/кг-К]',
    'ro_liq': 'ro [кг/м.куб]',
    'p_sat': 'P [Pa]',
}

props_yaml = {
    'heat_capacity_liquid': 'Cp_liq',
    'density': 'ro_liq',
    'saturation_vapor_pressure': 'p_sat',
}

fluent_journal_str_comments = {
    'Cp_liq': 'Cp',
    'ro_liq': 'Density',
    'p_sat': 'Saturation vapor pressure',
}

fluent_journal_quants = {
    'Cp_liq': '0.1',
    'ro_liq': '0.1',
    'p_sat': '0.1',
}

fluent_journal_str_start = {
    'ro_liq': ''.join(('/define/materials/change-create ', name, ' ', name, ' y piecewise-linear ')),
    'Cp_liq': ''.join(('/define/materials/change-create ', name, ' ', name, ' n y piecewise-linear ')),
    'p_sat': ''.join(('/define/materials/change-create ', name, ' ', name, ' n n n n n n n n y piecewise-linear ')),
}

fluent_journal_str_end = {
    'ro_liq': ' n n n n n n n n n n n n n\n',
    'Cp_liq': ' n n n n n n n n n n n n\n',
    'p_sat': ' n n n n n\n',
}




diffusion_key = 'D'
diffusion_column_name = 'D [m^2/s]'
props = props_headers.copy()




for key, value in props_headers.items():
    df = pd.read_excel(''.join((path_in, '/', file_props_excel)), sheet_name=key, usecols=[T_header, value], index_col=T_header)
    props[key] = df
    test = df.to_dict(orient='series')
    df.plot(y=value, use_index=True, style='o-', grid=True, label=value)
    plt.savefig(''.join(('prop_transfered_', key, '.jpeg')), dpi=400, bbox_inches='tight')

    if out_QUBIQ:
        for key in props_yaml:
            props_yaml[key] = list(props[props_yaml[key]].to_dict(orient='dict').values())[0]
        with open(file_out_QUBIQ, 'w') as f:
            yaml.dump(file_out_QUBIQ, f)











temperatures = np.arange(T_start, T_end + 1, T_delta)
df = pd.DataFrame(index=temperatures, columns=[diffusion_column_name])
for T in temperatures:
    df.loc[T, diffusion_column_name] = diffusion_coefficient(T, g_p_reference, g_M_vapor, g_M, g_etta_vapor, g_etta)
props_headers[diffusion_key] = diffusion_column_name
props[diffusion_key] = df
fluent_journal_str_comments[diffusion_key] = 'Diffusion'
fluent_journal_quants[diffusion_key] = '.3e'
fluent_journal_str_start[diffusion_key] = ''.join(('/define/materials/change-create ', name, ' ', name, ' n n n n n n y film-averaged 0.3333 piecewise-linear '))
fluent_journal_str_end[diffusion_key] = ''.join((' y constant ', str(g_p_reference), ' n n n n n n\n'))












def get_prop(df, str_start, x, y, str_end, quant):
    print('data from get props: ', df)
    print('y is: ', y)
    print(x, y)
    prop = str_start
    prop_points = ''
    n_points = 0
    for ind in df.index:
        if pd.notna(df.loc[ind, y]):
            n_points += 1
            if y != diffusion_column_name:
                prop_points += f" {ind} {Decimal(str(df.loc[ind, y])).quantize(Decimal(quant))}"
            else:
                prop_points += f" {ind} {format(df.loc[ind, y], quant)}"

    prop += str(n_points)
    prop += prop_points
    prop += str_end
    return prop


def get_prop_from_yaml(df, str_start, str_end, quant):
    print('data from get props: ', df)
    prop = str_start
    prop_points = ''
    n_points = 0
    for ind, item in enumerate(df):
        # print('check index: ', ind, item)
        if df[item] is not None:
            n_points += 1
            prop_points += ''.join((' ', str(item), ' ', str(Decimal(str(df[item])).quantize(Decimal(quant)))))
            # print(prop_points)
    prop += str(n_points)
    prop += prop_points
    prop += str_end
    return prop









if out_FLUENT and liquid:
    with open(''.join(('p_fluent_', name, '.jou')), 'w') as f:
        for key, value in props_headers.items():
            props_journal_string = get_prop(props[key], fluent_journal_str_start[key], T_header, props_headers[key], fluent_journal_str_end[key], fluent_journal_quants[key])
            f.write(''.join((';', fluent_journal_str_comments[key],'\n')))
            f.write(props_journal_string)




print('end')


