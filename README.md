# PDF to JSON API

API REST em Python para converter arquivos PDF em JSON com metadados e tabelas extraídas.

## 🚀 Novo Front-end Web

A aplicação agora inclui um front-end web moderno com Bootstrap! Acesse `http://localhost:8085/` após iniciar a aplicação.

### Recursos do Front-end:
- ✨ Interface moderna e responsiva com Bootstrap 5
- 📤 Upload por drag & drop ou seleção de arquivo
- 📊 Visualização do JSON resultante formatado
- 🔄 Indicador de status da API em tempo real
- ⚡ Feedback visual durante o processamento
- 🎨 Design elegante com gradientes e animações

## Endpoints da API

- `GET /` : interface web para upload de arquivos
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

## 🏃‍♂️ Execução

### Método 1: Docker (Recomendado)

Na raiz do projeto execute:

- Build: `docker build -t pdf2json-api .`  
- Run: `docker run -p 8085:8085 pdf2json-api`  

### Método 2: Docker-compose

Na raiz do projeto execute:

- Build and Run: `docker-compose up -d`
- Stop: `docker-compose down`

### Método 3: Execução local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python app.py
```

**A aplicação estará disponível em `http://localhost:8085/`**

## 🧪 Testes

### Executar Testes com Docker

```bash
# Executar testes standalone (sem iniciar a API)
docker-compose run test-standalone

# Executar testes após iniciar a API
docker-compose run test

# Executar API e testes juntos
docker-compose up api test
```

### Executar Testes Localmente

```bash
# Executar todos os testes
python3 -m unittest discover tests -v

# Executar um teste específico
python3 -m unittest tests.test_identify_document -v

# Usar o script de testes
bash scripts/test_only.sh
```

### Cobertura de Testes

Os testes cobrem:
- ✅ Parsers de documento (coordenadas e linhas)
- ✅ Identificação automática de tipo de documento
- ✅ Roteamento para parser correto
- ✅ Casos de borda e tratamento de erros
- ✅ Validação de dados extraídos

Leia o README na pasta `tests/` para mais detalhes.

## 📱 Como usar o Front-end

1. **Acesse**: `http://localhost:8085/`
2. **Upload**: Arraste um arquivo PDF para a área de upload ou clique para selecionar
3. **Conversão**: Clique em "Converter para JSON" 
4. **Resultado**: Visualize o JSON estruturado na área de resultado

## 🛠️ Tecnologias Utilizadas

### Backend:
- Flask (API REST)
- PyPDF2 (Processamento de PDF)
- pdfplumber (Extração de tabelas)
- Flask-CORS (Suporte a CORS)
- Oracle Database (Armazenamento)

### Frontend:
- HTML5 + CSS3 + JavaScript
- Bootstrap 5 (Interface responsiva)
- Font Awesome (Ícones)
- Fetch API (Comunicação com backend)

## 📂 Estrutura do Projeto

```
PDFtoJSON/
├── app.py                 # Aplicação Flask principal
├── config.py              # Configurações
├── requirements.txt       # Dependências Python
├── docker-compose.yml     # Configuração Docker
├── static/
│   └── index.html        # Front-end web
├── pdf2json/             # Módulo de processamento
│   ├── identify_document.py
│   ├── document_001.py
│   └── document_002.py
├── db/                   # Módulo de banco de dados
│   └── oracle_connection.py
├── tests/                # Testes unitários
├── scripts/              # Scripts utilitários
│   ├── start.sh         # Script de inicialização
│   ├── run_tests.sh     # Script de testes
│   └── test_only.sh     # Script de testes standalone
├── oracle/              # Wallet Oracle
└── README.md
```