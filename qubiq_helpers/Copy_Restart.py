import os
import re
import shutil
from pathlib import Path

path_from = r'D:\YASIM\VORON\2025_09_MPL\TASK_DECEMBER\04_TT2_OLD_MODELS\01_3comp_basic_master'
path_to = r'D:\YASIM\VORON\2025_09_MPL\TASK_DECEMBER\04_TT2_OLD_MODELS\01_3comp_basic_master_for_tracker'
copy_silo = False
copy_chk = True

first_save = 880000
last_save = 880000

copy_save = 880000


path_run = ''
path_out = 'out'
path_silo = 'silo'
path_chk = 'chk'
mesh_name = 'cylinder'

Path(''.join((path_to, '/', path_run, '/', path_out, '/', path_chk))).mkdir(parents=True, exist_ok=True)
Path(''.join((path_to, '/', path_run, '/', path_out, '/', path_silo))).mkdir(parents=True, exist_ok=True)


os.chdir(''.join((path_from, '/', path_run, '/', path_out, '/', path_silo)))
files = [f for f in os.listdir('.') if os.path.isfile(f)]
dirs = [f for f in os.listdir('.') if not os.path.isfile(f)]


# В случа если в названии сетки присутствует цифра, будем определять число вхождений с непрерывными цифрами
# чтобы далее следующим вхождением выделить нужный шаг по времени
# при нумерации от 0 индекс шага это будет число вхождений групп цифр в название сетки
# number_of_instance = 0
number_of_instance = len(re.findall(r'[0-9]+', mesh_name))


if copy_silo:
 print('form root silo dir:')
 for f in files:
  # ts = float(re.search(r'[0-9]+', f).group(0))
  ts = float(re.findall(r'[0-9]+', f)[number_of_instance])
  print(ts)
  if first_save <= ts <= last_save:
   shutil.copyfile(''.join((path_from, '/', path_run, '/', path_out, '/', path_silo, '/', f)),
                   ''.join((path_to, '/', path_run, '/', path_out, '/', path_silo, '/', f)))
   print(f, ts)
 print('form dirs:')
 for d in dirs:
  Path(''.join((path_to, '/', path_run, '/', path_out, '/', path_silo, '/', d))).mkdir(parents=True, exist_ok=True)
  os.chdir(''.join((path_from, '/', path_run, '/', path_out, '/', path_silo, '/', d)))
  files = [f for f in os.listdir('.') if os.path.isfile(f)]
  for f in files:
   # ts = float(re.search(r'[0-9]+', f).group(0))
   ts = float(re.findall(r'[0-9]+', f)[number_of_instance])
   # print(ts)
   if first_save <= ts <= last_save:
    shutil.copyfile(''.join((path_from, '/', path_run, '/', path_out, '/', path_silo, '/', d, '/', f)),
                    ''.join((path_to, '/', path_run, '/', path_out, '/', path_silo, '/', d, '/', f)))
    print(f, ts)


# В файлах DUMP CHK не используется название OUT директории, поэтому здесь берется первое вхожждение цифр
# Комментарий оставлен для быстрого исправления если Борис что-то изменит в будущем
if copy_chk:
 os.chdir(''.join((path_from, '/', path_run, '/', path_out, '/', path_chk)))
 dirs = [f for f in os.listdir('.') if not os.path.isfile(f)]
 for d in dirs:
  Path(''.join((path_to, '/', path_run, '/', path_out, '/', path_chk, '/', d))).mkdir(parents=True, exist_ok=True)
  os.chdir(''.join((path_from, '/', path_run, '/', path_out, '/', path_chk, '/', d)))
  files = [f for f in os.listdir('.') if os.path.isfile(f)]
  for f in files:
   ts = float(re.search(r'[0-9]+', f).group(0))
   # ts = float(re.findall(r'[0-9]+', f)[number_of_instance])
   if ts == copy_save:
    shutil.copyfile(''.join((path_from, '/', path_run, '/', path_out, '/', path_chk, '/', d, '/', f)),
                    ''.join((path_to, '/', path_run, '/', path_out, '/', path_chk, '/', d, '/', f)))
    print(f, ts)


print('debug')