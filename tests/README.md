# Unit Tests - PDF to JSON Converter

This directory contains all unit tests for the PDF to JSON parser.

## Test Structure

### `test_document_001.py`
Tests for coordinate-based parser (`document_001.py`):
- Tests for header extraction, sections, coordinate-based data extraction and integration.

### `test_document_002.py`
Tests for line-based parser (`document_002.py`):
- Tests for field extraction by line, tables, totals, integration and edge cases.

### `test_identify_document.py`
Tests for routing and automatic document type identification (`identify_document.py`):
- Tests for document title extraction
- Tests for routing to correct parser
- Tests for error responses and edge cases

## How to Run Tests

### Option 1: Using custom script
```bash
./scripts/run_tests.sh
```

### Option 2: Using unittest directly
```bash
python -m unittest discover tests -v
```

### Option 3: Using pytest (if installed)
```bash
pytest tests/ -v
```

### Option 4: Run a specific test
```bash
python -m unittest tests.test_document_002.TestPDFLineParser -v
```

## Test Coverage

Tests cover:

### ✅ Document Parsers
- `document_001.py` (coordinates): header extraction, sections, tabular data
- `document_002.py` (lines): field extraction, tables, totals, validations

### ✅ Routing and Identification
- `identify_document.py`: title extraction, automatic routing, error responses

### ✅ Edge Cases and Errors
- Empty PDFs, missing data, null values, unknown titles, exceptions

## Adding New Tests

To add new tests:

1. **Create a new test class** following the `TestClassName` pattern
2. **Use mocks** to simulate external dependencies (pdfplumber, etc.)
3. **Test positive and negative cases** for each function
4. **Document the purpose** of each test with docstrings
5. **Run tests** to ensure they pass

### Example of New Test:
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

## Test Maintenance

- **Run tests regularly** after code changes
- **Keep mocks updated** when external API changes
- **Add tests for new bugs** found
- **Refactor tests** when code is refactored
- **Keep coverage high** (ideally >90%)

## Test Reports

The `run_tests.sh` script generates detailed reports including:
- Total number of tests executed
- Success rate
- List of failures and errors
- Stack traces for debugging

## Continuous Integration

Tests can be integrated into CI/CD pipelines:
- Run `./scripts/run_tests.sh` in the build
- Use exit code to determine success/failure
- Configure alerts for test failures 