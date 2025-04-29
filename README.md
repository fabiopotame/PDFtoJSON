# pdf2json-api

API REST em Python para converter arquivos PDF em JSON com metadados e tabelas extraídas.

## Setup

1. Clone o repositório  
2. `pip install -r requirements.txt`  
3. `python app.py`  

A API estará disponível em `http://localhost:8085/`.

## Endpoints

- `GET /` : verifica status da API  
- `POST /convert` : envia um PDF (campo `file`) e recebe JSON  

## Docker

- Build: `docker build -t pdf2json-api .`  
- Run: `docker run -p 8085:8085 pdf2json-api`  

## Testes

`./scripts/run_tests.sh`