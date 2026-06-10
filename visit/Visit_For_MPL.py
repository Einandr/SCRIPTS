import visit
import os
import re

path_out = r'/SIM/06_MPL_one_cell_8mm/post_visit'
path_out = r'D:\YASIM\VORON\2025_04_MPL\03_test_MPL_one_cell\post_visit'
os.chdir(path_out)
# HideActivePlots()

# visit.HideActivePlots()
# visit.DrawPlots()

# visit.SetTimeSliderState(2)
# visit.DrawPlots()



# i = 0
# imax =
# for i <= imax:
#     i++
#

# data_timestep = []
# data_Temperature = []
#
# for state in TimeSliderGetNStates():
#     TimeSliderSetState(state)
#     # visit.DrawPlots()
#     res = visit.ZonePick(coord=(0, 0, 0), vars=("FLUID_MAIN/mass_fraction_CPCF", "FLUID_MAIN/mass_fraction_GV", "FLUID_MAIN/mass_fraction_N2",
#     "FLUID_MAIN/mass_fraction_N2", "FLUID_MAIN/mass_fraction_O2", "FLUID_MAIN/temperature"))
#     data_timestep.append(res['timestep'])
#     data_Temperature.append(res['FLUID_MAIN/temperature'])
#     ClearPickPoints()
#
# print('time steps are:', data_timestep)
# print('temperatures are:', data_Temperature)

# res = Query("Pick")
# print('res is:', res)
#
# with open('file_out.txt', 'w') as f:
#     f.write(str(res['FLUID_MAIN/temperature']))

# OpenDatabase("~juanita/silo/stuff/wave.visit")
# AddPlot("Pseudocolor", "pressure")
# DrawPlots()


QueryOverTimeAtts = GetQueryOverTimeAttributes()
QueryOverTimeAtts.timeType = QueryOverTimeAtts.Cycle  # Cycle, DTime, Timestep
SetQueryOverTimeAttributes(QueryOverTimeAtts)

mesh_name = 'one_cell_8mm'
number_of_instance = len(re.findall(r'[0-9]+', mesh_name))

fluid_name = '3D/FLUID_MAIN'
variables_names = ['temperature', 'pressure', 'mass_fractions_CPCF', 'mass_fractions_CPCP', 'mass_fractions_GV', 'mass_fractions_O2', 'mass_fractions_N2']
variables_full_names = []

header = ' '.join(variables_names)

print(variables_names)
print(variables_full_names)
print(header)

for name in variables_names:
    variables_full_names.append(''.join((fluid_name, '/', name)))

string_format = ''
i = 0
while i <= len(variables_names):
    string_format += '%g '
    i += 1
string_format = string_format[:-1]
string_format += '\n'

print('string format is: ', string_format)

max_time_steps = 1000000
n_time_steps = TimeSliderGetNStates()
f = open('points.txt', 'w', encoding='utf-8')
# f.write('time_step, x, y, z, u, v, w\n')
f.write(''.join(('time_step', ' ', header, '\n')))
for time_step in range(0, n_time_steps):
    if time_step < max_time_steps:
        TimeSliderSetState(time_step)
        # pick = PickByNode(domain=0, element=3726, vars=["vel_x", "vel_y", "vel_z"])
        # pick = ZonePick(coord=(0, 0, 0), vars=("FLUID_MAIN/vel_x", "FLUID_MAIN/vel_y", "FLUID_MAIN/vel_z"))
        pick = ZonePick(coord=(0, 0, 0), vars=tuple(variables_full_names))
        # pick = ZonePick(coord=(0, 0, 0), vars=("FLUID_MAIN/mass_fraction_CPCF", "FLUID_MAIN/mass_fraction_GV", "FLUID_MAIN/mass_fraction_N2",

        database_file = pick['filename']
        time_step = float(re.findall(r'[0-9]+', database_file)[number_of_instance])


        print('time step is:', time_step)
        print('time slider is:', GetActiveTimeSlider())
        print('res is:', pick)
        Query("Time")
        time = GetQueryOutputValue()

        output_tuple = (time_step,)
        for var in variables_full_names:
            output_tuple += (pick[var],)
        f.write(string_format % output_tuple)

        # f.write('%g, %g, %g, %g, %g, %g, %g\n' % (time_step, pick['point'][0], pick['point'][1], pick['point'][2], pick['FLUID_MAIN/vel_x'], pick['FLUID_MAIN/vel_y'], pick['FLUID_MAIN/vel_z']))
f.close()


