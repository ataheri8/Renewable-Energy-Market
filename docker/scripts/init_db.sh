#!/usr/bin/env bash

set -u
#set -x  # Enable for easy debugging (verbose logging).

if [[ ${DROP_DB} == "true" ]]; then
    echo "Droping database ${DB_NAME}"
    PGPASSWORD="${DB_PASSWORD}" psql -U "${DB_USERNAME}" -h "${DB_HOST}" -p "${DB_PORT}" -d postgres -c "DROP DATABASE ${DB_NAME};"
fi

if PGPASSWORD="${DB_PASSWORD}" psql -U "${DB_USERNAME}" -h "${DB_HOST}" -p "${DB_PORT}" -d postgres -c "CREATE DATABASE ${DB_NAME};" &>/dev/null; then
    echo "Database ${DB_NAME} created"
else
    echo "Database ${DB_NAME} already exists"
fi

echo "Running migrations"
exec flyway "-user=${DB_USERNAME}" "-password=${DB_PASSWORD}" "-url=jdbc:postgresql://${DB_HOST}:${DB_PORT}/${DB_NAME}" "-locations=${LOCATIONS}" migrate
