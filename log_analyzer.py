#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '  
#                     '$request_time';
import os
import shutil
import gzip
import re
from statistics import mean, median
from string import Template
from collections import namedtuple
from datetime import datetime
from pathlib import Path

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}

# TODO: Сделать логиррование
# TODO: sys.argv --config путь до другого конфига

# Паттерны
_http_methods = ["GET", "POST", "HEAD", "OPTIONS", "TRACE", "DELETE", "PUT", "POST", "PATCH", "CONNECT"]
_http_method = '|'.join(_http_methods)
_http_method = rf"(?:{_http_method})"
_url = rf'"{_http_method} ([\w\W]+) HTTP'
url_pattern = re.compile(_url)
request_time_pattern = re.compile(r"\d*\.\d*$")

LogFile = namedtuple('LogFile', ["date", "path"])


def get_config() -> dict:
    """Формирует конфигурацию"""
    # TODO: Формировать конфиг
    return config


def find_last_log(config: dict) -> LogFile:
    """
    Ищет самый последний файл лога
    """
    catalog = config.get("LOG_DIR", '.')
    last_log: LogFile = None
    files = os.listdir(catalog)
    for file_name in files:
        dates = re.findall(r"nginx-access-ui\.log-(\d{8})(?:.gz)*", file_name)
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
    return Path(catalog) / f"report-{date}.html"


def parse_row(row: str):
    """Извлекает данные из строки"""
    address = url_pattern.findall(row)
    request_time = request_time_pattern.findall(row)

    return address, request_time


def read_lines(log_path):
    log = gzip.open(log_path, 'rb') if log_path.endswith(".gz") else open(log_path)
    # TODO: Регуляркой добиться что бы не возвращались .bz файлы
    # TODO: протестировать на это
    i = 0
    try:
        for i, row in enumerate(log):
            if isinstance(row, bytes):
                row = row.decode("UTF-8")
            address, request_time = parse_row(row)
            gather_log_data.total_rows += 1
            if len(address) > 1 or len(request_time) > 1:
                raise ValueError(f"Неверно написанное регулярное выражение, строка {i + 1}")
            if address and request_time:
                addr = address[0]
                time = float(request_time[0])
                yield addr, time
            else:
                # TODO: Добавить подсчет пропущенных для парсинга строк
                pass
    finally:
        log.close()
    gather_log_data.total_rows = i + 1


def gather_log_data(log_path: str) -> list[dict]:
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
    stat = sorted(stat, key=lambda x: x['count'], reverse=True)  # TODO: сортировка по набиольшему time_sum
    return stat


def make_html_report(stat: list[dict], config: dict, last_log: LogFile):
    """
    Генерирует HTML отчет
    """
    report_size = config.get("REPORT_SIZE", 1_000)
    path = get_report_path(last_log=last_log)
    copy_js_script(config=config)
    with open("report_template.html", encoding="UTF-8") as template:
        with open(path, "w", encoding="UTF-8") as new_report:
            template = template.read()
            output = Template(template).safe_substitute({"table_json": stat[:report_size]})
            new_report.write(output)


def copy_js_script(config: dict):
    """
    Копирует js скрипт в папку с HTML отчетом
    для корректности отображения
    """
    copy_from = Path(__file__).parent / "jquery.tablesorter.min.js"
    copy_to = Path(config.get("REPORT_DIR", ".")) / "jquery.tablesorter.min.js"
    shutil.copy2(copy_from, copy_to)


def main():
    config = get_config()
    last_log = find_last_log(config=config)
    if report_exists(config=config, last_log=last_log):
        return print("Отчет уже существует")
    log_data = gather_log_data(log_path=last_log.path)
    stat = prepare_stat_table(log_data)
    make_html_report(stat=stat, config=config, last_log=last_log)


if __name__ == "__main__":
    main()
