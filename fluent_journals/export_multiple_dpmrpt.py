import os
import re





path = r"E:\YASIM\VORON_TEMP\2026_12_Iskra_OPZ\high_OPZ_b08"
case = "save-37.cas.h5"
data_start = 'save-37-1.729750.dat.h5'
data_end = 'save-37-1.745000.dat.h5'

output_journal = "particle_export_journal.jou"

case_file_name = [''.join((path, '/', case))]
print('case файл:')
print(case_file_name)

data_file_names = []
names = os.listdir(path)
data_name = data_start
for name in names:
    if data_start <= name <= data_end:
        data_file_names.append(name)
        # data_file_names.append(''.join((path, '/', name)))
print('Список data файлов:')
for x in range(len(data_file_names)):
    print(data_file_names[x])

data_file_names.sort()

os.chdir(path)

with open(output_journal, "w", encoding="utf-8") as f:

    f.write(f';/file/read-case "{case}"\n')

    for data in data_file_names:
        time_match = re.search(r"-(\d+\.\d+)\.dat\.h5$", data)
        if not time_match:
            continue
        time_str = time_match.group(1)

        f.write(f'/file/read-data "{data}"\n')

        f.write(f'''(cx-gui-do cx-set-list-tree-selections "NavigationPane*Frame2*Table1*List_Tree2" (list "Results|Graphics|Particle Tracks|particle-tracks-1"))
(cx-gui-do cx-activate-item "NavigationPane*Frame2*Table1*List_Tree2")
(cx-gui-do cx-set-list-tree-selections "NavigationPane*Frame2*Table1*List_Tree2" (list "Results|Graphics|Particle Tracks|particle-tracks-1"))
(cx-gui-do cx-set-toggle-button2 "Particle Tracks*Table2*Table2(Reporting)*Table1*ToggleBox3(Report to)*File" #t)
(cx-gui-do cx-activate-item "Particle Tracks*Table2*Table2(Reporting)*Table1*ToggleBox3(Report to)*File")
(cx-gui-do cx-set-toggle-button2 "Particle Tracks*Table2*Table2(Reporting)*Table1*ToggleBox1(Report Type)*Step By Step" #t)
(cx-gui-do cx-activate-item "Particle Tracks*Table2*Table2(Reporting)*Table1*ToggleBox1(Report Type)*Step By Step")
(cx-gui-do cx-activate-item "Particle Tracks*PanelButtons*PushButton1(OK)")
(cx-gui-do cx-set-file-dialog-entries "Select File" '( "particles_{time_str}.dpmrpt") "Particle Reports (*.dpmrpt)")
(cx-gui-do cx-activate-item "Particle Tracks*PanelButtons*PushButton2(Cancel)")\n
''')
#
#         # Экспорт в файл с временной меткой
#         report_file = f"file_time_{time_str}.dpmrpt"
#         f.write(f'/define/particle-tracks/particle-tracks-1/write-report "{report_file}"\n\n')

print(f"Журнал сгенерирован: {output_journal}")