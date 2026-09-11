
Данный набор скриптов позволяет проводить различные манипуляции при постпроцессинге благодаря Tecplot python API https://tecplot.com/products/pytecplot/

# config_iskra_high.ini
Возьми за основу этот наиболее актуальный конфиг и от него поменяй под свою задачу  
Актуальные секции и параметры пока перемешаны со старыми, не могу удалить, надо еще повозиться чтоб все сделать аккуратно, придется поразбираться в теле скрипта какие считываются какие нет.

# !postprocessor
Запускать по сути нужно только этот файл. В нем только выставить ссылку на config.ini. Остальные все настройки указываются непосредственно в config.ini

ДАЛЕЕ ЧАСТЬ ОТДЕЛЬНЫЕ СКРИПТЫ КОТОРЫЕ УЖЕ ВШИТЫ В !postprocessor, ЧАСТЬ БИБЛИОТЕКИ, ЧАСТЬ - ОСТАЛИСЬ ОТ СТАРЫХ ВЕРСИЙ, ОНИ ПОКА НУЖНЫ ПУСТЬ ПОЛЕЖАТ

После экспорта из VISIT в файле *tec в заголовке надо почистить лишние строчки, т.к. preplot ищет переменные во второй строке, а экспортер пишет их позже. Чтоб было примерно так:

TITLE = "D:\YASIM\VORON\2026_12_Iskra_OPZ\QUBIQ\LES_HOT_LOW\SILO\root\tet_04_3.5-2_10.7mln_step_4510000.root: ROOT file Driver: PDB Lite File: , silo-4.10.2 Plugin: hdf5-2.0.0, silo-4.12.0"  
VARIABLES = "X", "Y", "Z", "ALL/Mach", "ALL/pressure", "ALL/temperature", "ALL/density", "ALL/velocity_magnitude", "ALL/velocity_x", "ALL/velocity_y", "ALL/velocity_z", "ALL/mass_fractions_Air", "ALL/mass_fractions_CP", "ALL/mass_fractions_GPG", "ALL/mean_pressure", "ALL/mean_temperature", "ALL/mean_density", "ALL/mean_velocity_x", "ALL/mean_velocity_y", "ALL/mean_velocity_z", "ALL/mean_mass_fractions_Air", "ALL/mean_mass_fractions_CP", "ALL/mean_mass_fractions_GPG"  
ZONE T="DOMAIN 0", N=635261, E=3543244, F=FEBLOCK, ET=TETRAHEDRON

QUBIQ экспортированный в *tec формат полезно предварительно перегнать в *plt формат через утилиту preplot. Делается это из командной строки:  
"C:\Program Files\Tecplot\Tecplot 360 EX 2025 R2\bin\preplot.exe" visit_ex_db_3D3.tec visit_ex_db_3D3.plt

Предварительно нужно в текстовом редакторе откорректировать *tec файл так, чтобы в заголовке на второй строке оказались переменные, то есть строку TITLE = "..." всю перенести на первую строчку, строка VARIABLES = ... чтоб осталась на второй (это баги текплота)

# compute_average
Вычисление осредненных по времени полей.
Также на этом этапе проводится переименование переменных к общему виду для последующей верификации QUBIQ-FLUENT

# export_cross_slices
Экспорт данных на поперечных сечениях/
Этот скрипт предполагается применять после compute_average, однако тут тоже предусмотрено переименование переменных если на предыдущем этапе этого не произошло. Например, любой стационарный расчет где не нужно осреднения.

# movie_integrate_v2022_H5
Запись анимации, картинок, расчет дополнительных параметров и подготовка к пост-обработке с использованием библоитек кинетики. Версия от 2022 года.

# result_animation_many_2022_premixed_multizoneaveraged
Расчет параметров течения и построение графиков по результатам выгруженных экспортированных данных "movie_integrate_v2022_H5" Версия от 2022 года.

# utils
Вынесенные для общего пользования функции и классы, применяемые в скриптах выше

# tpmath, tputils
Библиотеки из открытого репозитория
https://tecplot.com/2022/06/29/pytecplot-scripts-to-calculate-transient-data-statistics/
https://github.com/Tecplot/handyscripts
