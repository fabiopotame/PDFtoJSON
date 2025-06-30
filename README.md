# pdf2json-api

API REST em Python para converter arquivos PDF em JSON com metadados e tabelas extraídas.


## Endpoints

- `GET /health` : verifica status da API. Retorna `{ "status": "healthy", "message": "PDF to JSON API is running" }`
- `POST /document` : envia um PDF (campo `file` em multipart/form-data) e recebe o JSON extraído automaticamente pelo parser correto, de acordo com o tipo do documento.

### Exemplo de uso do endpoint /document

**Requisição:**

POST http://localhost:8085/document

Form-data:
- file: <seu_arquivo.pdf>

**Resposta de sucesso:**
```json
{
  "document_type": "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS",
  "header": { ... },
  "sections": [ ... ]
}
```

**Resposta de erro:**
```json
{
  "error": "Document type not recognized",
  "document_title": "OUTRO DOCUMENTO",
  "supported_types": [
    "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS",
    "DEMONSTRATIVO DE CÁLCULO"
  ]
}
```

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