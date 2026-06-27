import time
import datetime

import tecplot as tp
from tecplot.exception import *
from tecplot.constant import *

import tpmath
import tputils
from utils import *


solver = Solver.FLUENT
calculate_combustion_efficiency = True
zones_average = [1,2,3,4,5,6]


tp.session.connect()

time_start = datetime.datetime.now()
print('Время старта:', time_start)
dataset = tp.active_frame().dataset
var_names = [var.name for var in dataset.variables()]

# Формирование списка компонент
species = parse_species(dataset, solver)

# Переименование переменных
rename_variables(dataset, solver)

# Вычисление новых переменных
if solver == Solver.FLUENT:
    execute_equation('Velocity', '({X Velocity}**2+{Y Velocity}**2+{Z Velocity}**2)**0.5', var_names)
    # execute_equation('Total Pressure', '{Static Pressure} +  {Density}*{Velocity}*{Velocity}/2', var_names)
    # execute_equation('Total Pressure Relative', '{Total Pressure} - 101000', var_names)

variables = ['Temperature', 'Pressure', 'Velocity']

for sp in species:
    name = f'Y_{sp}'
    variables.append(name)

if calculate_combustion_efficiency:
    name_mass_flux = 'RhoVx'
    execute_equation(name_mass_flux, '{Density}*{X Velocity}', var_names)
    variables.append(name_mass_flux)
    print('Вычисление RhoVx компонент...')
    for sp in species:
        name = f'RhoVx_{sp}'
        equation = f'{{RhoVx}}*{{Y_{sp}}}'
        execute_equation(name, equation, var_names)
        variables.append(name)

print('Вычисление средних значений в Tecplot...')
variables_to_average = [dataset.variable(name) for name in variables]
constant_variables = [dataset.variable("CoordinateX"), dataset.variable("CoordinateY"), dataset.variable("CoordinateZ")]
zones_by_strand = tputils.get_zones_by_strand(dataset)

for zone in zones_average:
    source_zones = zones_by_strand[zone]
    tpmath.compute_average(source_zones, variables_to_average, constant_variables)

time_end = datetime.datetime.now()
print('Время завершения:', time_end)
delta_time = time_end - time_start
print(f'Время выполнения скрипта {delta_time.seconds} секунд / {delta_time.seconds / 60:.2f} минут / {delta_time.seconds / 3600:.2f} часов')
