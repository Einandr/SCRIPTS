import yaml
import os
import pandas as pd
import math
import numpy as np
import matplotlib.pyplot as plt
from openpyxl import load_workbook


path = r'D:\YASIM\!VORON\!Materials'
file_props_excel = 'Свойства_керосин_Т1.xlsx'
file_yaml_out = 'props.yaml'

T_header = 'T [K]'

props_headers = {
    'Cp_liq': 'Cp [Дж/кг-К]',
    'ro_liq': 'ro [кг/м.куб]',
}

props_yaml_headers = {
    'density': 'ro_liq',
    'heat_capacity_liquid': 'Cp_liq',
}

# props_headers = {
#     'Cp_liq': 'Cp [Дж/кг-К]',
#     'Cp_gas': 'Cp [Дж/кг-К]',
#     'L_lh': 'L_lh [Дж/кг]',
#     'etta_gas_p1': 'nu [Н-с/м.кв.]',
#     'p_sat': 'P [Pa]',
#     'ro_liq': 'ro [кг/м.куб]',
#     'ro_sat_vapor': 'ro_sat_vap [кг/м.куб]',
#     'lam_gas_p1': 'lambda [Вт/м-град]',
#     'sigma': 'sigma [Н/м]'
# }
#
# props_yaml_headers = {
#     'density': 'ro_liq',
#     'density_sat_vapor': 'ro_sat_vapor',
#     'viscosity': 'etta_gas_p1',
#     'heat_capacity_liquid': 'Cp_liq',
#     'heat_capacity_gas': 'Cp_gas',
#     'surface_tension': 'sigma',
#     'latent_heat': 'L_lh',
#     'saturation_vapor_pressure': 'p_sat',
#     'heat_conductivity_gas': 'lam_gas_p1'
# }

os.chdir(path)


props = props_headers
props_yaml = props_yaml_headers

wb = load_workbook(file_props_excel, data_only=True)

for key, value in props_headers.items():
    ws = wb[key]
    df = pd.read_excel(file_props_excel, sheet_name=key, usecols=[T_header, value], index_col=T_header)
    props[key] = df
    test = df.to_dict(orient='series')
    df.plot(y=value, use_index=True, style='o-', grid=True, label=value)
    plt.savefig(''.join(('prop_transfered_', key, '.jpeg')), dpi=400, bbox_inches='tight')

for key in props_yaml:
    props_yaml[key] = list(props[props_yaml[key]].to_dict(orient='dict').values())[0]

with open(file_yaml_out, 'w') as f:
    yaml.dump(props_yaml, f)



print('end')


