"""
Модуль для работы с таблицами данных о ценах на продукты.
Module for working with product price data tables.

Основные возможности / Main features:
- Загрузка и обработка данных о ценах / Loading and processing price data
- Расчет статистики по ценам / Price statistics calculation
- Генерация отчетов / Report generation

Attributes:
    directory (Path): Директория с файлами данных / Directory with data files
    names (dict): Словарь для форматирования названий продуктов / Dictionary for formatting product names
"""
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import pandas as pd
import os
import glob
from pandas import DataFrame

from parse_shop import get_query
from parse_prices import generate_cvs


from icecream import ic
ic.configureOutput(includeContext=True)

# Директория, где хранятся файлы с данными / Directory where data files are stored
directory = Path('data', 'report')

# Получение списка файлов в директории / Get list of files in directory
files = os.listdir(Path('data'))

# Словарь для преобразования названий продуктов в удобочитаемый формат с эмодзи
# Dictionary for converting product names to readable format with emoji
names = {
    'масло': '🧈 Сливочное масло, 180гр',
    'молоко': '🥛 Молоко 2.5%, 1л',
    'хлеб': '🥖 Хлеб белый (батон)',
    'колбаса': '🌭 Колбаса вареная, 400г',
    'крупа': '🍲 Крупа гречневая, 800г',
    'сахар': '🧂 Сахар-песок, 1кг',
    'яйцо': '🥚 Яйцо 10шт',
    'филе': '🍗 Курица филе, 1кг',
}


@dataclass
class Product:
    """
    Класс для хранения информации о продукте.
    Class for storing product information.

    Attributes:
        name (str): Название продукта / Product name
        date (datetime): Дата записи данных / Data recording date
        middle_price (float): Средняя цена продукта / Average product price
        min_price (float): Минимальная цена продукта / Minimum product price
    """
    name: str
    date: datetime
    middle_price: float
    min_price: float


def create_table():
    """
    Создает таблицы с отчетами по ценам для каждого продукта.
    Creates price report tables for each product.
    
    Структура отчета / Report structure:
    - Дата / Date
    - Продукт / Product
    - Минимальная цена / Minimum price
    - Средняя цена / Average price
    """
    # Создаем директорию для отчетов если её нет
    report_dir = Path('data', 'report')
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # Для каждого продукта из словаря names
    for product_key, product_name in names.items():
        # Ищем директории с данными продукта
        search_patterns = [
            product_key,
        ]
        
        # Получаем все возможные директории с данными
        product_dir: Path = None
        for pattern in search_patterns:
            for dir_name in os.listdir('data'):
                if pattern in dir_name.lower():
                    product_dir = (Path('data', dir_name))
        
        ic(f"Найденные директории для {product_name}:", product_dir)
        
        if not product_dir:
            print(f"Не найдены директории с данными для продукта {product_name}")
            continue
        
        # Список для хранения данных по всем магазинам
        all_data = []
        
        # Получаем текущую дату
        current_date = datetime.now().strftime('%d-%m-%Y')
        
        # Ищем CSV файлы во всех найденных директориях
        if product_dir:
            csv_pattern = str(product_dir / 'cvs/*.csv')
            csv_files = glob.glob(csv_pattern)
            ic(f"CSV файлы в {product_dir}:", csv_files)
            
            # Читаем данные из всех CSV файлов
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    if not df.empty:
                        min_price = df['Цена'].min()
                        avg_price = df['Цена'].mean()
                        all_data.append({
                            'Дата': current_date,
                            'Продукт': product_name,
                            'Минимальная цена': min_price,
                            'Средняя цена': avg_price
                        })
                        ic(f"Обработан файл {csv_file}: min={min_price}, avg={avg_price}")
                except Exception as e:
                    print(f"Ошибка при обработке файла {csv_file}: {e}")
                    continue
        
        if not all_data:
            print(f"Нет данных для анализа продукта {product_name}")
            continue
            
        # Создаем DataFrame из собранных данных
        df_all = pd.DataFrame(all_data)
        
        # Находим минимальную цену и среднюю цену среди всех магазинов
        report_data = {
            'Дата': current_date,
            'Продукт': product_name,
            'Минимальная цена': df_all['Минимальная цена'].min(),
            'Средняя цена': df_all['Средняя цена'].mean()
        }
        
        # Путь к файлу отчета
        report_file = report_dir / f"{product_key}.csv"
        
        # Если файл существует, добавляем новую строку
        if report_file.exists():
            df_existing = pd.read_csv(report_file)
            df_new = pd.DataFrame([report_data])
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_csv(report_file, index=False)
        else:
            # Создаем новый файл с первой строкой
            pd.DataFrame([report_data]).to_csv(report_file, index=False)
            
        print(f"Создан отчет для {product_name}")


def get_table(name: str) -> DataFrame:
    """
    Получает таблицу данных для указанного продукта.
    Gets data table for specified product.

    Args:
        name (str): Название продукта (ключ из словаря names) / Product name (key from names dictionary)

    Returns:
        DataFrame: Таблица данных с ценами на продукт / Data table with product prices

    Raises:
        IndexError: Если файл с данными не найден / If data file is not found
    """
    return pd.read_csv(Path(directory, name))


def get_product_from_table(table: DataFrame, index: int) -> Product:
    """
    Извлекает информацию о продукте из таблицы по указанному индексу.
    Extracts product information from table at specified index.

    Args:
        table (DataFrame): Таблица данных / Data table
        index (int): Индекс строки в таблице / Row index in table

    Returns:
        Product: Объект продукта или None, если индекс неверный / 
                Product object or None if index is invalid

    Raises:
        IndexError: Если индекс выходит за пределы таблицы / If index is out of table bounds
    """
    try:
        row = table.iloc[index]
        product = Product(
            name=row['Продукт'],
            date=datetime.strptime(row['Дата'], '%d-%m-%Y'),
            middle_price=float(row['Средняя цена']),
            min_price=float(row['Минимальная цена'])
        )
        return product
    except IndexError as e:
        ic(e)  # Логирование ошибки / Error logging
        return None


def get_text_month(month: int):
    _dir = Path('data', 'report')

    text = []

    all_products_price = 0
    all_products_price_old = 0

    for file in _dir.iterdir():
        df = pd.read_csv(file)
        name = df['Продукт'][0]
        df['Дата'] = pd.to_datetime(df['Дата'], format='%d-%m-%Y')
        year = datetime.now().year
        filtered_data = df[(df['Дата'].dt.month == month) & (df['Дата'].dt.year == year)]
        middle_price = filtered_data['Средняя цена'].mean()
        min_price = filtered_data['Минимальная цена'].min()

        _new = float(filtered_data['Средняя цена'].iloc[0])
        _old = float(filtered_data['Средняя цена'].iloc[-1])

        all_products_price += float(filtered_data['Средняя цена'].iloc[0])
        all_products_price_old += float(filtered_data['Средняя цена'].iloc[-1])

        percent = (_new / (_old * 0.01)) - 100
        ic(percent)
        percent = round(percent, 1)

        text.append(
            f'<b>{name}</b>\n'
            f'Средняя цена - <b>{str(round(middle_price, 2)).replace('.', ',')} р. {["⬇️ ", "⬆️ +"][percent >= 0]}{percent}%</b>\n'
            f'Min {str(min_price).replace('.', ',')} p.\n\n'
        )

    # Расчет общего изменения цен
    percent_sum = 0
    try:
        percent_sum = (all_products_price / (all_products_price_old * 0.01)) - 100
    except ZeroDivisionError as e:
        ic(e)
    percent_sum = round(percent_sum, 1)
    separator = '_' * 32
    all_products_price = round(all_products_price, 2)
    all_products_price = str(all_products_price).replace('.', ',')

    # Формирование итоговой строки
    summary_text = (
        f'<b>{separator}\nСумма продуктовой корзины:</b>\n'
        f'🛒 {all_products_price} р. {["⬇️ ", "⬆️ +"][percent_sum >= 0]}{str(percent_sum).replace(".", ",")}%\n'
        f'{separator}\n\n'
    )

    text.insert(0, summary_text)  # Вставка итоговой строки в начало

    result = ''.join(text)
    result += '📊 Отчет подготовлен на основе цен, представленных на официальных сайтах крупнейших продуктовых сетей на дату отчета.\n<i>Магазин распродаж <a href="https://fstok.ru/">FSTOK</a></i>'

    return result


def get_text() -> str:
    """
    Генерирует текстовый отчет о ценах на продукты.
    Generates text report about product prices.

    Returns:
        str: Текстовый отчет с информацией о ценах и изменениях /
             Text report with information about prices and changes

    Note:
        Отчет включает: / Report includes:
        - Общую сумму продуктовой корзины / Total sum of product basket
        - Процент изменения общей суммы / Percentage change of total sum
        - Детальную информацию по каждому продукту / Detailed information for each product
        - Эмодзи для визуального представления изменений / Emoji for visual representation of changes
    """
    text = []
    all_products_price_old = 0
    all_products_price = 0

    reports = os.listdir(directory)

    for name in reports:
        table = get_table(name)

        new_product = get_product_from_table(table, -1)  # Последняя запись
        old_product = get_product_from_table(table, -2)  # Предпоследняя запись

        percent = 0

        if new_product:
            all_products_price += new_product.middle_price

        if old_product:
            all_products_price_old += old_product.middle_price
            percent = (new_product.middle_price / (old_product.middle_price * 0.01)) - 100
            percent = round(percent, 1)

        # Формирование строки с информацией о продукте
        text.append(
            f'<b>{new_product.name}</b>\n'
            f'Средняя цена - <b>{str(round(new_product.middle_price, 2)).replace('.', ',')} р.</b> {["⬇️ ", "⬆️ +"][percent >= 0]}{percent}%\n'
            f'Min {str(new_product.min_price).replace('.', ',')} p.\n\n'
        )

    # Расчет общего изменения цен
    percent_sum = 0
    try:
        percent_sum = (all_products_price / (all_products_price_old * 0.01)) - 100
    except ZeroDivisionError as e:
        ic(e)
    percent_sum = round(percent_sum, 1)
    separator = '_' * 32
    all_products_price = round(all_products_price, 2)
    all_products_price = str(all_products_price).replace('.', ',')

    # Формирование итоговой строки
    summary_text = (
        f'<b>{separator}\nСумма продуктовой корзины:</b>\n'
        f'🛒 {all_products_price} р. {["⬇️ ", "⬆️ +"][percent_sum >= 0]}{str(percent_sum).replace(".", ",")}%\n'
        f'{separator}\n\n'
    )

    text.insert(0, summary_text)  # Вставка итоговой строки в начало

    result = ''.join(text)
    result += '📊 Отчет подготовлен на основе цен, представленных на официальных сайтах крупнейших продуктовых сетей на дату отчета.\n<i>Магазин распродаж <a href="https://fstok.ru/">FSTOK</a></i>'

    return result


def parse():
    queries = [
        'сливочное масло 180',
        'молоко ультрапастеризованное',
        'хлеб пшеничный',
        'крупа гречневая',
        'колбаса вареная 400',
        'сахар песок 1',
        'яйцо 10',
        'филе куриное'
    ]

    for query in queries:
        get_query(query)
        generate_cvs(query)

if __name__ == '__main__':
    parse()
    time.sleep(5)
    create_table()

