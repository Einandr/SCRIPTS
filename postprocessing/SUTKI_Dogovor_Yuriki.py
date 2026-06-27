import os
from datetime import datetime
import locale
from num2words import num2words

import pandas as pd

from utils_documents import (
    months,
    decline_word,
    num_to_words,
    decline_fio,
    setup_document_styles,
    add_text,
    add_floating_image,
    convert_docx_to_pdf
)

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_ALIGN_PARAGRAPH, WD_BREAK, WD_UNDERLINE
from docx.shared import Cm, Pt, RGBColor, Inches
from docx.oxml.ns import qn, nsdecls
from docx.oxml import OxmlElement


# TODO: добавить парсинг адресов с расстановкой неразрывных пробелов
# TODO: добавить гиперссылки на почту
# TODO: проработать завертку в исполняемый файл
# TODO: сделать отдельный скрипт на автоматизацию счетов
# TODO: выровнять таблицы в подписи с реквизитами - для данных счета отдельную строку чтоб было на одном уровне
# TODO: склонения для женских фамилий


# Путь к рабочей директории
path = r'C:\Users\YA\Desktop\СУТКИ\Контрагенты\ДОГОВОРЫ_ЮРЛИЦА'
excel_file = 'Юрики.xlsx'

# сокращенное наименование организации контрагента
name_short = 'ООО «А100»'


# name_short = 'ИП Мельник М.М.'

# apartments = [
#     # "1-комнатная кв., г. Люберцы, ул. Камова, д. 5к2; стоимость 3000 в сутки",
#     # "1-комнатная кв., г. Люберцы, ул. Озёрная, д.3; стоимость 3500 в сутки.",
#     # "евро 2-х комнатная кв., г. Люберцы ул. Камова 5к2; стоимость 4000 в сутки",
#     "2-х комнатная кв., г. Люберцы ул. Камова 3к2; стоимость 4000 в сутки.",
#     # "3-х комнатная кв., г. Люберцы ул. Камова 5к2; стоимость 5000 в сутки при посуточной оплате либо 130000 в месяц при помесячной оплате"
# ]

# unit = 'месяц'
# services_data = [
#     ['2026-06', '02.03.2026', 1, 100000],
#     ['2026-16', '01.04.2026', 1, 100000],
# ]



# unit = 'суток'
# services_data = [
#     ['2025-33', '29.09.2025', 2, 2686],
#     ['2025-34', '01.10.2025', 9, 3000],
#     ['2025-35', '09.10.2025', 10, 3000],
#     ['2025-36', '17.10.2025', 5, 3000],
#     # ['2026-02', '24.02.2026', 5, 3500],
#     # ['2026-05', '02.03.2026', 6, 3500],
#     # ['2026-07', '06.03.2026', 7, 3500],
#     # ['2026-10', '13.03.2026', 5, 3500],
#     # ['2026-12', '19.03.2026', 7, 3500],
#     # ['2026-15', '26.03.2026', 7, 3500]
# ]

contract = True
certificate = True
certificate_without_contract = False
pdf = True




os.chdir(path)
df = pd.read_excel(os.path.join(path, excel_file), header=None)

fields = df.iloc[:, 0].tolist()

client_column_index = None
for col_idx in range(1, df.shape[1]):
    current_name_short = df.iloc[0, col_idx]
    if current_name_short == name_short:
        client_column_index = col_idx
        break

if client_column_index is None:
    raise ValueError(f"Контрагент '{name_short}' не найден")

tenant = {}

for field_idx, field_name in enumerate(fields):
    print(field_idx, field_name)
    field_value = df.iloc[field_idx, client_column_index]
    if not pd.isna(field_value):
        if field_name == 'наименование сокращенное':
            field_value = field_value.replace(' ', '\u00A0')
        tenant[field_name] = field_value
    else:
        tenant[field_name] = None


def determine_legal_status(tenant):
    ogrn = tenant.get("ОГРН")
    ogrnip = tenant.get("ОГРНИП")
    if ogrn and ogrnip:
        raise ValueError("Ошибка: Не могут быть заполнены оба поля ОГРН и ОГРНИП одновременно.")
    elif ogrn:
        return "ООО"
    elif ogrnip:
        return "ИП"
    else:
        raise ValueError("Ошибка: Одно из полей ОГРН или ОГРНИП должно быть заполнено.")


try:
    tenant['статус'] = determine_legal_status(tenant)
    print(f"Статус контрагента: {tenant['статус']}")
except ValueError as e:
    print(e)

print(tenant)






# Склонение слов
# rent_length_word = decline_word(rent_length, 'сутки', 'суток', 'суток')
# rent_cost_prepayment_word = decline_word(rent_cost_prepayment, 'рубль', 'рубля', 'рублей')
# rent_cost_onsite_word = decline_word(rental_cost_onsite, 'рубль', 'рубля', 'рублей')
# rent_cost_overall_word = decline_word(rent_cost_overall, 'рубль', 'рубля', 'рублей')
# rent_price_daily_word = decline_word(daily_price, 'рубль', 'рубля', 'рублей')

# Преобразование суммы в слова
# rent_cost_overall_translite = num_to_words(rent_cost_overall)

# Функция для получения даты в формате "16 марта 2026 г."
# def format_date(date):
#     day = date.day
#     month = MONTHS[date.month]
#     year = date.year
#     return f"{day} {month} {year} г."
day = tenant['дата договора'].day
month = months[tenant['дата договора'].month]
year = tenant['дата договора'].year

# Дата и город
date = f"{day} {month} {year} г."
city = tenant.get('город', '')

# Счета
services_data_raw = tenant.get('счета', '')
services_data = []
for line in services_data_raw.strip().splitlines():
    parts = line.split()
    formatted_line = [
        parts[0],           # N счёта (2026-14)
        parts[1],           # Дата (25.03.2026)
        int(parts[2]),      # Количество (7)
        int(parts[3])       # Цена (4000)
    ]
    services_data.append(formatted_line)

# Единицы измерения (сутки, месяц)
unit = tenant.get('ед.изм.', '')

# квартиры
apartments_raw = tenant.get('квартиры', '')
apartments = []
for line in apartments_raw.strip().splitlines():
    apartments.append(line)

# Данные арендодателя
landlord = {
    'статус': 'ИП',
    'имя': 'Яковчук Андрей Юрьевич',
    'паспорт': '0709\u00A0294154',
    'дата выдачи': '24.10.2009',
    'кем выдан': 'отделом УФМС РФ по\u00A0Ставропольскому\u00A0краю в г.\u00A0Будённовске и\u00A0Будённовском районе',
    'код подразделения': '260-006',
    'индекс адреса': '143442',
    'адрес прописки': 'Московская\u00A0область, г.\u00A0Красногорск, пгт.\u00A0Сабурово, ул.\u00A0Садовая, д.\u00A012, кв.\u00A024',
    'ИНН': '262409090402',
    'ОГРНИП': '320502700015367',
    'дата выдачи ОГРНИП': '20.02.2020',
    'телефон': '+7\u00A0926\u00A03400187',
    'email': 'yaflat@yandex.ru',
    'расчетный счет': '40802810538000180470',
    'наименование банка': 'ПАО СБЕРБАНК',
    'адрес банка': '109544, г.\u00A0Москва, ул.\u00A0Большая\u00A0Андроньевская, д.\u00A06',
    'корреспондентский счет': '30101810400000000225',
    'БИК': '044525225'
}


# Функция для разбора ФИО и формирования инициалов
def format_fio(full_name):
    if not full_name:
        return ""
    parts = full_name.split()
    if len(parts) == 3:
        # Формат: Фамилия И.О.
        surname = parts[0]
        initials = f"{parts[1][0]}.{parts[2][0]}."
        return f"{surname} {initials}"
    elif len(parts) == 2:
        # Формат: Фамилия И.
        surname = parts[0]
        initials = f"{parts[1][0]}."
        return f"{surname} {initials}"
    else:
        return full_name


def format_contract_title(tenant):
    if tenant.get("статус") == "ООО":
        name_short = tenant.get("наименование сокращенное", '')
        # name_short_clean = name_short.replace("ООО", "").replace('"', '').replace('«', '').replace('»', '').strip().replace("\u00A0", "-")
        name_short_clean = name_short.replace("ООО", "").replace('"', '').replace('«', '').replace('»', '').strip().replace("\u00A0", "\u2011")
        print('name short clean is', name_short_clean)
        title_contract = f"{tenant['номер договора']}\u2011{name_short_clean}"
        return title_contract, name_short_clean
    elif tenant.get("статус") == "ИП":
        name_full = tenant.get("наименование полное", '')
        if "ИП" in name_full:
            fio = name_full.replace("ИП", "").strip()
        fio_parts = fio.split()
        print(len(fio_parts), fio_parts)
        initials = ""
        if len(fio_parts) >= 3:
            # Фамилия, Имя, Отчество
            initials = fio_parts[0][0] + fio_parts[1][0] + fio_parts[2][0]
        elif len(fio_parts) == 2:
            # Фамилия, Имя
            initials = fio_parts[0][0] + fio_parts[1][0]
        elif len(fio_parts) == 1:
            # Только фамилия
            initials = fio_parts[0][0]
        else:
            initials = "XXX"
        title_contract = f"{tenant['номер договора']}-{initials.upper()}"
        return title_contract, initials.upper()


def clear_cell(cell):
    for paragraph in cell.paragraphs:
        p = paragraph._element
        p.getparent().remove(p)
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcPr.tcBorders = None


def add_hyperlink(paragraph, text, url):
    # Создаем объект гиперссылки
    part = paragraph.part
    r_id = part.relate_to(url, "http://openxmlformats.org", is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    # Создаем текстовый прогон (run) внутри гиперссылки
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    # Добавляем стандартный стиль оформления ссылки (синий цвет и подчеркивание)
    c = OxmlElement('w:color')
    c.set(qn('w:val'), '0000FF')
    rPr.append(c)
    u = OxmlElement('w:u')
    u.set(qn('w:val'), 'single')
    rPr.append(u)

    new_run.append(rPr)
    text_obj = OxmlElement('w:t')
    text_obj.text = text
    new_run.append(text_obj)
    hyperlink.append(new_run)

    paragraph._p.append(hyperlink)
    return hyperlink


def add_hyperlink_safe(paragraph, text, url):
    """Безопасное добавление гиперссылки в конец абзаца"""
    part = paragraph.part
    r_id = part.relate_to(url, "http://openxmlformats.org", is_external=True)

    # 1. Создаем узел гиперссылки
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    # 2. Создаем узел прогона (run)
    new_run = OxmlElement('w:r')

    # 3. Оформление (синий цвет и подчеркивание)
    rPr = OxmlElement('w:rPr')
    c = OxmlElement('w:color')
    c.set(qn('w:val'), '0563C1')  # Стандартный синий Word
    rPr.append(c)
    u = OxmlElement('w:u')
    u.set(qn('w:val'), 'single')
    rPr.append(u)
    new_run.append(rPr)

    # 4. Текст ссылки
    t = OxmlElement('w:t')
    t.text = text
    new_run.append(t)

    hyperlink.append(new_run)

    # ВАЖНО: добавляем гиперссылку в конец внутреннего XML-дерева абзаца
    paragraph._p.append(hyperlink)


def set_font_size_in_table(table, font_size=12):
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(font_size)


def generate_requisites_and_signs(doc):
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.allow_autofit = False
    table.columns[0].width = Cm(9)
    table.columns[1].width = Cm(9)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT if cell == row.cells[0] else WD_PARAGRAPH_ALIGNMENT.LEFT
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcPr.tcBorders = None
    # Левая ячейка (Арендатор)
    cell_tenant = table.cell(0, 0)
    clear_cell(cell_tenant)
    cell_tenant.add_paragraph("АРЕНДАТОР").runs[0].bold = True
    cell_tenant.add_paragraph()
    cell_tenant.add_paragraph(f"{tenant.get('наименование сокращенное', '')}")
    cell_tenant.add_paragraph(f"ИНН {tenant.get('ИНН', '')}")
    cell_tenant.add_paragraph(f"ОГРН {tenant.get('ОГРН', '')}")
    cell_tenant.add_paragraph(f"{tenant.get('юридический адрес', '')}")
    cell_tenant.add_paragraph(f"тел: {tenant.get('телефон', '')}")
    cell_tenant.add_paragraph(f"e-mail: {tenant.get('email', '')}")
    cell_tenant.add_paragraph()
    cell_tenant.add_paragraph(f"р/с {tenant.get('расчетный счет', '')}")
    cell_tenant.add_paragraph(f"в {tenant.get('наименование банка', '')}")
    cell_tenant.add_paragraph(f"к/с {tenant.get('корреспондентский счет', '')}")
    cell_tenant.add_paragraph(f"БИК: {tenant.get('БИК', '')}")
    cell_tenant.add_paragraph(f"{tenant.get('адрес банка', '')}")

    # Правая ячейка (Арендодатель)
    cell_landlord = table.cell(0, 1)
    clear_cell(cell_landlord)
    cell_landlord.add_paragraph("АРЕНДОДАТЕЛЬ").runs[0].bold = True
    cell_landlord.add_paragraph()
    cell_landlord.add_paragraph(f"{landlord.get('статус', '')} {landlord.get('имя', '')}")
    cell_landlord.add_paragraph(f"ИНН {landlord.get('ИНН', '')}")
    cell_landlord.add_paragraph(f"ОГРН ИП {landlord.get('ОГРНИП', '')} от {landlord.get('дата выдачи ОГРНИП', '')}")
    cell_landlord.add_paragraph(f"{landlord.get('индекс адреса', '')}, {landlord.get('адрес прописки', '')}")
    cell_landlord.add_paragraph(f"тел: {landlord.get('телефон', '')}")
    cell_landlord.add_paragraph(f"e-mail: {landlord.get('email', '')}")
    # cell_landlord.add_paragraph()
    # p = cell_landlord.paragraphs[7]
    # p.add_run("e-mail: ")
    # add_hyperlink_safe(p, f"{landlord.get('email', '')}", f"mailto:{landlord.get('email', '')}")
    # email_paragraph = cell_landlord.add_paragraph("e-mail: ")
    # add_hyperlink(email_paragraph, f"{landlord.get('email', '')}", f"mailto:{landlord.get('email', '')}")
    cell_landlord.add_paragraph()
    cell_landlord.add_paragraph(f"р/с {landlord.get('расчетный счет', '')}")
    cell_landlord.add_paragraph(f"в {landlord.get('наименование банка', '')}")
    cell_landlord.add_paragraph(f"к/с {landlord.get('корреспондентский счет', '')}")
    cell_landlord.add_paragraph(f"БИК: {landlord.get('БИК', '')}")
    cell_landlord.add_paragraph(f"{landlord.get('адрес банка', '')}")

    table.add_row()

    cell_tenant_sign = table.cell(1, 0)
    for paragraph in cell_tenant_sign.paragraphs:
        p = paragraph._element
        p.getparent().remove(p)
    tenant_director_fio = tenant.get('директор', '')
    formatted_fio = format_fio(tenant_director_fio)
    cell_tenant_sign.add_paragraph()
    cell_tenant_sign.add_paragraph()
    cell_tenant_sign.add_paragraph()
    cell_tenant_sign.add_paragraph(f"________________ /{formatted_fio}/")

    cell_landlord_sign = table.cell(1, 1)
    for paragraph in cell_landlord_sign.paragraphs:
        p = paragraph._element
        p.getparent().remove(p)
    landlord_fio = landlord.get('имя', '')
    formatted_landlord_fio = format_fio(landlord_fio)
    cell_landlord_sign.add_paragraph()
    cell_landlord_sign.add_paragraph()
    cell_landlord_sign.add_paragraph()
    cell_landlord_sign.add_paragraph(f"________________ /{formatted_landlord_fio}/")

    set_font_size_in_table(table, font_size=12)

    # Вставляем подпись во вторую ячейку (Арендодатель)
    add_floating_image(cell_landlord_sign.paragraphs[3], 'подпись.png', width=Cm(4.8), x_offset=0, y_offset=-250000)


def generate_signs(doc):
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.allow_autofit = False
    table.columns[0].width = Cm(9)
    table.columns[1].width = Cm(9)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT if cell == row.cells[0] else WD_PARAGRAPH_ALIGNMENT.LEFT
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcPr.tcBorders = None
    # Левая ячейка (Арендатор)
    cell_tenant = table.cell(0, 0)
    clear_cell(cell_tenant)
    cell_tenant.add_paragraph("Арендатор:")
    # cell_tenant.add_paragraph("Арендатор:").runs[0].bold = True
    # cell_tenant.add_paragraph()

    # Правая ячейка (Арендодатель)
    cell_landlord = table.cell(0, 1)
    clear_cell(cell_landlord)
    cell_landlord.add_paragraph("Арендодатель:")
    # cell_landlord.add_paragraph("Арендодатель").runs[0].bold = True
    # cell_landlord.add_paragraph()

    table.add_row()

    cell_tenant_sign = table.cell(1, 0)
    for paragraph in cell_tenant_sign.paragraphs:
        p = paragraph._element
        p.getparent().remove(p)
    tenant_director_fio = tenant.get('директор', '')
    formatted_fio = format_fio(tenant_director_fio)
    cell_tenant_sign.add_paragraph()
    cell_tenant_sign.add_paragraph()
    cell_tenant_sign.add_paragraph(f"________________ /{formatted_fio}/")

    cell_landlord_sign = table.cell(1, 1)
    for paragraph in cell_landlord_sign.paragraphs:
        p = paragraph._element
        p.getparent().remove(p)
    landlord_fio = landlord.get('имя', '')
    formatted_landlord_fio = format_fio(landlord_fio)
    cell_landlord_sign.add_paragraph()
    cell_landlord_sign.add_paragraph()
    cell_landlord_sign.add_paragraph(f"________________ /{formatted_landlord_fio}/")

    # set_font_size_in_table(table, font_size=12)

    # Вставляем подпись во вторую ячейку (Арендодатель)
    add_floating_image(cell_landlord_sign.paragraphs[2], 'подпись.png', width=Cm(4.8), x_offset=0, y_offset=-250000)

title_contract, name_short_clean = format_contract_title(tenant)
contract_number_str = tenant.get('номер договора', '').replace("/", "\u2011")

# ДОГОВОР
if contract:
    doc_contract = Document()

    sections = doc_contract.sections
    for section in sections:
        section.top_margin = Cm(1)
        section.bottom_margin = Cm(1)
        section.left_margin = Cm(1)
        section.right_margin = Cm(1)

    setup_document_styles(doc_contract, size_normal=12, size_heading_1=12, size_heading_2=12, line_spacing=1.15)

    doc_contract.add_heading("ДОГОВОР № " + title_contract + "\nпосуточной аренды квартиры", level=1)

    table = doc_contract.add_table(rows=1, cols=2)
    table.autofit = False
    table.allow_autofit = False
    table.columns[0].width = Cm(9)
    table.columns[1].width = Cm(9)

    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT if cell == row.cells[0] else WD_PARAGRAPH_ALIGNMENT.RIGHT
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcPr.tcBorders = None

    left_cell = table.cell(0, 0)
    left_paragraph = left_cell.paragraphs[0]
    left_paragraph.text = f"г. {city}"
    left_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    right_cell = table.cell(0, 1)
    right_paragraph = right_cell.paragraphs[0]
    right_paragraph.text = date
    right_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT


    # Добавляем абзац с данными сторон
    doc_contract.add_paragraph()
    paragraph = doc_contract.add_paragraph()
    add_text(paragraph, f"Мы, нижеподписавшиеся:")
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    paragraph = doc_contract.add_paragraph()
    add_text(paragraph, f"{landlord.get('статус', '')} {landlord.get('имя', '')}, паспорт: {landlord.get('паспорт', '')}, выдан {landlord.get('дата выдачи', '')} г. {landlord.get('кем выдан', '')}, зарегистрированный по адресу: {landlord.get('индекс адреса', '')}, {landlord.get('адрес прописки', '')}, в дальнейшем «Арендодатель», с одной стороны, и {tenant.get('наименование сокращенное', '')}")
    if tenant.get('статус', '') == 'ООО':
        print('проверка статуса')
        tenant_director_declined_roditelny = decline_fio(tenant.get('директор', ''))
        add_text(paragraph, f" в лице генерального директора {tenant_director_declined_roditelny}")
    add_text(paragraph, f", в дальнейшем «Арендатор», с другой стороны, заключили настоящий договор (далее «Договор») о нижеследующем:")

    # Добавляем разделы договора
    # paragraph = doc_contract.add_paragraph()
    doc_contract.add_heading("1. Предмет Договора.", level=2).add_run().bold = True
    doc_contract.add_paragraph().add_run(f"1.1.	Арендодатель предоставляет Арендатору в посуточную аренду квартиры для размещения персонала, а Арендатор обязуется выплачивать арендную плату в размере и в сроки, указанные в статье 5 Договора.")
    doc_contract.add_paragraph().add_run(f"1.2. Арендодатель обязуется передать Арендатору квартиры, оборудованные мебелью аксессуарами, бытовой техникой, включая постельное белье, полотенца и гигиенические принадлежности.")
    doc_contract.add_paragraph().add_run(f"1.3. Перечень квартир указывается в Приложении № 1 к Договору.")
    doc_contract.add_paragraph().add_run(f"1.4. Заселение обеспечивается на основании Заявки на заселение (Приложение № 2 к Договору). Заявка на размещение подписывается и скрепляется печатями (при наличии печати Арендодателя) Арендатора и Арендодателя.")
    doc_contract.add_paragraph().add_run(f"1.5. В стоимость посуточной арены включены расходы по оплате коммунальных услуг и использованию постельного белья в соответствии с количеством лиц, указанных в Заявке на размещение. НДС не предусмотрен.")
    doc_contract.add_paragraph().add_run(f"1.6. Расчетное время - 12.00 часов дня, следующего за днем заселения.")

    # paragraph = doc_contract.add_paragraph()
    doc_contract.add_heading("2. Обязанности сторон.", level=2).add_run().bold = True
    doc_contract.add_paragraph().add_run(f"2.1. Арендодатель обязуется:").bold = True
    doc_contract.add_paragraph().add_run(f"2.1.1. Предоставить в посуточную аренду Арендатору квартиры в пригодном для проживания состоянии.")
    doc_contract.add_paragraph().add_run(f"2.1.2. Предоставить квартиры на основании: (а) Свидетельства о регистрации квартиры или (б) Договора на аренду квартиры с правом сдачи в субаренду. Арендодатель гарантирует, что на момент заключения данного Договора квартира не продана, не подарена, не является предметом судебного спора, не находится под арестом, не сдана внаем и не имеет прочих обременений.")
    doc_contract.add_paragraph().add_run(f"2.1.3. Содержать установленные в квартирах технические устройства в соответствии с требованиями жилищного Кодекса РФ.")
    doc_contract.add_paragraph().add_run(f"2.1.4. Обеспечивать предоставление коммунальных и других услуг.")
    doc_contract.add_paragraph().add_run(f"2.1.5. До истечения срока действия Заявки на заселение не производить в отношении квартир обмен, продажу, дарение, сдачу под залог или в аренду одновременно нескольким физическим или юридическим лицам.")
    doc_contract.add_paragraph().add_run(f"2.1.6. Не изменять в течение срока действия Заявки на заселение арендную плату.")
    doc_contract.add_paragraph().add_run(f"2.1.7. Оплачивать счета за коммунальные услуги.")
    doc_contract.add_paragraph().add_run(f"2.1.8. В случае аварии немедленно принимать меры по ее устранению и в установленном порядке ставить вопрос о возмещении ущерба, причиненного аварией, если ущерб причинен по вине Арендатора.")
    paragraph = doc_contract.add_paragraph()
    paragraph = doc_contract.add_paragraph()
    doc_contract.add_paragraph().add_run(f"2.2. Арендатор обязуется:").bold = True
    doc_contract.add_paragraph().add_run(f"2.2.1. Использовать сданные ему по Договору посуточной аренды квартиры по назначению, то есть, для проживания персонала Арендатора.")
    doc_contract.add_paragraph().add_run(f"2.2.2. Не сдавать жилое помещение в субаренду и не использовать квартиры для проведения праздников, вечеринок и других видов коллективных собраний.")
    doc_contract.add_paragraph().add_run(f"2.2.3. Соблюдать Правила пользования жилыми помещениями, содержания жилого дома и придомовой территории, действующие в Российской Федерации.")
    doc_contract.add_paragraph().add_run(f"2.2.4. Незамедлительно сообщать Арендодателю о выявленных неисправностях элементов, оборудования и оснащения квартир и дома.")
    doc_contract.add_paragraph().add_run(f"2.2.5. Допускать в дневное время, а при авариях или иных форс-мажорных обстоятельствах и в ночное время в арендуемые квартиры представителей Арендодателя или самого Арендодателя, а также представителей предприятий по обслуживанию и ремонту жилья для проведения осмотра и ремонта конструкций и технических устройств квартир.")
    doc_contract.add_paragraph().add_run(f"2.2.6. Освободить арендуемые квартиры   по истечению срока аренды, указанного в заявке на заселение.")
    doc_contract.add_paragraph().add_run(f"2.2.7. В трехдневный срок уведомить Арендодателя об изменении своего юридического адреса и банковских реквизитов.")
    doc_contract.add_paragraph().add_run(f"2.3. Перед началом аренды квартиры Арендатор принимает от Арендодателя жилое помещение, указанное в Приложении №1 к Договору, а также все его оборудование, оснащение и элементы интерьера в соответствии с Актом приема-передачи (Приложение №3).  Акт подписывается Арендодателем и Представителем Арендатора (Статья 6 Договора).")

    # paragraph = doc_contract.add_paragraph()
    doc_contract.add_heading("3. Права сторон.", level=2).add_run().bold = True
    doc_contract.add_paragraph().add_run(f"3.1. Арендодатель имеет право:").bold = True
    doc_contract.add_paragraph().add_run(f"3.1.1. Требовать от Арендатора соблюдения Правил пользования жилыми помещениями, содержания жилого дома и придомовой территории, действующих в Российской Федерации.")
    doc_contract.add_paragraph().add_run(f"3.1.2. Требовать от Арендатора своевременного внесения платы за аренду.")
    doc_contract.add_paragraph().add_run(f"3.1.3. Осуществлять проверку порядка использования имущества в соответствии с условиями Договора.")
    doc_contract.add_paragraph().add_run(f"3.2. Арендатор имеет право:").bold = True
    doc_contract.add_paragraph().add_run(f"3.2.1. Требовать от Арендодателя своевременного и качественного выполнения комплекса работ по содержанию жилого дома, квартир и придомовых территорий, а также предоставления коммунальных и других услуг, предусмотренных Договором.")

    # paragraph = doc_contract.add_paragraph()
    doc_contract.add_heading("4. Ответственность сторон.", level=2).add_run().bold = True
    doc_contract.add_paragraph().add_run(f"4.1. Ответственность Арендодателя:").bold = True
    doc_contract.add_paragraph().add_run(f"4.1.1. Материальная ответственность Арендодателя перед Арендатором во всех случаях ограничена суммой арендной платы, указанной в Приложение №1к Договору.")
    doc_contract.add_paragraph().add_run(f"4.1.2 Арендодатель не несет ответственности за сохранность материальных и других ценностей Арендатора, находящихся в арендуемом помещении, а также автомобилей и других видов транспорта Арендатора, находящихся на парковке.")
    doc_contract.add_paragraph().add_run(f"4.2. Ответственность Арендатора:").bold = True
    doc_contract.add_paragraph().add_run(f"4.2.1. Арендатор обязуется бережно относиться к имуществу, находящемуся в арендуемой квартире, не курить внутри помещений, не распивать спиртные напитки.")
    doc_contract.add_paragraph().add_run(f"4.2.2. Арендатор несет имущественную ответственность за повреждение арендованного помещения, а также за ущерб, причиненный имуществу, связанный с нарушением правил технической эксплуатации, пожарной безопасности или в результате аварии, происшедшей по вине Арендатора.")
    doc_contract.add_paragraph().add_run(f"4.3. За нарушение условий Договора стороны несут ответственность, предусмотренную законодательством Российской Федерации.")

    # paragraph = doc_contract.add_paragraph()
    doc_contract.add_heading("5. Арендная плата.", level=2).add_run().bold = True
    doc_contract.add_paragraph().add_run(f"5.1. Арендатор пользуется арендуемыми помещениями на условиях посуточной аренды. Размер платы за посуточную аренду каждой квартиры указан в Приложении №1 к Договору. Арендуемые помещения предоставляются Арендатору на основании Заявки на заселение (Приложение № 2), в которой указывается период проживания.")
    doc_contract.add_paragraph().add_run(f"5.2. Валюта Договора и валюта платежей по Договору – российский рубль.")
    doc_contract.add_paragraph().add_run(f"5.3. Оплата аренды производится в форме предоплаты не менее, чем за 2 (два) дня до начала срока аренды, согласно Заявке на заселение, в соответствии со стоимостью посуточной аренды (Приложение №1) к Договору и согласно выставленному счету Арендодателя путем перечисления безналичных средств с расчетного счета Арендатора на расчетный счет Арендодателя.")
    doc_contract.add_paragraph().add_run(f"5.4. В период, оплаченный Арендатором, Арендодатель обязан держать квартиру свободной и готовой для размещения.")
    doc_contract.add_paragraph().add_run(f"5.5. Арендатор вправе уведомить Арендодателя об отказе от аренды квартиры после внесения предоплаты не менее, чем за 3 (три) дня до даты заезда, указанной в Заявке на размещение. В этом случае Арендодатель производит возврат денежных средств в размере 100% ранее перечисленной суммы. В случае, если Арендатор уведомит Арендодателя об отказе от аренды менее, чем за 2 (два) дня до даты начала аренды, Арендатор производит возврат денежных средств в размере 80% от ранее перечисленной суммы. В случае не уведомления Арендатором Арендодателя об отказе от аренды после перечисления денежных средств, услуга по предоставлению квартиры будет считаться выполненной в полном объеме, а ранее перечисленные денежные средства возврату не подлежат. Датой уведомления Арендодателя будет считаться дата направления соответствующего сообщения, переданного на электронный адрес, указанный в реквизитах.")
    doc_contract.add_paragraph().add_run(f"5.6. Арендодатель самостоятельно оплачивает из суммы арендной платы налог на доход физических лиц в соответствии с налоговым законодательством РФ.")
    doc_contract.add_paragraph().add_run(f"5.7. Обязанность по оплате Арендатором считается исполненной с момента списания денежных средств с расчетного счета Арендатора. Сканированная копия платежного поручения с печатью банка Арендатора направляется Арендодателю по электронной почте.")

    # paragraph = doc_contract.add_paragraph()
    doc_contract.add_heading("6. Представитель Арендатора.", level=2).add_run().bold = True
    doc_contract.add_paragraph().add_run(f"6.1. Стороны согласуют контактное лицо из числа инженерного состава Арендатора (ФИО, номер мобильного телефона, адрес электронной почты, далее «Представитель Арендатора»), представляющее интересы Арендатора и уполномоченное решать любые вопросы, возникающие в связи с исполнением Договора, в том числе, связанные с нарушением требований пунктов 2.2.1 и 2.2.2.")

    # paragraph = doc_contract.add_paragraph()
    doc_contract.add_heading("7. Условия заключения, изменения, расторжения, прекращения Договора.", level=2).add_run().bold = True
    doc_contract.add_paragraph().add_run(f"7.1. Договор вступает в силу с момента его подписания сторонами и действует в течение одного года.")
    doc_contract.add_paragraph().add_run(f"7.2. Изменение условий Договора аренды, его расторжение и прекращение допускаются по соглашению сторон.")
    doc_contract.add_paragraph().add_run(f"7.3. Договор может быть расторгнут по инициативе любой из сторон при наличии условий и в порядке, установленном законодательством Российской Федерации.")
    doc_contract.add_paragraph().add_run(f"7.4. Договор может быть расторгнут по решению суда в соответствии с действующим законодательством.")
    paragraph = doc_contract.add_paragraph()
    paragraph = doc_contract.add_paragraph()
    doc_contract.add_paragraph().add_run(f"7.5. Договор может быть расторгнут по требованию Арендодателя в следующих случаях:")
    subparagraphs = [
        "однократное или неоднократное нарушение Арендатором правил использования имущества или использование имущества не по назначению с существенным нарушением условий Договора;",
        "невнесение Арендатором арендной платы более двух раз подряд после истечения обусловленных Договором сроков платежа;",
        "несоблюдение Арендатором технических правил эксплуатации помещений, правил санитарной и противопожарной безопасности;",
        "умышленное ухудшение Арендатором состояния имущества."
    ]
    for subparagraph in subparagraphs:
        paragraph = doc_contract.add_paragraph(style='List')
        run = paragraph.add_run(f"\u2014 {subparagraph}")
        paragraph.paragraph_format.left_indent = Cm(1.5)
    doc_contract.add_paragraph().add_run(f"7.6. Возникшие при исполнении Договора споры между сторонами разрешаются в порядке, установленном законодательством Российской Федерации.")
    doc_contract.add_paragraph().add_run(f"7.7. Договор составлен в 2-х экземплярах, один из которых находится у Арендодателя, другой – у Арендатора.")
    doc_contract.add_paragraph().add_run(f"7.8. Условия Договора по посуточной аренде квартир сохраняют свою силу в течение всего срока действия Договора.")

    paragraph = doc_contract.add_paragraph()
    doc_contract.add_heading("8. Реквизиты и подписи Сторон.", level=2).add_run().bold = True

    # doc_contract.add_paragraph().add_heading("8. Реквизиты и подписи Сторон.", level=2).add_run().bold = True

    doc_contract.add_paragraph()

    generate_requisites_and_signs(doc_contract)

    # Добавляем разрыв раздела с новой страницы перед приложением
    paragraph = doc_contract.add_paragraph()
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    sectPr = OxmlElement('w:sectPr')
    pPr.append(sectPr)
    br = OxmlElement('w:br')
    br.set(qn('w:type'), 'page')
    p.append(br)

    # Настройка номеров страниц
    sections = doc_contract.sections
    for section in sections:
        footer = section.footer
        for paragraph in footer.paragraphs:
            p = paragraph._element
            p.getparent().remove(p)
        paragraph = footer.add_paragraph()
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = paragraph.add_run()
        fldChar = OxmlElement('w:fldChar')
        fldChar.set(qn('w:fldCharType'), 'begin')
        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = 'PAGE'
        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar)
        run._r.append(instrText)
        run._r.append(fldChar2)

    # Настройка нового раздела (для приложения) без нумерации
    new_section = doc_contract.sections[-1]

    # Отключаем связь с предыдущим колонтитулом
    new_section.different_first_page_header_footer = False
    new_section.header.is_linked_to_previous = False
    new_section.footer.is_linked_to_previous = False
    new_footer = new_section.footer
    # Очищаем колонтитул для нового раздела
    for paragraph in new_footer.paragraphs:
        p = paragraph._element
        p.getparent().remove(p)

    # Устанавливаем поля: 1 см со всех сторон
    sections = doc_contract.sections
    for section in sections:
        section.top_margin = Cm(1)
        section.bottom_margin = Cm(1)
        section.left_margin = Cm(1)
        section.right_margin = Cm(1)

    font_size = Pt(14)
    (paragraph := doc_contract.add_paragraph()).add_run("Приложение №1").font.size = font_size; paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
    (paragraph := doc_contract.add_paragraph()).add_run("к Договору посуточной аренды квартир").font.size = font_size; paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
    (paragraph := doc_contract.add_paragraph()).add_run(f"№ {title_contract} от {date}").font.size = font_size; paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
    doc_contract.add_paragraph()
    doc_contract.add_paragraph()
    (paragraph := doc_contract.add_paragraph()).add_run("ПЕРЕЧЕНЬ").font.size, (paragraph.runs[0]).font.bold, paragraph.alignment = Pt(14), True, WD_PARAGRAPH_ALIGNMENT.CENTER
    (paragraph := doc_contract.add_paragraph()).add_run("квартир для заселения.").font.size, (paragraph.runs[0]).font.bold, paragraph.alignment = Pt(14), True, WD_PARAGRAPH_ALIGNMENT.CENTER
    doc_contract.add_paragraph()

    total_apartments = len(apartments)
    for i, apartment in enumerate(apartments):
        text = apartment.strip()
        separator = '.' if i == total_apartments - 1 else ';'
        paragraph = doc_contract.add_paragraph(f"{text}{separator}", style='List Number')
        for run in paragraph.runs:
            run.font.size = font_size
    doc_contract.add_paragraph()
    doc_contract.add_paragraph()

    generate_requisites_and_signs(doc_contract)

    date_str = pd.to_datetime(tenant['дата договора']).strftime('%Y-%m-%d')
    contract_filename_docx = f"Д_{contract_number_str}_{name_short_clean}_{date_str}.docx"
    doc_contract.save(os.path.join(path, contract_filename_docx))

    contract_filename_pdf = f"Д_{contract_number_str}_{name_short_clean}_{date_str}.pdf"
    if pdf:
        convert_docx_to_pdf(
            os.path.join(path, contract_filename_docx),
            os.path.join(path, contract_filename_pdf)
        )

    print(f"Договор успешно сгенерирован: {os.path.abspath(os.path.join(path, contract_filename_docx))}")
    if pdf:
        print(f"PDF-версия договора: {os.path.abspath(os.path.join(path, contract_filename_pdf))}")



# АКТ
if not certificate_without_contract:
    certificate_number = tenant.get('номер акта', '')
else:
    certificate_number = f"{title_contract}\u2011{tenant.get('номер акта', '')}"

# certificate_number_str = certificate_number.replace("/", "\u2011")
certificate_number_str = tenant.get('номер акта', '')

certificate_day = tenant['дата акта'].day
certificate_month = months[tenant['дата акта'].month]
certificate_year = tenant['дата акта'].year
certificate_date = f"{certificate_day} {certificate_month} {certificate_year} г."

# Создаем новый документ для акта
doc_certificate = Document()

# Устанавливаем поля: 1 см со всех сторон
sections = doc_certificate.sections
for section in sections:
    section.top_margin = Cm(1)
    section.bottom_margin = Cm(1)
    section.left_margin = Cm(1.25)
    section.right_margin = Cm(1.25)

# Настройка стилей документа
setup_document_styles(doc_certificate, size_normal=13, size_heading_1=14, size_heading_2=14, line_spacing=1.05)


(p := doc_certificate.add_paragraph()).add_run(f"Акт №{certificate_number}"); p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER; p.paragraph_format.line_spacing = 1.15
if not certificate_without_contract:
    (p := doc_certificate.add_paragraph()).add_run("об оказании услуг по Договору посуточной аренды квартир"); p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER; p.paragraph_format.line_spacing = 1.15
    (p := doc_certificate.add_paragraph()).add_run(f"№ {title_contract} от {date}"); p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER; p.paragraph_format.line_spacing = 1.15
else:
    (p := doc_certificate.add_paragraph()).add_run("об оказании услуг по посуточной аренде квартир."); p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER; p.paragraph_format.line_spacing = 1.15
# doc_certificate.add_paragraph()
(p := doc_certificate.add_paragraph()).add_run(); p.paragraph_format.line_spacing = 1.15



# Добавляем таблицу для выравнивания города и даты
table = doc_certificate.add_table(rows=1, cols=2)
table.autofit = False
table.allow_autofit = False
table.columns[0].width = Cm(9)  # Левая колонка
table.columns[1].width = Cm(9)  # Правая колонка

# Убираем границы таблицы
for row in table.rows:
    for cell in row.cells:
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT if cell == row.cells[0] else WD_PARAGRAPH_ALIGNMENT.RIGHT
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcPr.tcBorders = None  # Убираем границы

# Заполняем таблицу с выравниванием
left_cell = table.cell(0, 0)
left_paragraph = left_cell.paragraphs[0]
left_paragraph.text = f"г. {city}"
left_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

right_cell = table.cell(0, 1)
right_paragraph = right_cell.paragraphs[0]
right_paragraph.text = certificate_date
right_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT


# Добавляем абзац с данными сторон
doc_certificate.add_paragraph()
paragraph = doc_certificate.add_paragraph()
add_text(paragraph, f"Мы, нижеподписавшиеся:")
paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
paragraph = doc_certificate.add_paragraph()
add_text(paragraph, f"{landlord.get('статус', '')} {landlord.get('имя', '')}, в\u00A0дальнейшем «Арендодатель», с\u00A0одной стороны, и\u00A0{tenant.get('наименование сокращенное', '')}")
if tenant.get('статус', '') == 'ООО':
    print('проверка статуса')
    tenant_director_declined_roditelny = decline_fio(tenant.get('директор', ''))
    add_text(paragraph, f" в\u00A0лице генерального директора {tenant_director_declined_roditelny}")
add_text(paragraph, f", в\u00A0дальнейшем «Арендатор», с\u00A0другой стороны, составили настоящий акт о\u00A0нижеследующем. ")
if not certificate_without_contract:
    add_text(paragraph, f"Арендодателем по\u00A0Договору посуточной аренды квартир №\u00A0{title_contract} от\u00A0{date} оказаны Арендатору следующие услуги:")
else:
    add_text(paragraph, f"Арендодателем оказаны Арендатору следующие услуги:")


doc_certificate.add_paragraph()



df_services_data = pd.DataFrame(services_data, columns=['номер счета', 'дата счета', 'количество', 'цена'])
df_services_data['сумма'] = df_services_data['количество'] * df_services_data['цена']
total_sum = float(df_services_data['сумма'].sum())

table = doc_certificate.add_table(rows=1, cols=6)
table.autofit = False
table.allow_autofit = False

header_cells = table.rows[0].cells
header_cells[0].text = '№'
header_cells[1].text = 'Наименование работы (услуги)'
header_cells[2].text = 'Кол-во'
header_cells[3].text = 'Ед.Изм.'
header_cells[4].text = 'Цена'
header_cells[5].text = 'Сумма'

for cell in table.rows[0].cells:
    cell.paragraphs[0].alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

row_cells = table.add_row().cells
row_cells[1].text = f"Аренда квартиры в г. Люберцы (МО)"


row_cells = table.add_row().cells

for index, row in df_services_data.iterrows():
    (p := row_cells[0].paragraphs[0] if index == 0 else row_cells[0].add_paragraph()).add_run(str(index + 1)); p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    (p := row_cells[1].paragraphs[0] if index == 0 else row_cells[1].add_paragraph()).add_run(f"(Счет № {row['номер счета']} от {row['дата счета']} г.)").italic = True; p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
    (p := row_cells[2].paragraphs[0] if index == 0 else row_cells[2].add_paragraph()).add_run(str(row['количество'])); p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    (p := row_cells[4].paragraphs[0] if index == 0 else row_cells[4].add_paragraph()).add_run(f"{row['цена']:,.2f}".replace(',', ' ').replace('.', ',')); p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    (p := row_cells[5].paragraphs[0] if index == 0 else row_cells[5].add_paragraph()).add_run(f"{row['сумма']:,.2f}".replace(',', ' ').replace('.', ',')); p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER


(paragraph := row_cells[3].paragraphs[0]).add_run(unit); paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
row_cells[3].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


widths = [Cm(0.75), Cm(9.0), Cm(2.0), Cm(2.2), Cm(2.5), Cm(3.0)]

table.autofit = False

for i, width in enumerate(widths):
    table.columns[i].width = width
    for cell in table.columns[i].cells:
        cell.width = width

table.style = 'Table Grid'


def set_border(cell, side, val='nil'):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn('w:tcBorders'))
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)

    # Находим или создаем нужную сторону (top, bottom, left, right)
    border = OxmlElement(f'w:{side}')
    border.set(qn('w:val'), val)
    tcBorders.append(border)

# 1. У второй строки (индекс 1) убираем НИЗ
for cell in table.rows[1].cells:
    set_border(cell, 'bottom', 'nil')

# 2. У третьей строки (индекс 2) убираем ВЕРХ
for cell in table.rows[2].cells:
    set_border(cell, 'top', 'nil')

row_cells = table.add_row().cells
# Объединяем ячейки для текста "Итого:"
start_cell = row_cells[0]
end_cell = row_cells[4]
start_cell.merge(end_cell)



merged_cell = start_cell

(p := merged_cell.paragraphs[0]).add_run(f"Итого:").bold = True; p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
(p := merged_cell.add_paragraph()).add_run(f"Без налога (НДС)").bold = True; p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

(p := row_cells[5].paragraphs[0]).add_run(f"{total_sum:,.2f}".replace(',', ' ').replace('.', ',')).bold = True; p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
row_cells[5].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

set_border(merged_cell, 'bottom', 'nil')
set_border(merged_cell, 'left', 'nil')

total_sum_int = int(total_sum)
doc_certificate.add_paragraph()

sum_in_words = num2words(total_sum, to='currency', currency='RUB', lang='ru').replace('ноль', '00').replace(',', '').replace(' копеек', '\u00A0коп')
(p := doc_certificate.add_paragraph()).add_run(f"Всего оказано услуг на сумму {sum_in_words}.").bold = True; p.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
# doc_certificate.add_paragraph()
(p := doc_certificate.add_paragraph()).add_run(f"Вышеперечисленные услуги оказаны полностью и в срок. Арендатор претензий по\u00A0объему, качеству и срокам оказания услуг не имеет."); p.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY
doc_certificate.add_paragraph()

if not certificate_without_contract:
    generate_signs(doc_certificate)
else:
    generate_requisites_and_signs(doc_certificate)



date_certificate_str = pd.to_datetime(tenant['дата акта']).strftime('%Y-%m-%d')

certificate_filename_docx = f"АКТ_N{certificate_number_str}_{contract_number_str}_{name_short_clean}_{date_certificate_str}.docx"
doc_certificate.save(os.path.join(path, certificate_filename_docx))

certificate_filename_pdf = f"АКТ_N{certificate_number_str}_{contract_number_str}_{name_short_clean}_{date_certificate_str}.pdf"
if pdf:
    convert_docx_to_pdf(
        os.path.join(path, certificate_filename_docx),
        os.path.join(path, certificate_filename_pdf)
    )

print(f"Акт № {certificate_number} успешно сгенерирован: {os.path.abspath(os.path.join(path, certificate_filename_docx))}")
if pdf:
    print(f"PDF-версия акта: {os.path.abspath(os.path.join(path, certificate_filename_pdf))}")

