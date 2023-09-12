import unittest
from pathlib import Path

from log_analyzer import find_last_log, get_config, config


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


if __name__ == '__main__':
    unittest.main()
