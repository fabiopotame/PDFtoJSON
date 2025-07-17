import pdfplumber
from .document_001 import read_pdf_and_analyze
from .document_002 import PDFLineParser

def extract_document_title(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                if text:
                    # Split text into lines and get the first non-empty line
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    if lines:
                        first_line = lines[0]
                        key = 'DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS'
                        if key in first_line:
                            return key
                        return first_line
        return None
    except Exception as e:
        print(f"Error extracting document title: {e}")
        return None

def analyze_document_by_type(pdf_path):
    """
    Identifies document type and calls appropriate parser
    """
    try:
        title = extract_document_title(pdf_path)
        
        if title is None:
            return {
                "error": "Could not extract document title",
                "supported_types": [
                    "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS",
                    "DEMONSTRATIVO DE CÁLCULO"
                ]
            }
        
        if title == "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS":
            # Use document_001.py (coordinate parser)
            with open(pdf_path, 'rb') as pdf_file:
                result = read_pdf_and_analyze(pdf_file)
            result["document_type"] = "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS"
            return result
        
        elif "DEMONSTRATIVO DE CÁLCULO" in title:
            # Use document_002.py (line parser)
            parser = PDFLineParser()
            result = parser.parse_pdf(pdf_path)
            result["document_type"] = "DEMONSTRATIVO DE CÁLCULO"
            return result
        
        else:
            # Document not recognized
            return {
                "error": "Document type not recognized",
                "document_title": title,
                "supported_types": [
                    "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS",
                    "DEMONSTRATIVO DE CÁLCULO"
                ]
            }
    except Exception as e:
        return {
            "error": "Could not extract document title",
            "exception": str(e),
            "supported_types": [
                "DEMONSTRATIVO DE CÁLCULO DE SERVIÇOS",
                "DEMONSTRATIVO DE CÁLCULO"
            ]
        } 