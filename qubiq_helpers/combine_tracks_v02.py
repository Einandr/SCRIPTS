import os
import re
import pandas as pd

# path = '/sim/r_01_ker_bigmesh_comb'

# path = '/sim/r_01_ker_bigmesh_vap_hotdrops'
path = '/mnt/lustre/groupshare/mgtu_baumana/ayakovchuk/2023_02_KTRV/1-1_hot_High'

path_tracks = 'tracks'
# path_out = 'run/out'
path_out = 'out'



os.chdir(''.join((path, '/', path_out, '/', path_tracks)))
# regions = [f for f in os.listdir('.') if not os.path.isfile(f)]

ts_list = []



files = [f for f in os.listdir('.') if os.path.isfile(f)]
print(files)
for f in files:
  try:
    ts = re.search(r'track-log_\d{1,10}', f).group(0)
  except:
    pass
  else:
    ts = int(re.sub(r'track-log_', '', ts))
    if ts not in ts_list:
     ts_list.append(ts)
     print(f, ts)

print(ts_list)

# names = ['x', 'y', 'z', 'temperature', 'diameter', 'velocity', 'dt']
names = ['region_id', 'track_id', 'CoordinateX', 'CoordinateY', 'CoordinateZ', 'temperature', 'diameter', 'velocity', 'dt', 'n_particles']
# data_all = d = pd.DataFrame(columns=names)



ts_max = max(ts_list)
print('max iter is ', ts_max)

list_df = []
# os.chdir(''.join((path, '/', path_out, '/', path_tracks, '/', d)))
files = [f for f in os.listdir('.') if os.path.isfile(f) and re.match(''.join(('track-log_', str(ts_max))), f)]
for f in files:
 data = pd.read_csv(f, delimiter=' ', names=names, index_col=False, skiprows=1)
 list_df.append(data)
data_all_region = pd.concat(list_df, ignore_index=True)
data_all_region.sort_values(by=['region_id'], inplace=True)
data_all_region['time'] = data_all_region['dt'].cumsum()

os.chdir(''.join((path, '/', path_out)))
# data_all_region.to_csv(''.join(('tracks_', d, '.csv')), index=False)
# list_df_regions.append(data_all_region)


# data_all = pd.concat(list_df_regions, ignore_index=True)
# data_all.sort_values(by=['CoordinateZ'], inplace=True)
# data_all['time'] = data_all['dt'].cumsum()


# os.chdir(''.join((path, '/', path_out, '/', path_tracks)))
data_all_region.to_csv('tracks_all.csv', index=False)

print('debug')