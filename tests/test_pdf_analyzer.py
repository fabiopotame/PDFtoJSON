import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import json
from io import BytesIO

# Import the functions to test
from pdf2json.pdf_analyzer import (
    extract_header_info,
    is_blue_line,
    extract_text_by_coordinates,
    is_header_line,
    is_valid_data_row,
    is_new_record,
    extract_section_data,
    extract_data_with_header_mapping,
    read_pdf_and_analyze,
    HEADER_MAPPING,
    MULTI_LINE_FIELDS,
    VALID_SECTIONS,
    PORTUGUESE_HEADER_KEYWORDS,
    ENGLISH_HEADER_KEYWORDS,
    BLUE_COLOR,
    PAGE1_START_Y,
    OTHER_PAGES_START_Y,
    FOOTER_Y_MIN
)


class TestPDFAnalyzerConstants(unittest.TestCase):
    """Test constants and configurations"""
    
    def test_header_mapping_structure(self):
        """Test that HEADER_MAPPING has the correct structure"""
        self.assertIsInstance(HEADER_MAPPING, dict)
        self.assertGreater(len(HEADER_MAPPING), 0)
        
        for field_name, coords in HEADER_MAPPING.items():
            self.assertIsInstance(field_name, str)
            self.assertIsInstance(coords, dict)
            self.assertIn('x0', coords)
            self.assertIn('x1', coords)
            self.assertIsInstance(coords['x0'], (int, float))
            self.assertIsInstance(coords['x1'], (int, float))
            self.assertLess(coords['x0'], coords['x1'])
    
    def test_multi_line_fields(self):
        """Test that MULTI_LINE_FIELDS contains all header mapping keys"""
        self.assertEqual(set(MULTI_LINE_FIELDS), set(HEADER_MAPPING.keys()))
    
    def test_valid_sections(self):
        """Test that VALID_SECTIONS contains expected values"""
        expected_sections = ['Armazenagem', 'Cadastro', 'Handling', 'Presenca', 'Repasse', 'Scanner']
        self.assertEqual(set(VALID_SECTIONS), set(expected_sections))
    
    def test_constants_values(self):
        """Test that constants have expected values"""
        self.assertEqual(BLUE_COLOR, "(0.098, 0.098, 0.439)")
        self.assertEqual(PAGE1_START_Y, 159.0)
        self.assertEqual(OTHER_PAGES_START_Y, 67.5)
        self.assertEqual(FOOTER_Y_MIN, 515.0)


class TestExtractHeaderInfo(unittest.TestCase):
    """Test header extraction functionality"""
    
    def test_extract_header_info_with_valid_text(self):
        """Test header extraction with valid PDF text"""
        mock_text = """
        CLIENTE: TESTE EMPRESA LTDA
        NAVIO: TESTE VESSEL / 001W
        ATRAÇÃO: BERCO 1
        DEMONSTRATIVO: 123456
        VALOR BRUTO R$: (BRL) 1.234,56
        """
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_page = Mock()
            mock_page.extract_text.return_value = mock_text
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
            
            result = extract_header_info(Mock())
            
            self.assertIn('header', result)
            header = result['header']
            self.assertEqual(header['Cliente (Customer)'], 'TESTE EMPRESA LTDA')
            self.assertIn('TESTE VESSEL / 001W', header['Navio (Viessel)'])
            self.assertEqual(header['Atração (BERTH_ATA)'], 'BERCO 1')
            self.assertEqual(header['Demonstrativo (Draft)'], '123456')
            self.assertEqual(header['Valor Bruto'], 1234.56)
            self.assertEqual(header['Moeda'], 'BRL')
    
    def test_extract_header_info_with_missing_fields(self):
        """Test header extraction with missing fields"""
        mock_text = "CLIENTE: TESTE EMPRESA LTDA"
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_page = Mock()
            mock_page.extract_text.return_value = mock_text
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
            
            result = extract_header_info(Mock())
            header = result['header']
            
            if 'Cliente (Customer)' in header:
                self.assertEqual(header['Cliente (Customer)'], 'TESTE EMPRESA LTDA')
            self.assertIsNone(header.get('Atração (BERTH_ATA)'))
            self.assertEqual(header['Moeda'], 'BRL')


class TestIsBlueLine(unittest.TestCase):
    """Test blue line detection functionality"""
    
    def test_is_blue_line_with_stroking_color(self):
        """Test blue line detection with stroking color"""
        lines = [{'top': 100, 'stroking_color': BLUE_COLOR}]
        rects = []
        
        result = is_blue_line(100, lines, rects)
        self.assertTrue(result)
    
    def test_is_blue_line_with_non_stroking_color(self):
        """Test blue line detection with non-stroking color"""
        lines = []
        rects = [{'top': 100, 'non_stroking_color': BLUE_COLOR}]
        
        result = is_blue_line(100, lines, rects)
        self.assertTrue(result)
    
    def test_is_blue_line_with_different_color(self):
        """Test blue line detection with different color"""
        lines = [{'top': 100, 'stroking_color': '(1.0, 0.0, 0.0)'}]
        rects = []
        
        result = is_blue_line(100, lines, rects)
        self.assertFalse(result)
    
    def test_is_blue_line_with_tolerance(self):
        """Test blue line detection with coordinate tolerance"""
        lines = [{'top': 103, 'stroking_color': BLUE_COLOR}]  # 3 pixels difference
        rects = []
        
        result = is_blue_line(100, lines, rects)
        self.assertTrue(result)
    
    def test_is_blue_line_outside_tolerance(self):
        """Test blue line detection outside tolerance"""
        lines = [{'top': 110, 'stroking_color': BLUE_COLOR}]  # 10 pixels difference
        rects = []
        
        result = is_blue_line(100, lines, rects)
        self.assertFalse(result)


class TestExtractTextByCoordinates(unittest.TestCase):
    """Test text extraction by coordinates functionality"""
    
    def test_extract_text_by_coordinates_with_chars(self):
        """Test text extraction with valid characters"""
        chars_list = [
            {'text': 'Hello', 'x0': 10, 'x1': 15},
            {'text': 'World', 'x0': 20, 'x1': 25},
            {'text': 'Test', 'x0': 30, 'x1': 35}
        ]
        
        result = extract_text_by_coordinates(chars_list, 15, 35)
        self.assertEqual(result, 'WorldTest')
    
    def test_extract_text_by_coordinates_no_chars(self):
        """Test text extraction with no characters in range"""
        chars_list = [
            {'text': 'Hello', 'x0': 10, 'x1': 15},
            {'text': 'World', 'x0': 20, 'x1': 25}
        ]
        
        result = extract_text_by_coordinates(chars_list, 50, 60)
        self.assertEqual(result, '')
    
    def test_extract_text_by_coordinates_empty_list(self):
        """Test text extraction with empty character list"""
        result = extract_text_by_coordinates([], 10, 20)
        self.assertEqual(result, '')
    
    def test_extract_text_by_coordinates_boundary_chars(self):
        """Test text extraction with boundary characters"""
        chars_list = [
            {'text': 'Hello', 'x0': 10, 'x1': 15},
            {'text': 'World', 'x0': 15, 'x1': 20}
        ]
        
        result = extract_text_by_coordinates(chars_list, 10, 20)
        self.assertEqual(result, 'HelloWorld')


class TestIsHeaderLine(unittest.TestCase):
    """Test header line detection functionality"""
    
    def test_is_header_line_with_portuguese_keywords(self):
        """Test header detection with Portuguese keywords"""
        test_cases = [
            'Data Inicial',
            'Data Final',
            'Container',
            'Categoria',
            'Armador',
            'Manifesto',
            'Importador',
            'Exportador',
            'Observacoes'
        ]
        
        for keyword in test_cases:
            result = is_header_line(keyword)
            self.assertTrue(result, f"Failed for keyword: {keyword}")
    
    def test_is_header_line_with_english_keywords(self):
        """Test header detection with English keywords"""
        test_cases = [
            'Start Time',
            'End Time',
            'Equipment',
            'Category',
            'Line',
            'Manifest',
            'Consignee',
            'Shipper',
            'Notes'
        ]
        
        for keyword in test_cases:
            result = is_header_line(keyword)
            self.assertTrue(result, f"Failed for keyword: {keyword}")
    
    def test_is_header_line_with_amount_total(self):
        """Test header detection with AmountTotal (should be False)"""
        result = is_header_line('AmountTotal')
        self.assertFalse(result)
    
    def test_is_header_line_with_regular_text(self):
        """Test header detection with regular text"""
        test_cases = [
            '14/06/25',
            'CAIU9480556',
            'CMA',
            '10409614000347',
            'Some random text'
        ]
        
        for text in test_cases:
            result = is_header_line(text)
            self.assertFalse(result, f"Should be False for: {text}")


class TestIsValidDataRow(unittest.TestCase):
    """Test data row validation functionality"""
    
    def test_is_valid_data_row_with_valid_data(self):
        """Test validation with valid data row"""
        row = {
            'CNPJ / CPF (ID)': '10409614000347',
            'Data Inicial (Start Time)': '14/06/25',
            'Container (Equipment ID)': 'CAIU9480556'
        }
        
        result = is_valid_data_row(row)
        self.assertTrue(result)
    
    def test_is_valid_data_row_missing_cnpj(self):
        """Test validation with missing CNPJ"""
        row = {
            'CNPJ / CPF (ID)': '',
            'Data Inicial (Start Time)': '14/06/25',
            'Container (Equipment ID)': 'CAIU9480556'
        }
        
        result = is_valid_data_row(row)
        self.assertFalse(result)
    
    def test_is_valid_data_row_missing_date(self):
        """Test validation with missing date"""
        row = {
            'CNPJ / CPF (ID)': '10409614000347',
            'Data Inicial (Start Time)': '',
            'Container (Equipment ID)': 'CAIU9480556'
        }
        
        result = is_valid_data_row(row)
        self.assertFalse(result)
    
    def test_is_valid_data_row_missing_container(self):
        """Test validation with missing container"""
        row = {
            'CNPJ / CPF (ID)': '10409614000347',
            'Data Inicial (Start Time)': '14/06/25',
            'Container (Equipment ID)': ''
        }
        
        result = is_valid_data_row(row)
        self.assertFalse(result)
    
    def test_is_valid_data_row_with_none_values(self):
        """Test validation with None values"""
        row = {
            'CNPJ / CPF (ID)': None,
            'Data Inicial (Start Time)': '14/06/25',
            'Container (Equipment ID)': 'CAIU9480556'
        }
        
        result = is_valid_data_row(row)
        self.assertFalse(result)


class TestIsNewRecord(unittest.TestCase):
    """Test new record detection functionality"""
    
    def test_is_new_record_with_valid_data(self):
        """Test new record detection with valid data"""
        next_row = {
            'CNPJ / CPF (ID)': '10409614000347',
            'Data Inicial (Start Time)': '14/06/25',
            'Container (Equipment ID)': 'CAIU9480556'
        }
        
        result = is_new_record(next_row)
        self.assertTrue(result)
    
    def test_is_new_record_with_short_cnpj(self):
        """Test new record detection with short CNPJ"""
        next_row = {
            'CNPJ / CPF (ID)': '123',
            'Data Inicial (Start Time)': '14/06/25',
            'Container (Equipment ID)': 'CAIU9480556'
        }
        
        result = is_new_record(next_row)
        self.assertFalse(result)
    
    def test_is_new_record_without_date_slash(self):
        """Test new record detection without date slash"""
        next_row = {
            'CNPJ / CPF (ID)': '10409614000347',
            'Data Inicial (Start Time)': '140625',
            'Container (Equipment ID)': 'CAIU9480556'
        }
        
        result = is_new_record(next_row)
        self.assertFalse(result)
    
    def test_is_new_record_with_short_container(self):
        """Test new record detection with short container"""
        next_row = {
            'CNPJ / CPF (ID)': '10409614000347',
            'Data Inicial (Start Time)': '14/06/25',
            'Container (Equipment ID)': 'ABC'
        }
        
        result = is_new_record(next_row)
        self.assertFalse(result)


class TestExtractSectionData(unittest.TestCase):
    """Test section data extraction functionality"""
    
    def test_extract_section_data_no_blue_lines(self):
        """Test section extraction with no blue lines"""
        sorted_char_lines = []
        lines = []
        rects = []
        
        result = extract_section_data(0, sorted_char_lines, lines, rects)
        self.assertEqual(result, [])
    
    def test_extract_section_data_with_blue_line_outside_boundaries(self):
        """Test section extraction with blue line outside boundaries"""
        # Create mock data with blue line outside boundaries
        mock_chars = [{'text': 'Test', 'x0': 10, 'x1': 15}]
        sorted_char_lines = [(FOOTER_Y_MIN + 10, mock_chars)]  # Outside footer boundary
        
        lines = [{'top': FOOTER_Y_MIN + 10, 'stroking_color': BLUE_COLOR}]
        rects = []
        
        result = extract_section_data(0, sorted_char_lines, lines, rects)
        self.assertEqual(result, [])


class TestExtractDataWithHeaderMapping(unittest.TestCase):
    """Test main data extraction functionality"""
    
    @patch('pdfplumber.open')
    def test_extract_data_with_header_mapping_empty_pdf(self, mock_pdf):
        """Test data extraction with empty PDF"""
        mock_page = Mock()
        mock_page.lines = []
        mock_page.rects = []
        mock_page.chars = []
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
        
        result = extract_data_with_header_mapping(Mock())
        self.assertEqual(result, [])


class TestReadPdfAndAnalyze(unittest.TestCase):
    """Test main PDF analysis functionality"""
    
    @patch('pdf2json.pdf_analyzer.extract_header_info')
    @patch('pdf2json.pdf_analyzer.extract_data_with_header_mapping')
    def test_read_pdf_and_analyze_success(self, mock_extract_data, mock_extract_header):
        """Test successful PDF analysis"""
        mock_extract_header.return_value = {'header': {'test': 'value'}}
        mock_extract_data.return_value = [{'section': 'data'}]
        
        result = read_pdf_and_analyze(Mock())
        
        self.assertIn('header', result)
        self.assertIn('sections', result)
        self.assertEqual(result['header'], {'test': 'value'})
        self.assertEqual(result['sections'], [{'section': 'data'}])
    
    @patch('pdf2json.pdf_analyzer.extract_header_info')
    @patch('pdf2json.pdf_analyzer.extract_data_with_header_mapping')
    def test_read_pdf_and_analyze_exception(self, mock_extract_data, mock_extract_header):
        """Test PDF analysis with exception"""
        mock_extract_header.side_effect = Exception("Test error")
        
        result = read_pdf_and_analyze(Mock())
        
        self.assertIn('error', result)
        self.assertIn('header', result)
        self.assertIn('sections', result)
        self.assertEqual(result['error'], 'Test error')
        self.assertEqual(result['header'], {})
        self.assertEqual(result['sections'], [])


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow"""
    
    def test_constants_consistency(self):
        """Test that all constants are consistent"""
        # Test that all header mapping keys are in multi-line fields
        self.assertEqual(set(MULTI_LINE_FIELDS), set(HEADER_MAPPING.keys()))
        
        # Test that Portuguese and English keywords don't overlap
        portuguese_set = set(PORTUGUESE_HEADER_KEYWORDS)
        english_set = set(ENGLISH_HEADER_KEYWORDS)
        self.assertEqual(len(portuguese_set.intersection(english_set)), 0)
        
        # Test that coordinates are in ascending order
        x_coords = [coords['x0'] for coords in HEADER_MAPPING.values()]
        self.assertEqual(x_coords, sorted(x_coords))


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestPDFAnalyzerConstants,
        TestExtractHeaderInfo,
        TestIsBlueLine,
        TestExtractTextByCoordinates,
        TestIsHeaderLine,
        TestIsValidDataRow,
        TestIsNewRecord,
        TestExtractSectionData,
        TestExtractDataWithHeaderMapping,
        TestReadPdfAndAnalyze,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"TESTS SUMMARY:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}") 