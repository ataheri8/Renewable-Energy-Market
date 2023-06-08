#!/usr/bin/env sh

export KAFKA_LISTENER=kafka:9092

PROJECT_NAME="pmcore" 
keep_running="true"
DB_PORT=5432
PG_CONTAINER_NAME=postgresdb
DB_MIGRATION_CONTAINER_NAME=db-migrations
TESTING_CONTAINER_NAME=testing
NETWORK_NAME=core
while [ "${keep_running}" = "true" ]; do
    running_containers_with_port="$(docker ps --filter publish=${DB_PORT} --filter status=running | wc -l)"
    echo "Containers running with exposing port ${DB_PORT}: $((running_containers_with_port-1))"
    if [ $running_containers_with_port -eq 1 ]; then
        echo "Found a free port to run the postgress ${DB_PORT}"        
        keep_running="false"
        PROJECT_NAME="test-pmcore-${DB_PORT}"
    else
        DB_PORT=$((DB_PORT+1))
    fi
done

export PG_CONTAINER_NAME="${PROJECT_NAME}-${PG_CONTAINER_NAME}"
export DB_MIGRATION_CONTAINER_NAME="${PROJECT_NAME}-${DB_MIGRATION_CONTAINER_NAME}"
export TESTING_CONTAINER_NAME="${PROJECT_NAME}-${TESTING_CONTAINER_NAME}"
export NETWORK_NAME="${PROJECT_NAME}-${NETWORK_NAME}"
export DB_PORT=${DB_PORT} 
docker compose -p $PROJECT_NAME -f ./docker/docker-compose.yml --env-file ./.env --profile ci up -d --remove-orphans --build
docker compose -p $PROJECT_NAME -f ./docker/docker-compose.yml --env-file ./.env logs ${DB_MIGRATION_CONTAINER_NAME}
keep_running="true"
timeout=10s
exit_code=2
while [ "${keep_running}" = "true" ]; do
    echo "Sleeping for ${timeout}"
    sleep "${timeout}"
    echo "Getting logs from all services"
    docker compose  -p $PROJECT_NAME  -f ./docker/docker-compose.yml --env-file ./.env ps --filter status=running
    docker compose  -p $PROJECT_NAME  -f ./docker/docker-compose.yml --env-file ./.env --profile ci logs --since "${timeout}"
    echo "Following services are running"
    status="$(docker compose  -p $PROJECT_NAME  -f ./docker/docker-compose.yml --env-file ./.env ps --filter status=running --services)"
    echo "$status"
    testing_container_Status="$(docker inspect ${TESTING_CONTAINER_NAME} --format='{{.State.Status}}')"
    echo "testing container is ${testing_container_Status}"
    if [ $testing_container_Status = "exited" ]; then
        keep_running="false"
        echo "Stopping all services"
        testing_exit_code="$(docker inspect ${TESTING_CONTAINER_NAME} --format='{{.State.ExitCode}}')"
        docker compose  -p $PROJECT_NAME  -f ./docker/docker-compose.yml --env-file ./.env --profile ci down -v --remove-orphans
        exit_code=${testing_exit_code}
    fi
done

echo "Bye!"
exit "${exit_code}"
