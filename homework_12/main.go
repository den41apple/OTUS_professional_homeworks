package main

import (
	"bufio"
	"compress/gzip"
	"errors"
	"flag"
	"fmt"
	"github.com/bradfitz/gomemcache/memcache"
	"google.golang.org/protobuf/proto"
	"log"
	"memcload/appsinstalled"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

type (
	config struct {
		pattern    string
		workers    uint
		loaders    uint
		idfa       string
		gaid       string
		adid       string
		dvid       string
		timeout    int
		retries    int
		retryDelay int
		test       bool
	}

	memcacheInfo struct {
		client *memcache.Client
		queue  chan *memcache.Item
	}

	appsInstalled struct {
		devType string
		devId   string
		lat     float64
		lon     float64
		apps    []uint32
	}
)

const (
	constQueueSize = 1_024
)

func parse(s string) (*appsInstalled, error) {
	d := strings.Split(strings.TrimSpace(s), "\t")
	if len(d) != 5 {
		log.Printf("Ошибка обработки: \"%s\"\n", s)
		return nil, errors.New("Ошибка обработки")
	}
	devType, devId, lat, lon, rawApps := d[0], d[1], d[2], d[3], d[4]
	if devType == "" || devId == "" {
		log.Printf("Ошибка обработки: \"%s\"\n", s)
		return nil, errors.New("Ошибка обработки")
	}
	parsedApps := appsInstalled{devType: devType, devId: devId}
	for _, strApp := range strings.Split(rawApps, ",") {
		v, err := strconv.ParseInt(strApp, 10, 32)
		if err == nil {
			parsedApps.apps = append(parsedApps.apps, uint32(v))
		} else {
			log.Printf("Не все user apps являются цифрами: \"%s\"\n", s)
		}
	}
	latF, err := strconv.ParseFloat(lat, 64)
	if err != nil {
		log.Printf("Неверные координата lat \"%s\"\n", s)
		latF = 0
	}
	parsedApps.lat = latF
	lonF, err := strconv.ParseFloat(lon, 64)
	if err != nil {
		log.Printf("Неверные координатa lon  \"%s\"\n", s)
		lonF = 0
	}
	parsedApps.lon = lonF
	return &parsedApps, nil
}

func worker(job chan string, loadersJob map[string]*memcacheInfo, errorsStat *int) {

	for s := range job {
		parsedApps, err := parse(s)
		if err != nil {
			*errorsStat++
			continue
		}
		key := parsedApps.devType + ":" + parsedApps.devId
		data, err := proto.Marshal(&appsinstalled.UserApps{Apps: parsedApps.apps,
			Lat: proto.Float64(parsedApps.lat),
			Lon: proto.Float64(parsedApps.lon)})
		if err != nil {
			log.Println(err)
			*errorsStat++
			continue
		}
		if _, ok := loadersJob[parsedApps.devType]; ok {
			loadersJob[parsedApps.devType].queue <- &memcache.Item{Key: key, Value: data}
		} else {
			*errorsStat++
		}
	}
}

func loader(job chan *memcache.Item, client *memcache.Client,
	errorsStat *int, processedStat *int,
	retries int, retryDelay int, rowsCount *int) {

	for d := range job {
		attempts := retries
		var err error
		for attempts > 0 {
			err = client.Set(d)
			if err == nil {
				break
			}
			attempts -= 1
			time.Sleep(time.Duration(retryDelay) * time.Second)
		}
		if err != nil {
			log.Printf("%s", err)
			*errorsStat++
		} else {
			*processedStat++
		}
		*rowsCount++
		if *rowsCount%100 == 0 {
			fmt.Printf("\rЗагружено строк: %d", *rowsCount)
		}
	}
}

func dotRename(path string) {
	head, fn := filepath.Split(path)
	if err := os.Rename(path, filepath.Join(head, "."+fn)); err != nil {
		log.Printf("%s", err)
	}
}

func finalizeProcess(path string, errors int, processed int, isTest bool) {
	if !isTest {
		dotRename(path)
	}
	log.Printf("ОБРАБОТАНО: %d стр. :: ОШИБОК: %d стр.", processed, errors)

}

func processFile(file_name string, mc map[string]*memcacheInfo, workers uint,
	loaders uint, retries int, retryDelay int) (int, int) {
	var workersWg sync.WaitGroup
	var loadersWg sync.WaitGroup

	errorsStat := 0
	processedStat := 0
	rowsCount := 0
	job := make(chan string, constQueueSize)
	for _, v := range mc {
		v.queue = make(chan *memcache.Item, constQueueSize)
	}
	f, err := os.Open(file_name)
	defer f.Close()
	if err != nil {
		log.Fatalln(err)
	}
	gr, err := gzip.NewReader(f)
	if err != nil {
		log.Fatalln(err)
	}
	defer gr.Close()

	scanner := bufio.NewScanner(gr)

	for i := uint(0); i < workers; i++ {
		workersWg.Add(1)
		go func() {
			defer workersWg.Done()
			worker(job, mc, &errorsStat)
		}()
	}

	for _, v := range mc {
		for i := uint(0); i < loaders; i++ {
			loadersWg.Add(1)
			go func(v *memcacheInfo) {
				defer loadersWg.Done()
				loader(v.queue, v.client, &errorsStat, &processedStat, retries, retryDelay, &rowsCount)
			}(v)

		}
	}
	for scanner.Scan() {
		job <- scanner.Text()
	}
	close(job)
	workersWg.Wait()
	for _, v := range mc {
		close(v.queue)
	}
	loadersWg.Wait()
	fmt.Printf("\rЗагружено строк: %d\n", rowsCount)
	return errorsStat, processedStat
}

func getConfig() *config {
	cfg := &config{}
	flag.StringVar(&cfg.pattern, "pattern", "[^.]*.tsv.gz", "Паттерн имени файла")
	flag.UintVar(&cfg.workers, "workers", uint(runtime.NumCPU()), "Кол-во обработчиков")
	flag.UintVar(&cfg.loaders, "loaders", 4, "Кол-во обработчиков на каждый Memcached адрес")
	flag.StringVar(&cfg.idfa, "idfa", "127.0.0.1:33013", "idfa device Memcached address")
	flag.StringVar(&cfg.gaid, "gaid", "127.0.0.1:33014", "gaid device Memcached address")
	flag.StringVar(&cfg.adid, "adid", "127.0.0.1:33015", "adid device Memcached address")
	flag.StringVar(&cfg.dvid, "dvid", "127.0.0.1:33016", "dvid device Memcached address")
	flag.IntVar(&cfg.retries, "retries", 5, "Кол-во повторений в сек записи в Memcached")
	flag.IntVar(&cfg.retryDelay, "retry_delay", 1, "Кол-во секунд задержки между попытками записи в Memcached")
	flag.BoolVar(&cfg.test, "test", false, "Не переименовывать файл")
	flag.Parse()
	return cfg
}

func main() {
	cfg := getConfig()
	memcacheAddr := map[string]string{
		"idfa": cfg.idfa,
		"gaid": cfg.gaid,
		"adid": cfg.adid,
		"dvid": cfg.dvid,
	}
	memcacheCQ := map[string]*memcacheInfo{}
	for k, v := range memcacheAddr {
		memcacheCQ[k] = &memcacheInfo{client: memcache.New(v), queue: nil}
		memcacheCQ[k].client.MaxIdleConns = int(cfg.loaders)
		memcacheCQ[k].client.Timeout = time.Duration(cfg.timeout) * time.Second
	}

	files, _ := filepath.Glob(cfg.pattern)
	fmt.Printf("Найдено %d файла\n", len(files))
	sort.Strings(files)
	startTime := time.Now()
	for i, filename := range files {
		log.Printf("[%d] Обработка файла \"%s\"\n", i+1, filename)
		errors, processed := processFile(filename, memcacheCQ, cfg.workers,
			cfg.loaders, cfg.retries, cfg.retryDelay)
		finalizeProcess(filename, errors, processed, cfg.test)
	}
	endTime := time.Now()
	elapsedTime := endTime.Sub(startTime)
	elapsedTime = elapsedTime.Round(time.Second)
	if len(files) != 0 {
		fmt.Printf("Время выполнения: %s\n", elapsedTime)
	} else {
		fmt.Println("Файлов для обработки нет")
	}

}
