#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import glob
import gzip
import logging
import multiprocessing
import os
import sys
import threading
from optparse import OptionParser

# pip install python-memcached
import memcache
from tqdm import tqdm

# brew install protobuf
# protoc  --python_out=. ./appsinstalled.proto
# pip install protobuf
import appsinstalled_pb2

NORMAL_ERR_RATE = 0.01
AppsInstalled = collections.namedtuple("AppsInstalled", ["dev_type", "dev_id", "lat", "lon", "apps"])

THREADS_COUNT = 10  # Количество потоков в одном процессе
LINES_PER_THREAD = 100  # Количество строк на 1 поток
thread_pool = threading.BoundedSemaphore(THREADS_COUNT)
lock = threading.RLock()
local = threading.local()
ROWS_COUNT = 0  # Количество строк
BAR: tqdm = None  # Прогресс-бар


def dot_rename(path):
    head, fn = os.path.split(path)
    # atomic in most cases
    os.rename(path, os.path.join(head, "." + fn))


def insert_appsinstalled(memc_addr, appsinstalled, dry_run=False):
    ua = appsinstalled_pb2.UserApps()
    ua.lat = appsinstalled.lat
    ua.lon = appsinstalled.lon
    key = "%s:%s" % (appsinstalled.dev_type, appsinstalled.dev_id)
    ua.apps.extend(appsinstalled.apps)
    packed = ua.SerializeToString()
    # @TODO persistent connection
    # @TODO retry and timeouts!
    try:
        if dry_run:
            logging.debug("%s - %s -> %s" % (memc_addr, key, str(ua).replace("\n", " ")))
        else:
            memc = memcache.Client([memc_addr])
            with lock:
                memc.set(key, packed)
    except Exception as e:
        logging.exception("Cannot write to memc %s: %s" % (memc_addr, e))
        return False
    return True


def parse_appsinstalled(line):
    line_parts = line.strip().split("\t")
    if len(line_parts) < 5:
        return
    dev_type, dev_id, lat, lon, raw_apps = line_parts
    if not dev_type or not dev_id:
        return
    try:
        apps = [int(a.strip()) for a in raw_apps.split(",")]
    except ValueError:
        apps = [int(a.strip()) for a in raw_apps.split(",") if a.isidigit()]
        logging.info("Not all user apps are digits: `%s`" % line)
    try:
        lat, lon = float(lat), float(lon)
    except ValueError:
        logging.info("Invalid geo coords: `%s`" % line)
    return AppsInstalled(dev_type, dev_id, lat, lon, apps)


def process_file(args):
    """Обработка отдельного файла"""
    # Разбор аргументов
    fn, device_memc, options, queue = args

    def process_line(lines: tuple, thread_pool):
        """Обработка строки файла"""
        nonlocal processed, errors

        with thread_pool:
            for line in lines:
                line = line.strip()
                if not line:
                    return

                appsinstalled = parse_appsinstalled(line)
                if not appsinstalled:
                    errors += 1
                    return

                memc_addr = device_memc.get(appsinstalled.dev_type)
                if not memc_addr:
                    errors += 1
                    logging.error("Unknown device type: %s" % appsinstalled.dev_type)
                    return

                ok = insert_appsinstalled(memc_addr, appsinstalled, options.dry)
            with lock:
                if ok:
                    processed += 1
                else:
                    errors += 1

    def wait_and_refresh_threads():
        nonlocal threads, cnt_threads
        [t.join() for t in threads]
        cnt_threads = 0
        threads = []

    def start_thread(lines, thread_pool):
        nonlocal cnt_threads
        """Запуск потока"""
        thread = threading.Thread(target=process_line, args=(lines, thread_pool))
        threads.append(thread)
        thread.start()
        cnt_threads += 1

    processed = errors = 0
    logging.info('Processing %s' % fn)
    fd = gzip.open(fn, "rt", encoding="UTF-8")
    threads = []
    lines = []
    cnt_threads = 0
    cnt_lines = 0
    for line in fd:
        lines.append(line)
        cnt_lines += 1
        if cnt_lines >= LINES_PER_THREAD:
            start_thread(tuple(lines), thread_pool)
            queue.put(cnt_lines)
            cnt_lines = 0
            if cnt_threads >= THREADS_COUNT:
                # Если набираем необходимое кол-во потоков
                wait_and_refresh_threads()
            lines.clear()

    # В конце запускаем поток с оставшимися строками
    if lines:
        start_thread(lines, thread_pool)
        lines.clear()
    # И дожидаемся оставшихся потоков
    wait_and_refresh_threads()
    queue.put(cnt_lines)

    if not processed:
        fd.close()
        dot_rename(fn)
        return

    err_rate = float(errors) / processed
    if err_rate < NORMAL_ERR_RATE:
        logging.info("Acceptable error rate (%s). Successful load" % err_rate)
    else:
        logging.error("High error rate (%s > %s). Failed load" % (err_rate, NORMAL_ERR_RATE))
    fd.close()
    dot_rename(fn)


def count_rows(file_name) -> int:
    with gzip.open(file_name, "rb") as file:
        return sum(1 for line in file)


def count_lines(options: OptionParser):
    """
    Подсчитывает общее количество строк в файлах
    """
    global ROWS_COUNT, BAR

    args = [file_name for file_name in glob.iglob(options.pattern)]
    if len(args) == 0:
        return 0
    if not options.not_count:
        # Если подсчитываем количество строк
        logging.info(f"Подсчет строк в {len(args)} файлах...")
        pool = multiprocessing.Pool(processes=3)
        try:
            results = pool.map(count_rows, args)
            ROWS_COUNT = sum(results)
        finally:
            pool.close()
            pool.join()
        logging.info(f'Общее количество строк: {ROWS_COUNT:,}'.replace(",", " "))
    else:
        # Если не подсчитываем количество строк
        logging.info("Подсчет строк пропущен")
    BAR = tqdm(total=ROWS_COUNT, desc="Обработано строк",
               unit_scale=True)


def bar_updater(queue: multiprocessing.Queue):
    """
    Обновляет прогресс-бар
    """
    while True:
        num = queue.get()
        if num == -1:
            # Означает конец обработки
            return
        BAR.update(num)


def main(options):
    device_memc = {
        "idfa": options.idfa,
        "gaid": options.gaid,
        "adid": options.adid,
        "dvid": options.dvid,
    }
    pool = multiprocessing.Pool(processes=options.workers)
    # При использовании очереди с pool.map
    # не обойтись без менеджера
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    if count_lines(options) == 0:
        return logging.error(f"Нет файлов для обработки")
    file_args = [(fn, device_memc, options, queue) for fn in glob.iglob(options.pattern)]
    try:
        threading.Thread(target=bar_updater, args=(queue,)).start()
        pool.map(process_file, file_args)
    finally:
        pool.close()
        pool.join()
    queue.put(-1)


def prototest():
    sample = ("idfa\t1rfw452y52g2gq4g\t55.55\t42.42\t1423,43,567,3,7,23\n"
              "gaid\t7rfw452y52g2gq4g\t55.55\t42.42\t7423,424")
    for line in sample.splitlines():
        dev_type, dev_id, lat, lon, raw_apps = line.strip().split("\t")
        apps = [int(a) for a in raw_apps.split(",") if a.isdigit()]
        lat, lon = float(lat), float(lon)
        ua = appsinstalled_pb2.UserApps()
        ua.lat = lat
        ua.lon = lon
        ua.apps.extend(apps)
        packed = ua.SerializeToString()
        unpacked = appsinstalled_pb2.UserApps()
        unpacked.ParseFromString(packed)
        assert ua == unpacked


def set_opt_parser() -> OptionParser:
    op = OptionParser()
    op.add_option("-t", "--test", action="store_true", default=False)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--dry", action="store_true", default=False)
    op.add_option("--pattern", action="store", default="./*.tsv.gz")
    op.add_option("--idfa", action="store", default="127.0.0.1:33013")
    op.add_option("--gaid", action="store", default="127.0.0.1:33014")
    op.add_option("--adid", action="store", default="127.0.0.1:33015")
    op.add_option("--dvid", action="store", default="127.0.0.1:33016")
    op.add_option("-w", "--workers", action="store", default=3, type="int")
    op.add_option("--not_count", action="store_true", default=False)
    return op


if __name__ == '__main__':
    op = set_opt_parser()
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO if not opts.dry else logging.DEBUG,
                        format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    if opts.test:
        prototest()
        sys.exit(0)

    logging.info("Memc loader started with options: %s" % opts)
    try:
        main(opts)
    except Exception as e:
        logging.exception("Unexpected error: %s" % e)
        sys.exit(1)
