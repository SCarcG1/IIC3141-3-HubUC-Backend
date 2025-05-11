FROM edoburu/pgbouncer

# Copiamos nuestro custom entrypoint y config
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini
COPY entrypoint.sh /entrypoint.sh

# Dar permisos de ejecución al entrypoint
RUN chmod +x /entrypoint.sh

# Usar nuestro entrypoint custom
ENTRYPOINT ["/entrypoint.sh"]