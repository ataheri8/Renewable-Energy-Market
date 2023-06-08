#!/usr/bin/env bash

set -u

modules_names=("worker" "scheduler" "bucket_watcher")
valid_params=("pm" "pytest" "api" "der_gateway_relay" "${modules_names[@]}")

if [[ ! ${valid_params[*]} =~ ${TASK_TO_RUN} ]]; then
    echo "Error: module name '${TASK_TO_RUN}' is invalid" >&2
    echo "Possible values: ${valid_params[*]}"
    exit 2
else
    cmd=()
    cd src || exit 1
    echo "Starting ${TASK_TO_RUN}"

    if [[ ${TASK_TO_RUN} == "pm" ]]; then
        cmd=(gunicorn "${TASK_TO_RUN}.restapi.web:create_app()" -b 0.0.0.0:8000)
    elif [[ ${TASK_TO_RUN} == "pytest" ]]; then
        cmd=(pytest -v "--cov=./pm" "--cov-config=../pyproject.toml")
        cmd=("${cmd[@]}" "--cov-fail-under=95" "--ignore=./der_gateway_relay" .)
    elif [[ ${TASK_TO_RUN} == "api" ]]; then
        cmd=(gunicorn "pm.restapi.web:create_app()" -b 0.0.0.0:3001 --reload)
    elif [[ ${TASK_TO_RUN} == "der_gateway_relay" ]]; then
        cmd=(python -m "der_gateway_relay.main")
    elif [[ ${modules_names[*]} =~ ${TASK_TO_RUN} ]]; then
        cmd=(python -m "pm.${TASK_TO_RUN}")
    fi

    exec "${cmd[@]}"
fi
