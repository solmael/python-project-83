#!/usr/bin/env bash

curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
set -e

if [ -z "$DATABASE_URL" ]; then
    echo "Ошибка: DATABASE_URL не задана"
    exit 1
fi

echo "Выполняем миграции..."
make install && psql -a -d $DATABASE_URL -f database.sql