import os
import re
import pandas as pd

# path = '/sim/r_01_ker_bigmesh_comb'

# path = '/sim/r_01_ker_bigmesh_vap_hotdrops'
# path = '/SIM/06_MPL_one_cell_8mm'
# MPL
# path = r'D:\YASIM\VORON\2025_04_MPL\03_test_MPL_one_cell'
path = r'D:\YASIM\VORON\2025_09_MPL\TASK_DECEMBER\04_TT2_OLD_MODELS\01_3comp_basic_master'
# Spalding
# path = r'D:\YASIM\VORON\2025_04_SpaldComb\TEST_convective_1particle_10x200_QUBIQ'

path_tracks = 'tracks'
# path_out = 'run/out'
path_out = 'out'

BORIS_HUJNA = True
transient = False

os.chdir(''.join((path, '/', path_out, '/', path_tracks)))
# regions = [f for f in os.listdir('.') if not os.path.isfile(f)]

ts_list = []



files = [f for f in os.listdir('.') if os.path.isfile(f)]
print(files)

if not transient:
    filtered_files = [f for f in files if "steady" in f and "transient" not in f]
else:
    filtered_files = [f for f in files if "steady" not in f and "transient" in f]
print(filtered_files)

if not transient:
    for f in filtered_files:
      try:
        # ts = re.search(r'track-log_step_\d{1,10}', f).group(0)
        ts = re.search(r'track-log_step_\d{1,10}', f)
        # print(ts.group(0))
      except AttributeError:
        pass
      else:
        string = re.sub(r'track-log_step_(\d{1,10})', r'\1', ts.group(0))
        # print('string is ', string)
        ts = int(string)
        # print(ts)
        if ts not in ts_list:
         ts_list.append(ts)
         print(f, ts)

print(ts_list)


def extract_number(filename):
    match = re.search(r'step_(\d+)', filename)
    if match:
        return int(match.group(1))
    return 0

sorted_files = sorted(filtered_files, key=extract_number)








# names = ['x', 'y', 'z', 'temperature', 'diameter', 'velocity', 'dt']
# MPL
# names = ['region_id', 'track_id', 'iteration', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'temperature', 'diameter', 'density', 'mass', 'velocity_x', 'velocity_y', 'velocity_z', 'velocity', 'dt', 'n_particles', 'Y1', 'Y2', 'Y3']
# basic extended
# names = ['region_id', 'track_id', 'iteration', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'temperature', 'diameter', 'density', 'mass', 'velocity_x', 'velocity_y', 'velocity_z', 'velocity', 'dt', 'n_particles', 'Y1']

# БОРИСОВСКАЯ ХУЙНЯ НА МИНИМАЛКАХ
names = ['region_id', 'track_id', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'temperature', 'diameter', 'velocity', 'dt', 'n_particles']


# Spalding
# names = ['region_id', 'track_id', 'iteration', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'temperature', 'diameter', 'density', 'mass', 'velocity_x', 'velocity_y', 'velocity_z', 'velocity', 'dt', 'n_particles', 'Y1']
# names = ['region_id', 'track_id', 'iteration', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'temperature', 'diameter', 'density', 'mass', 'velocity_x', 'velocity_y', 'velocity_z', 'velocity', 'dt', 'n_particles']


# data_all = d = pd.DataFrame(columns=names)


if not transient:
    ts_max = max(ts_list)
    print('max iter is ', ts_max)

list_df = []
# os.chdir(''.join((path, '/', path_out, '/', path_tracks, '/', d)))


def determine_column_type(column):
    if column.apply(lambda x: isinstance(x, float) or '.' in str(x)).any():
        return 'float'
    else:
        return 'int'


if not transient:
    sorted_files = [f for f in os.listdir('.') if os.path.isfile(f) and re.match(''.join(('track-log_step_', str(ts_max))), f)]


for f in sorted_files:
    data = pd.read_csv(f, delimiter=' ', names=names, index_col=False, skiprows=1)
    for column in data.columns:
        column_type = determine_column_type(data[column])
        if column_type == 'int':
            data[column] = data[column].astype(int)
            print('read as int column: ', column)
        else:
            data[column] = pd.to_numeric(data[column], errors='coerce').astype(float)
            print('read as float column: ', column)
    list_df.append(data)
data_all_region = pd.concat(list_df, ignore_index=True)

# Если захочется выделить стартовые треки потом вручную - то убрать эту строчку с сортировкой
if BORIS_HUJNA:
    data_all_region = data_all_region.sort_values(by=['region_id', 'track_id'])
else:
    data_all_region = data_all_region.sort_values(by=['region_id', 'track_id', 'iteration'])

if not BORIS_HUJNA:
    # Вычисляем разницу между текущей и предыдущей итерацией для каждого трека
    data_all_region['iteration_diff'] = data_all_region.groupby('track_id')['iteration'].diff().fillna(1)
    # Вычисляем время как dt * iteration_diff и затем кумулятивную сумму
    data_all_region['cumulative_dt'] = data_all_region['dt'] * data_all_region['iteration_diff']
    data_all_region['time'] = data_all_region.groupby('track_id')['cumulative_dt'].cumsum()

    # Удаляем вспомогательный столбец, если он больше не нужен
    data_all_region.drop(columns=['iteration_diff', 'cumulative_dt'], inplace=True)

# data_all_region['time'] = data_all_region.groupby('track_id')['dt'].cumsum()

# data_all_region['Y1'] = 1
# data_all_region['Y2'] = 0
# data_all_region['Y3'] = 0


os.chdir(''.join((path, '/', path_out)))
# data_all_region.to_csv(''.join(('tracks_', d, '.csv')), index=False)
# list_df_regions.append(data_all_region)


# data_all = pd.concat(list_df_regions, ignore_index=True)
# data_all.sort_values(by=['CoordinateZ'], inplace=True)
# data_all['time'] = data_all['dt'].cumsum()


# os.chdir(''.join((path, '/', path_out, '/', path_tracks)))
data_all_region.to_csv('tracks_all.txt', index=False)

print('debug')