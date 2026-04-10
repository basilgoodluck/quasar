ARG DOCKER_USERNAME
FROM ${DOCKER_USERNAME}/quasar-base:latest

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7052", "--app-dir", "/app/backend"]