# MemcLoad v2
Задание: нужно переписать Python версию memc_load.py на Go. Программа по‐прежнему парсит и заливает в
мемкеш поминутную выгрузку логов трекера установленных приложений. Ключом является тип и идентификатор
устройства через двоеточие, значением является protobuf сообщение 

## Build
#### *(опционально)*
```shell
# linux / Mac
go build -o memcload main.go
```
```shell
# Windows
go build -o memcload.exe main.go
```

## Запуск
```shell
go run main.go
```

```
Параметры запуска:
  
  -loaders <uint>                                                  
        Кол-во обработчиков на каждый Memcached адрес (по умолчанию 4)
  -pattern <string>                                                
        Паттерн имени файла (по умолчанию "[^.]*.tsv.gz")                 
  -retries <int>                                                   
        Кол-во повторений в сек записи в Memcached (по умолчанию 5)
  -retry_delay <int>
        Кол-во секунд задержки между попытками записи в Memcached (по умолчанию 1)
  -test
        Не переименовывать файл
  -workers <uint>
        Кол-во обработчиков (по умолчанию кол-во ядер ЦП)
        
  -adid <string>                                                   
        adid device Memcached address (default "127.0.0.1:33015")
  -dvid <string>                                                   
        dvid device Memcached address (default "127.0.0.1:33016")
  -gaid <string>                                                   
        gaid device Memcached address (default "127.0.0.1:33014")
  -idfa <string>                                                   
        idfa device Memcached address (default "127.0.0.1:33013")

```