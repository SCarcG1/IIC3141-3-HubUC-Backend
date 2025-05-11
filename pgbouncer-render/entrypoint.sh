#!/bin/bash

# Crea el archivo userlist.txt dinámicamente con el usuario y contraseña de las env vars
echo "\"$PG_USER\" \"$PG_PASSWORD\"" > /etc/pgbouncer/userlist.txt

# Ejecuta el comando original (pgbouncer)
exec pgbouncer /etc/pgbouncer/pgbouncer.ini
