import os
import re

path = r'D:\YASIM\VORON\2025_09_MPL\TASK_DECEMBER\04_TT2_OLD_MODELS\01_3comp_basic_master'
clear_silo = True
clear_chk = True

# DELETE all in between
first_save = -10
last_save = 1220000

path_out = 'out'
path_silo = 'silo'
path_chk = 'chk'
mesh_name = 'cylinder'

os.chdir(''.join((path, '/', path_out, '/', path_silo)))

files = [f for f in os.listdir('.') if os.path.isfile(f)]
dirs = [f for f in os.listdir('.') if not os.path.isfile(f)]

# В случа если в названии сетки присутствует цифра, будем определять число вхождений с непрерывными цифрами
# чтобы далее следующим вхождением выделить нужный шаг по времени
# при нумерации от 0 индекс шага это будет число вхождений групп цифр в название сетки
# number_of_instance = 0
number_of_instance = len(re.findall(r'[0-9]+', mesh_name))

if clear_silo:
 files_of_other_format = []
 for f in files:
     try:
         # ts = float(re.search(r'[0-9]+', f).group(0))
         instances = (re.findall(r'[0-9]+', f))
         if len(instances) == number_of_instance + 1:
             ts = float(instances[number_of_instance])
             if first_save < ts < last_save:
                 os.remove(f)
                 print(f, ts)
         else:
             files_of_other_format.append(f)
     except:
         files_of_other_format.append(f)

 for f in files_of_other_format:
     print('file of other format: ', f)

 for d in dirs:
     os.chdir(''.join((path, '/', path_out, '/', path_silo, '/', d)))
     files = [f for f in os.listdir('.') if os.path.isfile(f)]
     files_of_other_format = []
     for f in files:
         try:
             # ts = float(re.search(r'[0-9]+', f).group(0))
             instances = (re.findall(r'[0-9]+', f))
             if len(instances) == number_of_instance + 1:
                 ts = float(instances[number_of_instance])
                 if first_save < ts < last_save:
                     os.remove(f)
                     print(d, f, ts)
             else:
                 files_of_other_format.append(f)
         except:
             files_of_other_format.append(f)

if clear_chk:
 # В файлах DUMP CHK не используется название OUT директории, поэтому здесь берется первое вхожждение цифр
 # Комментарий оставлен для быстрого исправления если Борис что-то изменит в будущем
 os.chdir(''.join((path, '/', path_out, '/', path_chk)))
 dirs = [f for f in os.listdir('.') if not os.path.isfile(f)]
 for d in dirs:
     os.chdir(''.join((path, '/', path_out, '/', path_chk, '/', d)))
     files = [f for f in os.listdir('.') if os.path.isfile(f)]
     for f in files:
         ts = float(re.search(r'[0-9]+', f).group(0))
         # ts = float(re.findall(r'[0-9]+', f)[number_of_instance])
         if first_save < ts < last_save:
             os.remove(f)
             print(d, f, ts)

print('debug')
