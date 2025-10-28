#!/bin/sh

set -e

GREEN='\033[0;32m'
ENDC='\e[0m'
CYAN='\033[0;36m'

# check backend is online
printf "\nPerforming health check\n"
until timeout 60s wget -qO /dev/null ${FASTAPI_HEALTH}; do
    printf "Pinging ${FASTAPI_HEALTH}...\n"
    sleep 1
done

printf "\n${GREEN}Fastapi health check Complete${ENDC}\n"

# start celery
celery --quiet -A worker.celery worker --loglevel=${LOG_LEVEL} --logfile=${LOG_FILE} --detach

printf "\nWaiting for celery workers...\n"
until timeout 120s celery -A worker inspect ping; do
    >&2 echo "Celery workers not available\n"
done

# start flower dashboard
celery --quiet --broker=${CELERY_BROKER_URL} flower --port=${FLOWER_PORT}