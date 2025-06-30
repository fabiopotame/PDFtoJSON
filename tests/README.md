# Testes Unitários - PDF to JSON Converter

Este diretório contém todos os testes unitários para o parser de PDF para JSON.

## Estrutura dos Testes

### `test_document_001.py`
Testes para o parser baseado em coordenadas (`document_001.py`):
- Testes de extração de cabeçalho, seções, dados por coordenadas e integração.

### `test_document_002.py`
Testes para o parser baseado em linhas (`document_002.py`):
- Testes de extração de campos por linha, tabelas, totais, integração e casos de borda.

### `test_identify_document.py`
Testes para roteamento e identificação automática do tipo de documento (`identify_document.py`):
- Testes de extração do título do documento
- Testes de roteamento para o parser correto
- Testes de respostas de erro e casos de borda

## Como Executar os Testes

### Opção 1: Usando o script personalizado
```bash
./scripts/run_tests.sh
```

### Opção 2: Usando unittest diretamente
```bash
python -m unittest discover tests -v
```

### Opção 3: Usando pytest (se instalado)
```bash
pytest tests/ -v
```

### Opção 4: Executar um teste específico
```bash
python -m unittest tests.test_document_002.TestPDFLineParser -v
```

## Cobertura dos Testes

Os testes cobrem:

### ✅ Parsers de Documento
- `document_001.py` (coordenadas): extração de cabeçalho, seções, dados tabulares
- `document_002.py` (linhas): extração de campos, tabelas, totais, validações

### ✅ Roteamento e Identificação
- `identify_document.py`: extração do título, roteamento automático, respostas de erro

### ✅ Casos de Borda e Erro
- PDFs vazios, dados ausentes, valores nulos, títulos desconhecidos, exceções

## Adicionando Novos Testes

Para adicionar novos testes:

1. **Crie uma nova classe de teste** seguindo o padrão `TestClassName`
2. **Use mocks** para simular dependências externas (pdfplumber, etc.)
3. **Teste casos positivos e negativos** para cada função
4. **Documente o propósito** de cada teste com docstrings
5. **Execute os testes** para garantir que passam

### Exemplo de Novo Teste:
```python
class TestNewFunction(unittest.TestCase):
    """Test new function functionality"""
    
    def test_new_function_success(self):
        """Test successful execution"""
        # Arrange
        input_data = "test"
        
        # Act
        result = new_function(input_data)
        
        # Assert
        self.assertEqual(result, "expected")
    
    def test_new_function_error(self):
        """Test error handling"""
        # Arrange
        input_data = None
        
        # Act & Assert
        with self.assertRaises(ValueError):
            new_function(input_data)
```

## Manutenção dos Testes

- **Execute os testes regularmente** após mudanças no código
- **Mantenha os mocks atualizados** quando a API externa mudar
- **Adicione testes para novos bugs** encontrados
- **Refatore testes** quando o código for refatorado
- **Mantenha a cobertura alta** (idealmente >90%)

## Relatórios de Teste

O script `run_tests.sh` gera relatórios detalhados incluindo:
- Número total de testes executados
- Taxa de sucesso
- Lista de falhas e erros
- Stack traces para debugging

## Integração Contínua

Os testes podem ser integrados em pipelines CI/CD:
- Execute `./scripts/run_tests.sh` no build
- Use o código de saída para determinar sucesso/falha
- Configure alertas para falhas de teste 