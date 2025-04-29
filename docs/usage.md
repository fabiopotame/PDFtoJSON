# Uso da API

## Converter PDF

```bash
curl -F 'file=@exemplo.pdf' http://localhost:8085/convert
```

Resposta:

```json
{
  "metadata": { ... },
  "tables": { ... }
}
```