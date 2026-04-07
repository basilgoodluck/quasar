FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y curl ca-certificates && rm -rf /var/lib/apt/lists/*

RUN curl --proto '=https' --tlsv1.2 -LsSf \
    https://github.com/krakenfx/kraken-cli/releases/latest/download/kraken-cli-installer.sh | sh

ENV PATH="/root/.cargo/bin:/root/.local/bin:${PATH}"
ENV KRAKEN_FUTURES_URL="https://demo-futures.kraken.com"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "agent/main.py"]