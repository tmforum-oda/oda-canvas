package util

import (
	"github.com/joho/godotenv"
	"os"
	"sigs.k8s.io/controller-runtime/pkg/log"
	"strconv"
)

var globalConfig *Config
var logger = log.Log.WithName("UtilConfig")

type Config struct {
	RequeueIntervalSeconds    int
	EnsureStorageAvailability bool
}

func GetConfig() *Config {
	if globalConfig != nil {
		return globalConfig
	}
	err := godotenv.Load()

	if err != nil {
		logger.Error(err, "error loading env file")
	}
	if globalConfig != nil {
		return globalConfig
	}

	RequeueIntervalSeconds, err := strconv.Atoi(os.Getenv("REQUEUE_INTERVAL_SECONDS"))
	if err != nil {
		logger.Error(err, "error parsing REQUEUE_INTERVAL_SECONDS, setting to default value")
		RequeueIntervalSeconds = 1
	}

	EnsureStorageAvailability, err := strconv.ParseBool(os.Getenv("ENSURE_STORAGE_AVAILABILITY"))
	if err != nil {
		logger.Error(err, "error parsing ENSURE_STORAGE_AVAILABILITY, setting default value")
		EnsureStorageAvailability = false
	}

	globalConfig = &Config{
		RequeueIntervalSeconds:    RequeueIntervalSeconds,
		EnsureStorageAvailability: EnsureStorageAvailability,
	}
	return globalConfig
}
