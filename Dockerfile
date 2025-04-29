FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       default-jre \
       ghostscript \
       libopencv-dev \
       python3-opencv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir jpype1 tabula-py

COPY . .

EXPOSE 8085

CMD ["python", "app.py"]
