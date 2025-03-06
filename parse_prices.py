"""
Модуль для извлечения данных о ценах из JSON файлов разных магазинов.
Module for extracting price data from different stores' JSON files.
"""

import json
from pathlib import Path
import pandas as pd
from typing import Dict, List, Tuple
import re


def parse_5ka_prices(data: dict) -> List[Tuple[str, float]]:
    """
    Парсит данные о ценах из JSON Пятёрочки.
    Parses price data from 5ka JSON.
    """
    products = []
    for product in data.get('products', []):
        name = product.get('name')
        price = product.get('prices', {}).get('regular', '0')
        discount_price = product.get('prices', {}).get('discount')
        
        # Используем скидочную цену, если она есть
        final_price = float(discount_price if discount_price else price)
        products.append((name, final_price))
    return products


def parse_dixi_prices(data: list) -> List[Tuple[str, float]]:
    """
    Парсит данные о ценах из JSON Дикси.
    Parses price data from Dixi JSON.
    """
    products = []
    if data and isinstance(data, list) and len(data) > 0:
        if data[0].get('cards'):
            for card in data[0].get('cards'):
                name = card.get('title')
                price = card.get('priceSimple')

                if name and price:
                    products.append((name, float(price)))
    return products


def parse_magnit_prices(data: dict) -> List[Tuple[str, float]]:
    """
    Парсит данные о ценах из JSON Магнита.
    Parses price data from Magnit JSON.
    """
    products = []
    for product in data.get('items', []):
        name = product.get('name')
        price = product.get('price')

        if name and price:
            products.append((name, float(price/100)))
    return products


def parse_lenta_prices(data: dict) -> List[Tuple[str, float]]:
    """
    Парсит данные о ценах из JSON Ленты.
    Parses price data from Lenta JSON.
    """
    products = []
    for product in data.get('items', []):
        name = product.get('name')
        price = product.get('prices', {}).get('price')

        if name and price:
            products.append((name, float(price/100)))
    return products


def load_json_file(file_path: Path) -> dict:
    """
    Загружает JSON файл.
    Loads JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")
        return {}


def save_to_csv(products: List[Tuple[str, float]], output_dir: str, filename: str):
    """
    Сохраняет данные в CSV файл.
    Saves data to CSV file.
    """
    df = pd.DataFrame(products, columns=['Название', 'Цена'])
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_dir / filename, index=False, encoding='utf-8')


def filter_for_product(products: list, positive_promt: list, negative_promt: list) -> list:
    """
    Фильтрует список продуктов по ключевым словам.
    Filters product list by keywords.

    Args:
        products (list): Список продуктов (кортежи с названием и ценой)
        positive_promt (list): Список слов, которые должны быть в названии
        negative_promt (list): Список слов, которых не должно быть в названии

    Returns:
        list: Отфильтрованный список продуктов
    """
    filtered_products = []
    
    # Предобработка запроса
    def preprocess_query(query):
        # Заменяем возможные варианты записи размеров
        replacements = {
            r'(\d+)\s*г\b': r'\1g',  # 180г -> 180g
            r'(\d+)\s*гр\b': r'\1g',  # 180гр -> 180g
            r'(\d+)\s*мл\b': r'\1ml',  # 180мл -> 180ml
            r'(\d+)\s*кг\b': r'\1kg',  # 1кг -> 1kg
            r'(\d+)\s*шт\b': r'\1шт',  # 10шт -> 10шт
        }
        
        for pattern, replacement in replacements.items():
            query = re.sub(pattern, replacement, query, flags=re.IGNORECASE)
        return query.lower()
    
    for product in products:
        name = preprocess_query(product[0].lower())
        
        # Проверяем наличие положительных ключевых слов
        positive_match = all(
            any(
                re.search(rf'{re.escape(word.lower())}', name, re.IGNORECASE) 
                for variant in [word, preprocess_query(word)]
            )
            for word in positive_promt
        )
        
        # Проверяем отсутствие отрицательных ключевых слов
        negative_match = any(
            re.search(rf'{re.escape(word.lower())}', name, re.IGNORECASE) 
            for word in negative_promt
        )
        
        if positive_match and not negative_match:
            filtered_products.append(product)
            
    return filtered_products

negative_promt = ["Своя цена", "365 дней", "маркет", "Моя цена", "пр!сто", "Красная цена", "багет", "FRESH", "в соусе", '3.2%', '200мл', '0,2л', '0,05%', '200г', '500мл', 'Тёма']

def generate_cvs(query: str):
    """
    Основная функция для обработки файлов и сохранения результатов.
    Main function for processing files and saving results.
    """
    json_dir = Path('data', query.replace(' ', ''))
    
    # Словарь с парсерами для каждого магазина
    parsers = {
        '5ka.json': parse_5ka_prices,
        'dixi.json': parse_dixi_prices,
        'magnit.json': parse_magnit_prices,
        'lenta.json': parse_lenta_prices
    }
    
    # Обработка каждого файла
    for filename, parser in parsers.items():
        file_path = json_dir / filename
        if file_path.exists():
            data = load_json_file(file_path)
            if data:
                products = parser(data)
                filtred_products = filter_for_product(products, query.split(), negative_promt)
                csv_filename = f"{filename.replace('.json', '')}_prices.csv"
                save_to_csv(filtred_products, Path(json_dir, 'cvs'), csv_filename)
                print(f"Данные из {filename} сохранены в {csv_filename}")
        else:
            print(f"Файл {filename} не найден")

