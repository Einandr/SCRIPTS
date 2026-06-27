import yaml
import os


def yaml_to_fluent(
    yaml_dir: str,
    material_name_qubiq: str,
    output_dir: str = None,
    material_name_fluent: str = None
) -> None:
    """
    Конвертирует YAML-файл с свойствами материала в формат журнала ANSYS Fluent.

    Args:
        yaml_dir (str): Путь к директории, содержащей YAML-файл материала.
        material_name_qubiq (str): Имя материала QUBIQ (без расширения .yaml).
        output_dir (str, optional): Путь к директории для сохранения результата.
            Если не указан, используется директория с YAML-файлом.
        material_name_fluent (str, optional): Имя материала FLUENT.
            Если не указано, используется имя материала.

    Raises:
        FileNotFoundError: Если YAML-файл не найден.
        yaml.YAMLError: Если YAML-файл поврежден.
        KeyError: Если в YAML-файле отсутствуют обязательные поля.

    Notes:
        - Поддерживает неполные YAML-файлы (если отсутствуют некоторые свойства,
          они не будут включены в выходной файл).
        - Формат выходного файла: текстовый файл с командами для Fluent.
        - Свойства материала (heat_capacity, heat_conductivity, viscosity, mass_diffusivity)
          должны быть заданы в виде словаря {температура: значение}.
    """
    yaml_path = os.path.join(yaml_dir, f"{material_name_qubiq}.yaml")
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(f"Файл {yaml_path} не найден!")
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Ошибка при чтении YAML-файла {yaml_path}: {str(e)}")

    if output_dir is None:
        output_dir = yaml_dir
    os.makedirs(output_dir, exist_ok=True)

    if material_name_fluent is None:
        material_name_fluent = material_name_qubiq
    output_path = os.path.join(output_dir, f"{material_name_fluent}.txt")

    commands = []

    # Теплоёмкость
    try:
        cp_items = sorted(data['heat_capacity'].items())
        cp_str = ' '.join([f"{t} {v}" for t, v in cp_items])
        cp_cmd = f";heat_capacity\n/define/materials/change-create/{material_name_fluent} mixture-template y piecewise-linear {len(cp_items)} {cp_str} n n n n n n\n"
        commands.append(cp_cmd)
    except KeyError:
        print(f"Внимание: свойство 'heat_capacity' отсутствует в файле {yaml_path}")

    # Теплопроводность
    try:
        lam_items = sorted(data['heat_conductivity'].items())
        lam_str = ' '.join([f"{t} {v:.6f}" for t, v in lam_items])
        lam_cmd = f";heat_conductivity\n/define/materials/change-create/{material_name_fluent} mixture-template n y piecewise-linear {len(lam_items)} {lam_str} n n n n n\n"
        commands.append(lam_cmd)
    except KeyError:
        print(f"Внимание: свойство 'heat_conductivity' отсутствует в файле {yaml_path}")

    # Вязкость
    try:
        visc_items = sorted(data['viscosity'].items())
        visc_str = ' '.join([f"{t} {v:.6e}" for t, v in visc_items])
        visc_cmd = f";viscosity\n/define/materials/change-create/{material_name_fluent} mixture-template n n y piecewise-linear {len(visc_items)} {visc_str} n n n n\n"
        commands.append(visc_cmd)
    except KeyError:
        print(f"Внимание: свойство 'viscosity' отсутствует в файле {yaml_path}")

    # Диффузия
    try:
        diff_items = sorted(data['mass_diffusivity'].items())
        diff_str = ' '.join([f"{t} {v:.6e}" for t, v in diff_items])
        diff_cmd = f";mass_diffusivity\n/define/materials/change-create/{material_name_fluent} mixture-template n n n y piecewise-linear {len(diff_items)} {diff_str} n n n\n"
        commands.append(diff_cmd)
    except KeyError:
        print(f"Внимание: свойство 'mass_diffusivity' отсутствует в файле {yaml_path}")

    # Проверяем, что хотя бы одно свойство было обработано
    if not commands:
        raise ValueError(f"В файле {yaml_path} отсутствуют все обязательные свойства материала!")

    # Запись в файл
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(commands))
        print(f"✅ Экспорт {yaml_path} ==> {output_path}")
        print(f"   Материал QUBIQ: {material_name_qubiq} ==> Материал FLUENT: {material_name_fluent}")
    except IOError as e:
        raise IOError(f"Ошибка при записи файла {output_path}: {str(e)}")


dir_yaml = r'D:\YASIM\VORON\2026_15_Spalding_Combustion\materials\gas'
name_yaml = 'CP_air_kerosene_Dagaut'
work_path = r'D:\YASIM\VORON\2026_15_Spalding_Combustion'
dir_fluent = 'materials_fluent'

path_fluent = os.path.join(work_path, dir_fluent)
os.makedirs(path_fluent, exist_ok=True)

materials_qubiq = ['CP_air_kerosene_Dagaut', 'KEROSENE_Dagaut', 'AIR_simple']
materials_fluent = ['cp', 'kerosene', 'air']
for material_qubiq, material_fluent, in zip(materials_qubiq, materials_fluent):
    yaml_to_fluent(dir_yaml, material_qubiq, path_fluent, material_fluent)
