#!/usr/bin/env bash

SCRIPT_DIR=`dirname -- "$( readlink -f -- "$0"; )"`
VENV_BIN_DIR=`readlink -f $SCRIPT_DIR/../../.venv/bin`

$VENV_BIN_DIR/poetry run invoke lint
