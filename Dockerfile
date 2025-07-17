FROM python:3.12-slim

# Install system dependencies including Oracle Instant Client
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       default-jre \
       ghostscript \
       libopencv-dev \
       python3-opencv \
       wget \
       unzip \
       libaio1 \
       gcc \
       g++ \
       build-essential \
       libffi-dev \
       libssl-dev \
       python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN wget -q https://download.oracle.com/otn_software/linux/instantclient/2340000/instantclient-basiclite-linux.x64-23.4.0.24.05.zip \
    && unzip instantclient-basiclite-linux.x64-23.4.0.24.05.zip \
    && mv instantclient_23_4 /opt/oracle \
    && rm instantclient-basiclite-linux.x64-23.4.0.24.05.zip

# Configure Oracle environment variables
ENV LD_LIBRARY_PATH="/opt/oracle:$LD_LIBRARY_PATH"
ENV ORACLE_HOME="/opt/oracle"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir jpype1 tabula-py

COPY . .

# Make startup script executable
RUN chmod +x scripts/start.sh

EXPOSE 8085

CMD ["bash", "scripts/start.sh"]
