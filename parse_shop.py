"""
Модуль для работы с API различных продуктовых маркетплейсов.
Module for working with various grocery marketplace APIs.

Основные возможности / Main features:
- Поиск товаров в разных магазинах / Search for products in different stores
- Обработка ответов API / API response handling
- Конфигурация для каждого магазина / Configuration for each store
"""

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict

from curl_cffi import requests
from curl_cffi.requests import Response
from icecream import ic

class RequestType(Enum):
    """
    Типы HTTP-запросов.
    HTTP request types.
    """
    GET = "GET"
    POST = "POST"


class MarketError(Exception):
    """
    Базовый класс для ошибок маркетплейсов.
    Base class for marketplace errors.
    """
    pass


class ConfigError(MarketError):
    """
    Ошибка конфигурации маркетплейса.
    Marketplace configuration error.
    """
    pass


class RequestError(MarketError):
    """
    Ошибка при выполнении запроса к API маркетплейса.
    Error when executing marketplace API request.
    """
    pass


@dataclass
class Config:
    """
    Класс для работы с конфигурационными файлами.
    Class for working with configuration files.

    Attributes:
        config_dir (Path): Путь к директории с конфигурационными файлами / Path to configuration files directory
    """
    config_dir: Path = Path('config')

    def load_config(self, filename: str) -> dict:
        """
        Загружает конфигурацию из JSON файла.
        Loads configuration from JSON file.

        Args:
            filename (str): Имя конфигурационного файла / Configuration filename

        Returns:
            dict: Загруженная конфигурация / Loaded configuration

        Raises:
            ConfigError: Если файл не найден или содержит некорректный JSON
                        If file not found or contains invalid JSON
        """
        try:
            with open(self.config_dir / filename, 'r', encoding='utf-8') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ConfigError(f"Ошибка загрузки конфигурации {filename}: {str(e)}")

    def load_proxies(self) -> dict:
        """
        Загружает конфигурацию прокси.
        Loads proxy configuration.

        Returns:
            dict: Конфигурация прокси / Proxy configuration
        """
        return self.load_config('proxies.json')


class BaseQuery:
    """
    Базовый класс для выполнения запросов.
    Base class for executing requests.

    Attributes:
        _params (dict): Параметры запроса / Request parameters
    """
    def __init__(self, **kwargs):
        self._params = kwargs

    def update_params(self, **kwargs) -> None:
        """
        Обновляет параметры запроса.
        Updates request parameters.

        Args:
            **kwargs: Новые параметры / New parameters
        """
        for key, value in kwargs.items():
            if key in self._params and isinstance(self._params[key], dict):
                self._params[key].update(value)
            else:
                self._params[key] = value

    def get_params(self) -> dict:
        """
        Возвращает текущие параметры запроса.
        Returns current request parameters.

        Returns:
            dict: Параметры запроса / Request parameters
        """
        return self._params

    def execute(self, **kwargs) -> Response:
        """
        Выполняет запрос (абстрактный метод).
        Executes request (abstract method).

        Raises:
            NotImplementedError: Метод должен быть переопределен в дочерних классах
                               Method must be overridden in child classes
        """
        raise NotImplementedError


class GetQuery(BaseQuery):
    """
    Класс для выполнения GET-запросов.
    Class for executing GET requests.
    """
    def execute(self, **kwargs) -> Response:
        """
        Выполняет GET-запрос.
        Executes GET request.

        Args:
            **kwargs: Дополнительные параметры запроса / Additional request parameters

        Returns:
            Response: Ответ от сервера / Server response

        Raises:
            RequestError: При ошибке выполнения запроса / On request execution error
        """
        self.update_params(**kwargs)
        try:
            return requests.get(**self._params)
        except Exception as e:
            raise RequestError(f"Ошибка GET-запроса: {str(e)}")


class PostQuery(BaseQuery):
    """
    Класс для выполнения POST-запросов.
    Class for executing POST requests.
    """
    def execute(self, **kwargs) -> Response:
        """
        Выполняет POST-запрос.
        Executes POST request.

        Args:
            **kwargs: Дополнительные параметры запроса / Additional request parameters

        Returns:
            Response: Ответ от сервера / Server response

        Raises:
            RequestError: При ошибке выполнения запроса / On request execution error
        """
        self.update_params(**kwargs)
        try:
            return requests.post(**self._params)
        except Exception as e:
            raise RequestError(f"Ошибка POST-запроса: {str(e)}")


class Market:
    """
    Класс для работы с конкретным маркетплейсом.
    Class for working with specific marketplace.

    Attributes:
        name (str): Название магазина / Store name
        config (Config): Конфигурация / Configuration
        query (BaseQuery): Объект для выполнения запросов / Query execution object
        search_param (Dict): Параметры поиска / Search parameters
    """
    def __init__(self, name: str, query_type: RequestType, config: Config):
        self.name = name
        self.config = config
        self.query = self._create_query(query_type)
        self.search_param = self._get_search_param()

    def _create_query(self, query_type: RequestType) -> BaseQuery:
        """
        Создает объект для выполнения запросов.
        Creates query execution object.

        Args:
            query_type (RequestType): Тип запроса / Query type

        Returns:
            BaseQuery: Объект для выполнения запросов / Query execution object
        """
        config_data = self.config.load_config(f"{self.name}.json")
        proxies = self.config.load_proxies()
        query_class = GetQuery if query_type == RequestType.GET else PostQuery
        return query_class(**config_data, proxies=proxies)

    def _get_search_param(self) -> Dict[str, str]:
        """
        Возвращает параметры поиска для конкретного магазина.
        Returns search parameters for specific store.

        Returns:
            Dict[str, str]: Параметры поиска / Search parameters
        """
        search_params = {
            '5ka': {'params': {'q': 'query'}},
            'perekrestok': {'json': {'filter': {'textQuery': 'query'}}},
            'magnit': {'json': {'term': 'query'}},
            'dixi': {'params': {'q': 'query'}},
            'lenta': {'json': {'query': 'query'}}
        }
        return search_params.get(self.name, {'params': {'q': 'query'}})

    def search(self, query: str) -> Response:
        """
        Выполняет поиск товаров в магазине.
        Performs product search in store.

        Args:
            query (str): Поисковый запрос / Search query

        Returns:
            Response: Ответ от API магазина / Store API response

        Raises:
            RequestError: При ошибке запроса или неуспешном статусе ответа
                        On request error or unsuccessful response status
        """
        param_key = list(self.search_param.keys())[0]
        param_dict = self.search_param[param_key].copy()
        
        if self.name == 'dixi':
            self.query._params['params'].update({
                'block': 'product-list',
                'sid': '0',
                'perPage': '30',
                'page': '1',
                'searchQuery': query,
                'getFullData': '',
                'gl_filter': ''
            })
            ic(f"Параметры запроса для Дикси: {self.query._params['params']}")
            response = self.query.execute()
        else:
            for key in param_dict:
                if isinstance(param_dict[key], dict):
                    for subkey in param_dict[key]:
                        param_dict[key][subkey] = query
                else:
                    param_dict[key] = query
            response = self.query.execute(**{param_key: param_dict})
        
        ic(f"{self.name} response status: {response.status_code}")
        ic(f"{self.name} response headers: {dict(response.headers)}")
        if response.status_code != 200:
            raise RequestError(f"Неуспешный статус ответа: {response.status_code}")
        return response


def get_query(search_query: str):
    """
    Основная функция для демонстрации работы с маркетплейсами.
    Main function for demonstrating marketplace operations.
    """
    config = Config()
    markets = [
        Market('5ka', RequestType.GET, config),
        Market('magnit', RequestType.POST, config),
        Market('lenta', RequestType.POST, config),
        Market('dixi', RequestType.GET, config)
    ]
    
    for i, market in enumerate(markets):
        try:
            response = market.search(search_query)
            try:
                json_data = response.json()
                folder_path = Path('data', f'{search_query.replace(' ', '')}')
                folder_path.mkdir(parents=True,exist_ok=True)

                ic(f"Успешный ответ от {market.name}")
                with open(Path(folder_path, f'{market.name}.json'), 'w', encoding='utf-8') as file:
                    json.dump(json_data, file, ensure_ascii=False, indent=4)
                    file.flush()
                    os.fsync(file.fileno())

            except json.JSONDecodeError as e:
                ic(f"Ошибка декодирования JSON от {market.name}")
                ic(f"Содержимое ответа: {response.text[:500]}")
                ic(f"Ошибка: {str(e)}")
        except MarketError as e:
            ic(f"Ошибка при работе с {market.name}: {str(e)}")
            continue



