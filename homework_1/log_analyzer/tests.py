import sys
import unittest
from datetime import datetime
from pathlib import Path

from log_analyzer import (find_last_log, config, create_report_folders_tree_is_not_exists,
                          write_html_report, LogFile, get_report_path)


class Tests(unittest.TestCase):

    def test_bz2_log_file(self):
        """
        Не должны браться bz2 файлы
        """
        config['LOG_DIR'] = "./tmp_log"
        filename = "nginx-access-ui.log-30001231.gz.bz2"
        catalog = Path(config['LOG_DIR'])
        catalog_exists = catalog.exists()
        if not catalog_exists:
            catalog.mkdir()
        path = catalog / filename
        try:
            with open(path, "wb") as file:
                file.write(b"test")
            last_log = find_last_log(config=config)
            self.assertIsNone(last_log, "Файл .bz2 берется в работу")
        finally:
            # Удаляем файл
            path.unlink(missing_ok=True)
            if not catalog_exists:
                # Удаляем каталог если не присутствовал ранее
                catalog.rmdir()

    def test_create_folder_tree(self):
        """
        Создание древа каталогов
        """
        report_path = "one_111/two_222/three_333/report.html"
        catalog_path = Path(report_path).parent
        try:
            create_report_folders_tree_is_not_exists(report_path)
            self.assertTrue(catalog_path.exists(), "Не создается древо каталогов")
        finally:
            self._delete_folders_tree(catalog_path)

    def test_write_html_report(self):
        """
        Запись HTML отчета
        """
        log_dir = "./tmp_log"
        config['LOG_DIR'] = log_dir
        last_log = LogFile(date=datetime.strptime("2020-01-01", "%Y-%m-%d"),
                           path="nginx-access-ui.log-20200101")
        stat = [{'one': 1}, {"two": 2}]
        report_path = get_report_path(last_log=last_log)
        report_path = Path(report_path)
        catalog_path = report_path.parent
        try:
            write_html_report(stat=stat, config=config, last_log=last_log)
            self.assertTrue(report_path.exists(), "Не создается HTML файл с отчетом")
        finally:
            report_path.unlink()
            self._delete_folders_tree(catalog_path)

    def _delete_folders_tree(self, catalog_path):
        """
        Удаляет древо каталогов
        """
        try:
            catalog_path.rmdir()
            for cat in catalog_path.parents[:-1]:
                cat.rmdir()
        except OSError:
            pass


if __name__ == '__main__':
    unittest.main()
