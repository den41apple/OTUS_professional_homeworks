#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '  
#                     '$request_time';
import argparse
import logging
import os
import shutil
import gzip
import re
from configparser import ConfigParser
from statistics import mean, median
from string import Template
from collections import namedtuple
from datetime import datetime
from pathlib import Path

argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("--config", help="Путь до файла ini  с конфигурацией")

config = {
    "REPORT_SIZE": 1_000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}
# Допустимый процент ошибок
ERRORS_PERCENT = 30
# Путь к конфигурационному файлу по умолчанию
DEFAULT_CONFIG_FILE_PATH = "./config.ini"

# Паттерны
_http_methods = ["GET", "POST", "HEAD", "OPTIONS", "TRACE",
                 "DELETE", "PUT", "POST", "PATCH", "CONNECT"]
_http_method = '|'.join(_http_methods)
_http_method = rf"(?:{_http_method})"
_url = rf'"{_http_method} ([\w\W]+) HTTP'
url_pattern = re.compile(_url)  # URL
request_time_pattern = re.compile(r"\d*\.\d*$")  # Время запроса
filename_pattern = re.compile(r"nginx-access-ui\.log-(\d{8})(?:.gz)*$")  # Валидное имя файла лога

LogFile = namedtuple('LogFile', ["date", "path"])


def configure_logging(cl_args: argparse.Namespace):
    """
    Конфигурирование логирования
    """
    config = get_config(cl_args=cl_args)
    kwargs = {"format": "[%(asctime)s] %(levelname).1s %(message)s",
              "datefmt": "%Y.%m.%d %H:%M:%S"}
    log_file = config.get("LOGING_FILE")
    if log_file:
        kwargs.update(filename=log_file)
    logging.basicConfig(**kwargs, encoding="UTF-8")


def get_configparser() -> ConfigParser:
    """
    Инициализирует объект чтения конфига
    """
    configparser = ConfigParser()
    # Что бы Ключи в нижний регистр не приводил
    configparser.optionxform = str
    return configparser


def read_config_from_cli(cl_args: argparse.Namespace) -> dict:
    """
    Читает конфигурацию из файла
    переданного в командную строку
    """
    config_path = cl_args.config
    if config_path is not None:
        new_config = read_config_by_path(path=config_path)
        if "REPORT_SIZE" in new_config:
            new_config['REPORT_SIZE'] = int(new_config['REPORT_SIZE'])
        return new_config
    return read_default_config()


def read_config_by_path(path: str) -> dict:
    """
    Читает конфигурацию по заданному пути
    """
    configparser = get_configparser()
    configparser.read(path, encoding='UTF-8')
    return dict(configparser['CONFIG'])


def read_default_config() -> dict:
    """
    Читает конфигурацию расположенному по дефолтному пути
    """
    default_config_path = Path(DEFAULT_CONFIG_FILE_PATH)
    if not default_config_path.exists():
        # Если конфига по умолчанию нет -> выходим без ошибки
        return {}
    return read_config_by_path(DEFAULT_CONFIG_FILE_PATH)


def get_config(cl_args: argparse.Namespace) -> dict:
    """Формирует конфигурацию"""
    default_config = config.copy()
    try:
        cli_config = read_config_from_cli(cl_args=cl_args)
    except Exception as err:
        logging.error(err, exc_info=True)
        raise err
    default_config.update(cli_config)
    return default_config


def find_last_log(config: dict) -> LogFile:
    """
    Ищет самый последний файл лога
    """
    catalog = config.get("LOG_DIR", '..')
    last_log: LogFile = None
    files = os.listdir(catalog)
    for file_name in files:
        dates = filename_pattern.findall(file_name)
        if dates:
            _date = dates[0]
            date = datetime.strptime(_date, "%Y%m%d")
            path = Path(catalog) / file_name
            if last_log is not None:
                if date > last_log.date:
                    last_log = LogFile(date=date, path=str(path))
            else:
                last_log = LogFile(date=date, path=str(path))
    return last_log


def report_exists(last_log: LogFile) -> bool:
    """
    Проверяет выполнены ли отчет по этому логу ранее
    """
    path = get_report_path(last_log=last_log)
    path = Path(path).resolve()
    return path.exists()


def get_report_path(last_log: LogFile) -> str:
    """Формирует путь до файла с отчетом"""
    _date = last_log.date
    date = _date.strftime("%Y.%m.%d")
    catalog = config.get("REPORT_DIR", ".")
    return str(Path(catalog) / f"report-{date}.html")


def parse_row(row: str):
    """Извлекает данные из строки"""
    address = url_pattern.findall(row)
    request_time = request_time_pattern.findall(row)

    return address, request_time


def read_lines(log_path):
    """
    Генератор для парсинга данных построчно
    """
    log = gzip.open(log_path, 'rb') if log_path.endswith(".gz") else open(log_path, encoding="UTF-8")
    i = 0
    missing_rows = 0
    try:
        for i, row in enumerate(log):
            if isinstance(row, bytes):
                row = row.decode("UTF-8")
            address, request_time = parse_row(row)
            gather_log_data.total_rows += 1
            if len(address) > 1 or len(request_time) > 1:
                msg = f"Неверно написанное регулярное выражение, строка {i + 1}"
                logging.error(msg)
                raise ValueError(msg)
            if address and request_time:
                addr = address[0]
                time = float(request_time[0])
                yield addr, time
            else:
                missing_rows += 1
    except:
        pass
    finally:
        log.close()
    if missing_rows:
        errors_percent = missing_rows / gather_log_data.total_rows * 100
        if errors_percent >= ERRORS_PERCENT:
            logging.error(f"Большое количество ({errors_percent:.2f} %) "
                          f"строк пропущено, они имели неверный формат")
    gather_log_data.total_rows = i + 1


def gather_log_data(log_path: str) -> list[dict]:
    """
    Собирает данные из лога в нужную структуру
    """
    log_data = {}
    gather_log_data.total_rows = 0
    for addr, time in read_lines(log_path):
        if addr not in log_data:
            log_data[addr] = []
        log_data[addr].append(time)
    return log_data


gather_log_data.total_rows = 0


def prepare_stat_table(log_data: dict) -> list[dict]:
    """
    Подготавливает таблицу для веба
    """

    def calculate_row(item: tuple) -> dict:
        """
        Подсчитывает статистику в строке
        """
        nonlocal all_requests_time
        total_rows = gather_log_data.total_rows
        url, times = item
        row = {"url": url,
               "count": len(times),
               "time_avg": mean(times),
               "time_max": max(times),
               "time_sum": sum(times),
               "time_med": median(times),
               "count_perc": len(times) / total_rows * 100,
               "time_perc": sum(times) / all_requests_time * 100}
        return row

    all_requests_times = [sum(v) for v in log_data.values()]  # Суммарное время всех запросов
    all_requests_time = sum(all_requests_times)
    stat = [calculate_row(item) for item in log_data.items()]
    stat = sorted(stat, key=lambda x: x['time_sum'], reverse=True)
    return stat


def create_report_folders_tree_is_not_exists(report_path: str):
    """
    Создает древо папок, если они не существуют
    """
    report_path = Path(report_path).parent
    report_path.mkdir(parents=True, exist_ok=True)


def write_html_report(stat: list[dict], config: dict, last_log: LogFile):
    """
    Генерирует HTML отчет
    """
    report_size = config.get("REPORT_SIZE", 1_000)
    path = get_report_path(last_log=last_log)
    create_report_folders_tree_is_not_exists(report_path=path)
    report_template_path = Path(__file__).parent / "report_template.html"
    try:
        copy_js_script(config=config)
        with open(report_template_path, encoding="UTF-8") as template:
            with open(path, "w", encoding="UTF-8") as new_report:
                template = template.read()
                output = Template(template).safe_substitute({"table_json": stat[:report_size]})
                new_report.write(output)
    except IOError as err:
        logging.exception("Произошла ошибка при сохранении HTML отчета", exc_info=True)
        raise err


def copy_js_script(config: dict):
    """
    Копирует js скрипт в папку с HTML отчетом
    для корректности отображения
    """
    copy_from = Path(__file__).parent / "jquery.tablesorter.min.js"
    copy_to = Path(config.get("REPORT_DIR", "..")) / "jquery.tablesorter.min.js"
    shutil.copy2(copy_from, copy_to)


def main():
    try:
        cl_args = argument_parser.parse_args()
        configure_logging(cl_args=cl_args)
        config = get_config(cl_args=cl_args)
        last_log = find_last_log(config=config)
        if report_exists(last_log=last_log):
            report_path = get_report_path(last_log)
            return logging.error(f'Отчет "{report_path}" уже существует')
        log_data = gather_log_data(log_path=last_log.path)
        stat = prepare_stat_table(log_data)
        write_html_report(stat=stat, config=config, last_log=last_log)
    except Exception as err:
        logging.exception(err, exc_info=True)


if __name__ == "__main__":
    main()
