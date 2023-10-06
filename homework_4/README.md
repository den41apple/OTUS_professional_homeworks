# HTTP Server

## Описание

Базовый HTTP-сервер с использованием thread pool

Запуск сервера:

```
python httpd.py
```

```
Параметры запуска:
  -h, --help       Дополнительная информация
  -w, --workers    Количество обработчиков
  -r, --root       Корневая директория
  -p, --port       Номер порта
  -l, --log        Уровень логирования


```

Запуск тестов:
```
python tests/httptest.py
```

Нагрузочное тестирование:

```
# Установка
apt install apache2-utils 
```
    
```
ab -n 50000 -c 100 -r http://localhost:80/
```

Результаты:

    Server Software:        http_server
    Server Hostname:        localhost
    Server Port:            80
    
    Document Path:          /
    Document Length:        109 bytes
    
    Concurrency Level:      100
    Time taken for tests:   25.511 seconds
    Complete requests:      50000
    Failed requests:        0
    Non-2xx responses:      50000
    Total transferred:      12950000 bytes
    HTML transferred:       5450000 bytes
    Requests per second:    1959.97 [#/sec] (mean)
    Time per request:       51.021 [ms] (mean)
    Time per request:       0.510 [ms] (mean, across all concurrent requests)
    Transfer rate:          495.73 [Kbytes/sec] received
    
    Connection Times (ms)
                  min  mean[+/-sd] median   max
    Connect:        0    8  90.2      0    3138
    Processing:     4   43  12.5     44     913
    Waiting:        4   43  12.4     43     912
    Total:          4   51  94.3     44    3183
    
    Percentage of the requests served within a certain time (ms)
      50%     44
      66%     45
      75%     46
      80%     47
      90%     50
      95%     52
      98%     56
      99%     63
     100%   3183 (longest request)


