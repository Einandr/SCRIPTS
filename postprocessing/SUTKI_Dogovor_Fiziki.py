import os
from datetime import datetime

import pandas as pd

from utils_documents import (
    months,
    decline_word,
    num_to_words,
    decline_fio_pytrovich,
    setup_document_styles,
    add_text,
    add_floating_image,
    convert_docx_to_pdf
)

from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor, Inches
from docx.oxml.ns import qn, nsdecls
from docx.oxml import OxmlElement


# TODO: проработать завертку в исполняемый файл


# Путь к рабочей директории
path = r'C:\Users\YA\Desktop\СУТКИ\Контрагенты\ДОГОВОРЫ_ФИЗЛИЦО_2026'
excel_file = 'Физики.xlsx'

# Номер строки в EXCEL на кого делаем договор
row_index = 31

acceptance_certificate = False

os.chdir(path)
df = pd.read_excel(os.path.join(path, excel_file))

tenant = df.iloc[row_index-2].to_dict()

if 'индекс адреса прописки' in tenant:
    index = tenant['индекс адреса прописки']
    if isinstance(index, (int, float)):
        tenant['индекс адреса прописки'] = str(int(index))

if 'индекс адреса квартиры' in tenant:
    index = tenant['индекс адреса квартиры']
    if isinstance(index, (int, float)):
        tenant['индекс адреса квартиры'] = str(int(index))

# Неразрывные дефисы в телефоне
tenant['телефон'] = tenant['телефон'].replace('-', '\u2011')

# Неразрывные пробелы в адресе
non_breaking_words_after = ['г.', 'д.', 'c.', 'х.', 'п.', 'пос.', 'ст-ца', 'пгт.', 'ст.', 'ул.', 'пер.', 'б-р', 'наб.', 'пл.', 'кв.', 'оф.', 'стр.', 'корп.', 'помещ.', 'респ.', 'р-н', 'мкр.', 'кв-л']
non_breaking_words_before = ['обл.', 'край', 'пр-кт']

address_tenant = tenant['адрес прописки']
address_flat = tenant['адрес квартиры']
for word in non_breaking_words_after:
    address_tenant = address_tenant.replace(f'{word} ', f'{word}\u00A0')
    address_flat = address_flat.replace(f'{word} ', f'{word}\u00A0')
for word in non_breaking_words_before:
    address_tenant = address_tenant.replace(f' {word}', f'\u00A0{word}')
    address_flat = address_flat.replace(f' {word}', f'\u00A0{word}')
tenant['адрес прописки'] = address_tenant
tenant['адрес квартиры'] = address_flat

# Неразрывные дефисы в адресе, например Южно-Сахалинск
tenant['адрес прописки'] = tenant['адрес прописки'].replace('-', '\u2011')

rent_length = (pd.to_datetime(tenant['выезд']) - pd.to_datetime(tenant['заезд'])).days
rent_cost_prepayment = tenant['предоплата']
rental_cost_onsite = tenant['оплата при заезде']
rent_cost_overall = rent_cost_prepayment + rental_cost_onsite

# Проверка корректности оплаты
daily_price = tenant.get('цена суток', 0)
expected_cost = rent_length * daily_price

if abs(rent_cost_overall - expected_cost) > 0.02:  # Допустимое отклонение для учета ошибок округления
    raise ValueError(f"Ошибка: Сумма предоплаты и оплаты при заезде ({rent_cost_overall}) не равна {rent_length} * {daily_price} = {expected_cost}")

# Склонение слов
rent_length_word = decline_word(rent_length, 'сутки', 'суток', 'суток')
rent_cost_prepayment_word = decline_word(rent_cost_prepayment, 'рубль', 'рубля', 'рублей')
rent_cost_onsite_word = decline_word(rental_cost_onsite, 'рубль', 'рубля', 'рублей')
rent_cost_overall_word = decline_word(rent_cost_overall, 'рубль', 'рубля', 'рублей')
rent_price_daily_word = decline_word(daily_price, 'рубль', 'рубля', 'рублей')

# Преобразование суммы в слова
rent_cost_overall_translite = num_to_words(rent_cost_overall)

# Функция для получения даты в формате "16 марта 2026 г."
# def format_date(date):
#     day = date.day
#     month = MONTHS[date.month]
#     year = date.year
#     return f"{day} {month} {year} г."
day = tenant['заезд'].day
month = months[tenant['заезд'].month]
year = tenant['заезд'].year

# Дата и город
date = f"{day} {month} {year} г."
city = tenant.get('город', '')

# Данные арендодателя
landlord = {
    'имя': 'Яковчук Андрей Юрьевич',
    'ИНН': '262409090402',
    'дата рождения': '20.10.1989',
    'паспорт': '0709 294154',
    'дата выдачи': '24.10.2009',
    'кем выдан': 'отделом УФМС РФ по\u00A0Ставропольскому краю в г.\u00A0Будённовске и Будённовском районе',
    'код подразделения': '260\u2011006',
    'индекс адреса': '143442',
    'адрес прописки': 'Московская\u00A0обл., г.\u00A0Красногорск, пгт.\u00A0Сабурово, ул.\u00A0Садовая, д.\u00A012, кв.\u00A024',
    'телефон': '+7\u2011926\u20113400187'
}

rent_start_time = '14\u00A0часов\u00A000\u00A0минут'
rent_end_time = '12\u00A0часов\u00A000\u00A0минут'

# Создаём DOCX-документ для договора
doc_contract = Document()

# Устанавливаем поля: 1 см со всех сторон
sections = doc_contract.sections
for section in sections:
    section.top_margin = Cm(1)
    section.bottom_margin = Cm(1)
    section.left_margin = Cm(1)
    section.right_margin = Cm(1)

# Настройка стилей документа
setup_document_styles(doc_contract, size_normal=10.5, size_heading_1=14, size_heading_2=12, line_spacing=1.0)

# Добавляем заголовок
doc_contract.add_heading(level=1).add_run("ДОГОВОР\nпосуточной аренды квартиры")

# Добавляем таблицу для выравнивания города и даты
table = doc_contract.add_table(rows=1, cols=2)
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
left_paragraph.text = city
left_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

right_cell = table.cell(0, 1)
right_paragraph = right_cell.paragraphs[0]
right_paragraph.text = date
right_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

# Добавляем абзац с данными сторон
paragraph = doc_contract.add_paragraph()
add_text(paragraph, "Гр. ")
add_text(paragraph, f"{landlord.get('имя', '')}", bold=True)
add_text(paragraph, f", ИНН: ")
add_text(paragraph, f"{landlord.get('ИНН', '')}", bold=True)
add_text(paragraph, f", паспорт: ")
add_text(paragraph, f"{landlord.get('паспорт', '')}", bold=True)
add_text(paragraph, f", выданный {landlord.get('дата выдачи', '')} г. {landlord.get('кем выдан', '')}, зарегистрированный по адресу: {landlord.get('индекс адреса', '')}, {landlord.get('адрес прописки', '')}, тел: {landlord.get('телефон', '')}, именуемый в дальнейшем «Арендодатель», с\u00A0одной стороны, и гр. ")
add_text(paragraph, f"{tenant.get('имя', '')}", bold=True)
add_text(paragraph, f", паспорт: ")
add_text(paragraph, f"{tenant.get('паспорт', '')}", bold=True)
add_text(paragraph, f", выданный {tenant.get('дата выдачи', '').strftime('%d.%m.%Y')} г. {tenant.get('кем выдан', '')}, зарегистрированный по адресу: {tenant.get('индекс адреса прописки', '')}, {tenant.get('адрес прописки', '')}, тел: {tenant.get('телефон', '')}, именуемый в дальнейшем «Арендатор», с\u00A0другой стороны, заключили настоящий договор о нижеследующем:")

# Добавляем разделы договора
doc_contract.add_heading("1. ПРЕДМЕТ ДОГОВОРА", level=2).add_run().bold = True
paragraph_1_1 = doc_contract.add_paragraph()
add_text(paragraph_1_1, f"1.1. Арендодатель предоставляет Арендатору квартиру общей площадью {tenant.get('площадь квартиры', '')} кв.м., расположенную по адресу: {tenant.get('индекс адреса квартиры', '')}, {tenant.get('адрес квартиры', '')}, в посуточную аренду на ")
add_text(paragraph_1_1, f"{rent_length} {rent_length_word}", bold=True)
add_text(paragraph_1_1, ", с ")
add_text(paragraph_1_1, f"{tenant.get('заезд', '').strftime('%d.%m.%Y')}", bold=True)
add_text(paragraph_1_1, f", {rent_start_time}, по ")
add_text(paragraph_1_1, f"{tenant.get('выезд', '').strftime('%d.%m.%Y')}", bold=True)
add_text(paragraph_1_1, f", {rent_end_time}. Возможно продление срока аренды по согласованию сторон. Квартира оборудована мебелью, аксессуарами и бытовой техникой.")
doc_contract.add_paragraph().add_run(f"1.2. Квартира передается для использования в качестве жилого помещения для Арендатора и совместно проживающих с ним лиц, всего не более 4 человек.")
paragraph_1_3 = doc_contract.add_paragraph()
add_text(paragraph_1_3, f"1.3. По соглашению сторон договором устанавливается плата за посуточную аренду квартиры в размере ")
add_text(paragraph_1_3, f"{daily_price} {rent_price_daily_word}", bold=True)
add_text(paragraph_1_3, f" в сутки, в состав которой включены расходы по оплате коммунальных услуг и аренде постельного белья по количеству лиц, указанных в данном договоре. Общая сумма арендной платы составляет ")
add_text(paragraph_1_3, f"{rent_cost_overall} ({rent_cost_overall_translite}) {rent_cost_overall_word}", bold=True)
add_text(paragraph_1_3, " (без учета срока продления). НДС не предусмотрен.")
doc_contract.add_paragraph().add_run("1.4. Расчётное время: 12:00. Ранний заезд и поздний выезд согласовываются и оплачиваются дополнительно.")

doc_contract.add_heading("2. ОБЯЗАННОСТИ СТОРОН", level=2).add_run().bold = True
doc_contract.add_paragraph().add_run("2.1. Арендодатель обязуется:").bold = True
doc_contract.add_paragraph().add_run("2.1.1. Предоставить в посуточную аренду Арендатору квартиру в пригодном для проживания состоянии, включая постельное белье, полотенца и гигиенические принадлежности.")
doc_contract.add_paragraph().add_run("2.1.2. Осуществлять содержание дома и технических устройств квартиры в соответствии с требованиями Жилищного Кодекса РФ.")
doc_contract.add_paragraph().add_run("2.1.3. Обеспечивать предоставление коммунальных и других услуг.")
doc_contract.add_paragraph().add_run("2.1.4. До истечения срока действия настоящего Договора не производить обмен, продажу, дарение квартиры, сдавать под залог и в аренду вышеуказанное жилое помещение (предмет настоящего Договора) одновременно нескольким физическим или юридическим лицам.")
doc_contract.add_paragraph().add_run("2.1.5. В течение срока действия настоящего Договора не изменять арендную плату.")
doc_contract.add_paragraph().add_run("2.1.6. Оплачивать счета на коммунальные услуги.")
doc_contract.add_paragraph().add_run("2.2. Арендатор обязуется:").bold = True
doc_contract.add_paragraph().add_run("2.2.1. Использовать сданную ему по договору посуточной аренды квартиру по назначению, то есть для проживания лиц, указанных в п.1.2 настоящего Договора. Арендатор обязуется не сдавать жилое помещение в субаренду или использовать жилое помещение для проведения праздников, вечеринок и других видов коллективных собраний. Факт подписания данного договора одновременно является подтверждением того, Арендатор принял от Арендодателя жилое помещение, указанное в п.1.1 и все его оборудование, оснащение и элементы интерьера в технически исправном состоянии, и без наружных повреждений.")
doc_contract.add_paragraph().add_run("2.2.2. Соблюдать Правила пользования жилыми помещениями, содержания жилого дома и придомовой территории в РФ.")
doc_contract.add_paragraph().add_run("2.2.3. Незамедлительно сообщать Арендодателю о выявленных неисправностях элементов, оборудования и оснащения квартиры и дома.")
doc_contract.add_paragraph().add_run("2.2.4. Допускать в дневное время, а при авариях или иных форс мажорных обстоятельствах и в ночное время, в арендуемую квартиру работников Арендодателя или самого Арендодателя, а также представителей предприятий по обслуживанию и ремонту жилья для проведения осмотра и ремонта конструкций и технических устройств квартиры (по согласованию сторон).")
doc_contract.add_paragraph().add_run("2.2.5. Освободить арендуемую квартиру по истечении обусловленного в настоящем договоре срока аренды.")
doc_contract.add_paragraph().add_run("2.2.6. Оплатить в соответствии с действительными расходами Арендодателя любые повреждения жилого помещения и/или оснащения, мебели и оборудования квартиры, возникшие по вине Арендатора.")
# doc_contract.add_paragraph()
# doc_contract.add_paragraph()
# doc_contract.add_paragraph()
# doc_contract.add_paragraph()

doc_contract.add_heading("3. ПРАВА СТОРОН", level=2).add_run().bold = True
doc_contract.add_paragraph().add_run("3.1. Арендодатель имеет право:").bold = True
doc_contract.add_paragraph().add_run("3.1.1. Требовать от Арендатора соблюдения Правил пользования жилыми помещениями, содержания жилого дома и придомовой территории РФ.")
doc_contract.add_paragraph().add_run("3.1.2. Требовать от Арендатора своевременного внесения платы за аренду.")
doc_contract.add_paragraph().add_run("3.1.3. Требовать от Арендатора освобождения жилого помещения по истечении срока договора аренды.")
doc_contract.add_paragraph().add_run("3.1.4. Предоставить Арендатору дополнительные услуги такие как трансферты по городу, предоставление автомобиля с водителем, аренда сотового телефона, предоставление сопровождающего, экскурсионные услуги.")
doc_contract.add_paragraph().add_run("3.2. Арендатор имеет право:").bold = True
doc_contract.add_paragraph().add_run("3.2.1. Арендатор имеет право производить осмотр сданного в наем жилого помещения и имущества на предмет сохранности и санитарного состояния, предварительно уведомив и согласовав время визита с Арендодателем.")
doc_contract.add_paragraph().add_run("3.2.2. Требовать от Арендодателя своевременного и качественного выполнения комплекса работ по содержанию жилого дома, квартиры и придомовой территории, а также предоставления коммунальных и других услуг, предусмотренных договором аренды.")

doc_contract.add_heading("4. ОТВЕТСТВЕННОСТЬ СТОРОН", level=2).add_run().bold = True
doc_contract.add_paragraph().add_run("4.1. Ответственность Арендодателя:").bold = True
doc_contract.add_paragraph().add_run("4.1.1. Материальная ответственность Арендодателя перед Арендатором во всех случаях ограничена суммой Общей арендной платы, указанной в п.1.2 настоящего Договора, превышать которую сумма ответственности Арендодателя не может.")
doc_contract.add_paragraph().add_run("4.1.2. Арендодатель не несет ответственности за сохранность вещей, ценностей и документов Арендатора, оставленных в жилом помещении, равно как авто и других видов транспорта Арендатора, паркуемых вблизи жилого помещения.")
doc_contract.add_paragraph().add_run("4.2. Ответственность Арендатора:").bold = True
doc_contract.add_paragraph().add_run("4.2.1. Арендатор возмещает Арендодателю материальный ущерб, причиненный в результате невыполнения обязанностей, предусмотренных в п.2.2.1 и п.2.2.2 настоящего договора, в установленном законом порядке.")
doc_contract.add_paragraph().add_run("4.2.2. При расторжении настоящего Договора досрочно по инициативе Арендатора, сумма за неиспользованные сутки проживания Арендодателем не возвращается.")

doc_contract.add_heading("5. УСЛОВИЯ ОПЛАТЫ", level=2).add_run().bold = True
doc_contract.add_paragraph().add_run("5.1. Оплата посуточной аренды квартиры производится единовременно за весь срок проживания не позднее первого дня аренды, указанного в п.1.1. При отказе произвести оплату в вышеуказанный срок настоящий договор аренды утрачивает свою силу.")
paragraph_5_2 = doc_contract.add_paragraph()
add_text(paragraph_5_2, "5.2. При подписании Договора Арендатором вносится Арендодателю залоговая сумма (за потерю ключей и/или ущерб имуществу) ")
add_text(paragraph_5_2, f"{tenant.get('залог', 0)} рублей", bold=True)
add_text(paragraph_5_2, ", которая возвращается Арендатору при выезде его из квартиры.")
doc_contract.add_paragraph().add_run("5.3. Оплата производится посредством внесения наличных денежных средств Арендодателю, или посредством безналичного перечисления денежных средств на расчетный счет Арендодателя по согласованию сторон.")
doc_contract.add_paragraph().add_run("5.4. По требованию Арендодателя предварительная оплата одних первых суток аренды жилого помещения по цене, указанной в п.1.2 настоящего Договора производится в качестве депозита путем безналичного перечисления денежных средств на счет Арендодателя.")
doc_contract.add_paragraph().add_run("5.4.1. В случае расторжения настоящего Договора по инициативе Арендатора по любым причинам, депозит, указанный в п.5.4 настоящего Договора Арендатору не возвращается, если расторжение настоящего Договора произошло в срок менее чем за 1 суток до даты начала аренды, указанной в п.1.1. В иных случаях, Арендодатель возвращает Арендатору 50% от суммы внесенного депозита.")

doc_contract.add_heading("6. ЗАКЛЮЧИТЕЛЬНЫЕ УСЛОВИЯ ПОСУТОЧНОЙ АРЕНДЫ КВАРТИРЫ", level=2).add_run().bold = True
doc_contract.add_paragraph().add_run("6.1. Настоящий договор может быть расторгнут по инициативе любой из сторон при наличии условий и в порядке, предусмотренном законодательством.")
doc_contract.add_paragraph().add_run("6.2. Возникшие при исполнении настоящего договора споры между сторонами разрешаются в установленном законом порядке.")
doc_contract.add_paragraph().add_run("6.3. Настоящий договор составлен в 2-х экземплярах, один из которых находится у Арендодателя, другой – у Арендатора.")
doc_contract.add_paragraph().add_run("6.4. Договор вступает в силу с момента полной оплаты Арендатором всей суммы стоимости аренды. Бронирование жилого помещения, оплата стоимости депозита или аренды и/или заезд в жилое помещение означает принятие Арендатором условий настоящего Договора.")
doc_contract.add_paragraph().add_run("6.5. Условия настоящего договора по посуточной аренде квартиры сохраняют свою силу на весь срок действия договора.")
doc_contract.add_paragraph().add_run("6.6. Настоящий договор может быть продлен по согласованию сторон при условии внесения дополнительной арендной платы.")
doc_contract.add_paragraph().add_run("6.7. С документами Арендодателя Арендатор ознакомлен и претензий к нему не имеет.")

# Отступы перед подписями
doc_contract.add_paragraph()
doc_contract.add_paragraph()
doc_contract.add_paragraph()
doc_contract.add_paragraph()

# Создаем таблицу 1x2
table = doc_contract.add_table(rows=1, cols=2)
table.autofit = False
table.allow_autofit = False
table.columns[0].width = Cm(9)
table.columns[1].width = Cm(9)

# Убираем границы таблицы
for row in table.rows:
    for cell in row.cells:
        for paragraph in cell.paragraphs:
            paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT if cell == row.cells[0] else WD_PARAGRAPH_ALIGNMENT.LEFT
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcPr.tcBorders = None

# Настройка ячеек
cells = table.rows[0].cells
cells[0].text = "Арендатор _______________________"
cells[1].text = "Арендодатель ____________________"

# Вставляем подпись во вторую ячейку (Арендодатель)
add_floating_image(cells[1].paragraphs[0], 'подпись.png', width=Cm(4.8), x_offset=800000, y_offset=-250000)

# Настройка номеров страниц
sections = doc_contract.sections
for section in sections:
    # Получаем нижний колонтитул
    footer = section.footer
    # Добавляем параграф с номером страницы
    paragraph = footer.add_paragraph()
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
    # Добавляем номер страницы
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

# Извлекаем фамилию из поля 'имя' (предполагаем, что фамилия первая)
full_name = tenant.get('имя', '').split()
surname = full_name[0] if full_name else 'Unknown'

# Форматируем дату заезда для названия файла
date_str = pd.to_datetime(tenant['заезд']).strftime('%Y-%m-%d')

apartment_address_str = tenant.get('адрес квартиры', '')

# Создаем имя файла
contract_filename_docx = f"Д_{surname}_{date_str}_{apartment_address_str}.docx"
doc_contract.save(os.path.join(path, contract_filename_docx))

contract_filename_pdf = f"Д_{surname}_{date_str}_{apartment_address_str}.pdf"
convert_docx_to_pdf(
    os.path.join(path, contract_filename_docx),
    os.path.join(path, contract_filename_pdf)
)

print(f"Договор успешно сгенерирован: {os.path.abspath(os.path.join(path, contract_filename_docx))}")
print(f"PDF-версия договора: {os.path.abspath(os.path.join(path, contract_filename_pdf))}")


if acceptance_certificate:
    # Создаем новый документ для акта приема передачи квартиры
    doc_acceptance_certificate = Document()

    # Устанавливаем поля: 1 см со всех сторон
    sections = doc_acceptance_certificate.sections
    for section in sections:
        section.top_margin = Cm(1)
        section.bottom_margin = Cm(1)
        section.left_margin = Cm(1)
        section.right_margin = Cm(1)

    # Настройка стилей документа
    setup_document_styles(doc_acceptance_certificate, size_normal=14, size_heading_1=16, size_heading_2=14, line_spacing=1.05)

    doc_acceptance_certificate.add_paragraph()
    doc_acceptance_certificate.add_paragraph()
    doc_acceptance_certificate.add_paragraph()
    doc_acceptance_certificate.add_heading(level=1).add_run(f"АКТ\nприема-передачи квартиры в посуточную аренду")
    doc_acceptance_certificate.add_paragraph()
    doc_acceptance_certificate.add_paragraph()
    doc_acceptance_certificate.add_paragraph()

    # Добавляем таблицу для выравнивания города и даты
    table = doc_acceptance_certificate.add_table(rows=1, cols=2)
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
    left_paragraph.text = city
    left_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

    right_cell = table.cell(0, 1)
    right_paragraph = right_cell.paragraphs[0]
    right_paragraph.text = date
    right_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    doc_acceptance_certificate.add_paragraph()

    # Добавляем основной текст АПП
    p1 = doc_acceptance_certificate.add_paragraph(f"На основании Договора посуточной аренды квартиры от {date} Арендодатель, гр. {landlord.get('имя', '')}, с\u00A0одной стороны, и Арендатор, гр.\u00A0{tenant.get('имя', '')}, с\u00A0другой стороны, составили настоящий Акт о том, что Арендодатель сдал, а Арендатор принял в пользование квартиру, расположенную по адресу: {tenant.get('индекс адреса квартиры', '')}, {tenant.get('адрес квартиры', '')}.")
    p1.paragraph_format.first_line_indent = Cm(1.25)

    p2 = doc_acceptance_certificate.add_paragraph(f"В пользование Арендатора передаётся следующая мебель, оборудование и принадлежности:")
    p2.paragraph_format.first_line_indent = Cm(1.25)

    subparagraphs = [
        "кухонный гарнитур, холодильник, электрическая плита, микроволновая печь;",
        "кровать, шкаф, диван, телевизор;",
        "стиральная машина, зеркало;",
        "постельное белье, полотенца, кухонная посуда.",
    ]
    for subparagraph in subparagraphs:
        p = doc_acceptance_certificate.add_paragraph(style='List')
        run = p.add_run(f"\u2014 {subparagraph}")
        p.paragraph_format.left_indent = Cm(1.5)


    p3 = doc_acceptance_certificate.add_paragraph(f"Мебель и бытовая техника находятся в исправном рабочем состоянии. Жилое помещение пригодно для проживания и находится в надлежащем санитарном, техническом и противопожарном состоянии.")
    p3.paragraph_format.first_line_indent = Cm(1.25)

    # Заезд
    doc_acceptance_certificate.add_paragraph()
    doc_acceptance_certificate.add_paragraph().add_run(f"Квартира принята:").bold = True
    doc_acceptance_certificate.add_paragraph()
    doc_acceptance_certificate.add_paragraph()

    # Создаем таблицу 1x2
    table = doc_acceptance_certificate.add_table(rows=1, cols=2)
    table.autofit = False
    table.allow_autofit = False
    table.columns[0].width = Cm(9)
    table.columns[1].width = Cm(9)

    # Убираем границы таблицы
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT if cell == row.cells[0] else WD_PARAGRAPH_ALIGNMENT.LEFT
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcPr.tcBorders = None

    # Настройка ячеек
    cells = table.rows[0].cells
    cells[0].text = "Арендатор _______________________"
    cells[1].text = "Арендодатель ____________________"

    # Вставляем подпись во вторую ячейку (Арендодатель)
    add_floating_image(cells[1].paragraphs[0], 'подпись.png', width=Cm(4.8), x_offset=1000000, y_offset=-250000)
    doc_acceptance_certificate.add_paragraph().add_run(f"Дата: {tenant.get('заезд', '').strftime('%d.%m.%Y')}")

    # Добавляем параграф с нижней границей (линией)
    paragraph = doc_acceptance_certificate.add_paragraph()
    # Получаем элемент <w:pPr> (свойства параграфа)
    pPr = paragraph._p.get_or_add_pPr()
    # Добавляем границу снизу (горизонтальная линия)
    pBdr = OxmlElement('w:pBdr')
    pPr.append(pBdr)
    # Добавляем нижнюю границу (линию)
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'double')  # Тип линии: сплошная
    bottom.set(qn('w:sz'), '8')  # Толщина линии (в восьмых долях пункта, 4 = 0.5 пт)
    bottom.set(qn('w:space'), '1')  # Отступ от текста
    bottom.set(qn('w:color'), '000000')  # Цвет линии (чёрный)
    pBdr.append(bottom)


    # Выселение
    doc_acceptance_certificate.add_paragraph()
    doc_acceptance_certificate.add_paragraph().add_run(f"Квартира сдана:").bold = True
    doc_acceptance_certificate.add_paragraph()
    doc_acceptance_certificate.add_paragraph()

    # Создаем таблицу 1x2
    table = doc_acceptance_certificate.add_table(rows=1, cols=2)
    table.autofit = False
    table.allow_autofit = False
    table.columns[0].width = Cm(9)
    table.columns[1].width = Cm(9)

    # Убираем границы таблицы
    for row in table.rows:
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT if cell == row.cells[0] else WD_PARAGRAPH_ALIGNMENT.LEFT
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcPr.tcBorders = None

    # Настройка ячеек
    cells = table.rows[0].cells
    cells[0].text = "Арендатор _______________________"
    cells[1].text = "Арендодатель ____________________"

    # Вставляем подпись во вторую ячейку (Арендодатель)
    add_floating_image(cells[1].paragraphs[0], 'подпись.png', width=Cm(4.8), x_offset=1000000, y_offset=-250000)
    doc_acceptance_certificate.add_paragraph().add_run(f"Дата: {tenant.get('выезд', '').strftime('%d.%m.%Y')}")








    # Создаем имя файла для АПП
    acceptance_certificate_surname = tenant.get('имя', '').split()[0]
    acceptance_certificate_date_str = pd.to_datetime(tenant['заезд']).strftime('%Y-%m-%d')
    acceptance_certificate_filename_docx = f"А_{acceptance_certificate_surname}_{acceptance_certificate_date_str}_{apartment_address_str}.docx"
    doc_acceptance_certificate.save(os.path.join(path, acceptance_certificate_filename_docx))

    acceptance_certificate_filename_pdf = f"А_{acceptance_certificate_surname}_{acceptance_certificate_date_str}_{apartment_address_str}.pdf"
    convert_docx_to_pdf(
        os.path.join(path, acceptance_certificate_filename_docx),
        os.path.join(path, acceptance_certificate_filename_pdf)
    )

    print(f"Акт приема передачи квартиры успешно сгенерирован: {os.path.abspath(os.path.join(path, acceptance_certificate_filename_docx))}")
    print(f"PDF-версия акта: {os.path.abspath(os.path.join(path, acceptance_certificate_filename_pdf))}")
















# РАСПИСКА

# Создаем новый документ для расписки
doc_receipt = Document()

# Устанавливаем поля: 1 см со всех сторон
sections = doc_receipt.sections
for section in sections:
    section.top_margin = Cm(1)
    section.bottom_margin = Cm(1)
    section.left_margin = Cm(1)
    section.right_margin = Cm(1)

# Настройка стилей документа
setup_document_styles(doc_receipt, size_normal=14, size_heading_1=16, size_heading_2=14, line_spacing=1.05)

doc_receipt.add_paragraph()
doc_receipt.add_paragraph()
doc_receipt.add_paragraph()
doc_receipt.add_heading(level=1).add_run(f"РАСПИСКА\nв получении денежных средств\nпо договору аренды квартиры от {date}")
doc_receipt.add_paragraph()
doc_receipt.add_paragraph()
doc_receipt.add_paragraph()

# Добавляем таблицу для выравнивания города и даты
table = doc_receipt.add_table(rows=1, cols=2)
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
left_paragraph.text = city
left_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

right_cell = table.cell(0, 1)
right_paragraph = right_cell.paragraphs[0]
right_paragraph.text = date
right_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

doc_receipt.add_paragraph()
doc_receipt.add_paragraph()
doc_receipt.add_paragraph()

# Склоняем ФИО арендатора
tenant_name = tenant.get('имя', '')
declined_tenant_name = decline_fio_pytrovich(tenant_name)

# Добавляем основной текст расписки
main_text = f"Я, {landlord.get('имя', '')}, {landlord.get('дата рождения', '')} года рождения, паспорт {landlord.get('паспорт', '')}, выдан {landlord.get('дата выдачи', '')}\u00A0г. {landlord.get('кем выдан', '')}, код подразделения {landlord.get('код подразделения', '')}, зарегистрированный по адресу: {landlord.get('индекс адреса', '')}, {landlord.get('адрес прописки', '')}, тел:\u00A0{landlord.get('телефон', '')}, получил от {declined_tenant_name}, {tenant.get('дата рождения', '').strftime('%d.%m.%Y')} года рождения, паспорт {tenant.get('паспорт', '')}, выдан {tenant.get('дата выдачи', '').strftime('%d.%m.%Y')} г. {tenant.get('кем выдан', '')}, код подразделения {tenant.get('код подразделения', '')}, зарегистрированный по адресу: {tenant.get('индекс адреса прописки', '')}, {tenant.get('адрес прописки', '')}, тел:\u00A0{tenant.get('телефон', '')}, сумму в размере {tenant.get('оплата при заезде', 0)} ({num_to_words(tenant.get('оплата при заезде', 0))}) {rent_cost_onsite_word} в счет оплаты по договору аренды квартиры по адресу: {tenant.get('индекс адреса квартиры', '')}, {tenant.get('адрес квартиры', '')}."

# Добавляем текст о комиссии, если она есть
if 'предоплата' in tenant and tenant['предоплата'] > 0:
    main_text += f" Дополнительно {tenant.get('предоплата', 0)} ({num_to_words(tenant.get('предоплата', 0))}) {rent_cost_prepayment_word} было получено площадной «{tenant.get('площадка', '')}» в качестве комиссии."

main_paragraph = doc_receipt.add_paragraph(main_text)
main_paragraph.paragraph_format.first_line_indent = Cm(1.25)

doc_receipt.add_paragraph()
doc_receipt.add_paragraph()
doc_receipt.add_paragraph()

# Добавляем дату и подпись текстом
p = doc_receipt.add_paragraph(f"{pd.to_datetime(tenant['заезд']).strftime('%d.%m.%Y')} ____________________ / {landlord.get('имя', '').split()[0]} {landlord.get('имя', '').split()[1][0]}.{landlord.get('имя', '').split()[2][0]}. /")
p.alignment = WD_ALIGN_PARAGRAPH.CENTER

add_floating_image(p, 'подпись.png', width=Cm(5.5), x_offset=2500000, y_offset=-250000)

# Создаем имя файла для расписки
receipt_surname = tenant.get('имя', '').split()[0]
receipt_date_str = pd.to_datetime(tenant['заезд']).strftime('%Y-%m-%d')
receipt_filename_docx = f"Р_{receipt_surname}_{receipt_date_str}_{apartment_address_str}.docx"
doc_receipt.save(os.path.join(path, receipt_filename_docx))

receipt_filename_pdf = f"Р_{receipt_surname}_{receipt_date_str}_{apartment_address_str}.pdf"
convert_docx_to_pdf(
    os.path.join(path, receipt_filename_docx),
    os.path.join(path, receipt_filename_pdf)
)

print(f"Расписка  успешно сгенерирована: {os.path.abspath(os.path.join(path, receipt_filename_docx))}")
print(f"PDF-версия расписки: {os.path.abspath(os.path.join(path, receipt_filename_pdf))}")

