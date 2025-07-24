FROM python:3.12-slim

USER root

# Instalar dependências do sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       default-jre \
       ghostscript \
       libopencv-dev \
       python3-opencv \
       wget \
       gcc \
       g++ \
       build-essential \
       libffi-dev \
       libssl-dev \
       libaio1 \
       python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir jpype1 tabula-py

COPY . .

RUN chmod +x scripts/start.sh

EXPOSE 8085

CMD ["bash", "scripts/start.sh"]
