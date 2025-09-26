# PostgreSQL Dockerfile
FROM postgres:16-alpine

# Устанавливаем переменные окружения
ENV POSTGRES_DB=${POSTGRES_DB}
ENV POSTGRES_USER=${POSTGRES_USER}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Открываем порт PostgreSQL
EXPOSE 5432

# Запускаем PostgreSQL
CMD ["postgres"]
