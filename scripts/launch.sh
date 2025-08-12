#!/bin/bash

DEFAULT_SQLLITE_FILE_PATH="/data/sql/lqbot.db"

if [ -z "$SQLLITE_FILE_PATH" ]; then
    export SQLLITE_FILE_PATH="$DEFAULT_SQLLITE_FILE_PATH"
fi

ABS_SQLLITE_FILE_PATH="$(realpath -m "$SQLLITE_FILE_PATH")"
mkdir -p "$(dirname "$ABS_SQLLITE_FILE_PATH")"

export SQL_DATABASE_URI="sqlite:///$ABS_SQLLITE_FILE_PATH"

bash ./scripts/create_db.sh

poetry run poe run
