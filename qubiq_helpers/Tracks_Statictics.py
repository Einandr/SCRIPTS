import pandas as pd
import os
import matplotlib.pyplot as plt

# path = '/sim/r_01_ker_bigmesh_comb'

# path = '/sim/r_01_ker_bigmesh_vap_hotdrops'
path = '/root/Desktop/sim/05_tube_Cd0'


path_out = 'out'
path_tracks = 'tracks'

os.chdir(''.join((path, '/', path_out, '/', path_tracks)))


regions = ['region0']
# legend = ['d2000']
legend = ['d200', 'd150', 'd100']

dfr = []

for r in regions:
    data = pd.read_csv(''.join(('tracks_', r, '.csv')))
    data.sort_values('CoordinateZ', inplace=True)
    dfr.append(data)

print('total time is:', data['dt'].sum())

plt.rcParams["figure.figsize"] = [15.00, 7]
plt.rcParams["figure.autolayout"] = True

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
    ax = dfr[0].plot(x=x, y=y, grid=True)
    for df in dfr[1:]:
        df.plot(ax=ax, x=x, y=y, grid=True)
    ax.legend(legend)
    # ax.set_ylim([0, 0.00021])
    plt.savefig(''.join((name, '.jpeg')))
    plt.close()

plot_picture('CoordinateZ', 'diameter', 'diameter')
plot_picture('CoordinateZ', 'temperature', 'temperature')
plot_picture('CoordinateZ', 'dt', 'dt')

print('end')