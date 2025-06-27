# Testes Unitários - PDF to JSON Converter

Este diretório contém todos os testes unitários para o parser de PDF para JSON.

## Estrutura dos Testes

### `test_pdf_analyzer.py`
Testes abrangentes para todas as funções do módulo `pdf_analyzer.py`:

- **TestPDFAnalyzerConstants**: Testa constantes e configurações
- **TestExtractHeaderInfo**: Testa extração de informações do cabeçalho
- **TestIsBlueLine**: Testa detecção de linhas azuis
- **TestExtractTextByCoordinates**: Testa extração de texto por coordenadas
- **TestIsHeaderLine**: Testa detecção de linhas de cabeçalho
- **TestIsValidDataRow**: Testa validação de linhas de dados
- **TestIsNewRecord**: Testa detecção de novos registros
- **TestExtractSectionData**: Testa extração de dados de seções
- **TestExtractDataWithHeaderMapping**: Testa extração principal de dados
- **TestReadPdfAndAnalyze**: Testa função principal de análise
- **TestIntegration**: Testes de integração e consistência

## Como Executar os Testes

### Opção 1: Usando o script personalizado
```bash
python run_tests.py
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
python -m unittest tests.test_pdf_analyzer.TestIsBlueLine -v
```

## Cobertura dos Testes

Os testes cobrem:

### ✅ Funções Principais
- `extract_header_info()` - Extração de cabeçalho
- `is_blue_line()` - Detecção de linhas azuis
- `extract_text_by_coordinates()` - Extração por coordenadas
- `is_header_line()` - Detecção de cabeçalhos
- `is_valid_data_row()` - Validação de dados
- `is_new_record()` - Detecção de novos registros
- `extract_section_data()` - Extração de seções
- `extract_data_with_header_mapping()` - Extração principal
- `read_pdf_and_analyze()` - Função principal

### ✅ Constantes e Configurações
- `HEADER_MAPPING` - Mapeamento de colunas
- `MULTI_LINE_FIELDS` - Campos multi-linha
- `VALID_SECTIONS` - Seções válidas
- `BLUE_COLOR` - Cor das linhas azuis
- Coordenadas de página

### ✅ Casos de Borda
- PDFs vazios
- Dados ausentes
- Valores nulos
- Coordenadas fora dos limites
- Textos inválidos

### ✅ Cenários de Erro
- Exceções durante processamento
- Dados malformados
- Valores inesperados

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

O script `run_tests.py` gera relatórios detalhados incluindo:
- Número total de testes executados
- Taxa de sucesso
- Lista de falhas e erros
- Stack traces para debugging

## Integração Contínua

Os testes podem ser integrados em pipelines CI/CD:
- Execute `python run_tests.py` no build
- Use o código de saída para determinar sucesso/falha
- Configure alertas para falhas de teste 