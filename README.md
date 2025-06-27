# pdf2json-api

API REST em Python para converter arquivos PDF em JSON com metadados e tabelas extraídas.


## Endpoints

- `GET /` : verifica status da API  
- `POST /analyze` : envia um PDF (campo `file`) e recebe JSON  

## Docker

Na raiz do projeto execute:

- Build: `docker build -t pdf2json-api .`  
- Run: `docker run -p 8085:8085 pdf2json-api`  

A API estará disponível em `http://localhost:8085/`.

## Docker-compose

Na raiz do projeto execute:

- Build and Run: `docker-compose up -d`
- Stop: `docker-compose down`

A API estará disponível em `http://localhost:8085/`.

## Testes

Leia o README na pasta tests