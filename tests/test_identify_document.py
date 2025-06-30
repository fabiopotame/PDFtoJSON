import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import json
from io import BytesIO

from pdf2json.identify_document import extract_document_title, analyze_document_by_type


class TestExtractDocumentTitle(unittest.TestCase):
    """Test document title extraction functionality"""
    
    def test_extract_document_title_with_demonstrativo_servicos(self):
        """Test title extraction with DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS"""
        mock_text = "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS\nOutras informações..."
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_page = Mock()
            mock_page.extract_text.return_value = mock_text
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
            
            result = extract_document_title('dummy_path')
            
            self.assertEqual(result, "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS")
    
    def test_extract_document_title_with_demonstrativo_calculo(self):
        """Test title extraction with DEMONSTRATIVO DE CÁLCULO"""
        mock_text = "DEMONSTRATIVO DE CÁLCULO\nOutras informações..."
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_page = Mock()
            mock_page.extract_text.return_value = mock_text
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
            
            result = extract_document_title('dummy_path')
            
            self.assertEqual(result, "DEMONSTRATIVO DE CÁLCULO")
    
    def test_extract_document_title_with_other_title(self):
        """Test title extraction with other document title"""
        mock_text = "OUTRO TÍTULO DE DOCUMENTO\nOutras informações..."
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_page = Mock()
            mock_page.extract_text.return_value = mock_text
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
            
            result = extract_document_title('dummy_path')
            
            self.assertEqual(result, "OUTRO TÍTULO DE DOCUMENTO")
    
    def test_extract_document_title_with_empty_pdf(self):
        """Test title extraction with empty PDF"""
        mock_text = ""
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_page = Mock()
            mock_page.extract_text.return_value = mock_text
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
            
            result = extract_document_title('dummy_path')
            
            self.assertIsNone(result)
    
    def test_extract_document_title_with_no_pages(self):
        """Test title extraction with PDF that has no pages"""
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf.return_value.__enter__.return_value.pages = []
            
            result = extract_document_title('dummy_path')
            
            self.assertIsNone(result)
    
    def test_extract_document_title_with_exception(self):
        """Test title extraction when an exception occurs"""
        with patch('pdfplumber.open') as mock_pdf:
            mock_pdf.side_effect = Exception("PDF error")
            
            result = extract_document_title('dummy_path')
            
            self.assertIsNone(result)
    
    def test_extract_document_title_with_whitespace_only(self):
        """Test title extraction with whitespace-only lines"""
        mock_text = "   \n  \n  DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS  \n"
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_page = Mock()
            mock_page.extract_text.return_value = mock_text
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
            
            result = extract_document_title('dummy_path')
            
            self.assertEqual(result, "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS")


class TestAnalyzeDocumentByType(unittest.TestCase):
    """Test document type analysis and routing functionality"""
    
    def test_analyze_document_by_type_demonstrativo_servicos(self):
        """Test analysis with DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS"""
        mock_result = {
            'header': {'test': 'value'},
            'sections': [{'section': 'data'}]
        }
        
        with patch('pdf2json.identify_document.extract_document_title', return_value="DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS"):
            with patch('builtins.open', create=True) as mock_open:
                mock_file = Mock()
                mock_file.name = 'dummy_path'
                mock_open.return_value.__enter__.return_value = mock_file
                with patch('pdf2json.document_001.read_pdf_and_analyze', return_value=mock_result):
                    result = analyze_document_by_type('dummy_path')
        
        self.assertEqual(result['document_type'], "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS")
        self.assertEqual(result['header'], {'test': 'value'})
        self.assertEqual(result['sections'], [{'section': 'data'}])
    
    def test_analyze_document_by_type_demonstrativo_calculo(self):
        """Test analysis with DEMONSTRATIVO DE CÁLCULO"""
        mock_result = {
            'header': {'test': 'value'},
            'beneficiario': {'test': 'value'}
        }
        
        with patch('pdf2json.identify_document.extract_document_title', return_value="DEMONSTRATIVO DE CÁLCULO"):
            with patch('pdf2json.document_002.PDFLineParser') as mock_parser_class:
                mock_parser = Mock()
                mock_parser.parse_pdf.return_value = mock_result
                mock_parser_class.return_value = mock_parser
                
                # Mock pdfplumber.open to avoid file not found error
                with patch('pdfplumber.open') as mock_pdf:
                    mock_page = Mock()
                    mock_page.extract_text.return_value = "DEMONSTRATIVO DE CÁLCULO"
                    mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
                    
                    result = analyze_document_by_type('dummy_path')
        
        self.assertEqual(result['document_type'], "DEMONSTRATIVO DE CÁLCULO")
        self.assertEqual(result['header'], {'test': 'value'})
        self.assertEqual(result['beneficiario'], {'test': 'value'})
    
    def test_analyze_document_by_type_unknown_document(self):
        """Test analysis with unknown document type"""
        with patch('pdf2json.identify_document.extract_document_title', return_value="DOCUMENTO DESCONHECIDO"):
            result = analyze_document_by_type('dummy_path')
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], "Document type not recognized")
        self.assertEqual(result['document_title'], "DOCUMENTO DESCONHECIDO")
        self.assertIn('supported_types', result)
        self.assertIn("DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS", result['supported_types'])
        self.assertIn("DEMONSTRATIVO DE CÁLCULO", result['supported_types'])
    
    def test_analyze_document_by_type_no_title(self):
        """Test analysis when no title can be extracted"""
        with patch('pdf2json.identify_document.extract_document_title', return_value=None):
            result = analyze_document_by_type('dummy_path')
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], "Could not extract document title")
        self.assertIn('supported_types', result)
    
    def test_analyze_document_by_type_case_insensitive(self):
        """Test analysis with case insensitive matching"""
        mock_result = {'header': {'test': 'value'}}
        
        with patch('pdf2json.identify_document.extract_document_title', return_value="demonstrativo de cálculo"):
            with patch('pdf2json.document_002.PDFLineParser') as mock_parser_class:
                mock_parser = Mock()
                mock_parser.parse_pdf.return_value = mock_result
                mock_parser_class.return_value = mock_parser
                
                # Mock pdfplumber.open to avoid file not found error
                with patch('pdfplumber.open') as mock_pdf:
                    mock_page = Mock()
                    mock_page.extract_text.return_value = "demonstrativo de cálculo"
                    mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
                    
                    result = analyze_document_by_type('dummy_path')
        
        self.assertEqual(result['document_type'], "demonstrativo de cálculo")
        self.assertEqual(result['header'], {'test': 'value'})


class TestAnalyzeDocumentByTypeIntegration(unittest.TestCase):
    """Integration tests for document analysis"""
    
    def test_analyze_document_by_type_with_real_file(self):
        """Test analysis with a real file path"""
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            with patch('pdf2json.identify_document.extract_document_title', return_value="DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS"):
                with patch('pdf2json.document_001.read_pdf_and_analyze') as mock_analyze:
                    mock_analyze.return_value = {'test': 'data'}
                    
                    result = analyze_document_by_type(temp_file_path)
                    
                    self.assertEqual(result['document_type'], "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS")
                    self.assertEqual(result['test'], 'data')
                    
                    # Verify that the analyzer was called
                    mock_analyze.assert_called_once()
        
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_analyze_document_by_type_error_handling(self):
        """Test error handling in document analysis"""
        with patch('pdf2json.identify_document.extract_document_title', side_effect=Exception("Test error")):
            result = analyze_document_by_type('dummy_path')
        
        self.assertIn('error', result)
        self.assertEqual(result['error'], "Could not extract document title")


class TestDocumentTypeEdgeCases(unittest.TestCase):
    """Test edge cases for document type detection"""
    
    def test_extract_document_title_with_partial_match(self):
        """Test title extraction with partial match of DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS"""
        mock_text = "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS ADICIONAIS\nOutras informações..."
        
        with patch('pdfplumber.open') as mock_pdf:
            mock_page = Mock()
            mock_page.extract_text.return_value = mock_text
            mock_pdf.return_value.__enter__.return_value.pages = [mock_page]
            
            result = extract_document_title('dummy_path')
            
            self.assertEqual(result, "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS ADICIONAIS")
    
    def test_analyze_document_by_type_with_variations(self):
        """Test analysis with various document title variations"""
        test_cases = [
            ("DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS", "document_001"),
            ("Demonstrativo de Cálculo de Serviços", "document_001"),
            ("DEMONSTRATIVO DE CÁLCULO", "document_002"),
            ("Demonstrativo de Cálculo", "document_002"),
            ("demonstrativo de cálculo", "document_002"),
            ("OUTRO DOCUMENTO", "unknown")
        ]
        
        for title, expected_parser in test_cases:
            with self.subTest(title=title):
                with patch('pdf2json.identify_document.extract_document_title', return_value=title):
                    if expected_parser == "document_001":
                        with patch('builtins.open', create=True) as mock_open:
                            mock_file = Mock()
                            mock_file.name = 'dummy_path'
                            mock_open.return_value.__enter__.return_value = mock_file
                            with patch('pdf2json.document_001.read_pdf_and_analyze', return_value={'test': 'data'}):
                                result = analyze_document_by_type('dummy_path')
                        self.assertEqual(result['document_type'], title)
                    elif expected_parser == "document_002":
                        with patch('pdf2json.document_002.PDFLineParser') as mock_parser_class:
                            mock_parser = Mock()
                            mock_parser.parse_pdf.return_value = {'test': 'data'}
                            mock_parser_class.return_value = mock_parser
                            result = analyze_document_by_type('dummy_path')
                        self.assertEqual(result['document_type'], title)
                    else:
                        result = analyze_document_by_type('dummy_path')
                        self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main() 