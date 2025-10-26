#!/bin/sh

echo "Aguardando o banco de dados ficar disponível..."

while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 1
done

echo "Banco disponível, iniciando aplicação..."
exec "$@"
