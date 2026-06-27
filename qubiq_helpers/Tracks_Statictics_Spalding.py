import pandas as pd
import os
import matplotlib.pyplot as plt
from pathlib import Path

# path = '/sim/r_01_ker_bigmesh_comb'

# path = '/sim/r_01_ker_bigmesh_vap_hotdrops'
# path = '/SIM/06_MPL_one_cell_8mm'
path = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_convective_1particle_10x200_QUBIQ'

# Частота вывода СИЛО и мониторов должна быть одинаковой
post_visit_gas = False
time_end = 0.02                    # for using qubiq monitors
qubiq_gas_dt = 1.928e-6          # not used if using qubiq monitors

dir_out = 'out'
dir_tracks = 'tracks'
dir_qubiq_postproc = r'postproc\monitors'
dir_post = 'post'
dir_post_visit = 'post_visit'


os.chdir(''.join((path, '/', dir_out)))


# regions = ['region0']
# legend = ['d2000']
# legend = ['d200', 'd150', 'd100']
# dfr = []
# for r in regions:
#     data = pd.read_csv(''.join(('tracks_', r, '.csv')))
#     data.sort_values('CoordinateZ', inplace=True)
#     dfr.append(data)

df = pd.read_csv(''.join((path, '/', dir_out, '/', 'tracks_all.txt')), dtype=float)
df['time'] = df['dt'].cumsum()
df.set_index('time', drop=False, inplace=True)

print('total time is:', df['dt'].sum())


plt.rcParams["figure.figsize"] = [15.00, 7]
plt.rcParams["figure.autolayout"] = True

if post_visit_gas:
    os.chdir(''.join((path, '/', dir_post_visit)))
    df_gas = pd.read_csv(''.join((path, '/', dir_post_visit, '/', 'points.txt')), sep=' ')
    # APPROXIMATELY!!! LATER CORRECT
    df_gas['time'] = df_gas['time_step']*qubiq_gas_dt
    # df_gas.set_index('time', drop=False, inplace=True)

    # getting time from monitors:
    # so far monitors doesn't provide first and last time points. So add them artificially
    monitors_headers = ['time', 'temperature', 'pressure', 'density']
    df_gas_monitors = pd.read_csv(''.join((path, '/', dir_out, '/', dir_qubiq_postproc, '/', 'monitor0.dat')), sep='\t', skiprows=1, dtype=float, header=None, names=monitors_headers)
    length_to_set = len(df_gas['time'])
    lenth_available = len(df_gas_monitors['time'].values)
    end_offset = length_to_set - lenth_available - 1

    test1 = len(df_gas['time'][1:].values)
    test2 = len(df_gas_monitors['time'].values)
    print(df_gas.loc[1:lenth_available, 'time'])
    print(df_gas_monitors['time'].values)

    df_gas.loc[1:lenth_available, 'time'] = df_gas_monitors['time'].values
    df_gas.loc[lenth_available+1, 'time'] = time_end
    df_gas.drop(df_gas.tail(end_offset-1).index, inplace=True)
    df_gas.set_index('time', drop=False, inplace=True)


# ax = dfr[0].plot(x='CoordinateZ', y='diameter', grid=True)
# for df in dfr[1:]:
#     df.plot(ax=ax, x='CoordinateZ', y='diameter', grid=True)
# ax.legend(legend)
# ax.set_ylim([0, 0.00021])
# plt.savefig('plot_diam.jpeg')


# ax = dfr[0].plot(x='CoordinateZ', y='temperature', grid=True)
# for df in dfr[1:]:
#     df.plot(ax=ax, x='CoordinateZ', y='temperature', grid=True)
# ax.legend(legend)
# ax.set_ylim([0, 0.00021])

# plt.savefig('plot_temp.jpeg')


def plot_picture(x, y, name):
    ax = df.plot(x=x, y=y, grid=True)
    # ax.legend(legend)
    # ax.set_ylim([0, 0.00021])
    plt.savefig(''.join((name, '.jpeg')))
    plt.close()


x_t_label = r'$время\ (с)$'

def plot_result(df, y, style, label, ylabel, pic_name):
    df.plot(y=y, use_index=True, style=style, grid=True, label=label, xlabel=x_t_label, ylabel=ylabel, xlim=0)
    # if t_complete_volatile_evaporation is not None:
    #     plt.axvline(t_complete_volatile_evaporation, color='black', linestyle='--', label=''.join(('полное испарение летучего,\nt = ', '{0:.{1}}'.format(t_complete_volatile_evaporation, 6), ' с')))
    # if t_complete_combustible_combustion is not None:
    #     plt.axvline(t_complete_combustible_combustion, color='black', linestyle='--', label=''.join(('полное сгорание горючего,\nt = ', '{0:.{1}}'.format(t_complete_combustible_combustion, 6), ' с')))
    # if t_complete_oxidizer_consumption is not None:
    #     plt.axvline(t_complete_oxidizer_consumption, color='black', linestyle='--', label=''.join(('полное выгорание окислителя,\nt = ', '{0:.{1}}'.format(t_complete_oxidizer_consumption, 6), ' с')))
    plt.legend(loc='best', fontsize='small')
    plt.savefig(''.join(('pic_', pic_name, '.jpeg')), dpi=400, bbox_inches='tight')
    plt.close()


path_post = ''.join((path, '/', dir_post))
Path(path_post).mkdir(parents=True, exist_ok=True)
os.chdir(path_post)

# plot_picture('time', 'diameter', 'diameter')
# plot_picture('time', 'temperature', 'temperature')
# plot_picture('time', 'dt', 'dt')

writer = pd.ExcelWriter(''.join(('qubiq_result_particles', '.xlsx')), engine="xlsxwriter")
df.to_excel(writer, index=False, sheet_name='result')
# mf_products_preliminary.to_excel(writer, index=True, sheet_name='mf_products_preliminary')
# mf_products_final.to_excel(writer, index=True, sheet_name='mf_products_final_full')
# g_CPCF.to_excel(writer, index=True, sheet_name='mf_products_final')
writer.close()

if post_visit_gas:
    writer = pd.ExcelWriter(''.join(('qubiq_result_gas', '.xlsx')), engine="xlsxwriter")
    df_gas.to_excel(writer, index=False, sheet_name='result')
    writer.close()



plot_result(df,['diameter'], ['-'], [r'$диаметр\ частицы\ [мкм]$'], r'$d\ (мкм)$', '01_p_diameter')
plot_result(df,['temperature'], ['-'], [r'$температура\ частицы\ [К]$'], r'$T\ (K)$', '04_p_temperature')
plot_result(df,['mass'], ['-'], [r'$масса\ частицы\ [кг]$'], r'$m\ (кг)$', '02_p_mass')
plot_result(df,['density'], ['-'], [r'$плотность частицы\ \left[\frac{кг}{м^3}\right]$'], r'$\rho\ \left(\frac{кг}{м^3}\right)$', '05_p_density')

if post_visit_gas:
    plot_result(df_gas, ['temperature'], ['-'], [r'$температура\ газа\ [К]$'], r'$T\ (K)$', '05_g_temperature')
    plot_result(df_gas,['mass_fractions_C7H16_nheptane', 'mass_fractions_O2', 'mass_fractions_N2'], ['-', '-', '-'], ['массовая доля н-гептана', 'массовая доля О2', 'массовая доля N2'], r'$Y$', '08_g_mass_fractions')
    plot_result(df_gas, ['pressure'], ['-'], [r'давление\ газа\ [Па]$'], r'$P\ (Па)$', '06_g_pressure')



print('end')