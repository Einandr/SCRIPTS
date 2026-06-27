# Для запуска скрипта необходимо установить следующие библиотеки:
# pip install pandas
# pip install numpy


import os

import sqlite3
import pandas as pd

import numpy as np
import math

from typing import List



rel_path = 'db'
os.chdir(os.path.dirname(os.path.abspath(__file__)))
db_p = os.path.join(os.getcwd(), rel_path, 'props_database_v1.2.db')




#region Const
R = 8.314
#endregion


#region Gibbs energy type polynomials

def Gibbs_energy_T(f: List[float]):
    def Gibbs_energy(T: float = 298.15) -> float:
        x = T * 1e-4
        return (f[0] + f[1] * math.log(x) + f[2] * x**-2 + f[3] * x**-1 +
                f[4] * x + f[5] * x**2 + f[6] * x**3)
    return Gibbs_energy # [G] = Дж/(моль.К)


def entropy_T(f: List[float]):
    def entropy(T: float = 298.15) -> float:
        x = T * 1e-4
        return (f[0] + f[1] + f[1] * math.log(x) - f[2] * x**-2 + 2 * f[4] * x +
                3 * f[5] * x**2 + 4 * f[6] * x**3)
    return entropy # [S] = Дж/(моль.К)


def enthalpy_T(f: List[float]):
    def enthalpy(T: float = 298.15) -> float:
        x = T * 1e-4
        return (f[1] * x - 2 * f[2] * x**-1 - f[3] + f[4] * x**2 +
                2 * f[5] * x**3 + 3 * f[6] * x**4) * 1e4
    return enthalpy # [H] = Дж/(моль)


def heat_capacity_T(f: List[float]):
    def heat_capacity(T: float = 298.15) -> float:
        x = T * 1e-4
        return (f[1] + 2 * f[2] * x**-2 + 2 * f[4] * x + 6 * f[5] * x**2 +
                12 * f[6] * x**3)
    return heat_capacity # [Cp] = Дж/(моль.К)


def viscosity_T(M: float = 1.0, sigma: float = 4.0, e_k: float = 100.0):
    def viscosity(T: float = 300.0) -> float:
        Tp = T / e_k
        # theta = 1.14 * (1 / Tp**0.145 + 1 / (Tp + 0.5)**2)
        theta = 1.16145 / Tp**0.14874 + 0.52487 / math.exp(0.7732 * Tp) + 2.16178 / math.exp(2.43787 * Tp)
        # В ANSYS Fluent (и в других реализациях кинетической теории) обычно аппроксимируют по формуле Bird, Stewart & Lightfoot (Transport Phenomena)
        return 0.26693e-5 * (M * T)**0.5 / (sigma**2 * theta)
    return viscosity # [M] = г/моль, [Cp] = Дж/(моль.К) -> [Mu] = Па.с


def thermal_conductivity_T(M: float = 1.0):
    def thermal_conductivity(mu: float = 1.0e-6, cp: float = 1000) -> float:
        R = 8.314
        # L = ((15 / 4) * (R / (M * 1e-3)) * mu * 
                # ((4 / 15) * (cp * M * 1e-3 / R) + 1 / 3)) # не совпадает с Ansys
        L = mu * (cp + 5 / 4 * R) / (M * 1e-3) # формула Эйкена
        return L
    return thermal_conductivity # [M] = г/моль, [Cp] = Дж/(моль.К) -> [L] = Вт/(м.К)

#endregion

# -----------------

#region NASA7 type polynomials
def NASA_heat_capacity_T(f: List[float]):
    def NASA_heat_capacity(T: float = 298.15) -> float:
        R = 8.314
        return (f[0] + f[1] * T + f[2] * T**2 + f[3] * T**3 +
                f[4] * T**4) * R
    return NASA_heat_capacity # [Cp] = Дж/(моль.К)


def NASA_entropy_T(f: List[float]):
    def NASA_entropy(T: float = 298.15) -> float:
        R = 8.314
        return (f[0] * math.log(T) + f[1] * T + f[2] * T**2 / 2 + f[3] * T**3 / 3 +
                f[4] * T**4 / 4 + f[5]) * R
    return NASA_entropy # [S] = Дж/(моль.К)


def NASA_enthalpy_T(f: List[float]):
    def NASA_enthalpy(T: float = 298.15) -> float:
        R = 8.314
        return (f[0] + f[1] * T / 2 + f[2] * T**2 / 3 + f[3] * T**3 / 4 +
                f[4] * T**4 / 5 + f[5] / T) * T * R
    return NASA_enthalpy # [H] = Дж/(моль)

#endregion

# -----------------

#region Material by index

def material_by_index(m_i: str = '1'):
    with sqlite3.connect(db_p) as conn:

        df_1 = pd.read_sql('''
                SELECT Formula, Molar_mass, Sigma, Epsilon_k, Enthalpy, Source, Material_name FROM Materials
                    WHERE Material_index_key = ''' + m_i + '''
                   ''', conn)

        df_2 = pd.read_sql('''
                SELECT Tmin, Tmax, f1, f2, f3, f4, f5, f6, f7, Type_of_polynomial FROM Polynomials
                    WHERE Material_index_key = ''' + m_i + '''
                   ''', conn)

    return(df_1, df_2)

#endregion

# print(material_by_index(m_i='0'))

#region Yaml file entry

def yaml_file_entry(T: List[float], M_m: float, Cp: List[float], Mu: List[float], L: List[float],
                    H0: float=0.0, D: float=2.88e-05, material: str='material',
                    s: float=0.0, eps: float=0.0, db: str='user_defined'):

    with open(f'{material}.yaml', 'w', encoding='utf-8') as f:
        f.write(f'''# --INFO--\n# material: {material}\n# database: {db}\n# L-J Characteristic Length [Angstrom]: {s}\n# L-J Energy Parameter [K]: {eps}\n\n\n''')
        f.write('# Heat of formation, J/kg\n' + \
                'formation_heat:\n  ' + '298.15' + ': ' + "{:.2f}".format(H0 / M_m) + '\n'*2)
        f.write('# Molar mass, kg/mol\n' + \
                'molar_mass: ' + "{:.6f}".format(M_m) + '\n'*2)
        f.write('# Gas constant, J/(kg.K)\n' + \
                '# gas_constant: ' + "{:.3f}".format(R / M_m) + '\n'*2)
        f.write('# Mass diffusivity (temp value), m2/s, as function of temperature, K\n' + \
                'mass_diffusivity: ' + str(D) + '\n'*2)
        f.write('# Heat conductivity, W/(m.K), as function of temperature, K\n' + 'heat_conductivity:'+ '\n')
        for i in range(0, L.size):
            f.write('  ' + str(T[i]) + ': ' + "{:.5e}".format(L[i]) + '\n')   
        f.write('\n'*2)   
        f.write('# Viscosity, Pa.s, as function of temperature, K\n' + 'viscosity:'+ '\n')
        for i in range(0, Mu.size):
            f.write('  ' + str(T[i]) + ': ' + "{:.5e}".format(Mu[i]) + '\n')  
        f.write('\n'*2)
        f.write('# Heat capacity, J/(kg.K), as function of temperature, K\n' + 'heat_capacity:'+ '\n')
        for i in range(0, Cp.size):
            f.write('  ' + str(T[i]) + ': ' + "{:.5e}".format(Cp[i] / M_m) + '\n')   
        f.write('\n'*2) 
        # print('\n'*2)
        print('-'*100)
        print(f"The YAML file is saved under the name: {material}.yaml\nin the working directory: {os.getcwd()}\nTerminating...")
        




with sqlite3.connect(db_p) as conn:
    conn.execute("PRAGMA foreign_keys = ON")

    df1 = pd.read_sql("SELECT * FROM Materials", conn)
    df2 = pd.read_sql("SELECT * FROM Polynomials", conn)
    df3 = pd.read_sql("SELECT * FROM Info", conn)


print('*'*100)

source_mapping = dict(zip(df3['Info_index'], df3['Source']))
df1['Source'] = df1['Source'].map(source_mapping)


# print('-'*100)
# print(df3)
# print('-'*100)


print('\n' + '-'*100)

text_input_1 = '''Write the formula (f) or name (n) of the material.\nTo terminate the program, enter "q!".
Example input:\nO2 f\nair n\n
To display all materials, enter "all". (The data will be written to the file "All_materials.txt")
Your input: '''

in_temp = input(text_input_1).split()
if in_temp[0].lower() == 'q!':
    print("Terminating...")
    exit()
if in_temp[0].lower() == 'all':
   in_temp[0] = ''
   with open('All_materials.txt', 'w', encoding='utf-8') as f:
    f.write(
        df1[df1['Formula'].str.upper().str.contains(in_temp[0].upper(), na=False)]
        .iloc[:, [0, 1, 15, 16, 19, 20, 21]]
        .to_string(index=False)
    )
    print(f"The file is saved under the name: All_materials.txt\nin the working directory: {os.getcwd()}\nTerminating...")
    exit()

if in_temp[-1].lower() == 'f':
    print('-'*100 + '\nPartial match: \n' + '-'*100)
    print(df1[df1['Formula'].str.upper().str.contains(in_temp[0].upper(), na=False)].iloc[:, [0, 1, 15, 16, 19, 20, 21]].to_string(index=False))
    print('-'*100 + '\nExact match: \n' + '-'*100)
    print(df1[df1['Formula'].str.upper() == in_temp[0].upper()].iloc[:, [0, 1, 15, 16, 19, 20, 21]].to_string(index=False))
    print('-'*100)
elif in_temp[-1].lower() == 'n':
    print('-'*100 + '\nPartial match: \n' + '-'*100 )
    print(df1[df1['Material_name'].str.lower().str.contains(in_temp[0].lower(), na=False)].iloc[:, [0, 1, 15, 16, 19, 20, 21]].to_string(index=False))
    print('-'*100 + '\nExact match: \n' + '-'*100)
    print(df1[df1['Material_name'].str.lower() == in_temp[0].lower()].iloc[:, [0, 1, 15, 16, 19, 20, 21]].to_string(index=False))
    print('-'*100)
else:
    print("Incorrect input\nTerminating...")
    exit()



mik = input('Enter index material or "q!" to terminate the program.\nYour input: ')
if mik.lower() == 'q!':
    print("Terminating...")
    exit()

print('-'*100)


#region Calc-par

df_1, df_2 = material_by_index(mik)
material_f_n = df_1.loc[:,'Formula'].values[0]  if  df_1.loc[:,'Formula'].values[0].lower() != 'n_f' else df_1.loc[:,'Material_name'].values[0]


df_3 = pd.DataFrame(columns=['T', 'Cp', 'S', 'H', 'H0', 'G*', 'Mu', 'L'])

data_temp = []

prop = df_1.iloc[0, 1:4]
H0 = float(df_1.iloc[0, 4:5].values[0])

step = 100

if df_2.iloc[:, 9].values[0] == 1:

    for i in range(0, len(df_2)):
        pol_coef_GE = df_2.iloc[i, 2:9].values.tolist()



        Cp_T = heat_capacity_T(pol_coef_GE)
        S_T = entropy_T(pol_coef_GE)
        H_T = enthalpy_T(pol_coef_GE)
        GE_T = Gibbs_energy_T(pol_coef_GE)

        if (prop.iloc[1] != 0 and not np.isnan(prop.iloc[1])) and ((prop.iloc[2] != 0) and pd.notna(prop.iloc[2])):
            Mu_T = viscosity_T(*prop)
            L_T = thermal_conductivity_T(prop.iloc[0])
            k = True
        else:
            k = False

        if i == 0:
            H0_yaml = H0 + H_T(298.15)

        Tmin = round(df_2.iloc[i, 0], -1) if i == 0 else round(df_2.iloc[i, 0], -1) + step
        Tmax = round(df_2.iloc[i, 1], -1)

        T_list = np.linspace(Tmin, Tmax, int((Tmax - Tmin) // step + 1))

        for T in T_list:
            data_temp.append([
                T,
                Cp_T(T),
                S_T(T),
                (H_T(T)) / 1000,
                (H0 + H_T(T)) / 1000,
                GE_T(T),
                Mu_T(T) if k else 1.72e-05,
                L_T(Mu_T(T), Cp_T(T)) if k else 0.0454
            ])


elif df_2.iloc[:, 9].values[0] == 2:


    for i in range(0, len(df_2)):
        pol_coef_GE = df_2.iloc[i, 2:9].values.tolist()


        Cp_T = NASA_heat_capacity_T(pol_coef_GE[:5])
        S_T = NASA_entropy_T(pol_coef_GE[:5] + pol_coef_GE[6:7])
        H_T = NASA_enthalpy_T(pol_coef_GE[:6])

        if (prop.iloc[1] != 0 and not np.isnan(prop.iloc[1])) and ((prop.iloc[2] != 0) and pd.notna(prop.iloc[2])):
            Mu_T = viscosity_T(*prop)
            L_T = thermal_conductivity_T(prop.iloc[0])
            k = True
        else:
            k = False

        if i == 0:
            H0_yaml = H_T(298.15)

        Tmin = round(df_2.iloc[i, 0], -1) if i == 0 else round(df_2.iloc[i, 0], -1) + step
        Tmax = round(df_2.iloc[i, 1], -1)

        T_list = np.linspace(Tmin, Tmax, int((Tmax - Tmin) // step + 1))

        for T in T_list:
            data_temp.append([
                T,
                Cp_T(T),
                S_T(T),
                (H_T(T) - pol_coef_GE[5] * R) / 1000,
                H_T(T) / 1000,
                S_T(T) - (H_T(T) - pol_coef_GE[5] * R) / T,
                Mu_T(T) if k else 1.72e-05,
                L_T(Mu_T(T), Cp_T(T)) if k else 0.0454
            ])


df_3 = pd.DataFrame(data_temp, columns=df_3.columns)

#endregion

df_temp = df_3
df_temp.columns = ['T, K', 'Cp, J/(mol.K)', 'S, J/(mol.K)', 
                   'H, kJ/mol', 'H0, kJ/mol', 'G*, J/(mol.K)', 
                   'Mu, Pa.s', 'L, W/(m.K)']

print(df_3.iloc[:13, :8])

print()

#region file recording

yaml_file_entry(T=df_3.iloc[:, 0].values, 
                M_m=prop.iloc[0] / 1000, 
                Cp=df_3.iloc[:, 1].values, 
                Mu=df_3.iloc[:, 6].values, 
                L=df_3.iloc[:, 7].values,
                H0=H0_yaml, material=material_f_n,
                s=prop.iloc[1], eps=prop.iloc[2],
                db=df3[df3['Info_index'] == df_1.iloc[:, 5].values[0]].iloc[0, 1])

#endregion

